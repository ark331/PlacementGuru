import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from speech import speak_text, listen_and_analyze
from ai import search_on_gemini
from utils import convert_to_wav, in_recorder_factory


def viva_tab():
    upload_files = st.file_uploader(
        label = "Please Upload your PDF or Docx file."
    )