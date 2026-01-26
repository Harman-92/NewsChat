import streamlit as st

def render_sidebar():
    st.sidebar.page_link("main.py", label="🏠 Home")
    st.sidebar.page_link("pages/1_Highlights.py", label="📰 News Highlights")
    st.sidebar.page_link("pages/2_Chatbot.py", label="🤖 Chatbot")