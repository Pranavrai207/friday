# 🛡️ F.R.I.D.A.Y. - Virtual AI Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen.svg" alt="Project Status">
  <img src="https://img.shields.io/badge/Brain-Groq_%26_Cohere-orange.svg" alt="AI Brain">
  <img src="https://img.shields.io/badge/Art-Hugging_Face-ff69b4.svg" alt="AI Art">
</p>

**F.R.I.D.A.Y.** (Female Replacement Intelligent Digital Assistant Youth) is a powerful, voice-activated AI assistant designed for high-performance automation, intelligent decision-making, and creative generation.

---

## 🚀 Key Features

*   **🧠 First-Layer DMM (Decision Making Model)**: Powered by Cohere, Friday analyzes user intent in real-time to route requests to the appropriate backend module.
*   **💬 High-Speed Chat**: Integrated with Groq's Llama-3.3-70b-versatile model for lightning-fast, natural conversations.
*   **🎨 AI Art Studio**: Generates high-quality images using the Hugging Face Inference API (Stable Diffusion 2.1 / FLUX).
*   **🌐 Real-time Web Search**: Perform live Google searches and get synthesized answers instantly.
*   **🎙️ Voice Interaction**: Seamless voice-to-text (STT) and text-to-speech (TTS) integration with a sleek GUI.
*   **⚡ Optimized Startup**: Implements lazy-loading for heavy drivers to ensure instant application launch.

---

## 🛠️ Tech Stack

- **Core**: Python 3.13
- **LLMs**: Groq (Llama 3.3), Cohere (Command R+)
- **Image Generation**: Hugging Face Inference API
- **GUI**: Tkinter / Pygame
- **Speech**: Selenium-based high-accuracy recognition

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Pranavrai207/friday.git
cd friday
```

### 2. Install Dependencies
```bash
pip install -r Requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
CohereAPIKey = "YOUR_COHERE_KEY"
GroqAPIKey = "YOUR_GROQ_KEY"
HuggingFaceAPIKey = "YOUR_HF_KEY"
Username = "Stark"
Assistantname = "Friday"
InputLanguage = "en"
AssistantVoice = "en-US-JennyNeural"
```

### 4. Run Friday
Simply execute the batch file:
```bash
friday.bat
```

---

## 📂 Project Structure

- `Main.py`: The central orchestrator and GUI.
- `Backend/`:
    - `Model.py`: Intent classification (DMM).
    - `Chatbot.py`: Main conversational logic.
    - `ImageGeneration.py`: Hugging Face API integration.
    - `RealtimeSearchEngine.py`: Google Search & data extraction.
    - `SpeechToText.py` & `TextToSpeech.py`: Voice handling.
- `Data/`: Stores chat logs and generated images.

---

## 🤝 Contributing
Feel free to fork this project and submit PRs! All contributions to making Friday smarter are welcome.

---

<p align="center">
  <i>"Always at your service, Boss."</i>
</p>
