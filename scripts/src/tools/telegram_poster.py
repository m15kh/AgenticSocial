from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
import logging

logger = logging.getLogger(__name__)


class TelegramPosterInput(BaseModel):
    """Input schema for Telegram Poster"""
    message: str = Field(..., description="Message to post to Telegram channel")
    bot_token: str = Field(..., description="Telegram bot token")
    channel_id: str = Field(..., description="Telegram channel ID")


class TelegramPosterTool(BaseTool):
    name: str = "Telegram Poster"
    description: str = "Posts messages to a Telegram channel"
    args_schema: Type[BaseModel] = TelegramPosterInput

    def _run(self, message: str, bot_token: str, channel_id: str) -> str:
        """
        Post message to Telegram using synchronous requests
        
        This method is completely synchronous - no async/await needed
        """
        try:
            # Build Telegram API URL
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            # Prepare payload
            payload = {
                "chat_id": channel_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            
            # Send request (synchronous)
            response = requests.post(url, json=payload, timeout=10)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    message_id = result['result']['message_id']
                    return f"✅ Successfully posted to Telegram! Message ID: {message_id}"
                else:
                    error_description = result.get('description', 'Unknown error')
                    logger.error(f"Telegram API error: {error_description}")
                    return f"❌ Telegram API error: {error_description}"
            else:
                error_text = response.text
                logger.error(f"HTTP Error {response.status_code}: {error_text}")
                return f"❌ HTTP Error {response.status_code}: {error_text}"
                
        except requests.exceptions.Timeout:
            error_msg = "❌ Telegram request timed out (10s limit)"
            logger.error(error_msg)
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Network error posting to Telegram: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error posting to Telegram: {str(e)}"
            logger.error(error_msg)
            return error_msg