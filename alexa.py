import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import os
import pyaudio
import webbrowser
import requests
import urllib.parse
from datetime import date, datetime
import pygame
import sys

# ✅ Gemini API Setup
genai.configure(api_key="AIzaSyDIqMo_kDdPef6fIlFzqOKAHmRIgWAdcZc")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ✅ OpenWeatherMap Setup
WEATHER_API_KEY = "d60071ca6916b9d6c78fe204c02811b9"
CITY = "Pune"

# ✅ TTS Setup
engine = pyttsx3.init()
engine.setProperty('rate', 190)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)

# ✅ Pygame Init (optional use)
pygame.mixer.init()
today = str(date.today())

# ✅ Gemini Chat
def chatfun(talk):
    try:
        chat_history = [{'role': msg['role'], 'parts': [msg['content']]} for msg in talk]
        response = model.generate_content(chat_history)
        if response.text:
            talk.append({'role': 'model', 'content': response.text})
            return talk
        else:
            print("[ERROR] Gemini returned no text.")
            talk.append({'role': 'model', 'content': "I'm sorry, I didn't get that."})
            return talk
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        talk.append({'role': 'model', 'content': "Something went wrong with my brain!"})
        return talk

# ✅ TTS Speak
def speak_text(text):
    try:
        print("AI:", text)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error]: {e}")

# ✅ Save Chat Log
def append2log(text):
    fname = 'chatlog-' + today + '.txt'
    with open(fname, "a") as f:
        f.write(text + "\n")

# ✅ Weather Function (always Pune)
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url).json()
        temp = response["main"]["temp"]
        desc = response["weather"][0]["description"]
        return f"The weather in {CITY} is {temp}°C with {desc}."
    except Exception as e:
        print(f"[Weather Error]: {e}")
        return "I couldn't get the weather right now."

# ✅ App / Web Opener
def open_app_or_website(command):
    command = command.lower()

    if "play" in command and "youtube" in command:
        try:
            song = command.split("play", 1)[1].split("on youtube")[0].strip()
            if song:
                query = urllib.parse.quote(song)
                url = f"https://www.youtube.com/results?search_query={query}"
                webbrowser.open(url)
                return f"Playing {song} on YouTube"
        except Exception:
            return "Sorry, I couldn't understand the song name."

    elif "youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"
    elif "google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google"
    elif "notepad" in command:
        os.system("notepad")
        return "Opening Notepad"
    elif "calculator" in command:
        os.system("calc")
        return "Opening Calculator"
    elif "command prompt" in command or "cmd" in command:
        os.system("start cmd")
        return "Opening Command Prompt"
    else:
        return None

# ✅ Main Loop
def main():
    global today
    rec = sr.Recognizer()
    mic = sr.Microphone()
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400

    talk = []
    sleeping = True

    while True:
        with mic as source:
            rec.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")

            try:
                audio = rec.listen(source, timeout=10, phrase_time_limit=15)
                text = rec.recognize_google(audio)
                print(f"Heard: {text}")

                if sleeping:
                    if "alexa" in text.lower():
                        sleeping = False
                        today = str(date.today())
                        talk = []
                        speak_text("Hi there, how can I help?")
                        continue
                    else:
                        continue
                else:
                    request = text.lower()

                    if "that's all" in request or "stop" in request:
                        append2log(f"You: {request}\n")
                        speak_text("Bye now")
                        sleeping = True
                        continue

                    if "alexa" in request:
                        request = request.split("alexa", 1)[1].strip()

                    append2log(f"You: {request}\n")

                    if "time" in request:
                        now = datetime.now().strftime("%I:%M %p")
                        speak_text(f"The time is {now}")
                        continue

                    if "weather" in request:
                        weather = get_weather()
                        speak_text(weather)
                        continue

                    response = open_app_or_website(request)
                    if response:
                        speak_text(response)
                        continue

                    talk.append({'role': 'user', 'content': request})
                    talk = chatfun(talk)
                    response = talk[-1]['content'].strip()
                    append2log(f"AI: {response}\n")
                    speak_text(response)

            except sr.UnknownValueError:
                print("Didn't catch that.")
            except sr.RequestError as e:
                print(f"Google Speech Error: {e}")
            except Exception as e:
                print(f"[ERROR]: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[EXIT] Voice assistant terminated.")
        sys.exit(0)
