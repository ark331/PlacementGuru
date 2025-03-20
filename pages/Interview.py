import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import whisper
import queue
import numpy as np
import threading
import google.generativeai as genai
import json
import tempfile
import os
from gtts import gTTS

# Load Whisper Model
model = whisper.load_model("base")

# Queue for audio processing
audio_queue = queue.Queue()

# Configure Gemini API
genai.configure(api_key=st.secrets["gemini"]["GEMINI_API_KEY"])

# RTC Configuration with STUN Servers
rtc_configuration = RTCConfiguration(
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
    }
)

# Function to transcribe audio in real-time
def transcribe_audio():
    while True:
        audio_frames = []
        while not audio_queue.empty():
            frame = audio_queue.get()
            audio_frames.append(frame)

        if audio_frames:
            # Convert audio frames to NumPy array
            audio_np = np.concatenate(
                [np.frombuffer(f.to_ndarray().tobytes(), dtype=np.int16) for f in audio_frames]
            )

            # Save as WAV file
            with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio:
                temp_audio.write(audio_np.tobytes())
                temp_audio.flush()

                # Transcribe with Whisper
                result = model.transcribe(temp_audio.name)
                st.session_state["transcription"] = result["text"]

# Audio callback function for WebRTC
def audio_callback(frame: av.AudioFrame):
    audio_queue.put(frame)

# Function to fetch AI-generated interview questions
def get_interview_questions(role, company, interviewer_type, company_type, difficulty_level):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = json.load(open("prompts/prompts.json"))

    response = model.generate_content(
        prompt.get("interviewer").format(
            role=role,
            company=company,
            interviewer_type=interviewer_type,
            difficulty_level=difficulty_level,
            company_type=company_type,
        )
    )

    return json.loads(response.text)

# Function for text-to-speech
def speak_text(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        tts = gTTS(text=text, lang="en")
        tts.save(temp_audio.name)

        with open(temp_audio.name, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

        os.remove(temp_audio.name)

# Streamlit UI Layout
st.set_page_config(page_title="PlacementGuru", page_icon="🧊", layout="wide")

# Tabs for Interview & Viva
tab1, tab2 = st.tabs(["Interview", "Viva"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        role = st.text_input("Role", placeholder="Enter role")
        company = st.selectbox("Company", ["Google", "Meta", "Wipro", "Accenture", "Other"])
        difficulty_level = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Expert"])
        interviewer_type = st.selectbox("Interviewer Type", ["Professional", "Technical", "Behavioral"])
        company_type = st.text_input("Company Type")

        if st.button("Generate Questions"):
            if role:
                st.session_state["questions"] = get_interview_questions(
                    role, company, interviewer_type, company_type, difficulty_level
                )["questions"]
                st.session_state["current_question"] = st.session_state["questions"][0]

    with col2:
        webstream = webrtc_streamer(
            key="interview",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={
                "video": {"width": 960, "height": 440, "frameRate": 30},
                "audio": {
                    "sampleRate": 16000,
                    "sampleSize": 16,
                    "echoCancellation": True,
                    "noiseSuppression": True,
                    "channelCount": 1,
                },
            },
            audio_receiver_size=1024,
            rtc_configuration=rtc_configuration,
            async_processing=True,
        )

        if webstream.state.playing:
            threading.Thread(target=transcribe_audio, daemon=True).start()

    # Display transcribed text
    if "transcription" in st.session_state:
        st.markdown(f"**📝 Transcribed Text:** {st.session_state['transcription']}")

    # Display current interview question
    if "current_question" in st.session_state:
        st.subheader("Current Question:")
        st.write(f"**{st.session_state['current_question']}**")

        if st.button("Next Question"):
            if st.session_state["questions"]:
                st.session_state["current_question"] = st.session_state["questions"].pop(0)
                speak_text(st.session_state["current_question"])
            else:
                st.success("Interview Completed 🎉")
                st.balloons()

with tab2:
    st.write("### Viva Section")

    uploaded_files = st.file_uploader("Upload your Project Files", accept_multiple_files=True)

    viva_stream = webrtc_streamer(
        key="viva",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": {"width": 960, "height": 440},
            "audio": {
                "sampleRate": 16000,
                "sampleSize": 16,
                "echoCancellation": True,
                "noiseSuppression": True,
                "channelCount": 1,
            },
        },
        rtc_configuration=rtc_configuration,
    )
