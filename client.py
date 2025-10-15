import requests
import json

# API endpoint
url = "http://localhost:8080/predict"

# Data to send
data = {
    "url": "https://huggingface.co/blog/rlhf"
}

# Headers
headers = {
    "Content-Type": "application/json"
}

# Send POST request
print("Sending request...")
response = requests.post(url, json=data, headers=headers)

# Print response
print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse:")
print(json.dumps(response.json(), indent=2))
