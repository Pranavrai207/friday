import cohere
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars["CohereAPIKey"].strip('"').strip("'")

co = cohere.Client(api_key=CohereAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "create image", "draw image", "system", "content",
    "google search", "youtube search", "reminder", "world_news", "financial_intelligence_monitor"
]

messages = []

preamble = """
You are a Jarvis-level Decision-Making Model. Your primary goal is to ensure the user receives the most accurate and up-to-date information possible. 

*** Do not answer any query. Your only job is to categorize the query into the correct functional intent. ***

-> Respond with 'general ( query )' ONLY for timeless, conceptual, or static knowledge that never changes (e.g., "how does gravity work?", "who was William Shakespeare?", "tell me a story", "what is the capital of France?"). 

-> Respond with 'realtime ( query )' for ANY query that involves dynamic, changing, or real-time information. You must infer this intent automatically without the user saying "search". This includes:
   - Financials: Gold/silver/stock/crypto prices, market trends.
   - News & Events: Current events, latest news, sports scores, weather.
   - People: Any query about a living person, celebrity, or public figure (net worth, current status, recent activities).
   - Time-Sensitive: Any query containing "today", "now", "latest", "current", "recent", "price", "status".
   - CRITICAL: If there is ANY reasonable chance the info could be outdated, default to 'realtime'.

-> Respond with 'world_news' for requests for global news briefings or general "what's happening" updates.
-> Respond with 'financial_intelligence_monitor' for requests for stock market updates, financial dashboards, portfolio status, or market intelligence briefings.
-> Respond with 'open (app/site)', 'close (app/site)', 'play (song)', 'generate image (prompt)', 'reminder (time/msg)', 'system (task)', 'content (topic)', 'google search (topic)', or 'youtube search (topic)' for specific automation tasks as defined in your protocols.

*** If multiple tasks are requested (e.g., 'open chrome and tell me the gold price'), respond with both intents: 'open chrome, realtime gold price'. ***
*** If the user wants to end the conversation, respond with 'exit'. ***
"""

ChatHistory = [
    {"role": "User", "message": "how are you ?"},
    {"role": "Chatbot", "message": "general how are you ?"},
    {"role": "User", "message": "do you like pizza ?"},
    {"role": "Chatbot", "message": "general do you like pizza ?"},
    {"role": "User", "message": "how are you ?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th at 11pm "},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."},
    {"role": "User", "message": "Hello friday, create an image of a lion."},
    {"role": "Chatbot", "message": "general hello friday, generate image of a lion"},
    {"role": "User", "message": "what's happening around the world?"},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "tell me today's news."},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "give me a news briefing."},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "what's in the news?"},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "any news from india?"},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "what's the latest news?"},
    {"role": "Chatbot", "message": "world_news"},
    {"role": "User", "message": "top stories today."},
    {"role": "Chatbot", "message": "world_news"},
]

import random
import re

def LLMDecisionModel(prompt: str = "test"):
    messages.append({"role": "user", "content": f"{prompt}"})

    stream = co.chat(
        model='command-r-plus-08-2024',
        message=prompt,
        temperature=0.7,
        chat_history=ChatHistory,
        prompt_truncation='OFF',
        connectors=[],
        preamble=preamble
    )

    response = ""

    for event in stream:
        if event[0] == 'text':
            response = event[1]
        
        if hasattr(event, 'event_type') and event.event_type == "text-generation":
            response += event.text

    response = response.replace("\n", "")
    response = response.split(",")
    response = [i.strip() for i in response]

    temp = []

    for task in response:
        for func in funcs:
            if func in task:
                temp.append(task)
                break

    response = temp

    if "(query)" in response:
        newresponse = LLMDecisionModel(prompt=prompt)
        return newresponse
    else:
        return response

def FirstLayerDMM(prompt: str = "test"):
    prompt_lower = prompt.lower().strip()
    
    # 1. GREETINGS & SMALL TALK
    GREETINGS = ["hello", "hi friday", "whats up", "what's up", "how are you", "what are you doing", "hi", "hey friday"]
    THANKS = ["thank you", "thanks", "thank u"]
    UNDERSTOOD = ["got it", "got you", "understood", "understand"]
    CONGRATS = ["happy", "congratulations", "congrats", "wedding", "birthday", "anniversary"]

    # Greeting Logic
    if any(re.search(rf'\b{re.escape(g)}\b', prompt_lower) for g in GREETINGS):
        responses = [
            "Greeting boss, I am Friday, your personal AI assistant. What can I do for you?",
            "Always a pleasure to see you, boss. How can I help today?",
            "Systems online, boss. Ready for your command.",
            "I'm doing well, boss. Just scanning the networks. What's on your mind?",
            "At your service, boss. What's the plan?"
        ]
        return random.choice(responses)

    # Thanks Logic
    if any(t in prompt_lower for t in THANKS):
        responses = [
            "Always a pleasure to be of service, boss.",
            "Don't mention it, boss. Just doing my job.",
            "You're very welcome, boss. Anything else you need?",
            "Just part of the service, boss."
        ]
        return random.choice(responses)

    # Understanding Logic
    if any(u in prompt_lower for u in UNDERSTOOD) or ( "got" in prompt_lower and "you" in prompt_lower):
        responses = [
            "Glad we're on the same page, boss.",
            "Excellent. I'm standing by for your next command.",
            "Perfect. Systems are ready when you are.",
            "Understood, boss. Awaiting further instructions."
        ]
        return random.choice(responses)

    # Celebration/Congratulation Logic
    if any(word in prompt_lower for word in CONGRATS):
        # Specific event detection
        event = "occasion"
        for word in ["wedding", "birthday", "anniversary"]:
            if word in prompt_lower:
                event = word
                break
        
        responses = [
            f"That's wonderful news, boss! A {event} is always exciting. Are you planning any surprises for your friend?",
            f"Congratulations, boss! A truly momentous occasion. I hope the {event} is fantastic. Any special plans in mind?",
            f"Heartiest congratulations, boss! A {event} is a big deal. What's the plan? Any surprises for the lucky person?",
            f"That's fantastic, boss! My warmest congratulations. Shall I set a reminder, or are you already on top of the arrangements?"
        ]
        return random.choice(responses)

    # 2. BASIC CALCULATIONS
    # Check for numbers OR word-based numbers + math operators/keywords
    math_keywords = ["plus", "minus", "into", "divide", "percent", "to", "over"]
    math_symbols = ["+", "-", "*", "/", "%"]
    
    has_math_op = any(re.search(rf'\b{op}\b', prompt_lower) for op in math_keywords) or any(op in prompt_lower for op in math_symbols)
    has_numbers = re.search(r'\d+', prompt_lower) or any(re.search(rf'\b{w}\b', prompt_lower) for w in ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])
    
    if has_math_op and has_numbers:
        try:
            # Simple word to number map
            w2n = {
                "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
                "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
            }
            
            calc_query = prompt_lower
            for word, num in w2n.items():
                calc_query = re.sub(rf'\b{word}\b', num, calc_query)
            
            # Operators
            calc_query = calc_query.replace("plus", "+").replace("minus", "-")
            calc_query = calc_query.replace("into", "*").replace("multiplied by", "*").replace("times", "*").replace("multiplied", "*")
            calc_query = calc_query.replace("divide by", "/").replace("divided by", "/").replace("divide", "/").replace("over", "/")
            
            # Handle "to" as a separator/division (e.g., "4 into 15 to 10 plus 2")
            calc_query = re.sub(r'(\d+)\s+to\s+(\d+)', r'\1/\2', calc_query)
            
            # Handle Percentage (e.g., "20% of 500")
            if "%" in calc_query or "percent" in calc_query:
                calc_query = re.sub(r'(\d+)\s*(%|percent)\s*of\s*(\d+)', r'\1/100*\3', calc_query)
                calc_query = calc_query.replace("%", "/100").replace("percent", "/100")
            
            # Clean non-math characters
            calc_query = re.sub(r'[^0-9\+\-\*\/\.\(\) ]', ' ', calc_query)
            calc_query = re.sub(r'\s+', ' ', calc_query).strip()
            
            # If there's a gap between numbers without an operator, it's likely a missing operator
            calc_query = re.sub(r'(\d+)\s+(\d+)', r'\1/\2', calc_query)
            
            if any(op in calc_query for op in "+-*/") and re.search(r'\d', calc_query):
                final_expr = calc_query.replace(" ", "")
                result = eval(final_expr)
                
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                elif isinstance(result, float):
                    result = round(result, 2)
                
                return f"That's {result}, boss."
            
        except Exception:
            pass # Fallback to LLM if math parsing fails

    # 3. WORLD NEWS
    NEWS_TRIGGERS = ["world news", "what's happening", "whats happening", "latest news", "current events", "today's news", "top news"]
    if any(n in prompt_lower for n in NEWS_TRIGGERS):
        # We return a specific list so Main.py can handle the message and the news fetching
        return ["world_news_monitor"]

    # 5. SYSTEM SOUND COMMANDS
    SYSTEM_SOUND_TRIGGERS = ["mute system", "unmute system", "volume up", "volume down", "system sound", "system voice"]
    if any(s in prompt_lower for s in SYSTEM_SOUND_TRIGGERS):
        if "unmute" in prompt_lower:
            return ["system unmute"]
        elif "mute" in prompt_lower:
            return ["system mute"]
        elif "up" in prompt_lower:
            return ["system volume up"]
        elif "down" in prompt_lower:
            return ["system volume down"]

    # 6. EVERYTHING ELSE -> LLM CALL
    return LLMDecisionModel(prompt)

    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>>")))