from huggingface_hub import InferenceClient
from dotenv import get_key
import os

hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")

client = InferenceClient(
    model="stable-diffusion-v1-5/stable-diffusion-v1-5",
    token=hf_key
)

import traceback
try:
    print("Testing with InferenceClient...")
    image = client.text_to_image("A futuristic city")
    print("Success! Image generated.")
    image.save("test_hf_client.png")
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error message: {e}")
    traceback.print_exc()
