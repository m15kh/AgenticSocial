from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class LinkedInPosterInput(BaseModel):
    """Input schema for LinkedIn Poster"""
    message: str = Field(..., description="Message to post to LinkedIn")
    access_token: str = Field(..., description="LinkedIn access token")
    author_urn: str = Field(..., description="LinkedIn author URN")
    image_path: Optional[str] = Field(None, description="Optional path to image file")


class LinkedInPosterTool(BaseTool):
    name: str = "LinkedIn Poster"
    description: str = "Posts messages and images to LinkedIn"
    args_schema: Type[BaseModel] = LinkedInPosterInput

    def _run(self, message: str, access_token: str, author_urn: str, image_path: Optional[str] = None) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202502",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }

            payload = {
                "author": author_urn,
                "commentary": message,
                "visibility": "PUBLIC",
                "distribution": {"feedDistribution": "MAIN_FEED"},
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }

            # Handle image upload if provided
            if image_path:
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

            # Create post
            response = requests.post(
                "https://api.linkedin.com/rest/posts",
                headers=headers,
                json=payload
            )

            if response.status_code == 201:
                return "✅ Successfully posted to LinkedIn!"
            else:
                error_text = response.text
                logger.error(f"LinkedIn API error: {error_text}")
                return f"❌ LinkedIn API error: {error_text}"

        except Exception as e:
            error_msg = f"❌ Error posting to LinkedIn: {str(e)}"
            logger.error(error_msg)
            return error_msg