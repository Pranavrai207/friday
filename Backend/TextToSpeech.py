import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import random
import asyncio
import edge_tts
import re
import os
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = (env_vars.get("AssistantVoice") or "en-US-JennyNeural").strip(" '\"")
VoicePitch = (env_vars.get("VoicePitch") or "+0Hz").strip(" '\"")
VoiceRate = (env_vars.get("VoiceRate") or "+0%").strip(" '\"")
Assistantname = (env_vars.get("Assistantname") or "Friday").strip(" '\"")

# Initialize pygame mixer once at the module level for maximum speed
pygame.mixer.init()

import re

async def TextToAudioFile(text, filename) -> None:
    file_path = os.path.join("Data", filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass 

    try:
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch=VoicePitch, rate=VoiceRate)
        await communicate.save(file_path)
    except Exception as e:
        print(f"Error in TextToAudioFile while generating {filename}: {e}")
        # Fallback to neutral if it fails
        communicate = edge_tts.Communicate(text, AssistantVoice)
        await communicate.save(file_path)

def TTS(Text, func=lambda r=None: True):
    # Split text into sentences for streaming (handles dots, exclamation, and question marks)
    sentences = re.split(r'(?<=[.!?]) +', Text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []

    try:
        from Backend.SpeechToText import StartRecognition, StopRecognition, GetCurrentRecognitionText
        
        # Initial generation for the first sentence
        current_file = "speech_1.mp3"
        next_file = "speech_2.mp3"
        
        asyncio.run(TextToAudioFile(sentences[0], current_file))
        
        # Start background recognition for interruption
        StartRecognition()
        
        for i in range(len(sentences)):
            # Play current sentence
            pygame.mixer.music.load(os.path.join("Data", current_file))
            pygame.mixer.music.play()
            
            # While playing, we can pre-generate the next sentence if we have one
            if i + 1 < len(sentences):
                # Start pre-generating next sentence
                asyncio.run(TextToAudioFile(sentences[i+1], next_file))
            
            # Wait for current sentence to finish or interruption
            clock = pygame.time.Clock()
            interrupted = False
            while pygame.mixer.music.get_busy():
                # Check for interruption keywords (including phonetic variants)
                recog_text = GetCurrentRecognitionText().lower()
                stop_keywords = ["wait", "pause", "stop", "hold on", "pose", "post", Assistantname.lower()]
                if any(word in recog_text for word in stop_keywords):
                    # Safety: If 'system' is mentioned, it's likely a sound command, not just a random stop
                    print(f"Interrupted by: {recog_text}")
                    pygame.mixer.music.stop()
                    interrupted = True
                    break
                
                if not func():
                    break
                clock.tick(10)
            
            if interrupted:
                StopRecognition()
                return sentences[i:] # Return remaining sentences starting from the interrupted one
                
            pygame.mixer.music.unload()
            
            # Swap files for the next iteration
            current_file, next_file = next_file, current_file

        StopRecognition()
        return [] # Return empty list if finished normally

    except Exception as e:
        print(f"Error in TTS : {e}")
        return []
    finally:
        try:
            func(False)
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass

def TextToSpeech(Text, func=lambda r=None: True):
    # Now that we have streaming, we don't need to shorten long texts as aggressively
    # But we still keep a safety limit for extremely long outputs
    if len(Text) > 1000:
        return TTS(Text[:1000] + "... and so on, sir.", func)
    else:
        return TTS(Text, func)
# jar tumhala purna read karaich lavaich asel tr TTS cha use kara jar 4 or tya peksha line 
# jast lines text asel tr TTS use kra ani Short made read karacih asel tr texttosppech use kara  
if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text : "))