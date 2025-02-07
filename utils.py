import time
import streamlit as st
from pathlib import Path
import moviepy as mp
import uuid
from aiortc.contrib.media import MediaRecorder

RECORD_DIR = Path("records")
RECORD_DIR.mkdir(exist_ok=True)

def get_recording_file():
    if "prefix" not in st.session_state:
        st.session_state["prefix"] = str(uuid.uuid4())
    prefix = st.session_state["prefix"]
    return RECORD_DIR / f"{prefix}_input.mp4"

def convert_to_wav():
    in_file = get_recording_file()
    if in_file.exists():
        time.sleep(1)
        output_wav = RECORD_DIR / f"{st.session_state['prefix']}_output.wav"
        try:
            video = mp.VideoFileClip(str(in_file))
            video.audio.write_audiofile(str(output_wav), codec='pcm_s16le')
            st.session_state['audio_file_path'] = str(output_wav)  # Store path
            st.session_state['stream_ended_and_file_saved'] = True
        except Exception as e:
            st.error(f"Error converting video to audio: {e}")
            st.session_state['stream_ended_and_file_saved'] = False

def in_recorder_factory():
    return MediaRecorder(str(get_recording_file()), format="mp4")
