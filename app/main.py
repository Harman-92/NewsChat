import streamlit as st
from app.utils import render_sidebar

st.set_page_config(page_title="NewsChat - Home", layout="wide")

render_sidebar()

st.title("🗞️ Welcome to NewsChat!")
st.markdown("""
### Stay informed with the latest news highlights and intelligent AI assistance

Use the sidebar to navigate:
- **📰 News Highlights** — Explore top stories and emerging clusters across categories  
- **🤖 Chatbot** — Ask questions and discuss news using AI-powered retrieval
""")
