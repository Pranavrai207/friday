import requests
from dotenv import get_key
import json

API_URL = "https://api-inference.huggingface.co/models/stable-diffusion-v1-5/stable-diffusion-v1-5"
hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")
headers = {"Authorization": f"Bearer {hf_key}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Content (not JSON): {response.content[:100]}")
    return response

payload = {
    "inputs": "A futuristic city in the style of Tony Stark, 4k resolution"
}

print("Testing Hugging Face API...")
query(payload)
