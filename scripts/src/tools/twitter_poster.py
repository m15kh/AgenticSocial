from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import tweepy
import logging

logger = logging.getLogger(__name__)


class TwitterPosterInput(BaseModel):
    """Input schema for Twitter Poster"""
    message: str = Field(..., description="The message to post to Twitter/X")
    api_key: str = Field(..., description="Twitter API key")
    api_secret: str = Field(..., description="Twitter API secret")
    access_token: str = Field(..., description="Twitter access token")
    access_token_secret: str = Field(..., description="Twitter access token secret")


class TwitterPosterTool(BaseTool):
    name: str = "Twitter Poster"
    description: str = "Posts a message to Twitter/X"
    args_schema: Type[BaseModel] = TwitterPosterInput

    def _run(self, message: str, api_key: str, api_secret: str, 
             access_token: str, access_token_secret: str) -> str:
        """Post message to Twitter using API v2"""
        try:
            # Authenticate with Twitter API v2 (same as your working code)
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            # Verify credentials
            try:
                me = client.get_me()
                username = me.data.username
            except Exception as auth_error:
                return f"❌ Twitter authentication failed: {str(auth_error)}"
            
            # Twitter has a 280 character limit
            if len(message) > 280:
                # Create a thread
                tweets = self._split_into_tweets(message)
                previous_tweet_id = None
                first_tweet_id = None
                
                for i, tweet_text in enumerate(tweets):
                    if previous_tweet_id:
                        response = client.create_tweet(
                            text=tweet_text,
                            in_reply_to_tweet_id=previous_tweet_id
                        )
                    else:
                        response = client.create_tweet(text=tweet_text)
                        first_tweet_id = response.data['id']
                    
                    previous_tweet_id = response.data['id']
                
                return f"✅ Successfully posted to Twitter as a thread ({len(tweets)} tweets)! https://x.com/{username}/status/{first_tweet_id}"
            else:
                # Single tweet
                response = client.create_tweet(text=message)
                tweet_id = response.data['id']
                return f"✅ Successfully posted to Twitter! Tweet ID: {tweet_id}\nhttps://x.com/{username}/status/{tweet_id}"
                
        except Exception as e:
            error_msg = f"❌ Error posting to Twitter: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _split_into_tweets(self, text: str, max_length: int = 270) -> list:
        """Split long text into multiple tweets"""
        words = text.split()
        tweets = []
        current_tweet = ""
        
        for word in words:
            if len(current_tweet) + len(word) + 1 <= max_length:
                current_tweet += word + " "
            else:
                tweets.append(current_tweet.strip())
                current_tweet = word + " "
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        # Add tweet numbers
        total = len(tweets)
        if total > 1:
            tweets = [f"{i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]
        
        return tweets