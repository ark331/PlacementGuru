import streamlit as st

def set_footer():
    st.markdown("""
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #222;
            text-align: center;
            padding: 15px 10px;
            font-size: 14px;
            color:black;
            background:#849baa;
        }
        .footer a{
            text-decoration:none;
            color:white;
            
        }
        .footer a:hover{
            color:#efff4b
        }
        
        .social-icons img {
            width: 24px;
            height: 24px;
            margin: 0 15px; /* Adds space between icons */
            vertical-align: middle;
        }
        </style>
        <div class="footer">
            <b>Developed By Abdul Rehman Khams & Abu Sufiyan Shaikh.</b>  <br>
            © 2025 All rights reserved.
                <br>
            <br>
            <span class="social-icons">
                <a href="https://github.com/yourgithub" target="_blank">
                    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg">
                </a>
                <a href="https://linkedin.com/in/yourlinkedin" target="_blank">
                    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg">
                </a>
            </span>
        </div>
    """, unsafe_allow_html=True)