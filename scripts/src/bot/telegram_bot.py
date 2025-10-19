import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import logging
import tempfile
import os

from config.loader import load_config
from utils.logger import setup_logger

logger = setup_logger('TelegramBot')


class ContentBot:
    def __init__(self):
        self.config = load_config()
        self.api_url = f"http://{self.config['server']['host']}:{self.config['server']['port']}/predict"
        self.enhance_url = f"http://{self.config['server']['host']}:{self.config['server']['port']}/enhance"
        self.bot_token = self.config['telegram']['bot_token']
        self.pending_posts = {}  # Store pending posts for confirmation
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        await update.message.reply_text(
            "👋 Hi! I can help you in three ways:\n\n"
            "🔗 <b>Option 1: Auto-post from URL</b>\n"
            "Send me any article URL and I'll summarize and post it automatically.\n\n"
            "✍️ <b>Option 2: Text-only post</b>\n"
            "Send me text and I'll:\n"
            "• Fix typos and grammar\n"
            "• Add formatting and details\n"
            "• Ask for confirmation\n"
            "• Post as text message\n\n"
            "📸 <b>Option 3: Photo + text post</b>\n"
            "Send me a photo with caption and I'll:\n"
            "• Enhance your caption\n"
            "• Ask for confirmation\n"
            "• Post with the image\n\n"
            "Try any of these now!",
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        await update.message.reply_text(
            "📚 <b>How to use:</b>\n\n"
            "<b>For URL auto-posting:</b>\n"
            "1. Send any article URL\n"
            "2. I'll process and post automatically\n\n"
            "<b>For text-only posts:</b>\n"
            "1. Send regular text\n"
            "2. I'll enhance it\n"
            "3. Review and confirm\n"
            "4. I'll post as text\n\n"
            "<b>For photo posts:</b>\n"
            "1. Send a photo with caption\n"
            "2. I'll enhance the caption\n"
            "3. Review and confirm\n"
            "4. I'll post with image\n\n"
            "Easy! ✨",
            parse_mode='HTML'
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - either URLs or text to enhance"""
        text = update.message.text.strip()
        
        # Check if it's a URL
        if text.startswith(('http://', 'https://')):
            await self.handle_url_processing(update, context, text)
        else:
            # It's regular text to enhance
            await self.handle_text_enhancement(update, context, text)
    
    async def handle_url_processing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Process URL and post automatically"""
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔄 Processing URL...\n\n"
            f"<code>{url}</code>\n"
            f"This might take 30-60 seconds...",
            parse_mode='HTML'
        )
        
        try:
            # Call your API
            response = requests.post(
                self.api_url,
                json={"url": url},
                timeout=120
            )
            
            if response.status_code == 200:
                await processing_msg.edit_text(
                    f"✅ <b>Success!</b>\n\n"
                    f"URL: <code>{url}</code>\n"
                    f"Content has been posted to the channel! 🎉",
                    parse_mode='HTML'
                )
            else:
                await processing_msg.edit_text(
                    f"❌ <b>Error:</b> {response.status_code}\n\n"
                    f"Something went wrong. Please try again.",
                    parse_mode='HTML'
                )
                
        except requests.exceptions.Timeout:
            await processing_msg.edit_text("⏱️ Request timed out. The URL might be too slow to load.")
        except Exception as e:
            logger.error(f"Error processing URL: {str(e)}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    async def handle_text_enhancement(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Enhance regular text and ask for confirmation"""
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🤖 Enhancing your text with AI...\n"
            "Fixing typos, adding details, formatting..."
        )
        
        try:
            # Enhance the text using your LLM
            enhanced_text = await self.enhance_text(text)
            
            # Check length
            char_count = len(enhanced_text)
            length_status = "✅" if char_count <= 4096 else "⚠️"  # Telegram text message limit
            
            # Store the pending post
            post_id = f"{update.effective_user.id}_{update.message.message_id}"
            self.pending_posts[post_id] = {
                'photo_path': None,  # No photo for text-only
                'original_text': text,
                'enhanced_text': enhanced_text,
                'user_id': update.effective_user.id,
                'type': 'text_only'  # Mark as text-only post
            }
            
            # Show preview with confirmation buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm & Post", callback_data=f"confirm_{post_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{post_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Truncate preview if too long
            preview_enhanced = enhanced_text[:800] + "..." if len(enhanced_text) > 800 else enhanced_text
            
            # Send preview
            preview_text = (
                f"📝 <b>Original:</b>\n"
                f"<code>{text[:150]}{'...' if len(text) > 150 else ''}</code>\n\n"
                f"✨ <b>Enhanced:</b>\n"
                f"{length_status} Length: {char_count} characters\n\n"
                f"{preview_enhanced}\n\n"
                f"👆 Review and confirm to post to the channel!"
            )
            
            await update.message.reply_text(
                text=preview_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"Error enhancing text: {str(e)}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages with captions"""
        caption = update.message.caption or ""
        
        if not caption.strip():
            await update.message.reply_text(
                "⚠️ Please add a caption to your image describing what you want to post!"
            )
            return
        
        # Download the photo
        photo = update.message.photo[-1]  # Get highest resolution
        photo_file = await photo.get_file()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            await photo_file.download_to_drive(tmp.name)
            photo_path = tmp.name
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🤖 Enhancing your text with AI...\n"
            "Fixing typos, adding details, formatting..."
        )
        
        try:
            # Enhance the text using your LLM
            enhanced_text = await self.enhance_text(caption)
            
            # Check length
            char_count = len(enhanced_text)
            length_status = "✅" if char_count <= 1024 else "⚠️"
            
            # Store the pending post
            post_id = f"{update.effective_user.id}_{update.message.message_id}"
            self.pending_posts[post_id] = {
                'photo_path': photo_path,
                'original_text': caption,
                'enhanced_text': enhanced_text,
                'user_id': update.effective_user.id,
                'type': 'photo'  # Mark as photo post
            }
            
            # Show preview with confirmation buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm & Post", callback_data=f"confirm_{post_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{post_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Truncate preview if too long
            preview_enhanced = enhanced_text[:800] + "..." if len(enhanced_text) > 800 else enhanced_text
            
            # Send preview
            preview_text = (
                f"✨ <b>Enhanced:</b>\n"
                f"{length_status} Length: {char_count}/1024 characters\n\n"
                f"{preview_enhanced}\n\n"
                f"👆 Review and confirm to post!"
            )
            
            # Send photo with preview
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(photo_path, 'rb'),
                caption=preview_text[:1024],  # Ensure preview itself fits
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"Error enhancing text: {str(e)}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
            # Clean up temp file
            if os.path.exists(photo_path):
                os.remove(photo_path)
    
    async def enhance_text(self, text: str) -> str:
        """Enhance text using LLM API"""
        try:
            response = requests.post(
                self.enhance_url,
                json={"text": text},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('enhanced_text', text)
            else:
                logger.error(f"Enhancement API error: {response.status_code}")
                return text
                
        except Exception as e:
            logger.error(f"Error calling enhancement API: {str(e)}")
            return text
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        action, post_id = query.data.split('_', 1)
        
        if post_id not in self.pending_posts:
            try:
                await query.message.edit_text("⚠️ This post has expired. Please send it again.")
            except:
                await query.edit_message_caption(
                    caption="⚠️ This post has expired. Please send it again.",
                    reply_markup=None
                )
            return
        
        post_data = self.pending_posts[post_id]
        post_type = post_data.get('type', 'photo')
        
        if action == "confirm":
            # Post to channel
            try:
                if post_type == 'text_only':
                    await query.message.edit_text("📤 Posting to channel...")
                else:
                    await query.edit_message_caption(caption="📤 Posting to channel...", reply_markup=None)
            except:
                pass
            
            try:
                enhanced_text = post_data['enhanced_text']
                
                if post_type == 'text_only':
                    # Post text only (no photo)
                    if len(enhanced_text) > 4096:
                        # Split into multiple messages if too long
                        chunks = [enhanced_text[i:i+4096] for i in range(0, len(enhanced_text), 4096)]
                        for chunk in chunks:
                            await context.bot.send_message(
                                chat_id=self.config['telegram']['channel_id'],
                                text=chunk,
                                parse_mode='MarkdownV2',  # Changed from HTML to MarkdownV2
                                disable_web_page_preview=False
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=self.config['telegram']['channel_id'],
                            text=enhanced_text,
                            parse_mode='HTML',
                            disable_web_page_preview=False
                        )
                    
                    await query.message.edit_text(
                        f"✅ <b>Posted successfully!</b>\n\n{enhanced_text[:200]}...",
                        parse_mode='HTML'
                    )
                
                else:  # photo post
                    if len(enhanced_text) > 1024:
                        # Send photo first, then text as separate message
                        await context.bot.send_photo(
                            chat_id=self.config['telegram']['channel_id'],
                            photo=open(post_data['photo_path'], 'rb'),
                            caption="📝 See caption below:"
                        )
                        await context.bot.send_message(
                            chat_id=self.config['telegram']['channel_id'],
                            text=enhanced_text,
                            parse_mode='HTML',
                            disable_web_page_preview=True
                        )
                        await query.edit_message_caption(
                            caption=f"✅ <b>Posted successfully!</b>\n\n(Photo + text sent separately due to length)",
                            reply_markup=None,
                            parse_mode='HTML'
                        )
                    else:
                        # Caption fits, send normally
                        await context.bot.send_photo(
                            chat_id=self.config['telegram']['channel_id'],
                            photo=open(post_data['photo_path'], 'rb'),
                            caption=enhanced_text,
                            parse_mode='HTML'
                        )
                        await query.edit_message_caption(
                            caption=f"✅ <b>Posted successfully!</b>",
                            reply_markup=None,
                            parse_mode='HTML'
                        )
                
            except Exception as e:
                logger.error(f"Error posting to channel: {str(e)}")
                error_msg = f"❌ Error posting to channel: {str(e)}"
                try:
                    if post_type == 'text_only':
                        await query.message.edit_text(error_msg)
                    else:
                        await query.edit_message_caption(caption=error_msg, reply_markup=None)
                except:
                    pass
            
            # Clean up
            if post_data.get('photo_path') and os.path.exists(post_data['photo_path']):
                os.remove(post_data['photo_path'])
            del self.pending_posts[post_id]
            
        elif action == "cancel":
            cancel_msg = "❌ Post cancelled."
            try:
                if post_type == 'text_only':
                    await query.message.edit_text(cancel_msg)
                else:
                    await query.edit_message_caption(caption=cancel_msg, reply_markup=None)
            except:
                pass
            
            # Clean up
            if post_data.get('photo_path') and os.path.exists(post_data['photo_path']):
                os.remove(post_data['photo_path'])
            del self.pending_posts[post_id]
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Run bot
        logger.info("Bot is running! Send URLs, text, or photos to process.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = ContentBot()
    bot.run()