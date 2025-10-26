from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import tweepy
import logging
import re

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
            # Authenticate with Twitter API v2
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
                # Create a thread - KEEP HASHTAGS IN FIRST TWEET
                tweets = self._split_into_tweets_smart(message)
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
    
    def _split_into_tweets_smart(self, text: str, max_length: int = 270) -> list:
        """
        Smart split that keeps hashtags and URLs in the first tweet
        """
        # Extract hashtags and URLs
        hashtags = re.findall(r'#\w+', text)
        urls = re.findall(r'https?://[^\s]+', text)
        
        # Remove hashtags and URLs temporarily for splitting
        text_without_special = text
        for hashtag in hashtags:
            text_without_special = text_without_special.replace(hashtag, '')
        for url in urls:
            text_without_special = text_without_special.replace(url, '')
        
        # Clean up extra spaces
        text_without_special = ' '.join(text_without_special.split())
        
        # Split main content
        words = text_without_special.split()
        tweets = []
        current_tweet = ""
        
        for word in words:
            if len(current_tweet) + len(word) + 1 <= max_length - 50:  # Leave room for hashtags/URLs
                current_tweet += word + " "
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = word + " "
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        # Add hashtags and URLs ONLY to the first tweet
        if tweets:
            first_tweet = tweets[0]
            
            # Add URLs first (higher priority)
            for url in urls:
                if len(first_tweet) + len(url) + 2 <= max_length:
                    first_tweet += f"\n{url}"
            
            # Add hashtags if there's space
            hashtag_str = " ".join(hashtags)
            if len(first_tweet) + len(hashtag_str) + 2 <= max_length:
                first_tweet += f"\n{hashtag_str}"
            else:
                # Try to fit as many hashtags as possible
                for hashtag in hashtags:
                    if len(first_tweet) + len(hashtag) + 1 <= max_length:
                        first_tweet += f" {hashtag}"
            
            tweets[0] = first_tweet
        
        # Add tweet numbers for threads
        total = len(tweets)
        if total > 1:
            tweets = [f"{i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]
        
        return tweets