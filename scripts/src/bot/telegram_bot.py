from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import logging
import os
import sys

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.src.config.loader import load_config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load config
config = load_config()
API_URL = config.get('api', {}).get('url', 'http://localhost:8080')

# Store user preferences temporarily (in production, use a database)
user_preferences = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with instructions"""
    welcome_message = """
👋 Welcome to Social Media Bot!

I can help you post content to multiple platforms:
- 🔵 Telegram
- 🐦 Twitter/X
- 💼 LinkedIn

📝 How to use:
1. Send me a URL or text with/without image
2. Choose which platform(s) to post to
3. I'll create and post engaging content!

Commands:
/start - Show this message
/help - Get help
/settings - Change default platforms
"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
🤖 Bot Commands:

/start - Welcome message
/help - This help message
/settings - Set default platforms

📤 How to post:
- Send a URL - I'll fetch and summarize it
- Send text - I'll enhance it
- Send text + image - I'll post with image
- Choose platforms using buttons

🎯 Platform Options:
- 🔵 Telegram only
- 🐦 Twitter/X only
- 💼 LinkedIn only
- 🌐 All platforms
"""
    await update.message.reply_text(help_text)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Let user choose default platforms"""
    keyboard = [
        [InlineKeyboardButton("🔵 Telegram", callback_data='default_telegram')],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data='default_twitter')],
        [InlineKeyboardButton("💼 LinkedIn", callback_data='default_linkedin')],
        [InlineKeyboardButton("🌐 All Platforms", callback_data='default_all')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ Choose your default platform:",
        reply_markup=reply_markup
    )


def get_platform_selection_keyboard():
    """Create inline keyboard for platform selection"""
    keyboard = [
        [InlineKeyboardButton("🔵 Telegram", callback_data='platform_telegram')],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data='platform_twitter')],
        [InlineKeyboardButton("💼 LinkedIn", callback_data='platform_linkedin')],
        [InlineKeyboardButton("🌐 All Platforms", callback_data='platform_all')],
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages (text, URL, or image)"""
    message = update.message
    user_id = message.from_user.id
    
    # Check if message contains URL or text
    text = message.text or message.caption or ""
    
    # Determine content type
    has_url = 'http' in text.lower()
    has_image = bool(message.photo)
    
    # Store message data for later use
    context.user_data['pending_content'] = {
        'text': text,
        'type': 'url' if has_url else 'text',
        'has_image': has_image,
        'image_file_id': message.photo[-1].file_id if has_image else None
    }
    
    # Ask user to select platform
    await message.reply_text(
        "📤 Where would you like to post this?",
        reply_markup=get_platform_selection_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # Handle default platform settings
    if callback_data.startswith('default_'):
        platform = callback_data.replace('default_', '')
        user_preferences[user_id] = platform
        
        platform_names = {
            'telegram': '🔵 Telegram',
            'twitter': '🐦 Twitter/X',
            'linkedin': '💼 LinkedIn',
            'all': '🌐 All Platforms'
        }
        
        await query.edit_message_text(
            f"✅ Default platform set to: {platform_names.get(platform, 'All')}"
        )
        return
    
    # Handle platform selection for posting
    if callback_data.startswith('platform_'):
        platform = callback_data.replace('platform_', '')
        
        # Get pending content
        pending = context.user_data.get('pending_content')
        if not pending:
            await query.edit_message_text("❌ No content to post. Please send a message first.")
            return
        
        await query.edit_message_text("⏳ Processing your content...")
        
        # Determine which platforms to enable
        platforms = {
            'telegram': platform in ['telegram', 'all'],
            'twitter': platform in ['twitter', 'all'],
            'linkedin': platform in ['linkedin', 'all']
        }
        
        try:
            # Download image if present
            image_path = None
            if pending.get('has_image') and pending.get('image_file_id'):
                file = await context.bot.get_file(pending['image_file_id'])
                os.makedirs('/tmp/telegram_images', exist_ok=True)
                image_path = f"/tmp/telegram_images/image_{user_id}_{query.message.message_id}.jpg"
                await file.download_to_drive(image_path)
                logger.info(f"Downloaded image to: {image_path}")
            
            # Process based on content type
            if pending['type'] == 'url':
                # Send URL to processing API
                logger.info(f"Sending URL to API: {pending['text']}")
                response = requests.post(
                    f"{API_URL}/predict",
                    json={
                        "url": pending['text'],
                        "platforms": platforms
                    },
                    timeout=300
                )
            else:
                # Send text for enhancement
                logger.info(f"Sending text to enhancement API")
                response = requests.post(
                    f"{API_URL}/enhance",
                    json={
                        "text": pending['text'],
                        "platforms": platforms,
                        "image_path": image_path
                    },
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format success message
                platform_names = []
                if platforms['telegram']:
                    platform_names.append('🔵 Telegram')
                if platforms['twitter']:
                    platform_names.append('🐦 Twitter/X')
                if platforms['linkedin']:
                    platform_names.append('💼 LinkedIn')
                
                platforms_str = ', '.join(platform_names)
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"✅ Successfully posted to: {platforms_str}!"
                )
            else:
                error_text = response.text[:500]  # Limit error length
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"❌ Error: {error_text}"
                )
        
        except requests.exceptions.Timeout:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Request timeout. The server took too long to respond."
            )
        except requests.exceptions.ConnectionError:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Connection error. Make sure the API server is running."
            )
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Error processing content: {str(e)}"
            )
        
        # Clear pending content
        context.user_data['pending_content'] = None


def main():
    """Start the bot"""
    # Get bot token from config
    token = config['telegram']['bot_token']
    
    logger.info(f"🤖 Starting bot with token: {token[:10]}...")
    logger.info(f"📡 API URL: {API_URL}")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    logger.info("✅ Bot is ready! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()