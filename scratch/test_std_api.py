import requests
from dotenv import get_key
import json

# Testing the standard inference URL now that token has permissions
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")
headers = {"Authorization": f"Bearer {hf_key}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Image received.")
    else:
        print(f"Response: {response.text}")
    return response

payload = {"inputs": "A lion in a futuristic city"}
query(payload)
