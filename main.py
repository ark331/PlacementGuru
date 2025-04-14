import streamlit as st
import time

# Set page layout
st.set_page_config(page_title="PlacementGuru | Home", layout="wide", page_icon="🧊")

# CSS for styling with enhanced animations and colors
st.markdown("""
    <style>
        /* General Page Styles */
        body {
            background: linear-gradient(135deg, #ff8a00, #e52e71); /* Gradient background */
            font-family: 'Arial', sans-serif;
            color: white;
        }

        .container {
            display: flex;
            justify-content: space-between;
            padding: 5% 10%;
        }

        /* Text Box Styles */
        .text-box {
            font-size: 28px;
            font-weight: bold;
            color: white;
            line-height: 1.5;
        }

        h1 {
            font-size: 50px;
            color: #fff;
            animation: fadeIn 2s ease-in-out;
        }

        h2 {
            font-size: 30px;
            font-weight: 600;
            color: #f9f9f9;
            margin-top: 20px;
            animation: fadeIn 3s ease-in-out;
        }

        p {
            font-size: 18px;
            line-height: 1.6;
            animation: slideIn 2s ease-out;
        }

        i {
            font-style: italic;
            color: #f0f0f0;
        }

        /* Hover Effects for the Button */
        .btn-start {
            background-color: #ff7f50; 
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            border: none;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-start:hover {
            background-color: #e52e71;
            transform: scale(1.1);
        }

        .btn-start:active {
            transform: scale(1.05);
        }

        /* Image Box Styles */
        .image-box {
            margin-top: 50px;
            width: 100%;
            border-radius: 20px;
            box-shadow: 2px 2px 20px rgba(0, 0, 0, 0.2);
            transition: transform 0.4s ease-in-out;
        }

        .image-box:hover {
            transform: scale(1.05);
            box-shadow: 4px 4px 25px rgba(0, 0, 0, 0.4);
        }

        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    </style>
""", unsafe_allow_html=True)

# Layout with two columns
col1, col2 = st.columns([1, 1])

# Display text with animations
with col1:
    st.markdown(
        """
        <h1>Welcome to Placement Guru! 🚀</h1>
        <p>Your AI-driven Interview Preparation Partner.</p>
        <h2>How this Works</h2>
        <p>Step 1: Setup your microphone and camera. Then Click on start.</p>
        <p>Step 2: Fill the details of the Form. Click Submit.</p>
        <p>Step 3: Your interview will start. After completing all the questions click stop to submit your stream.</p>
        <i>If you are encountering any problem or you have any suggestions, feel free to contact us by sharing your thoughts.</i>
        <br><br>
        """,
        unsafe_allow_html=True
    )

    if st.button("Let's get started", key="start_button", help="Click here to begin"):
        st.switch_page("pages/Interview.py")

# Image on the right with hover effect
with col2:
    st.markdown('<div class="image-box">', unsafe_allow_html=True)
    st.image("./assets/interview.jpg", use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
