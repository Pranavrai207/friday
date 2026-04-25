import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Backend.Model import FirstLayerDMM

def test_router():
    test_queries = [
        "hello friday",
        "how are you",
        "what is 2+2",
        "five into ten into six",
        "20% of 500",
        "what's happening around the world?",
        "4 into 15 to 10 + 2",  # User's complex query
        "thank you friday",
        "okay i got you",
        "happy wedding boss",
        "who was mahatma gandhi?",  # Should still go to LLM
        "open facebook",             # Should still go to LLM
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        decision = FirstLayerDMM(q)
        print(f"Decision: {decision}")

if __name__ == "__main__":
    test_router()
