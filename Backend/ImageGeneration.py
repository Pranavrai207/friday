import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from time import sleep
import base64
import json
import urllib3

# Suppress InsecureRequestWarning when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Using Pollinations.ai for truly free and unlimited high-quality image generation
# Correct API endpoint for raw image data
BASE_URL = "https://image.pollinations.ai/prompt/"

# Ensure the Data folder exists
if not os.path.exists("Data"):
    os.makedirs("Data")

def clean_filename(filename):
    # Remove invalid characters and trailing punctuation
    invalid_chars = '<>:"/\\|?*.'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename.replace(" ", "_").strip().strip('.')

def open_images(prompt):
    folder_path = "Data"
    safe_prompt = clean_filename(prompt)
    
    # Only look for 1 image to match the generation limit
    for i in range(1, 2):
        filename = f"{safe_prompt}{i}.jpg"
        image_path = os.path.abspath(os.path.join(folder_path, filename))

        if os.path.exists(image_path):
            try:
                print(f"Opening image: {image_path}")
                os.startfile(image_path)
            except Exception as e:
                print(f"Error opening {image_path}: {e}")
        else:
            print(f"File not found: {image_path}")

async def query(prompt, seed):
    try:
        # Construct the URL with parameters for high quality
        # Using 'turbo' model for lightning-fast generation (1-3 seconds)
        encoded_prompt = requests.utils.quote(f"{prompt}, 4k, cinematic, highly detailed, masterpiece")
        url = f"{BASE_URL}{encoded_prompt}?seed={seed}&width=1024&height=1024&model=turbo&nologo=true"
        
        # Adding verify=False to bypass SSL errors if the system clock is out of sync
        response = await asyncio.to_thread(requests.get, url, verify=False)
        
        if response.status_code == 200:
            # Verify if it's actually an image and not an HTML error page
            if response.content.startswith(b'<!DOCTYPE') or response.content.startswith(b'<html'):
                print("Pollinations returned an HTML page instead of an image.")
                return None
            return response.content
        else:
            print(f"Pollinations Error ({response.status_code})")
            return None
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

async def generate_images(prompt: str):
    tasks = []
    # Generating only 1 high-quality image to avoid Pollinations rate limiting (429 error)
    # This ensures perfect reliability for every request.
    for i in range(1):
        seed = randint(0, 1000000)
        task = asyncio.create_task(query(prompt, seed))
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)

    for i, response_content in enumerate(responses):
        if response_content:
            try:
                # Save the raw bytes directly to file
                safe_prompt = clean_filename(prompt)
                filepath = os.path.join("Data", f"{safe_prompt}{i + 1}.jpg")
                with open(filepath, "wb") as f:
                    f.write(response_content)
                print(f"Image {i + 1} saved to {filepath}")
            except Exception as e:
                print(f"Error saving image {i + 1}: {e}")

def GenerateImages(prompt: str):
    # Clean prompt: remove common task-related words to get the actual subject
    cleaned_prompt = prompt.lower()
    for word in ["generate", "create", "draw", "an images", "images", "an image", "image", "of"]:
        cleaned_prompt = cleaned_prompt.replace(word, "")
    cleaned_prompt = cleaned_prompt.strip()
    
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