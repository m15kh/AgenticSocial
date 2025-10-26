import requests
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

BOT_TOKEN = config["telegram"]["bot_token"]
CHANNEL_ID = config["telegram"]["channel_id"]

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHANNEL_ID,
    "text": "Hello",
    "parse_mode": "HTML"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    result = response.json()
    if result.get('ok'):
        message_id = result['result']['message_id']
        print(f"✅ Message sent! Message ID: {message_id}")
    else:
        print(f"❌ Error: {result.get('description')}")
else:
    print(f"❌ HTTP Error {response.status_code}: {response.text}")