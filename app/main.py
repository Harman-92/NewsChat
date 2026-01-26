import streamlit as st

from app.utils import render_sidebar

st.set_page_config(page_title="Home", layout="wide")

render_sidebar()
st.title("News")
st.caption("Use the sidebar to open **Highlights**.")
