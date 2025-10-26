import requests, json
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

TOKEN = config["linkedin"]["access_token"]
OWNER = config["linkedin"]["author_urn"]
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "LinkedIn-Version": "202502",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json"
}

# 1️⃣ initialize upload
r = requests.post(
    "https://api.linkedin.com/rest/images?action=initializeUpload",
    headers=headers,
    json={"initializeUploadRequest": {"owner": OWNER}}
).json()
upload_url, image_urn = r["value"]["uploadUrl"], r["value"]["image"]

# 2️⃣ upload binary
with open("logo.png", "rb") as f:
    requests.put(upload_url, data=f, headers={"Content-Type": "image/png"})

# 3️⃣ create post
# payload = {
#     "author": OWNER,
#     "commentary": "Automated image post 🧠",
#     "visibility": "PUBLIC",
#     "distribution": {"feedDistribution": "MAIN_FEED"},
#     "content": {"media": {"id": image_urn}},
#     "lifecycleState": "PUBLISHED"
# }


payload = {
    "author": OWNER,
    "commentary": "Read this paper on Vision-Language Models — very helpful! 🔗 https://huggingface.co/papers/2404.16006",
    "visibility": "PUBLIC",
    "distribution": {"feedDistribution": "MAIN_FEED"},
    "content": {
        "media": { "id": image_urn }
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False
}

resp = requests.post("https://api.linkedin.com/rest/posts",
                     headers=headers, json=payload)
print(resp.status_code)
print(resp.text)
