from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import dotenv_values
import os
import mtranslate as mt
import time

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# HTML content with speech recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            if (recognition) {
                try { recognition.stop(); } catch(e) {}
            }
            recognition = new (window.webkitSpeechRecognition || window.SpeechRecognition)();
            recognition.lang = '';
            recognition.continuous = true;
            recognition.interimResults = true;

            recognition.onresult = function(event) {
                let transcript = "";
                for (let i = 0; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                output.textContent = transcript;
            };

            recognition.onend = function() {
                try { recognition.start(); } catch(e) {}
            };
            
            output.textContent = "";
            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
            output.textContent = "";
        }
    </script>
</body>
</html>'''

# Inject Input Language
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Save HTML to file
os.makedirs("Data", exist_ok=True)
with open("Data/Voice.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Construct local file URL
current_dir = os.getcwd()
Link = os.path.abspath("Data/Voice.html").replace("\\", "/")

# Set Chrome options
chrome_options = Options()
# Find Chrome path
chrome_stable_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
]
chrome_path = None
for path in chrome_stable_paths:
    if os.path.exists(path):
        chrome_path = path
        break

if chrome_path:
    chrome_options.binary_location = chrome_path

chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")  # Modern headless mode
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36")

# Global driver variable
driver = None

def InitializeDriver():
    global driver
    if driver is None:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

# Setup temp status path
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation

def StartRecognition():
    global driver
    InitializeDriver()
    
    target_url = "file:///" + Link.replace("\\", "/")
    try:
        current_url = driver.current_url.replace("\\", "/")
    except Exception:
        current_url = ""

    if target_url.lower() not in current_url.lower():
        driver.get("file:///" + Link)
        
    try:
        driver.find_element(By.ID, "start").click()
    except Exception as e:
        # If click fails, maybe page re-load is needed
        driver.get("file:///" + Link)
        driver.find_element(By.ID, "start").click()

def StopRecognition():
    global driver
    if driver:
        try:
            driver.find_element(By.ID, "end").click()
        except Exception:
            pass

def GetCurrentRecognitionText():
    global driver
    if driver:
        try:
            return driver.execute_script("return document.getElementById('output').textContent;")
        except Exception:
            return ""
    return ""


def SpeechRecognition():
    StartRecognition()
    last_text = ""
    last_update_time = time.time()
    
    while True:
        try:
            Text = GetCurrentRecognitionText()
            if Text:
                if Text != last_text:
                    last_text = Text
                    last_update_time = time.time()
                
                # If no update for 0.8 seconds, assume finished
                if time.time() - last_update_time > 0.8:
                    StopRecognition()
                    if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                        return QueryModifier(Text)
                    else:
                        SetAssistantStatus("Translating...")
                        return QueryModifier(UniversalTranslator(Text))
            
            time.sleep(0.1)
        except Exception:
            pass

# Run the assistant
if __name__ == "__main__":
    while True:
        Text = SpeechRecognition()
        print(Text)
