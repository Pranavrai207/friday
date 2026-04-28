import sys
import os

# Add the parent directory to sys.path to import Backend.WorldNews
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Backend.WorldNews import GetWorldNews

print("Testing WorldNews...")
result = GetWorldNews(topic="world", max_articles=5)
print("\n--- Final Result ---")
print(result)
