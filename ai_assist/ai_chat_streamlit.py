import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import requests
import streamlit as st

# Optional: dotenv (if installed)
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return

# ---------------- Django setup ----------------

import django

BASE_DIR = Path(__file__).resolve().parent.parent

# UPDATE: Correct project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant.settings")

try:
    django.setup()
except Exception as e:
    st.error(f"Django setup failed: {e}")

from ai_assist.models import KBEntry, AIAnswer, AIRating, KBFlag
from accounts.models import Customer, Manager

# ---------------- Env / HF config ----------------

load_dotenv(BASE_DIR / ".env")

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "gpt2")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


# -----------------------------------------------------
# REAL LOGIN DETECTION (UC03)
# -----------------------------------------------------

def resolve_logged_in_user():
    """
    Streamlit receives username + role from Django login redirect:
    http://localhost:8506/ai_chat_streamlit?username=john&role=VIP
    """

    qp = st.query_params

    username = qp.get("username", None)
    role = qp.get("role", "VISITOR")

    if not username:
        return None, "VISITOR"

    # If manager exists with username
    if Manager.objects.filter(user__username=username).exists():
        return username, "MANAGER"

    # If customer exists
    cust = Customer.objects.filter(username=username).first()
    if cust:
        return username, "VIP" if cust.status == Customer.STATUS_VIP else "CUSTOMER"

    return username, "VISITOR"


# -----------------------------------------------------
# Helpers
# -----------------------------------------------------

def get_customer_for_username(username: str) -> Optional[Customer]:
    try:
        cust = Customer.objects.filter(user__username=username).first()
        if not cust:
            cust = Customer.objects.filter(username=username).first()
        return cust
    except Exception:
        return None


def find_local_answer(question: str) -> Optional[KBEntry]:
    q = (question or "").lower().strip().strip("?")
    if not q:
        return None

    for entry in KBEntry.objects.filter(active=True):
        kbq = (entry.question or "").lower().strip().strip("?")
        if kbq and (kbq in q or q in kbq):
            return entry

    return None


# -----------------------------------------------------
# HF LLM fallback
# -----------------------------------------------------

def build_hf_prompt(question: str, history: List[Dict]) -> str:
    system_instructions = """
You are the AI assistant for an AI-enabled Online Restaurant Order & Delivery System.
ONLY talk about:
- menu items, ingredients, allergens
- ordering, delivery, deposits, VIP rules and benefits
- warnings, complaints, discussion board features
- how to use this restaurant app
"""

    convo_lines = []
    for msg in history[-6:]:
        role = "Customer" if msg.get("role") == "user" else "Assistant"
        convo_lines.append(f"{role}: {msg.get('content', '')}")

    convo_text = "\n".join(convo_lines) or "(no previous messages)"

    return (
        system_instructions.strip()
        + "\n\nPrevious conversation:\n"
        + convo_text
        + f"\n\nCustomer: {question}\nAssistant:"
    )


def hf_chat(question: str, history: List[Dict]) -> str:
    if not HF_API_TOKEN:
        return "External AI service not configured."

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": build_hf_prompt(question, history),
        "parameters": {"max_new_tokens": 256, "temperature": 0.4},
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        full_text = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
        if "Assistant:" in full_text:
            return full_text.split("Assistant:", 1)[1].strip()
        return full_text.strip()

    except Exception:
        return "Sorry, the external AI service is currently unavailable."


# -----------------------------------------------------
# Session Handling
# -----------------------------------------------------

def init_session(username, role):

    st.session_state.username = username
    st.session_state.role = role

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None


def add_message(role: str, content: str, source: Optional[str] = None):
    st.session_state.messages.append({"role": role, "content": content, "source": source})


# -----------------------------------------------------
# Chat logic
# -----------------------------------------------------

def handle_user_question(question: str):

    if not question.strip():
        st.warning("Please enter a question.")
        return

    add_message("user", question, None)

    kb_entry = find_local_answer(question)
    if kb_entry:
        answer_text = kb_entry.answer
        source = "kb"
    else:
        answer_text = hf_chat(question, st.session_state.messages)
        source = "llm"

    try:
        ai_answer = AIAnswer.objects.create(
            kb_id=kb_entry if kb_entry else None,
            question=question,
            answer=answer_text,
            source=source,
        )
        ai_answer_id = str(ai_answer.ai_answer_id)
    except Exception as e:
        ai_answer_id = None
        st.error(f"Could not save AI answer: {e}")

    add_message("assistant", answer_text, source)
    st.session_state.last_answer = {"ai_answer_id": ai_answer_id, "source": source}


def render_chat_panel():
    st.markdown("### Conversation")

    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.write(msg["content"])

    user_input = st.chat_input("Ask something...")
    if user_input:
        handle_user_question(user_input)
        st.rerun()


# -----------------------------------------------------
# Ratings
# -----------------------------------------------------

def render_rating_panel():

    last = st.session_state.last_answer
    if not last or not last.get("ai_answer_id"):
        st.info("Ask a question to enable rating.")
        return

    ai_answer = AIAnswer.objects.filter(ai_answer_id=last["ai_answer_id"]).first()
    if not ai_answer:
        st.error("Error loading answer from database.")
        return

    st.write(f"Source: {'Local KB' if ai_answer.source == 'kb' else 'External LLM'}")

    with st.expander("Preview Answer"):
        st.write(ai_answer.answer)

    rating = st.slider("Rating (0–5)", 0, 5, 5)
    comment = st.text_input("Optional comment:")

    if st.button("Submit Rating"):
        username = st.session_state.username
        customer = get_customer_for_username(username)

        AIRating.objects.create(customer_id=customer, ai_answer_id=ai_answer, stars=rating)

        if rating == 0 and ai_answer.source == "kb":
            KBFlag.objects.get_or_create(
                report_id=ai_answer.kb_id,
                defaults={"customer_id": customer, "reason": comment or "Flagged by user."},
            )
            st.success("KB entry flagged for manager review.")
        else:
            st.success("Rating saved.")


# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():

    username, role = resolve_logged_in_user()
    init_session(username, role)

    st.set_page_config(page_title="AI Chat", page_icon="🤖", layout="wide")

    st.title("AI Customer Service Chat (UC20–21)")
    st.caption(f"Logged in as **{username}** | Role: **{role}**")

    col1, col2 = st.columns([2, 1])

    with col1:
        render_chat_panel()

    with col2:
        st.subheader("Rate Last Answer")
        render_rating_panel()


if __name__ == "__main__":
    main()
