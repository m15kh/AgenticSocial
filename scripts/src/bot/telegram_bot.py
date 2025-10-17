import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import logging

# Use local imports
from config.loader import load_config
from utils.logger import setup_logger

logger = setup_logger('TelegramBot')

class ContentBot:
    def __init__(self):
        self.config = load_config()
        self.api_url = f"http://{self.config['server']['host']}:{self.config['server']['port']}/predict"
        self.bot_token = self.config['telegram']['bot_token']
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        await update.message.reply_text(
            "👋 Hi! Send me any article URL and I'll summarize it and post to the channel!\n\n"
            "Just paste a URL like:\n"
            "https://huggingface.co/blog/rlhf"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        await update.message.reply_text(
            "📚 How to use:\n\n"
            "1. Send me any article URL\n"
            "2. I'll scrape and summarize it\n"
            "3. I'll post it to the channel automatically\n\n"
            "That's it! ✨"
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming URLs"""
        url = update.message.text.strip()
        
        # Check if it's a valid URL
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("⚠️ Please send a valid URL starting with http:// or https://")
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔄 Processing...\n\n"
            f"URL: {url}\n"
            f"This might take 30-60 seconds..."
        )
        
        try:
            # Call your API
            response = requests.post(
                self.api_url,
                json={"url": url},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                await processing_msg.edit_text(
                    f"✅ Success!\n\n"
                    f"URL: {url}\n"
                    f"Content has been posted to the channel! 🎉"
                )
            else:
                await processing_msg.edit_text(
                    f"❌ Error: {response.status_code}\n\n"
                    f"Something went wrong. Please try again."
                )
                
        except requests.exceptions.Timeout:
            await processing_msg.edit_text(
                "⏱️ Request timed out. The URL might be too slow to load."
            )
        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            await processing_msg.edit_text(
                f"❌ Error: {str(e)}\n\n"
                f"Please try again or contact support."
            )
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url))
        
        # Run bot
        logger.info("Bot is running! Send URLs to process.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = ContentBot()
    bot.run()