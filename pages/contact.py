import streamlit as st
import smtplib
import os
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER") 

def send_email(user_name, user_email, user_message):
    """Sends an email where the Reply-To address is the user's email."""
    try:
        msg = EmailMessage()
        msg.set_content(f"Name: {user_name}\nEmail: {user_email}\nMessage:\n{user_message}")
        msg["Subject"] = f"This is {user_name} regarding PlacementGuru."
        msg["From"] = EMAIL_SENDER  
        msg["To"] = EMAIL_RECEIVER  
        msg["Reply-To"] = user_email  

        # Connect to SMTP server and send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        return True  # Email sent successfully
    except Exception as e:
        print("Error:", e)
        return False  # Email sending failed



st.set_page_config(page_title='PlacementGuru', layout='wide')
with st.form("contact_form"):
    name = st.text_input("Name",max_chars=100)
    email = st.text_input("Email")
    # phone_number = st.number_input("Phone Number")
    message = st.text_area("Message")
    button = st.form_submit_button("Submit")

    if button:
        if name and email and message:
            success = send_email(name, email, message)
            if success:
                st.success("Your message has been sent successfully! ✅ You will receive a response soon.")
            else:
                st.error("Failed to send the message. Please try again.")
        else:
            st.warning("Please fill in all fields.")

