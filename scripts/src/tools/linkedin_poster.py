from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import requests
import logging
from SmartAITool.core import cprint , bprint
from datetime import datetime
import os

# Create logs directory if it doesn't exist
logs_dir = "/home/rteam2/m15kh/AgenticSocial/logs"
os.makedirs(logs_dir, exist_ok=True)

# Setup logging with timestamp
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
debug_file = os.path.join(logs_dir, f"linkedin_debug_{current_time}.log")

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for debug logs
file_handler = logging.FileHandler(debug_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class LinkedInPosterInput(BaseModel):
    """Input schema for LinkedIn Poster"""
    message: str = Field(..., description="Message to post to LinkedIn")
    access_token: str = Field(..., description="LinkedIn access token")
    author_urn: str = Field(..., description="LinkedIn author URN")
    image_path: Optional[str] = Field(None, description="Optional path to image file")


class LinkedInPosterTool(BaseTool):
    
    name: str = "LinkedIn Poster"
    description: str = "Posts messages and link to LinkedIn"
    args_schema: Type[BaseModel] = LinkedInPosterInput

    def _run(self, message: str, access_token: str, author_urn: str, image_path: Optional[str] = None) -> str:
        logger.debug(f"Starting LinkedIn post operation")
        logger.debug(f"Message length: {len(message)}")
        logger.debug(f"Author URN: {author_urn}")
        logger.debug(f"Image path provided: {image_path is not None}")
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202502",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            
            logger.debug("Headers prepared for API request")
            
            payload = {
            "author": author_urn,
            "commentary": message,
            "visibility": "PUBLIC",
            "distribution": { "feedDistribution": "MAIN_FEED" },
            "content": {
                "article": {
                "source": "https://huggingface.co/blog/vlms-2025",
                "title": "Vision-Language Models in 2025: Trends and Benchmarks",
                "description": "A concise overview of VLM capabilities, eval suites, and open challenges."
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
            }
            
            logger.debug("Payload prepared for API request")
            logger.debug(f"Payload content: {payload}")

            if image_path:
                logger.debug(f"Attempting to upload image: {image_path}")
                # Initialize upload
                init_response = requests.post(
                    "https://api.linkedin.com/rest/images?action=initializeUpload",
                    headers=headers,
                    json={"initializeUploadRequest": {"owner": author_urn}}
                )
                if init_response.status_code != 200:
                    raise Exception(f"Failed to initialize image upload: {init_response.text}")

                upload_data = init_response.json()
                upload_url = upload_data["value"]["uploadUrl"]
                image_urn = upload_data["value"]["image"]

                # Upload image
                with open(image_path, "rb") as f:
                    upload_response = requests.put(upload_url, data=f, headers={"Content-Type": "image/png"})
                if upload_response.status_code != 201:
                    raise Exception(f"Failed to upload image: {upload_response.text}")

                # Add image to payload
                payload["content"] = {"media": {"id": image_urn}}
                logger.debug("Image upload completed")

            logger.debug("Sending post request to LinkedIn API")
            response = requests.post(
                "https://api.linkedin.com/rest/posts",
                headers=headers,
                json=payload
            )
            
            logger.debug(f"LinkedIn API response status: {response.status_code}")
            logger.debug(f"LinkedIn API response: {response.text}")

            if response.status_code == 201:
                logger.info("Post successfully created on LinkedIn")
                return "✅ Successfully posted to LinkedIn!"
            else:
                error_text = response.text
                logger.error(f"LinkedIn API error: {error_text}")
                return f"❌ LinkedIn API error: {error_text}"

        except Exception as e:
            error_msg = f"❌ Error posting to LinkedIn: {str(e)}"
            logger.exception("Detailed error information:")
            return error_msg