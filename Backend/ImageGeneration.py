import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep
import base64
import json

# Set API URL and headers
API_URL = "https://api-inference.huggingface.co/models/sd-legacy/stable-diffusion-v1-5"
hf_key = get_key('.env', 'HuggingFaceAPIKey')
if hf_key:
    hf_key = hf_key.strip('"').strip("'")
headers = {"Authorization": f"Bearer {hf_key}"}

# Ensure the Data folder exists
if not os.path.exists("Data"):
    os.makedirs("Data")

def open_images(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)

        except IOError:
            print(f"Unable to open {image_path}. Ensure the image file exists and is valid.")

async def query(payload):
    try:
        response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for HTTP failures
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}")
        return None

async def generate_images(prompt: str):
    tasks = []
    for i in range(4):
        seed = randint(0, 1000000)
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={seed}"
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    responses = await asyncio.gather(*tasks)

    for i, response_content in enumerate(responses):
        if response_content:
            try:
                # Save the raw bytes directly to file
                filepath = fr"Data\{prompt.replace(' ', '_')}{i + 1}.jpg"
                with open(filepath, "wb") as f:
                    f.write(response_content)
                print(f"Image {i + 1} saved to {filepath}")
            except Exception as e:
                print(f"Error saving image {i + 1}: {e}")

def GenerateImages(prompt: str):
    # Clean prompt: remove 'generate', 'image', 'of'
    cleaned_prompt = prompt.replace("generate", "").replace("image", "").replace("of", "").strip()
    asyncio.run(generate_images(cleaned_prompt))
    open_images(cleaned_prompt)

# Main execution loop
while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            data = str(f.read())

        prompt, status = data.split(",")
        status = status.strip()

        if status.lower() == "true":
            print("Generating Images...")
            GenerateImages(prompt=prompt)

            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False, False")
            break
        else:
            sleep(1)

    except :
        pass