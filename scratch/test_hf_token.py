import requests
from dotenv import get_key
import json

API_URL = "https://api-inference.huggingface.co/models/gpt2"
hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")
headers = {"Authorization": f"Bearer {hf_key}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    return response

payload = {"inputs": "The universe is"}
query(payload)
