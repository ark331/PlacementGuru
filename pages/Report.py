import streamlit as st
from core.speech_to_text import recognize_speech_to_text
import google.generativeai as genai
import os
from dotenv import load_dotenv
from matplotlib import pyplot as plt

st.set_page_config(page_icon="🧊",page_title="PlacementGuru | Report")

# Load environment variables
load_dotenv()
genai.configure(api_key=st.secrets["gemini"]["GEMINI_API_KEY"])

b_click = st.button("< Back to Interview Page")
if b_click:
    st.switch_page("./pages/Interview.py")  
# Set up the Streamlit app
st.title("Analysis Report")

if "audio_file_path" not in st.session_state:
    st.error("No recording found! Please complete an interview first.")
    st.stop()

# File name for the audio to be transcribed
file_name = st.session_state["audio_file_path"]

def get_gemini_suggestions(transcript):
    prompt = (
        f"Give me suggestions on how to avoid using filler words like from {transcript} 'you know' during a conversation in an interview in 5-6 lines."
    )
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip() if response else "No suggestions found."

# Transcribing Audio
section_1, section_2 = st.columns([1, 1])
with section_1.container(height=500):     
    # st.session_state="transcripting_audio"
    with st.spinner("Transcribing Audio, it would take a few minutes."):
        result = recognize_speech_to_text(str(file_name))
        st.success("Transcription Completed", icon="✅")

        st.write(result["text"])

        suggestions = get_gemini_suggestions(result["text"])
        st.write("### Suggestions to Avoid Filler Words:")
        st.write(suggestions)

with section_2.container(height=500):
    def check_filler_words(transcript):
            filler_words = ["um", "uh", "you know", "like", "so", "actually", "basically", "I mean"]
            
            # Convert transcript to lowercase and split into words
            transcript_lower = transcript.lower()  
            words = transcript_lower.split()
            
            total_words = len(words)
            filler_count = sum(words.count(filler) for filler in filler_words)
            non_filler_count = total_words - filler_count

            filler_percentage = (filler_count / total_words * 100) if total_words > 0 else 0

            st.write(f"The total words in this transcript: {total_words}")
            st.write(f"The total filler count in this transcript: {filler_count}")
            st.write(f"The filler percentage in this transcript: {filler_percentage:.2f}%")
            st.write(f"The non-filler count in this transcript: {non_filler_count}")

            #  Fix: `sizes` must contain numbers, not lists
            labels = ["Filler Words", "Non-Filler Words"]
            sizes = [filler_count, non_filler_count]  # Fix: filler_count, not filler_words (which is a list!)
            colors = ["#ff9999", "#66b3ff"]

            fig, ax = plt.subplots(figsize=(5, 3))  # Smaller size
            ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

            plt.gca().set_facecolor("black")  # Set the background color to black
            plt.title("Filler vs Non-Filler Words", color="white")  # Title in white for contrast
            st.pyplot(fig)
        
    if "text" in result:
        st.write(check_filler_words(result["text"]))
    else:
        st.write("Error: Transcription text not found.")

    
