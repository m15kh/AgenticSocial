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
3. Your request will be queued and processed at 23:00

Commands:
/start - Show this message
/help - Get help
/settings - Change default platforms
/queue - Check queue status
"""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
    
    help_text = f"""
🤖 Bot Commands:

/start - Welcome message
/help - This help message
/settings - Set default platforms
/queue - Check queue status
/processall - Process all queued requests NOW

📤 How it works:
- Send URLs or text - added to queue (unlimited!)
- Choose platforms using buttons
- ALL requests processed daily at {scheduled_time}
- Or use /processall to process immediately

🎯 Platform Options:
- 🔵 Telegram only
- 🐦 Twitter/X only
- 💼 LinkedIn only
- 🌐 All platforms

⏰ Processing Schedule:
Queue is unlimited. All requests processed at {scheduled_time} daily
"""
    await update.message.reply_text(help_text)


async def process_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process all queued requests immediately"""
    
    user_id = update.message.from_user.id
    
    # Optional: Add admin check
    # ADMIN_IDS = [123456789]  # Replace with your Telegram user ID
    # if user_id not in ADMIN_IDS:
    #     await update.message.reply_text("❌ Only admins can use this command")
    #     return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Process All", callback_data='admin_process_all'),
            InlineKeyboardButton("❌ Cancel", callback_data='admin_cancel')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get queue status first
    try:
        response = requests.get(f"{API_URL}/queue/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            pending = data.get('pending', 0)
            
            if pending == 0:
                await update.message.reply_text("📭 Queue is empty! No requests to process.")
                return
            
            await update.message.reply_text(
                f"⚠️ Process All Queued Requests?\n\n"
                f"📊 Pending requests: {pending}\n"
                f"⏰ This will process ALL requests immediately\n"
                f"⏱️  Estimated time: {pending * 2} minutes\n\n"
                f"Are you sure?",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ Could not get queue status")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # Handle admin process all
    if callback_data == 'admin_process_all':
        await query.edit_message_text("⏳ Processing all requests... This may take several minutes.\n\nYou can close this chat and I'll notify you when done.")
        
        try:
            # Get count before processing
            response_before = requests.get(f"{API_URL}/queue/status", timeout=10)
            pending_before = 0
            if response_before.status_code == 200:
                pending_before = response_before.json().get('pending', 0)
            
            # Process all
            response = requests.post(f"{API_URL}/process/all", timeout=3600)  # 1 hour timeout
            
            if response.status_code == 200:
                result = response.json()
                processed = result.get('processed', 0)
                failed = result.get('failed', 0)
                
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"✅ Processing Complete!\n\n"
                         f"📊 Results:\n"
                         f"   • Total in queue: {pending_before}\n"
                         f"   • ✅ Processed: {processed}\n"
                         f"   • ❌ Failed: {failed}\n\n"
                         f"🎉 Queue is now cleared!"
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"❌ Error: {response.text}"
                )
        except requests.exceptions.Timeout:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="⏰ Processing is taking longer than expected.\n\nCheck /queue status or server logs."
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Error: {str(e)}"
            )
        return
    
    if callback_data == 'admin_cancel':
        await query.edit_message_text("❌ Cancelled")
        return
    
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
        
        await query.edit_message_text("⏳ Adding to queue...")
        
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
                    timeout=30
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
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Should always be queued
                if result.get("status") == "queued":
                    position = result.get("position", "?")
                    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
                    
                    # Format platform names for display
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
                        text=f"📥 Request queued!\n\n"
                             f"📍 Position: {position}\n"
                             f"🎯 Platforms: {platforms_str}\n"
                             f"⏰ Will be processed at: {scheduled_time}\n\n"
                             f"💡 Use /queue to check status\n"
                             f"⚡ Use /processall to process all now"
                    )
                else:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"✅ Request added: {result.get('message', 'Success')}"
                    )
            else:
                error_text = response.text[:500]
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
                text="❌ Connection error.\n\nMake sure the API server is running:\n"
                     "python3 scripts/src/server_queued.py"
            )
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Error processing content: {str(e)}"
            )
        
        # Clear pending content
        context.user_data['pending_content'] = None




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


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check queue status"""
    try:
        response = requests.get(f"{API_URL}/queue/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
                f"📊 Queue Status\n\n"
                f"📥 Pending: {data.get('pending', 0)}/5\n"
                f"✅ Available slots: {data.get('available_slots', 5)}\n"
                f"⏰ Next processing: {data.get('next_processing', '23:00')}\n\n"
                f"Send me a URL or text to add to the queue!"
            )
        else:
            await update.message.reply_text("❌ Could not get queue status. Is the server running?")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text(
            "❌ Cannot connect to server.\n\n"
            "Make sure the API server is running:\n"
            "python3 scripts/src/server_queued.py"
        )
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


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
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    logger.info("✅ Bot is ready! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Start the bot"""
    token = config['telegram']['bot_token']
    
    logger.info(f"🤖 Starting bot with token: {token[:10]}...")
    logger.info(f"📡 API URL: {API_URL}")
    
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CommandHandler("processall", process_all_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("✅ Bot is ready! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()