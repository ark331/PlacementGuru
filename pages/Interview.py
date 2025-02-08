import os, time
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import moviepy as me
import numpy as np
import pydub, av, uuid
from pathlib import Path
import json
from aiortc.contrib.media import MediaRecorder
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer, WebRtcMode
import pyttsx3
import speech_recognition as sr
import moviepy as mp
import threading 
import footer

load_dotenv()
st.set_page_config(page_title='PlacementGuru', page_icon='🧊', layout='wide')

tab1, tab2 = st.tabs(["Interview","Viva"])

with tab1:
    engine = pyttsx3.init()

    def speak_text(text):
        def run_engine():
            engine.say(text)
            engine.runAndWait()
        
        thread = threading.Thread(target=run_engine)
        thread.start()

    # Speech Recognition
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

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    def search_on_gemini(role, company, interviewer_type):
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = json.load(open("prompts/prompts.json"))
        response = model.generate_content(prompt.get('interviewer').format(role=role, difficulty_level=difficulty_level, company=company, interviewer_type=interviewer_type, company_type=company_type))
        results = json.loads(response.text)
        return results


    st.title("PlacementGuru")

    RECORD_DIR = Path("records")
    RECORD_DIR.mkdir(exist_ok=True)

    if "prefix" not in st.session_state:
        st.session_state["prefix"] = str(uuid.uuid4())
    prefix = st.session_state["prefix"]
    in_file = RECORD_DIR / f"{prefix}_input.mp4"

    if "stream_ended_and_file_saved" not in st.session_state:
        st.session_state["stream_ended_and_file_saved"] = None

    def convert_to_wav():
        ctx = st.session_state.get("Start Interview")
        if ctx:
            state = ctx.state
            if not state.playing and not state.signalling:
                if in_file.exists():
                    time.sleep(1)
                    output_wav = RECORD_DIR / f"{prefix}_output.wav"
                    try:
                        video = mp.VideoFileClip(str(in_file))
                        video.audio.write_audiofile(str(output_wav), codec='pcm_s16le')
                        st.session_state['audio_file_path'] = str(output_wav)  # Store path
                        st.session_state['stream_ended_and_file_saved'] = True
                    except Exception as e:
                        st.error(f"Error converting video to audio: {e}")
                        st.session_state['stream_ended_and_file_saved'] = False

    def in_recorder_factory() -> MediaRecorder:
        return MediaRecorder(str(in_file), format="mp4")

    def start_interview():
        if "pending_questions" in st.session_state and st.session_state["pending_questions"]:
            question = st.session_state["pending_questions"].pop()
            st.session_state["current_question"] = question
            st.write(f"**Question:** {question}")
            speak_text(question)

    def next_question():
        """Handle transition to next question professionally"""
        if st.session_state.get('pending_questions'):
            current_question = st.session_state['pending_questions'][0]
            response = listen_and_analyze()  # Get user's answer
            
            if response:
                # Store response
                if 'responses' not in st.session_state:
                    st.session_state['responses'] = {}
                st.session_state['responses'][current_question] = response
                
                # Remove current question
                st.session_state['pending_questions'].pop(0)
                
                # Check if there are more questions
                if st.session_state['pending_questions']:
                    # Get next question ready
                    next_q = st.session_state['pending_questions'][0]
                    st.session_state['current_question'] = next_q
                    # Speak next question
                    speak_text(next_q)
                    # Force streamlit to rerun and show new question
                    st.experimental_rerun()
                else:
                    st.success("🎉 Interview completed!")
                    if 'audio_file_path' in st.session_state:
                        time.sleep(1)
                        st.switch_page("pages/Report.py")

    # Columns for input
    col1, col2 = st.columns(2)

    with col1.container(height=350):
        role = st.text_input('Role', placeholder='What role are you seeking for!')
        sec1, sec2 = st.columns(2)
        with sec1:
            company = st.selectbox('Company', options=('Google', 'Meta', 'Wipro', 'Accenture', 'Other'))
            difficulty_level = st.selectbox('Difficulty', options=('Beginner', 'Intermediate', 'Expert'))
            button_click = st.button("Search")
        with sec2:
            interviewer_type = st.selectbox('Interviewer', options=('Professional', 'Technical', 'Behaviour','Friendly','Code Questions'))
            company_type = st.text_input("Company Type")

    with col2.container(height=350):
        webstream = webrtc_streamer(
            key="Start Interview",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                'video': {'width': 960, 'height': 440}, 
                "audio": {
                    "sampleRate": 16000,
                    "sampleSize": 16,
                    'echoCancellation': True,
                    "noiseSuppression": True,
                    "channelCount": 1
                }
            },
            on_change=convert_to_wav,
            in_recorder_factory=in_recorder_factory,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},  # Add STUN server
        )

        if st.session_state.get('stream_ended_and_file_saved'):
            st.switch_page('pages/Report.py')

    # Add this check to maintain stream state
    if webstream.state.playing:
        st.session_state['stream_active'] = True
    elif 'stream_active' in st.session_state:
        # Stream ended
        if st.session_state['stream_active']:
            st.session_state['stream_active'] = False
            convert_to_wav()  # Convert the recording

    with st.sidebar:
        st.logo("assets\\img.png")

    st.divider()
    if button_click:
        with st.container(height=300):
            st.markdown("""
            <style>
                div.stSpinner > div{
                text-align:center;
                align-items: center;
                justify-content: center;
                }
            </style>""", unsafe_allow_html=True)

            with st.spinner(text='Generating Questions...', ):
                if role:
                    result = search_on_gemini(role, company, interviewer_type)
                    st.session_state['interview_question'] = result['questions'].copy()
                    st.session_state['pending_questions'] = st.session_state['interview_question'][::-1]
                    st.subheader(result["topic-title"])
                    for i in result['questions']:
                        st.markdown(f'-  **{i}**')
                    start_interview()
                else:
                    st.warning("Please enter a role to search.")

    # Create two separate columns for question and button
    if st.session_state.get('pending_questions'):
        st.divider()
        question_col, button_col = st.columns([3, 1])
        
        with question_col:
            st.subheader("Current Question:")
            current_q = st.session_state['pending_questions'][0]
            st.markdown(f"**{current_q}**")
            
            if st.session_state.get('listening'):
                st.info("🎤 Recording your answer...")
        
        with button_col:
            st.write("")  # Spacing
            st.write("")  # Spacing
            # Use timestamp for unique key
            button_key = f"next_q_{int(time.time()*1000)}"
            next_button = st.button(
                "Next Question ➡️" if len(st.session_state['pending_questions']) > 1 else "Finish Interview ✅",
                key=button_key,
                use_container_width=True,
                type="primary"  # Make button more prominent
            )
            if next_button:
                next_question()

# Viva Section
with tab2:
    engine = pyttsx3.init()
    def speak_text(text):
        def run_engine():
            engine.say(text)
            engine.runAndWait()
        thread = threading.Thread(target=run_engine)
        thread.start()

    # Speech Recognition
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

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    def search_on_gemini(role, company, interviewer_type):
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = json.load(open("prompts/prompts.json"))
        response = model.generate_content(prompt.get('interviewer').format(role=role, difficulty_level=difficulty_level, company=company, interviewer_type=interviewer_type, company_type=company_type))
        results = json.loads(response.text)
        return results


    st.title("PlacementGuru")

    RECORD_DIR = Path("records")
    RECORD_DIR.mkdir(exist_ok=True)

    if "prefix" not in st.session_state:
        st.session_state["prefix"] = str(uuid.uuid4())
    prefix = st.session_state["prefix"]
    in_file = RECORD_DIR / f"{prefix}_input.mp4"

    if "stream_ended_and_file_saved" not in st.session_state:
        st.session_state["stream_ended_and_file_saved"] = None

    def convert_to_wav():
        ctx = st.session_state.get("Start Interview")
        if ctx:
            state = ctx.state
            if not state.playing and not state.signalling:
                if in_file.exists():
                    time.sleep(1)
                    output_wav = RECORD_DIR / f"{prefix}_output.wav"
                    try:
                        video = mp.VideoFileClip(str(in_file))
                        video.audio.write_audiofile(str(output_wav), codec='pcm_s16le')
                        st.session_state['audio_file_path'] = str(output_wav)  # Store path
                        st.session_state['stream_ended_and_file_saved'] = True
                    except Exception as e:
                        st.error(f"Error converting video to audio: {e}")
                        st.session_state['stream_ended_and_file_saved'] = False

    def in_recorder_factory() -> MediaRecorder:
        return MediaRecorder(str(in_file), format="mp4")

    def start_interview():
        if "pending_questions" in st.session_state and st.session_state["pending_questions"]:
            question = st.session_state["pending_questions"].pop()
            st.session_state["current_question"] = question
            st.write(f"**Question:** {question}")
            speak_text(question)

    def next_question():
        """Move to the next question, store the response, and continue the interview. """
        if st.session_state.get('pending_questions'):
            # Store current question's response
            current_question = st.session_state['pending_questions'][0]
            response = listen_and_analyze()  # Get user's answer
            
            if response:  # Only proceed if we got a response
                st.session_state['responses'][current_question] = response
                # Remove the current question from pending questions
                st.session_state['pending_questions'].pop(0)

                # Check if there are more questions
                if st.session_state['pending_questions']:
                    # Update current question for display
                    st.session_state['current_question'] = st.session_state['pending_questions'][0]
                    # Speak the next question
                    speak_text(st.session_state['pending_questions'][0])
                else:
                    st.success("🎉 Interview completed!")
                    # Ensure we have the audio file path in session state
                    if 'audio_file_path' in st.session_state:
                        time.sleep(1)  # Small delay to ensure file is saved
                        st.switch_page("pages/Report.py")
                    else:
                        st.error("Audio recording not found. Please try again.")

    # Columns for input
    col1, col2 = st.columns(2)
    
    def generate_questions(pdf_text):
        prompt = f"Read the following text and generate five interview-style questions based on it:\n\n{pdf_text[:3000]}"  # Limiting to 3000 characters
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text if response else "No questions generated."

    with col1.container(height=350):
        uploaded_files = st.file_uploader(
        "Upload your BlackBook/ Project File", accept_multiple_files=True
        )
        

    with col2.container(height=350):
        webstream = webrtc_streamer(
            key="Start Viva",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={'video': {'width': 960, 'height': 440}, "audio": {
                "sampleRate": 16000,
                "sampleSize": 16,
                'echoCancellation': True,
                "noiseSuppression": True,
                "channelCount": 1}},
            on_change=convert_to_wav,
            in_recorder_factory=in_recorder_factory,
        )

        if st.session_state.get('stream_ended_and_file_saved'):
            st.switch_page('pages/Report.py')
    with st.sidebar:
        st.logo("assets\\img.png")

    st.divider()
    if button_click:
        with st.container(height=300):
            st.markdown("""
            <style>
                div.stSpinner > div{
                text-align:center;
                align-items: center;
                justify-content: center;
                }
            </style>""", unsafe_allow_html=True)

            with st.spinner(text='Generating Questions...', ):
                if role:
                    result = search_on_gemini(role, company, interviewer_type)
                    st.session_state['interview_question'] = result['questions'].copy()
                    st.session_state['pending_questions'] = st.session_state['interview_question'][::-1]
                    st.subheader(result["topic-title"])
                    for i in result['questions']:
                        st.markdown(f'-  **{i}**')
                    start_interview()
                else:
                    st.warning("Please enter a role to search.")

    # Create two separate columns for question and button
    if st.session_state.get('pending_questions'):
        st.divider()
        question_col, button_col = st.columns([3, 1])
        
        with question_col:
            st.subheader("Current Question:")
            current_q = st.session_state['pending_questions'][0]
            st.markdown(f"**{current_q}**")
            
            # Show recording indicator
            if st.session_state.get('listening'):
                st.info("🎤 Recording your answer...")
        
        with button_col:
            st.write("")  # Add some spacing
            st.write("")  # Add some spacing
            # Add unique identifier using timestamp
            button_key = f"next_question_btn_{time.time()}"
            next_button = st.button(
                "Next Question ➡️" if len(st.session_state['pending_questions']) > 1 else "Finish Interview ✅",
                key=button_key,
                use_container_width=True
            )
            if next_button:
                next_question()