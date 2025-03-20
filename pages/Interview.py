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

pc = RTCPeerConnection()


@pc.on("signalingstatechange")
def on_signaling_state_change():
    for transceiver in pc.getTransceivers():
        if transceiver.receiver and transceiver.receiver.track.kind == "video/rtx":
            pc.removeTrack(transceiver.receiver.track)

@pc.on("track")
def on_track(track):
    if track.kind == "video" and track.codec and track.codec.mimeType == "video/rtx":
        pc.removeTrack(track)

#  Set Page Config
st.set_page_config(page_title='PlacementGuru', page_icon='🧊', layout='wide')

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


# Set up tabs
tab1, tab2 = st.tabs(["Interview", "Viva"])

with tab1:
    # Text-to-Speech function
    def speak_text(text):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name
            tts = gTTS(text=text, lang="en")
            tts.save(temp_audio_path)

        with open(temp_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
        
        os.remove(temp_audio_path)

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
    # Create a temp video file
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    in_file = Path(temp_video.name)

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
        try:
            ctx = st.session_state.get("Start Interview")
            if ctx:
                state = ctx.state
                if not state.playing and not state.signalling:
                    if in_file.exists() and in_file.stat().st_size > 1000:
                        output_wav = RECORD_DIR / f"{prefix}_output.wav"
                        
                        subprocess.run(
                            ["ffmpeg", "-i", str(in_file), "-vn", "-acodec", "pcm_s16le", str(output_wav)],
                            check=True,
                            capture_output=True
                        )

                        st.session_state['audio_file_path'] = str(output_wav)
                        st.session_state['stream_ended_and_file_saved'] = True
                        
                        # Fix event loop issue
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        # Delete temp video file after processing
                        in_file.unlink(missing_ok=True)

        except Exception as e:
            st.error(f"Conversion error: {str(e)}")

    # Handle media recorder for WebRTC (Temp File)
    def in_recorder_factory() -> MediaRecorder:
        temp_dir = tempfile.mkdtemp()  # Create a temporary directory
        temp_file = Path(temp_dir) / "recorded_video.mp4"  # Define temp file path
        return MediaRecorder(str(temp_file), format="mp4")

    # Safely redirect to report page
    def redirect_to_report():
        try:
            if st.session_state.get('audio_file_path') and os.path.exists(st.session_state['audio_file_path']):
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
                st.balloons()

    # Input section
    col1, col2 = st.columns([1, 1])

    with col1:
        role = st.text_input('Role', placeholder='What role are you seeking?')
        sec1, sec2 = st.columns(2)
        with sec1:
            company = st.selectbox('Company', options=('Google', 'Meta', 'Wipro', 'Accenture', 'Other'))
            difficulty_level = st.selectbox('Difficulty', options=('Beginner', 'Intermediate', 'Expert'))
        with sec2:
            interviewer_type = st.selectbox('Interviewer', options=('Professional', 'Technical', 'Behaviour', 'Friendly'))
            company_type = st.text_input("Company Type")
            button_click = st.button("Search")

    # WebRTC streamer
    with col2:
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
            rtc_configuration=rtc_Configuration
        )

    if st.session_state.get('stream_ended_and_file_saved'):
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

     


with tab2:
    
    # Columns for input
    col1, col2 = st.columns(2)

    with col1.container(height=350):
        uploaded_files = st.file_uploader(
        "Upload your BlackBook/ Project File", accept_multiple_files=True
        )
        # for uploaded_file in uploaded_files:
        #     bytes_data = uploaded_file.read()
        #     st.write("filename:", uploaded_file.name)
        #     st.write(bytes_data)

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
            rtc_configuration=rtc_Configuration
        )

        if st.session_state.get('stream_ended_and_file_saved'):
            redirect_to_report()
    # with st.sidebar:
    #     st.logo("assets\\img.png")

    st.divider()
    