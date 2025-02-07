import streamlit as st
from interview import interview_tab
from viva import viva_tab  

st.set_page_config(page_title='PlacementGuru', page_icon='🧊', layout='wide')

tab1, tab2 = st.tabs(["Interview", "Viva"])

with tab1:
    interview_tab()

with tab2:
    viva_tab()  
