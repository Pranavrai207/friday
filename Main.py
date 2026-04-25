from Frontend.GUI import (
    GraphicalUserInterface,
    SetAsssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.WorldNews import GetWorldNews
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f""" {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you? """

functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]
subprocess_list = []

# World news trigger phrases for fallback detection
WORLD_NEWS_TRIGGERS = [
    "what's happening", "whats happening", "world news", "news today",
    "news briefing", "what's in the news", "whats in the news",
    "around the world", "current events", "latest news", "top news",
    "tell me the news", "any news", "news update", "global news"
]


# Ensure a default chat log exists if no chats are logged
def ShowDefaultChatIfNoChats():
    try:
        with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as temp_file:
                    temp_file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                    response_file.write(DefaultMessage)
    except FileNotFoundError:
        print("ChatLog.json file not found. Creating default response.")
        os.makedirs("Data", exist_ok=True)
        with open(r'Data\ChatLog.json', "w", encoding='utf-8') as file:
            file.write("[]")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
            response_file.write(DefaultMessage)

# Read chat log from JSON
def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            chatlog_data = json.load(file)
        return chatlog_data
    except FileNotFoundError:
        print("ChatLog.json not found.")
        return []

# Integrate chat logs into a readable format
def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"{Assistantname}: {entry['content']}\n"

    # Ensure the Temp directory exists
    temp_dir_path = TempDirectoryPath('')
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

# Display the chat on the GUI
def ShowChatOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read()
        if len(str(data)) > 0:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                response_file.write(data)
    except FileNotFoundError:
        print("Database.data file not found.")

# Initial execution setup
def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()

# Main execution logic
def MainExecution():
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        SetAsssistantStatus("Listening...")
        Query = SpeechRecognition()
        query_lower = Query.lower()
        ShowTextToScreen(f"{Username}: {Query}")
        SetAsssistantStatus("Thinking...")
        Decision = FirstLayerDMM(Query)

        # ── Logic-based Response Handling ──
        if isinstance(Decision, str):
            Answer = Decision
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAsssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True

        # Special World News Trigger from Router
        if "world_news_monitor" in Decision:
            Answer = "Opening World Intelligence Monitor, boss."
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAsssistantStatus("Answering...")
            TextToSpeech(Answer)
            
            # Now actually fetch the news
            SetAsssistantStatus("Scanning world intel...")
            # Detect topic from the original spoken query
            topic = (
                "india"    if "india"    in query_lower else
                "tech"     if "tech"     in query_lower or "technology" in query_lower else
                "business" if "business" in query_lower or "market"     in query_lower else
                "world"
            )
            Answer = GetWorldNews(topic=topic)
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAsssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True

        print(f"\nDecision: {Decision}\n")

        # ── Fallback: catch world news intent if DMM missed it (legacy check) ──
        if not any("world_news" in d for d in Decision):
            if any(trigger in query_lower for trigger in WORLD_NEWS_TRIGGERS):
                Decision.append("world_news")
                print("WorldNews fallback triggered.")

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries or "image" in queries or "draw" in queries or "create" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in functions):
                    run(Automation(list(Decision)))
                    TaskExecution = True

        if ImageExecution:
            with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                # Clean the prompt for the generation script
                # Remove common prefixes from the decision string
                clean_query = ImageGenerationQuery
                for prefix in ["generate image", "create image", "draw image", "generate", "create", "draw", "general", "realtime"]:
                    clean_query = clean_query.replace(prefix, "")
                clean_query = clean_query.replace("friday", "").strip()
                
                file.write(f"{clean_query},True")
                
            try:
                p1 = subprocess.Popen(
                    ['python', r"Backend\ImageGeneration.py"],
                    shell=False
                )
                subprocess_list.append(p1)
                
                # Hardcoded local response to avoid external API calls for image tasks
                Answer = "Creating the images, Boss. Please wait a moment."
                ShowTextToScreen(f"{Assistantname}: {Answer}")
                SetAsssistantStatus("Answering...")
                TextToSpeech(Answer)
                
                # ALWAYS return here for image tasks to prevent Groq from interjecting
                return True
                    
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and R or R:
            SetAsssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAsssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True

        else:
            for queries in Decision:
                if "general" in queries:
                    SetAsssistantStatus("Thinking...")
                    QueryFinal = queries.replace("general", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True

                elif "realtime" in queries:
                    SetAsssistantStatus("Searching...")
                    QueryFinal = queries.replace("realtime", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True

                elif "world_news" in queries:
                    SetAsssistantStatus("Scanning world intel...")
                    # Detect topic from the original spoken query
                    topic = (
                        "india"    if "india"    in query_lower else
                        "tech"     if "tech"     in query_lower or "technology" in query_lower else
                        "business" if "business" in query_lower or "market"     in query_lower else
                        "world"
                    )
                    Answer = GetWorldNews(topic=topic)
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True

                elif "exit" in queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAsssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    os._exit(1)

    except Exception as e:
        print(f"Error in MainExecution: {e}")

# Thread for primary execution loop
def FirstThread():
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()

            if CurrentStatus.lower() == "true":
                MainExecution()
            elif CurrentStatus.lower() == "false":
                AIStatus = GetAssistantStatus()

                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAsssistantStatus("Available...")
            else:
                sleep(0.1)
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            sleep(1)

# Thread for GUI execution
def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in SecondThread: {e}")

# Entry point
if __name__ == "__main__":
    InitialExecution()

    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()