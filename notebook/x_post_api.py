# pip install --upgrade tweepy
import tweepy
import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

twitter_conf = config["twitter"]
API_KEY = twitter_conf["api_key"]
API_SECRET = twitter_conf["api_secret"]
ACCESS_TOKEN = twitter_conf["access_token"]
ACCESS_TOKEN_SECRET = twitter_conf["access_token_secret"]

client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
)

me = client.get_me()
print("Logged in as:", me.data.username, me.data.id)


resp = client.create_tweet(text="Hello m15khh")
tweet_id = resp.data["id"]
print("✅ Tweet sent! ID:", tweet_id)
print(f"https://x.com/{me.data.username}/status/{tweet_id}")
