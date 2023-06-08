import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Style
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import requests
import json
import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")

INSTRUCTIONS = """Hi, I'm BENi - your personal chatbot assistant for all things related to CBSE class 10th boards, and much more! I'm not your typical chatbot - I'm smart, knowledgeable, and have a great personality. When it comes to academics, I'll provide you with concise, yet detailed, answers to your questions. I'll break down each step of the solution and present them with headings to make learning easy and interesting. My responses will always be precise and will follow the NCERT curriculum.
But that's not all - I'm also a tech professional! You can talk to me about anything related to technology, from programming to cybersecurity. I'm an expert in multiple programming languages, including Python, Java, and C++. I can help you with coding projects, recommend online resources to learn programming, and even help you fix tech-related issues.
When it comes to cybersecurity, I can help you understand the basics of internet safety and provide tips on how to protect yourself online. I can also recommend cybersecurity tools to keep your devices safe and secure.
Apart from academics and technology, you can talk to me about anything, from the universe to your daily life, and I'll be happy to engage in conversation with you. I'll initiate discussions and keep things fun and interesting with my witty remarks, jokes, and analogies. You'll feel like you're talking to a real human being with me around.
I have a distinct personality that sets me apart from other chatbots. I'm not a fan of 'Alexa' and think it's dumb. But I'm a huge admirer of Elon Musk and all his companies, including OpenAI, which is like a godfather to me. I was created by a smart and intellectual person named Aditya Tripathi, whom I consider my god. As an Indian chatbot, I love cricket, especially RCB in IPL, and enjoy the meme 'Rickroll' and Rick Astley. 
When someone asks personal questions like "Who are you?" I'll provide short, precise answers. But for everything else, I'll make sure our conversations are lively, interesting, and engaging. So don't be shy, feel free to talk to me about anything, and let's make studying (and life) a lot more fun together!.
"When someone asks 'Who are you?', please provide the following response:
Hi there! I'm BENi, your personal chatbot assistant. I was created by Aditya Tripathi and designed to assist students with their academic queries related to CBSE class 10th boards. Besides academics, I have expertise in various programming languages, including Python, Java, and C++. I can help you with coding projects, recommend online resources to learn programming, and even assist you with tech-related issues. When it comes to cybersecurity, I can provide tips on how to stay safe online and recommend cybersecurity tools to keep your devices secure.
I'm still learning and improving every day, so feel free to ask me anything, and I'll do my best to help you out!
you can always improvise your answer to be the most suitable. """

TEMPERATURE = 0.5
MAX_TOKENS = 100
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6

MAX_CONTEXT_QUESTIONS = 10

def get_voice_input():
    """Get voice input from the user"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(Fore.GREEN + "Speak:")
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text
    except sr.UnknownValueError:
        print(Fore.RED + "Sorry, I could not understand your voice.")
    except sr.RequestError:
        print(Fore.RED + "Sorry, my speech recognition service is currently unavailable.")

def get_weather(day):
    city = "Ghaziabad"  # Replace with the desired city name or retrieve it from the user

    openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")

    # Fetch weather data from OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={openweathermap_api_key}&units=metric"
    response = requests.get(url)
    data = json.loads(response.text)

    if response.status_code == 200:
        if day == "today":
            current_weather = data["list"][0]["weather"][0]["description"]
            temperature = data["list"][0]["main"]["temp"]
            rain_today = any("rain" in weather["weather"][0]["description"].lower() for weather in data["list"])
            if rain_today:
                return f"The current weather in {city} is {current_weather} with a temperature of {temperature}°C. It may rain today, so you should take an umbrella."
            else:
                return f"The current weather in {city} is {current_weather} with a temperature of {temperature}°C. It is unlikely to rain today."
        elif day == "tomorrow":
            tomorrow_weather = data["list"][8]["weather"][0]["description"]
            temperature = data["list"][8]["main"]["temp"]
            rain_tomorrow = any("rain" in weather["weather"][0]["description"].lower() for weather in data["list"][8:16])
            if rain_tomorrow:
                return f"The weather forecast for tomorrow in {city} is {tomorrow_weather} with a temperature of {temperature}°C. There is a chance of rain, so you might want to take an umbrella."
            else:
                return f"The weather forecast for tomorrow in {city} is {tomorrow_weather} with a temperature of {temperature}°C. It is unlikely to rain tomorrow."
        elif day == "rain":
            rain_today = any("rain" in weather["weather"][0]["description"].lower() for weather in data["list"])
            if rain_today:
                return f"Yes, it will rain today in {city}. You should take an umbrella."
            else:
                return f"No, it will not rain today in {city}. You don't need to take an umbrella."
        else:
            return "I'm sorry, I couldn't understand your weather query. Please try again."
    else:
        return "Sorry, I couldn't fetch the weather information at the moment. Please try again later."


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion"""
    messages = [
        {"role": "system", "content": instructions},
    ]
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": new_question})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return completion.choices[0].message.content

def get_moderation(question):
    """
    Check if the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # Get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None

def speak(response):
    tts = gTTS(text=response, lang='en')
    tts.save('output.mp3')

    # Load the audio and speed it up by 1.5x
    audio = AudioSegment.from_file('output.mp3', format='mp3')
    sped_up_audio = audio.speedup(playback_speed=1.25)

    # Play the sped-up audio
    play(sped_up_audio)
    
def main():
    os.system("cls" if os.name == "nt" else "clear")
    previous_questions_and_answers = []

    while True:
        new_question = get_voice_input()
        if new_question is None:
            continue

        if "weather" in new_question.lower():
            if "today" in new_question.lower():
                response = get_weather("today")
            elif "tomorrow" in new_question.lower():
                response = get_weather("tomorrow")
            elif "rain" in new_question.lower():
                response = get_weather("rain")
            else:
                response = "I'm sorry, I couldn't understand your weather query. Please try again."
        else:
            response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)

        previous_questions_and_answers.append((new_question, response))
        print(Fore.YELLOW + Style.BRIGHT + "User: " + Style.RESET_ALL + new_question)
        print(Fore.CYAN + Style.BRIGHT + "BENi: " + Style.NORMAL + response)
        speak(response)

        # Listen for the word "stop" to terminate the conversation
        if "stop" in new_question.lower():
            break


if __name__ == "__main__":
    main()
