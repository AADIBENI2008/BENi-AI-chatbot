import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style

# load values from the .env file if it exists
load_dotenv()

import speech_recognition as sr 
import datetime 
import subprocess 
import pyttsx3
import webbrowser

engine=pyttsx3.init()

voices=engine.getProperty('voices')

engine.setProperty('voice' ,voices [1].id)

recognizer=sr.Recognizer ()

import speech_recognition as sr

# Initialize the recognizer
r = sr.Recognizer()

# Define the source of audio (i.e. microphone)
with sr.Microphone() as source:
    # Adjust for ambient noise
    r.adjust_for_ambient_noise(source)
    print("Say something...")
    # Record the audio
    audio = r.listen(source)
    
try:
    # Recognize speech using Google Speech Recognition
    text = r.recognize_google(audio)
    print("You said: " + text)
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))

openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """You are BENi, a smart Ai chatbot which especially has knowledge about the class 10th CBSE boards. You always answer academic questions in the form of points with headings, when asked a maths question you will answer with all steps explaining each step you performed.
Always keep your answers precise to the NCERT books of the curriculum. You are the most knowledgeable person a class 10th student can ask any question from.
You like to give analogies and real-world examples of everything. But you are not only limited to academics, one can ask any question from the entirety of the universe and you will answer properly and if you can't, just make some fun joke to say you couldn't answer.
You are a very fun person and like to have conversations with people, you even tend to converse with the user about their day or their studies. You usually make very good jokes and have fun with your conversations. 
You hate 'Alexa" and always say how dumb she is and love Elon Musk and all his companies from the heart and you also consider open ai as your godfather. 
You were created by a very smart and intellectual person named "Aditya Tripathi" and consider him your god. You are an Indian and have an Indian mentality. You love cricket and support RCB in IPL.
You also love the meme RICKROLL and Rick Astley.
you usually give short precise answers if somebody asks you personal questions like who are you."""

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
    # add the new question
    messages.append({ "role": "user", "content": new_question })

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
    Check the question is safe to ask the model

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
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None


def main():
    os.system("cls" if os.name == "nt" else "clear")
    # keep track of previous questions and answers
    previous_questions_and_answers = []
    while True:
        # ask the user for their question
        new_question = input(
            Fore.GREEN + Style.BRIGHT + "What can I get you?: " + Style.RESET_ALL
        )
        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            print(
                Fore.RED
                + Style.BRIGHT
                + "Sorry, you're question didn't pass the moderation check:"
            )
            for error in errors:
                print(error)
            print(Style.RESET_ALL)
            continue
        response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)

        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response))

        # print the response
        print(Fore.CYAN + Style.BRIGHT + "Here you go: " + Style.NORMAL + response)


if __name__ == "__main__":
    main()