import requests
from dotenv import get_key

hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")

response = requests.get("https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {hf_key}"})
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
