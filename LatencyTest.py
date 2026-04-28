import asyncio
import edge_tts
import time
import os

async def test_latency():
    text = "Hello Boss, I am checking the connection latency to the Microsoft servers right now."
    print(f"Testing voice generation for: '{text}'")
    
    start_time = time.time()
    
    # Test generation
    communicate = edge_tts.Communicate(text, "en-IE-EmilyNeural")
    await communicate.save("test_latency.mp3")
    
    end_time = time.time()
    print(f"Latency: {end_time - start_time:.2f} seconds")
    
    if os.path.exists("test_latency.mp3"):
        os.remove("test_latency.mp3")

if __name__ == "__main__":
    asyncio.run(test_latency())
