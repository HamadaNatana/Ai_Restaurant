import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# REMOVED: import requests (No longer needed for local Ollama)
import streamlit as st
import ollama  # ADDED: Local AI Library

from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar

generate_sidebar()

require_role(["VISITOR", "CUSTOMER", "VIP"])

# Optional: dotenv (if installed)
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return

# ---------------- Django setup ----------------

import django

BASE_DIR = Path(__file__).resolve().parent.parent  # project root (where manage.py lives)

# Correct project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant.settings")

try:
    django.setup()
except Exception as e:
    st.error(f"Django setup failed: {e}")

from ai_assist.models import KBEntry, AIAnswer, AIRating, KBFlag
from accounts.models import Customer, Manager

# ---------------- Env / Config ----------------

load_dotenv(BASE_DIR / ".env")

# REMOVED: HF_API_TOKEN, HF_MODEL, HF_API_URL logic
# We now rely on the local 'ollama' server running in the background.


# -----------------------------------------------------
# REAL LOGIN DETECTION (UC03 → Streamlit via query params)
# -----------------------------------------------------

def resolve_logged_in_user():
    """
    Django redirects here with:
        http://localhost:8506/ai_chat_streamlit?username=john&role=VIP
    """
    qp = st.query_params

    username = qp.get("username", [""])[0]
    role = qp.get("role", ["VISITOR"])[0]

    if not username:
        # Fallback when page is opened directly (not via Django)
        return "demo_customer", "CUSTOMER"

    # If manager exists with that username
    if Manager.objects.filter(user__username=username).exists():
        return username, "MANAGER"

    # If customer exists with that username
    cust = Customer.objects.filter(username=username).first()
    if cust:
        if cust.status == Customer.STATUS_VIP:
            return username, "VIP"
        return username, "CUSTOMER"

    # Default: visitor
    return username, role or "VISITOR"


# -----------------------------------------------------
# Helpers
# -----------------------------------------------------

def get_customer_for_username(username: str) -> Optional[Customer]:
    try:
        cust = Customer.objects.filter(username=username).first()
        if not cust:
            cust = Customer.objects.filter(user__username=username).first()
        return cust
    except Exception:
        return None


def find_local_answer(question: str) -> Optional[KBEntry]:
    """
    UC20 – Search KBEntry in DB with simple fuzzy match.
    """
    q = (question or "").lower().strip().strip("?")
    if not q:
        return None

    try:
        for entry in KBEntry.objects.filter(active=True):
            kbq = (entry.question or "").lower().strip().strip("?")
            if kbq and (kbq in q or q in kbq):
                return entry
    except Exception:
        return None

    return None


# -----------------------------------------------------
# LOCAL OLLAMA FALLBACK (UC20) -- REPLACED HF LOGIC
# -----------------------------------------------------

def ollama_chat(question: str, history: List[Dict]) -> str:
    """
    UC20 – External LLM fallback using Local Mistral (Ollama).
    """
    system_instructions = """
    You are the AI assistant for an AI-enabled Online Restaurant Order & Delivery System.

    ONLY talk about:
    - menu items, ingredients, allergens
    - ordering, delivery, deposits, VIP rules and benefits
    - warnings, complaints, discussion board features
    - how to use this restaurant app

    If the user asks about anything else (e.g., politics, math, life advice),
    reply exactly with:
    "I can only answer questions about this restaurant and this app."

    Do NOT invent new discounts, VIP rules, or policies.
    If you are unsure, say you don't know and ask the user to contact the manager.
    """

    # Build the messages list for Ollama
    # 1. Start with the system prompt
    messages = [{'role': 'system', 'content': system_instructions}]

    # 2. Add history (convert 'assistant'/'user' roles if needed)
    # Streamlit stores history as 'user'/'assistant', which matches Ollama API perfectly.
    for msg in history[-6:]: # Keep context short (last 6 messages)
        # Filter out keys that might confuse Ollama (like 'source')
        clean_msg = {'role': msg['role'], 'content': msg['content']}
        messages.append(clean_msg)

    # 3. Add the current question
    messages.append({'role': 'user', 'content': question})

    try:
        response = ollama.chat(model='mistral', messages=messages)
        answer = response['message']['content']
        return answer

    except Exception as e:
        # Fallback if Ollama is not running or crashes
        return (
            f"Error: The local AI service is unavailable ({str(e)}). "
            "Please ensure 'ollama run mistral' is running in the terminal."
        )


# -----------------------------------------------------
# Session Handling
# -----------------------------------------------------

def init_session(username: str, role: str):
    """
    Initialize Streamlit session with real login info from Django.
    """
    if "username" not in st.session_state:
        st.session_state.username = username
    if "role" not in st.session_state:
        st.session_state.role = role

    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of {role, content, source}

    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None  # {"ai_answer_id": str, "source": str}


def add_message(role: str, content: str, source: Optional[str] = None):
    st.session_state.messages.append(
        {"role": role, "content": content, "source": source}
    )


# -----------------------------------------------------
# Chat logic (UC20)
# -----------------------------------------------------

def handle_user_question(question: str):
    if not question.strip():
        st.warning("Please enter a question.")
        return

    add_message("user", question, None)

    # 1. Try Local DB
    kb_entry = find_local_answer(question)
    
    if kb_entry:
        answer_text = kb_entry.answer
        source = "kb"
    else:
        # 2. Try Local LLM (Ollama) - CHANGED FROM HF_CHAT
        with st.spinner("Asking Mistral AI..."):
            answer_text = ollama_chat(question, st.session_state.messages)
        source = "llm"

    # Persist AIAnswer
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
    st.session_state.last_answer = {
        "ai_answer_id": ai_answer_id,
        "source": source,
    }


def render_chat_panel():
    st.markdown("### Conversation")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input(
        "Ask a question about menu, VIP, deposits, warnings, delivery, or allergies..."
    )
    if user_input:
        handle_user_question(user_input)
        st.rerun()


# -----------------------------------------------------
# Ratings (UC21)
# -----------------------------------------------------

def render_rating_panel():
    st.markdown("### Rate the Last Answer")

    last = st.session_state.last_answer
    if not last or not last.get("ai_answer_id"):
        st.info("Ask a question first, then you can rate the AI's answer here.")
        return

    ai_answer = AIAnswer.objects.filter(
        ai_answer_id=last["ai_answer_id"]
    ).first()
    if not ai_answer:
        st.error("Internal error: last answer not found in database.")
        return

    source_label = (
        "Local Knowledge Base" if ai_answer.source == "kb" else "External LLM (Mistral)"
    )
    st.write(f"**Answer source:** {source_label}")

    with st.expander("Preview last answer", expanded=False):
        st.markdown(f"> {ai_answer.answer}")

    rating = st.slider("Rating (0–5 stars)", min_value=0, max_value=5, value=5, step=1)
    comment = st.text_input(
        "Optional comment (especially useful if you select 0):",
        value="",
        key="rating_comment",
    )

    if st.button("Submit Rating"):
        username = st.session_state.username or "anonymous"
        customer = get_customer_for_username(username)

        try:
            AIRating.objects.create(
                customer_id=customer,
                ai_answer_id=ai_answer,
                stars=rating,
            )
        except Exception as e:
            st.error(f"Could not save rating to database: {e}")
            return

        # Rating 0 + KB → create KBFlag for manager review
        if rating == 0 and ai_answer.source == "kb" and ai_answer.kb_id:
            try:
                KBFlag.objects.get_or_create(
                    customer_id=customer,
                    report_id=ai_answer.kb_id,
                    defaults={
                        "reason": comment or "Flagged as outrageous by user."
                    },
                )
                st.success(
                    "Rating saved. This local KB answer was rated 0 and flagged for manager review."
                )
            except Exception as e:
                st.error(f"Rating saved, but could not flag KB entry: {e}")
        else:
            st.success("Thank you! Your rating has been saved.")


# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():
    # Get real user + role from Django redirect
    username, role = resolve_logged_in_user()
    init_session(username, role)

    st.set_page_config(
        page_title="AI Restaurant – AI Chat",
        page_icon="🤖",
        layout="wide",
    )

    st.markdown(
        """
        <div style="background-color:#111827;padding:10px 16px;border-radius:0 0 8px 8px;">
            <h2 style="color:white;margin:0;">AI Customer Service Chat</h2>
            <p style="color:#9ca3af;margin:2px 0 0 0;font-size:13px;">
                UC20 – Local KB first, then Local Mistral AI fallback &nbsp;&nbsp;|&nbsp;&nbsp;
                UC21 – Rate answers 0–5 and flag bad KB content for manager review
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Logged in as **{username}** | Role: **{role}**")

    col1, col2 = st.columns([2, 1])

    with col1:
        render_chat_panel()

    with col2:
        st.markdown("#### User Info")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        st.markdown("---")
        render_rating_panel()

        st.markdown("---")
        st.markdown("#### System Status")
        st.write("AI Model: **Local Mistral (Ollama)**")
        st.write("Status: **Active**")
        st.caption("Running locally on port 11434")

        st.markdown("---")
        st.info(
            "- UC20: Local KB (KBEntry) is used first; if no match, Local Mistral AI is called.\n"
            "- UC21: Every answer can be rated 0–5; rating 0 on a **local KB** answer "
            "also flags it for manager review (KBFlag)."
        )

    st.markdown("---")
    st.caption(
        "Implements UC20 & UC21: hybrid local + LLM chat, with rating and flagging stored in Django models."
    )


if __name__ == "__main__":
    main()