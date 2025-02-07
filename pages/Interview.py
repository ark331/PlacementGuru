import streamlit as st
from interview import interview_tab
from viva import viva_tab  

st.set_page_config(page_title='PlacementGuru', page_icon='🧊', layout='wide')

tab1, tab2 = st.tabs(["Interview", "Viva"])

with tab1:
    interview_tab()

with tab2:
<<<<<<< HEAD
    viva_tab()  
=======
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

# Extract audio in Wav format
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
        listen_and_analyze()
        if "pending_questions" in st.session_state and st.session_state["pending_questions"]:
            start_interview()
        else:
            st.success("All questions have been answered.")
            st.balloons()

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

    # if "current_question" in st.session_state:
    #     if st.button("Next Question"):
    #         next_question()
>>>>>>> 54034d2684872dbe351a682a3409558a21e16b8c
