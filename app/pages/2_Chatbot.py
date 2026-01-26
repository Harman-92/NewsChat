import streamlit as st
from app.config import settings
from app.services import make_weaviate_client
from app.utils import render_sidebar
from app.news_chat import NewsChat
import time


st.set_page_config(page_title="Chatbot", layout="wide")
st.title("Chatbot")
render_sidebar()


def stream_text(text: str, placeholder, delay: float = 0.03):
    rendered = ""
    for chunk in text.split(" "):
        rendered += chunk + " "
        placeholder.markdown(rendered)
        time.sleep(delay)


@st.cache_resource
def get_chatbot() -> NewsChat:
    client = make_weaviate_client()
    return NewsChat(weaviate_client=client, model=settings.MODEL)

chatbot = get_chatbot()

# Header with clear and new chat buttons
b1, b2, b3 = st.columns([8, 0.4, 0.4], gap="xsmall")
with b1:
    st.caption("Ask questions from your news data")
with b2:
    if st.button("🗑️", help="Clear messages"):
        st.session_state.messages = []
        st.session_state.last_prompt = None
        st.session_state.last_error = None
        st.rerun()
with b3:
    if st.button("📝", help="New chat"):
        st.session_state.chat_session_id = chatbot.create_session(
            user_id=st.session_state.chat_user_id
        )
        st.session_state.messages = []
        st.session_state.last_prompt = None
        st.session_state.last_error = None
        st.rerun()


# Styling for compact buttons
st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button {
        padding-top: 0.20rem !important;
        padding-bottom: 0.20rem !important;
        min-height: 1.75rem !important;
        height: 1.75rem !important;
        line-height: 1.1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Start new chat session
if "chat_user_id" not in st.session_state:
    st.session_state.chat_user_id = "streamlit_user"

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = chatbot.create_session(user_id=st.session_state.chat_user_id)

if "messages" not in st.session_state:
    st.session_state.messages = []


# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])


# Text input
prompt = st.chat_input("Ask anything about news highlights")

if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.write("Thinking...")

        try:
            answer = chatbot.query(
                user_id=st.session_state.chat_user_id,
                session_id=st.session_state.chat_session_id,
                message=prompt,
            )

            # If ADK produced no final text, show a clearer message (and enable Retry)
            if not answer or answer.strip() == "No response generated.":
                err = "No response generated (ADK returned no final response event)."
                placeholder.warning(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                st.session_state.last_error = err
            else:
                # placeholder.write(answer)
                stream_text(answer, placeholder)
                st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            err = f"Chat error: {e}"
            placeholder.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
            st.session_state.last_error = err
