import pyttsx3
import speech_recognition as sr
import threading
import streamlit as st

engine = pyttsx3.init()

def speak_text(text):
    """ Speak the given text using pyttsx3 and wait until it finishes. """
    if engine._inLoop:  # Avoid RuntimeError
        engine.endLoop()
    
    engine.say(text)
    engine.runAndWait()

def listen_and_analyze():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        st.info("Listening for response...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        response_text = recognizer.recognize_google(audio)
        st.write("Candidate's Response: ", response_text)
        return response_text
    except sr.UnknownValueError:
        st.warning("Could not understand the response.")
    except sr.RequestError:
        st.error("Speech recognition request failed.")
