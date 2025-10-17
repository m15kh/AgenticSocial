from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import asyncio
from telegram import Bot
from telegram.error import TelegramError

class TelegramPosterInput(BaseModel):
    """Input schema for TelegramPosterTool"""
    message: str = Field(..., description="Message to post to Telegram channel")
    bot_token: str = Field(..., description="Telegram bot token")
    channel_id: str = Field(..., description="Telegram channel ID")

class TelegramPosterTool(BaseTool):
    name: str = "Telegram Poster"
    description: str = "Posts messages to a Telegram channel"
    args_schema: Type[BaseModel] = TelegramPosterInput

    def _run(self, message: str, bot_token: str, channel_id: str) -> str:
        """Post a message to Telegram channel"""
        try:
            # Run async function in sync context
            return asyncio.run(self._post_to_telegram(message, bot_token, channel_id))
        except Exception as e:
            return f"Error posting to Telegram: {str(e)}"
    
    async def _post_to_telegram(self, message: str, bot_token: str, channel_id: str) -> str:
        """Async function to post to Telegram"""
        try:
            bot = Bot(token=bot_token)
            result = await bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode='HTML'  # Supports basic HTML formatting
            )
            return f"✅ Successfully posted to Telegram! Message ID: {result.message_id}"
        except TelegramError as e:
            return f"❌ Telegram Error: {str(e)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"