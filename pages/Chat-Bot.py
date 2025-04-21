import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Chat with PlacementGuru AI!",
    page_icon=":brain:",  # Favicon emoji
    layout="centered",  # Page layout option
)

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-1.5-flash')

# Function to translate roles between Gemini-Pro and Streamlit terminology
def translate_role_for_streamlit(user_role):
    if user_role == "model":
        return "assistant"
    else:
        return user_role

# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(
            history=[
                {
                "role": "user",
                "parts": [
                    "I am PlacementGuru, an AI career advisor. I will only answer questions related to job placements, interview preparation, resume tips, soft skills, career advice, internships, and technical questions related to careers. If a question is not related to careers or placements, i will not be able to answer."
                    ]
                }
            ])

# Add a button to clear the chat
if st.button("Clear Chat"):
    st.session_state.chat_session = model.start_chat(history=[])  # Reset the chat session

# Display the chatbot's title on the page
st.title("🤖 PlacementGuru AI")

# Display the chat history
for message in st.session_state.chat_session.history:
    # Skip the initial system-like user prompt
    if message.parts[0].text.startswith("I am PlacementGuru Chatbot: Designed to help you with your career-related queries."):
        continue
    with st.chat_message(translate_role_for_streamlit(message.role)):
        st.markdown(message.parts[0].text)


# Input field for user's message
user_prompt = st.chat_input("Ask PlacementGuru AI...")
if user_prompt:
    # Add user's message to chat and display it
    st.chat_message("user").markdown(user_prompt)
    if "who are you" in user_prompt.lower() or "your name" in user_prompt.lower():
        bot_response = "I am PlacementGuru, your AI assistant here to guide you in placements and career-related queries. 😊"
    elif "your developer" in user_prompt.lower() or "who created you" in user_prompt.lower() or "who made you" in user_prompt.lower():
        bot_response = "I was developed by Abdul Rehman Khams & Abu Sufiyan Shaikh."
    else:
        # Send user's message to Gemini-Pro and get the response
        gemini_response = st.session_state.chat_session.send_message(user_prompt)
        bot_response = gemini_response.text

    # Display Gemini-Pro's response
    with st.chat_message("assistant"):
        st.markdown(bot_response)
