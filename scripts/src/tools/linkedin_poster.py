from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
import logging

logger = logging.getLogger(__name__)


class LinkedInPosterInput(BaseModel):
    """Input schema for LinkedIn Poster"""
    message: str = Field(..., description="Message to post to LinkedIn")
    access_token: str = Field(..., description="LinkedIn access token")
    author_urn: str = Field(..., description="LinkedIn author URN (organization or person ID)")


class LinkedInPosterTool(BaseTool):
    name: str = "LinkedIn Poster"
    description: str = "Posts messages to LinkedIn"
    args_schema: Type[BaseModel] = LinkedInPosterInput

    def _run(self, message: str, access_token: str, author_urn: str) -> str:
        """
        Post message to LinkedIn using API v2
        
        Args:
            message: Text to post
            access_token: OAuth2 access token
            author_urn: LinkedIn URN (e.g., "urn:li:person:ABC123" or "urn:li:organization:123456")
        """
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn API payload
            payload = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": message
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Send request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get('id', 'unknown')
                return f"✅ Successfully posted to LinkedIn! Post ID: {post_id}"
            else:
                error_text = response.text
                logger.error(f"LinkedIn API error {response.status_code}: {error_text}")
                return f"❌ LinkedIn error {response.status_code}: {error_text}"
                
        except requests.exceptions.Timeout:
            error_msg = "❌ LinkedIn request timed out"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error posting to LinkedIn: {str(e)}"
            logger.error(error_msg)
            return error_msg