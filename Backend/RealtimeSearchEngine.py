from duckduckgo_search import DDGS
import re
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import webbrowser

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey").strip('"').strip("'")

client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Synthesis the provided search data and present it as if you are reading and summarizing the live browser content for the user. ***
*** INSTANT RESPONSE: Be extremely direct. If the user asks for a price, start your response IMMEDIATELY with the price. No 'Thinking...', no 'According to...', just the data. ***
*** Ensure you capture the EXACT values from the browser data (e.g., 1,53,310.00). ***
*** If the provided search data is empty or irrelevant, tell the user clearly that you couldn't find up-to-date info. Do NOT make up facts. ***"""

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
        
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from googlesearch import search as google_search
import time

def GoogleSearch(query):
    # Open the search in the browser for visual results as per original logic
    webbrowser.open(f"https://www.google.com/search?q={query}")
    
    results = []
    
    # 0. SUPER FAST: Requests-based Scraper for Instant Answer
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # Try a fast-loading source if it's a price query
        if any(word in query.lower() for word in ["price", "gold", "silver", "stock"]):
            # Fast Google Search with specific headers often returns snippets in raw HTML
            r = requests.get(f"https://www.google.com/search?q={query}&hl=en", headers=headers, timeout=2)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Look for the 'Featured Snippet' or 'Knowledge Card' in HTML
                for cls in ["VwiC3b", "pclqee", "vk_bk", "gsrt"]:
                    found = soup.find('div', class_=cls)
                    if found and found.text.strip():
                        results.append({"title": "Instant Answer", "body": found.text.strip(), "href": "Google"})
                        break
    except:
        pass

    if results: return format_results(query, results)

    # 1. Try DuckDuckGo (Fast backup)
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({"title": r['title'], "body": r['body'], "href": r['href']})
    except Exception as e:
        print(f"DDG Search Error: {e}")

    # 2. If DDG failed, try Selenium for high-fidelity extraction (Option 1)
    if len(results) < 2:
        try:
            print("Starting Selenium (Optimized) for instant search...")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Disable images for speed
            chrome_options.page_load_strategy = 'eager' # Don't wait for full page load
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(10)
            
            driver.get(f"https://www.google.com/search?q={query}")
            time.sleep(1.5) # Reduced wait for instant results
            
            # Strategy A: Find regular results
            items = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for item in items[:5]:
                try:
                    title = item.find_element(By.TAG_NAME, "h3").text
                    link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    results.append({"title": title, "body": item.text[:500], "href": link})
                except:
                    continue
            
            # Strategy B: AI Overview / Featured Snippet / Knowledge Graph
            try:
                # Common selectors for Google's Knowledge Graph, Featured Snippets, and Financial Cards
                rich_selectors = [
                    "div.hgKElc", "div.kp-header", "div.Z0LcW", "div.LGOv1b", 
                    "div.pclqee", "div.vk_bk", "span.DxyBCb", "div.gsrt",
                    "div.webanswers-webanswers_table__webanswers-table",
                    "div[data-attrid='wa:/description']", "div.dDoNo"
                ]
                for selector in rich_selectors:
                    found = driver.find_elements(By.CSS_SELECTOR, selector)
                    if found and found[0].text.strip():
                        results.insert(0, {"title": "Direct Answer", "body": found[0].text, "href": "Google"})
                        print(f"Found match with selector: {selector}")
                        # If it's a very specific direct answer, we might want to stop or prioritize it
            except Exception as e:
                print(f"Strategy B Error: {e}")
                
            # Strategy C: Look for large font numbers (often prices/conversions)
            try:
                # Find elements that might contain the big price display
                possible_prices = driver.find_elements(By.XPATH, "//*[contains(@class, 'currency') or contains(@class, 'price') or contains(@class, 'kg')]")
                for p in possible_prices[:3]:
                    if p.text.strip():
                        results.append({"title": "Price Intel", "body": p.text, "href": "Google"})
            except:
                pass

            # Strategy D: Full Body Text Fallback (Cleaned)
            if not results:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                # Look for the query words + numbers near each other
                lines = [line.strip() for line in body_text.split('\n') if len(line.strip()) > 10]
                # Filter for lines that might be the answer (e.g. contains currency symbols or large numbers)
                relevant_lines = [l for l in lines if any(c in l for c in "₹$£€") or re.search(r'\d{1,3}(,\d{3})*(\.\d+)?', l)]
                results.append({"title": "Browser Page Content", "body": "\n".join(relevant_lines[:10]), "href": "Google"})
                
            driver.quit()
        except Exception as e:
            print(f"Selenium Error: {e}")

    # 3. Fallback to googlesearch-python for URLs if still empty
    if len(results) == 0:
        try:
            for url in google_search(query, num_results=3):
                results.append({"title": "Search Result", "body": f"Link found: {url}", "href": url})
        except Exception as e:
            print(f"Google Search Library Error: {e}")

    if not results:
        return f"No search results found for '{query}'."

    return format_results(query, results)

def format_results(query, results):
    Answer = f"The live search results for '{query}' are :\n[start]\n"
    for i in results:
        Answer += f"Source: {i.get('title', 'Unknown')}\nContent: {i.get('body', 'No description available.')}\nLink: {i.get('href', '')}\n\n"
    Answer += "[end]"
    return Answer

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, Sir, how can I help you?"}
]

def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    messages.append({"role": "user", "content": f"{prompt}"})

    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)

if __name__ == "__main__":
    while True:
        prompt = input("Enter Your Query: ")
        print(RealtimeSearchEngine(prompt))