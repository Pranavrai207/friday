import requests
from dotenv import get_key
import json

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
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
        try:
            print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Content: {response.text[:500]}")
    return response

payload = {"inputs": "A futuristic city"}
query(payload)
