from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import requests
import logging
from datetime import datetime
import os
import re

# Create logs directory if it doesn't exist
logs_dir = "/home/ubuntu7/m15kh/own/AgenticSocial/logs"
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


def clean_linkedin_text(text: str) -> str:
    """
    Clean text for LinkedIn by replacing problematic characters and formats
    
    Rules applied:
    1. Replace (ABC) with [ABC] - parentheses to square brackets
    2. Remove markdown bold **text** -> text
    3. Remove markdown italic *text* -> text
    4. Remove markdown headers # -> nothing
    5. Clean up multiple spaces
    6. Remove markdown links [text](url) -> text url
    """
    
    logger.debug(f"Original text length: {len(text)}")
    logger.debug(f"Original text preview: {text[:200]}")
    
    # 1. CRITICAL: Replace parentheses with square brackets
    # Matches: (ABC) or (Some Text) and replaces with [ABC] or [Some Text]
    text = re.sub(r'\(([^)]+)\)', r'[\1]', text)
    logger.debug("Applied parentheses replacement")
    
    # 2. Remove markdown bold **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    logger.debug("Removed markdown bold")
    
    # 3. Remove markdown italic *text* (but not asterisks in bullet points)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)
    logger.debug("Removed markdown italic")
    
    # 4. Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    logger.debug("Removed markdown headers")
    
    # 5. Remove markdown links [text](url) -> text url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)
    logger.debug("Removed markdown links")
    
    # 6. Clean up multiple spaces (but preserve intentional line breaks)
    text = re.sub(r' +', ' ', text)
    logger.debug("Cleaned up multiple spaces")
    
    # 7. Clean up multiple newlines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    logger.debug("Cleaned up multiple newlines")
    
    logger.debug(f"Cleaned text length: {len(text)}")
    logger.debug(f"Cleaned text preview: {text[:200]}")
    
    return text.strip()


class LinkedInPosterInput(BaseModel):
    """Input schema for LinkedIn Poster"""
    message: str = Field(..., description="Plain text message to post (NO markdown)")
    access_token: str = Field(..., description="LinkedIn access token")
    author_urn: str = Field(..., description="LinkedIn author URN")
    source_url: str = Field(..., description="Source URL of the article")
    article_title: Optional[str] = Field(None, description="Title of the article")
    article_description: Optional[str] = Field(None, description="Description of the article")
    image_path: Optional[str] = Field(None, description="Optional path to image file")


class LinkedInPosterTool(BaseTool):
    
    name: str = "LinkedIn Poster"
    description: str = "Posts plain text messages with article links to LinkedIn"
    args_schema: Type[BaseModel] = LinkedInPosterInput

    def _run(
        self, 
        message: str, 
        access_token: str, 
        author_urn: str, 
        source_url: str,
        article_title: Optional[str] = None,
        article_description: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> str:
        logger.debug(f"=" * 80)
        logger.debug(f"Starting LinkedIn post operation")
        logger.debug(f"Author URN: {author_urn}")
        logger.debug(f"Source URL: {source_url}")
        logger.debug(f"Article title (before clean): {article_title}")
        logger.debug(f"Image path provided: {image_path is not None}")
        logger.debug(f"=" * 80)
        
        try:
            # CRITICAL: Clean the message text BEFORE posting
            logger.debug("=" * 80)
            logger.debug("CLEANING MESSAGE TEXT")
            logger.debug("=" * 80)
            logger.debug(f"Message BEFORE cleaning:\n{message}\n")
            
            cleaned_message = clean_linkedin_text(message)
            
            logger.debug(f"\nMessage AFTER cleaning:\n{cleaned_message}\n")
            logger.debug("=" * 80)
            
            # Also clean the article title
            if article_title:
                logger.debug(f"Article title BEFORE cleaning: {article_title}")
                cleaned_title = clean_linkedin_text(article_title)
                logger.debug(f"Article title AFTER cleaning: {cleaned_title}")
            else:
                cleaned_title = "Article"
            
            # Clean article description
            if article_description:
                cleaned_description = clean_linkedin_text(article_description)
            else:
                cleaned_description = "Read more at the source"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "LinkedIn-Version": "202502",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            
            logger.debug("Headers prepared for API request")
            
            # Build payload dynamically
            payload = {
                "author": author_urn,
                "commentary": cleaned_message,  # USE CLEANED MESSAGE
                "visibility": "PUBLIC",
                "distribution": {"feedDistribution": "MAIN_FEED"},
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            
            # Add article content if URL is provided
            if source_url:
                payload["content"] = {
                    "article": {
                        "source": source_url,
                        "title": cleaned_title,  # USE CLEANED TITLE
                        "description": cleaned_description  # USE CLEANED DESCRIPTION
                    }
                }
                logger.debug(f"Article content added with cleaned data")
            
            logger.debug("Payload prepared for API request")
            logger.debug(f"Full payload: {payload}")

            # Handle image upload if provided
            if image_path:
                logger.debug(f"Attempting to upload image: {image_path}")
                
                # Initialize upload
                init_response = requests.post(
                    "https://api.linkedin.com/rest/images?action=initializeUpload",
                    headers=headers,
                    json={"initializeUploadRequest": {"owner": author_urn}}
                )
                
                logger.debug(f"Image init response: {init_response.status_code}")
                
                if init_response.status_code != 200:
                    raise Exception(f"Failed to initialize image upload: {init_response.text}")

                upload_data = init_response.json()
                upload_url = upload_data["value"]["uploadUrl"]
                image_urn = upload_data["value"]["image"]

                # Upload image
                with open(image_path, "rb") as f:
                    upload_response = requests.put(
                        upload_url, 
                        data=f, 
                        headers={"Content-Type": "image/png"}
                    )
                
                logger.debug(f"Image upload response: {upload_response.status_code}")
                
                if upload_response.status_code != 201:
                    raise Exception(f"Failed to upload image: {upload_response.text}")

                # Replace article with image (images and articles are mutually exclusive)
                payload["content"] = {"media": {"id": image_urn}}
                logger.debug("Image upload completed, replaced article content with image")

            logger.debug("Sending post request to LinkedIn API")
            response = requests.post(
                "https://api.linkedin.com/rest/posts",
                headers=headers,
                json=payload
            )
            
            logger.debug(f"LinkedIn API response status: {response.status_code}")
            logger.debug(f"LinkedIn API response: {response.text[:500]}")

            if response.status_code == 201:
                logger.info("Post successfully created on LinkedIn")
                return "✅ Successfully posted to LinkedIn!"
            elif response.status_code == 422:
                # Handle duplicate posts gracefully
                error_data = response.json()
                if "DUPLICATE_POST" in str(error_data):
                    logger.warning("Duplicate post detected")
                    return "⚠️ Skipped: LinkedIn detected duplicate content (already posted recently)"
                else:
                    logger.error(f"LinkedIn API error: {response.text}")
                    return f"❌ LinkedIn API error: {response.text}"
            else:
                error_text = response.text
                logger.error(f"LinkedIn API error: {error_text}")
                return f"❌ LinkedIn API error: {error_text}"

        except Exception as e:
            error_msg = f"❌ Error posting to LinkedIn: {str(e)}"
            logger.exception("Detailed error information:")
            return error_msg