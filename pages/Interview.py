from sys import prefix
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from aiortc.contrib.media import MediaRecorder
from gtts import gTTS
import speech_recognition as sr
import moviepy as mp
import tempfile
import os
import json
import uuid
import time
from pathlib import Path
import logging
import google.generativeai as genai
from aiortc import RTCPeerConnection,RTCRtpReceiver
import subprocess
import asyncio
import io
import gtts
import playsound
# from deepface import DeepFace
# import av
# import cv2

# pc = RTCPeerConnection()


# @pc.on("signalingstatechange")
# def on_signaling_state_change():
#     for transceiver in pc.getTransceivers():
#         if transceiver.receiver and transceiver.receiver.track.kind == "video/rtx":
#             pc.removeTrack(transceiver.receiver.track)

# @pc.on("track")
# def on_track(track):
#     if track.kind == "video" and track.codec and track.codec.mimeType == "video/rtx":
#         pc.removeTrack(track)

#  Set Page Config
st.set_page_config(page_title='PlacementGuru | Interview', page_icon='🧊', layout='wide')
# def video_frame_callback(frame):
#     img = frame.to_ndarray(format="bgr24")

#     try:
#         analysis = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
#         dominant_emotion = analysis[0]["dominant_emotion"]
#         # Draw the detected emotion on the frame
#         cv2.putText(img, f"Emotion: {dominant_emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#     except Exception as e:
#         print(f"Emotion detection failed: {e}")

#     return av.VideoFrame.from_ndarray(img, format="bgr24")
# RTC Configuration with STUN
rtc_Configuration = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun3.l.google.com:5349"]},
            {"urls": ["stun:stun4.l.google.com:19302"]},
            {"urls": ["stun:stun4.l.google.com:5349"]}
        ],
        "iceTransportPolicy": "all",
        "bundlePolicy": "max-bundle",
        "rtcpMuxPolicy": "require",
        "sdpSemantics": "unified-plan",
        "codecPreferences": ["video/H264", "video/VP8"]
    }
)

st.title("PlacementGuru-AI Driven Interview Prep System")
if st.session_state.get('stream_ended_and_file_saved'):
    st.balloons()
    st.success("🎉 Hurray you successfully completed mock interview, now submit stream and be patient.")
# Set up tabs
tab1, tab2 = st.tabs(["Interview", "Viva"])

with tab1:
    # Text-to-Speech function
    def speak_text(text):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name  # Store file path
        tts = gtts.gTTS(text)
        tts.save(temp_audio_path)  # Save after closing file
        playsound.playsound(temp_audio_path)  # Play the audio
        os.remove(temp_audio_path) 

        st.session_state["question_spoken"] = True

    # Audio listening & analysis
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

    # Load Gemini API Key
    genai.configure(api_key=st.secrets["gemini"]["GEMINI_API_KEY"])

    # Fetch interview questions via Gemini
    def search_on_gemini(role, company, interviewer_type, company_type, difficulty_level):
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = json.load(open("prompts/prompts.json"))
        response = model.generate_content(
            prompt.get('interviewer').format(
                role=role,
                company=company,
                interviewer_type=interviewer_type,
                difficulty_level=difficulty_level,
                company_type=company_type
            )
        )
        results = json.loads(response.text)
        return results

    # Directory for recordings
    RECORD_DIR = Path("records")
    RECORD_DIR.mkdir(exist_ok=True)

    if "prefix" not in st.session_state:
        st.session_state["prefix"] = str(uuid.uuid4())
    prefix = st.session_state["prefix"]
    in_file = RECORD_DIR / f"{prefix}_input.mp4"

    # Ensure RECORD_DIR exists
    RECORD_DIR = Path("records")
    RECORD_DIR.mkdir(exist_ok=True)

    # Generate a unique prefix
    if "prefix" not in st.session_state:
        st.session_state["prefix"] = "audio_" + str(uuid.uuid4())[:8]  # Shorter ID
    prefix = st.session_state["prefix"]

    if "stream_ended_and_file_saved" not in st.session_state:
        st.session_state["stream_ended_and_file_saved"] = None

    # Convert video to audio
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

    # Safely redirect to report page
    def redirect_to_report():
        try:
            if st.session_state.get('audio_file_path') and os.path.exists(st.session_state['audio_file_path']):
                st.balloons()
                st.switch_page('pages/Report.py')
            else:
                st.error("Audio file not found. Please try again.")
                st.session_state['stream_ended_and_file_saved'] = False
        except Exception as e:
            st.error(f"Error redirecting to report: {str(e)}")
            logging.error(f"Redirect error: {str(e)}")

    # Start interview logic
    def start_interview():
        if "pending_questions" in st.session_state and st.session_state["pending_questions"]:
            if "current_question" not in st.session_state or st.session_state["current_question"] is None:
                st.session_state["current_question"] = st.session_state["pending_questions"].pop(0)
            
            st.write(f"**Question:** {st.session_state['current_question']}")
            speak_text(st.session_state['current_question'])

    # Handle next question
    def next_question():
        if "pending_questions" in st.session_state and st.session_state["pending_questions"]:
            st.session_state["current_question"] = st.session_state["pending_questions"].pop(0)
            if st.session_state["current_question"]:
                speak_text(st.session_state["current_question"])
            else:
                st.success("Interview Completed 🎉")

    # Input section
    col1, col2 = st.columns([1, 1])

    with col1.container(height=350,border=1):
        role = st.text_input('Role', placeholder='What role are you seeking?')
        sec1, sec2 = st.columns(2)
        with sec1:
            company = st.selectbox('Company', options=('Google', 'Meta', 'Wipro', 'Accenture', 'Other'))
            difficulty_level = st.selectbox('Difficulty', options=('Beginner', 'Intermediate', 'Expert'))
            button_click = st.button("Search")
        with sec2:
            interviewer_type = st.selectbox('Interviewer', options=('Professional', 'Technical', 'Behaviour', 'Friendly'))
            company_type = st.text_input("Company Type")

    # WebRTC streamer
    with col2.container(height=350,border=1):
        webstream = webrtc_streamer(
            key="Start Interview",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                "video":{
                    "width":960,
                    "height":440,
                    "frameRate":30
                },
                "audio":{
                    "sampleRate": 16000,
                    "sampleSize": 16,
                    "echoCancellation": True,
                    "noiseSuppression": True,
                    "channelCount": 1
                }
                
            },
            on_change=convert_to_wav,
            in_recorder_factory=in_recorder_factory,
            # rtc_configuration=rtc_Configuration
        )

    if st.session_state.get('stream_ended_and_file_saved'):
            st.balloons()
            st.success("Recording Completed!!!")
            redirect_to_report()

    st.divider()

    # Generate questions
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
            with st.spinner(text='Generating Questions...'):
                if role:
                    result = search_on_gemini(role, company, interviewer_type, company_type, difficulty_level)
                    st.session_state['interview_question'] = result['questions'].copy()
                    st.session_state['pending_questions'] = st.session_state['interview_question']
                    st.subheader(result["topic-title"])
                    for i in result['questions']:
                        st.markdown(f'- **{i}**')
                    start_interview()
                else:
                    st.warning("Please enter a role to search.")

    # Show current question
    if "current_question" in st.session_state and st.session_state["current_question"]:
        st.divider()
        question_col, button_col = st.columns([3, 1])

        with question_col:
            st.subheader("Current Question:")
            st.markdown(f"**{st.session_state['current_question']}**")

        with button_col:
            if st.button("Next Question"):
                    next_question()
                    if st.session_state.get("question_spoken"):
                        st.session_state["question_spoken"] = False
                        st.rerun()
                    st.balloons()
                    st.success("Hurray you successfully completed mock interview, now submit stream and be patient.", icon="🎉")
                    # st.experimental_set_query_params(interview_status="completed")

    # if st.session_state.get("question_spoken"):
    #     st.session_state["question_spoken"] = False
    #     st.rerun()   


with tab2:
    
    # Columns for input
    col1, col2 = st.columns(2)

    with col1.container(height=350):
        uploaded_files = st.file_uploader(
        "Upload your BlackBook/ Project File", accept_multiple_files=True
        )
        for uploaded_file in uploaded_files:
            bytes_data = uploaded_file.read()
            st.write("Filename:", uploaded_file.name)
            st.write(bytes_data)

    with col2.container(height=350,border=1):
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
            rtc_configuration=rtc_Configuration
        )

        if st.session_state.get('stream_ended_and_file_saved'):
            redirect_to_report()
    # with st.sidebar:
    #     st.logo("assets\\img.png")

    st.divider()
    