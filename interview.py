import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from speech import speak_text, listen_and_analyze
from ai import search_on_gemini
from utils import convert_to_wav, in_recorder_factory

def start_interview():
    """ Speak and listen to one question at a time. """
    if st.session_state.get('pending_questions'):
        question = st.session_state['pending_questions'][0]  # Get current question
        st.session_state['current_question'] = question  # Store it for display
        speak_text(question)  # Speak the question
        st.session_state['listening'] = True

def next_question():
    """ Move to the next question, store the response, and continue the interview. """
    if st.session_state['listening']:
        response = listen_and_analyze()  # Get user's answer
        st.session_state['listening'] = False  # Stop listening

        # Store response
        question = st.session_state['pending_questions'].pop(0)
        st.session_state['responses'][question] = response

    # Move to next question
    if st.session_state['pending_questions']:
        st.session_state['current_question'] = st.session_state['pending_questions'][0]  # Update UI
        start_interview()  # Speak next question
    else:
        st.success("Interview completed!")

def interview_tab():
    st.title("PlacementGuru - Interview")

    col1, col2 = st.columns(2)
    with col1.container(height=350):
        sec1, sec2 = st.columns(2)
        with sec1:
            role = st.text_input('Role', placeholder='What role are you seeking for!')
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

            with st.spinner(text='Generating Questions...'):
                result = search_on_gemini(role, company, interviewer_type, difficulty_level, company_type)
                
                # Store questions in session state
                st.session_state['interview_questions'] = result['questions']
                st.session_state['pending_questions'] = result['questions'][:]
                st.session_state['current_question_index'] = 0  # Reset index
                st.session_state['listening'] = False  # Ensure it starts fresh
                
                # Display questions in UI
                st.subheader(result["topic-title"])
                for q in result['questions']:
                    st.markdown(f'- **{q}**')

                # Start interview (first question)
                start_interview()

    if "interview_questions" in st.session_state and st.session_state["interview_questions"]:
        st.subheader(st.session_state["interview_questions"][0])  # Display the first question

    if st.button("Next Question"):
        next_question()  # Move to the next question

