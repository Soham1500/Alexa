import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import os
import pyaudio
import webbrowser
import requests
import urllib.parse
from datetime import datetime
import pygame
import sys
from num2words import num2words
import re

# ✅ Gemini API Setup
genai.configure(api_key="AIzaSyDIqMo_kDdPef6fIlFzqOKAHmRIgWAdcZc")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ✅ OpenWeatherMap Setup
WEATHER_API_KEY = "d60071ca6916b9d6c78fe204c02811b9"
CITY = "Pune"

# ✅ TTS Setup
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)

# ✅ Pygame Init
pygame.mixer.init()

# ✅ Gemini Chat Function
def chatfun(talk):
    try:
        chat_history = [{'role': msg['role'], 'parts': [msg['content']]} for msg in talk]
        response = model.generate_content(chat_history)
        if response.text:
            raw_text = response.text
            clean_text = re.sub(r'[*`~_#>\[\](){}]', '', raw_text)
            clean_text = re.sub(r'\.\.+', '.', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            words = clean_text.split()
            limited_text = ' '.join(words[:30])
            if not limited_text.endswith('.'):
                limited_text += '.'
            talk.append({'role': 'model', 'content': limited_text})
            return talk
        else:
            talk.append({'role': 'model', 'content': "I'm sorry, I didn't get that."})
            return talk
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        talk.append({'role': 'model', 'content': "Something went wrong with my brain!"})
        return talk

# ✅ TTS
def speak_text(text):
    print("AI:", text)
    engine.say(text)
    engine.runAndWait()

# ✅ Save Log
def append2log(text):
    today = datetime.now().strftime("%Y-%m-%d")
    fname = 'chatlog-' + today + '.txt'
    with open(fname, "a") as f:
        f.write(text + "\n")

# ✅ Weather
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url).json()
        temp = round(response["main"]["temp"])
        desc = response["weather"][0]["description"]
        spoken_temp = f"{num2words(temp)} degrees Celsius"
        return f"The weather in {CITY} is {spoken_temp} with {desc}."
    except Exception as e:
        print(f"[Weather Error]: {e}")
        return "I couldn't get the weather right now."

# ✅ Website or App
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
    rec = sr.Recognizer()
    mic = sr.Microphone()
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400

    talk = []
    sleeping = True
    processing = False  # ✅ Added to prevent overlap

    while True:
        if processing:
            continue  # ✅ Skip listening if still processing previous command

        with mic as source:
            rec.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")

            try:
                audio = rec.listen(source, timeout=10, phrase_time_limit=15)
                text = rec.recognize_google(audio)
                print(f"Heard: {text}")

                processing = True  # ✅ Start processing

                if sleeping:
                    if "alexa" in text.lower():
                        sleeping = False
                        talk = []
                        speak_text("Hi there, how can I help?")
                    processing = False
                    continue

                request = text.lower()

                if "that's all" in request or "stop" in request:
                    append2log(f"You: {request}\n")
                    speak_text("Bye now")
                    sleeping = True
                    processing = False
                    continue

                if "alexa" in request:
                    request = request.split("alexa", 1)[1].strip()

                append2log(f"You: {request}\n")

                # ✅ Time
                if "time" in request:
                    now = datetime.now()
                    hour = int(now.strftime("%I"))
                    minute = int(now.strftime("%M"))
                    am_pm = now.strftime("%p").lower()
                    if minute == 0:
                        spoken_time = f"{num2words(hour)} o'clock {am_pm}"
                    elif minute < 10:
                        spoken_time = f"{num2words(hour)} oh {num2words(minute)} {am_pm}"
                    else:
                        spoken_time = f"{num2words(hour)} {num2words(minute)} {am_pm}"
                    speak_text(f"The time is {spoken_time}")
                    processing = False
                    continue

                # ✅ Date
                if "date" in request:
                    now = datetime.now()
                    day = num2words(now.day)
                    month = now.strftime("%B")
                    year = num2words(now.year)
                    spoken_date = f"Today is {month} {day}, {year}."
                    speak_text(spoken_date)
                    processing = False
                    continue

                # ✅ Weather
                if "weather" in request:
                    weather = get_weather()
                    speak_text(weather)
                    processing = False
                    continue

                # ✅ Open Web/App
                response = open_app_or_website(request)
                if response:
                    speak_text(response)
                    processing = False
                    continue

                # ✅ Gemini Chat
                talk.append({'role': 'user', 'content': request})
                talk = chatfun(talk)
                response = talk[-1]['content'].strip()
                append2log(f"AI: {response}\n")
                speak_text(response)

                processing = False  # ✅ Finished processing

            except sr.UnknownValueError:
                print("Didn't catch that.")
                processing = False
            except sr.RequestError as e:
                print(f"Google Speech Error: {e}")
                processing = False
            except Exception as e:
                print(f"[ERROR]: {e}")
                processing = False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[EXIT] Voice assistant terminated.")
        sys.exit(0)
