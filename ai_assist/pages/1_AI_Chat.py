import os
import csv
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
import streamlit as st

# -------------------------------------------------
# Paths & data files
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # ai_assist/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

KB_CSV = DATA_DIR / "knowledge_base.csv"
KB_FLAGS_CSV = DATA_DIR / "kb_flags.csv"
AI_RATINGS_CSV = DATA_DIR / "ai_ratings.csv"

# -------------------------------------------------
# Env & Hugging Face config
# -------------------------------------------------
load_dotenv(BASE_DIR / ".env")

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
# You can change this to another model if you get access later
HF_MODEL = "gpt2"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------
# Local Knowledge Base (UC20 – part 1)
# -------------------------------------------------
def load_knowledge_base():
    """Return list of dict rows from local KB CSV."""
    items = []
    if not KB_CSV.exists():
        return items

    with open(KB_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items.extend(reader)
    return items


def find_local_answer(question: str):
    """
    Simple fuzzy match:
    - lowercase
    - strip '?'
    - match if stored question is substring of user q or vice versa
    Returns the KB row or None.
    """
    q = question.lower().strip().strip("?")
    if not q:
        return None

    for row in load_knowledge_base():
        kbq = row["question"].lower().strip().strip("?")
        if kbq and (kbq in q or q in kbq):
            return row
    return None


def append_kb_flag(kb_id: str, flagged_by: str, rating: int, comment: str):
    """
    UC21 – store rating 0 ("outrageous") for manager review.
    """
    exists = KB_FLAGS_CSV.exists()
    with open(KB_FLAGS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["kb_id", "flagged_by", "rating", "comment", "created_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "kb_id": kb_id,
                "flagged_by": flagged_by,
                "rating": rating,
                "comment": comment,
                "created_at": now_str(),
            }
        )


def append_ai_rating(username: str, source: str, kb_id, question: str,
                     answer: str, rating: int, comment: str):
    """
    UC21 – log every rating (for both KB + LLM answers) into ai_ratings.csv.
    """
    exists = AI_RATINGS_CSV.exists()
    with open(AI_RATINGS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "username",
            "source",        # "kb" or "llm"
            "kb_id",         # may be None/"" for llm answers
            "question",
            "answer",
            "rating",
            "comment",
            "created_at",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "username": username,
                "source": source,
                "kb_id": kb_id or "",
                "question": question,
                "answer": answer,
                "rating": rating,
                "comment": comment,
                "created_at": now_str(),
            }
        )


# -------------------------------------------------
# Hugging Face LLM (UC20 – fallback)
# -------------------------------------------------
def build_hf_prompt(question: str, history: list[dict]):
    """
    Build a prompt that keeps the model within restaurant domain.

    history: list of {"role": "user"/"assistant", "content": "...", "source": "kb"/"llm"}
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

    convo_lines = []
    for msg in history[-6:]:
        role = "Customer" if msg["role"] == "user" else "Assistant"
        convo_lines.append(f"{role}: {msg['content']}")

    convo_text = "\n".join(convo_lines) if convo_lines else "(no previous messages)"

    prompt = (
        system_instructions.strip()
        + "\n\nPrevious conversation:\n"
        + convo_text
        + f"\n\nCustomer: {question}\nAssistant:"
    )
    return prompt


def hf_chat(question: str, history: list[dict]) -> str:
    """
    Call Hugging Face Inference API.

    If HF returns an error (like 410), we *hide* the ugly error from the user
    and show the UC20-friendly "AI unavailable" message instead.
    """
    if not HF_API_TOKEN:
        return (
            "The external AI service is not configured. "
            "Please contact the manager or system administrator."
        )

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": build_hf_prompt(question, history),
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.4,
        },
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list) and data:
            full_text = data[0].get("generated_text", "")
        else:
            full_text = data.get("generated_text", "")

        if "Assistant:" in full_text:
            answer = full_text.split("Assistant:", 1)[1].strip()
        else:
            answer = full_text.strip()

        return answer or "(The AI did not return any content.)"

    except Exception:
        # For you (developer) – you can log the real error in terminal if needed
        # print("Hugging Face error:", e)
        # For the user – UC20 exceptional flow: LLM unavailable
        return (
            "Sorry, the external AI service is currently unavailable. "
            "Please try again later or contact the manager."
        )


# -------------------------------------------------
# Session helpers for chat state
# -------------------------------------------------
def init_session():
    # user identity (would normally come from UC03 login)
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = "CUSTOMER"

    if "messages" not in st.session_state:
        st.session_state.messages = []  # list[{role, content, source}]
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = None  # {"question","answer","source","kb_id"}


def add_message(role: str, content: str, source: str | None = None):
    st.session_state.messages.append(
        {"role": role, "content": content, "source": source}
    )


# -------------------------------------------------
# UI rendering
# -------------------------------------------------
def render_header():
    st.markdown(
        """
        <div style="background-color:#111827;padding:10px 16px;border-radius:0 0 8px 8px;">
            <h2 style="color:white;margin:0;">AI Customer Service Chat</h2>
            <p style="color:#9ca3af;margin:2px 0 0 0;font-size:13px;">
                UC20 – Local KB first, then external AI fallback &nbsp;&nbsp;|&nbsp;&nbsp;
                UC21 – Rating every answer (0–5) with 0-star flagging for KB replies
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_panel():
    st.markdown("### Conversation")

    # past messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            label = "AI"
            if msg["source"] == "kb":
                label = "AI (Local KB)"
            elif msg["source"] == "llm":
                label = "AI (External LLM – Hugging Face)"

            with st.chat_message("assistant"):
                st.markdown(f"**{label}:**")
                st.write(msg["content"])

    # input
    user_input = st.chat_input(
        "Ask a question about menu, VIP, deposits, warnings, delivery, or allergies..."
    )
    if user_input:
        handle_user_question(user_input)
        # make first question+answer visible immediately
        st.rerun()


def handle_user_question(question: str):
    # store the user message
    add_message("user", question, None)

    # 1) Try local KB
    kb_row = find_local_answer(question)
    if kb_row:
        answer_text = kb_row["answer"]
        source = "kb"
        kb_id = kb_row.get("kb_id")
    else:
        # 2) Fallback to HF LLM (may return "AI unavailable" text if HF fails)
        history = st.session_state.messages
        answer_text = hf_chat(question, history)
        source = "llm"
        kb_id = None

    add_message("assistant", answer_text, source)
    st.session_state.last_answer = {
        "question": question,
        "answer": answer_text,
        "source": source,
        "kb_id": kb_id,
    }


def render_rating_panel():
    st.markdown("### Rate the Last Answer")

    last = st.session_state.last_answer
    if not last:
        st.info("Ask a question first, then you can rate the AI's answer here.")
        return

    source_label = "Local Knowledge Base" if last["source"] == "kb" else "External LLM"
    st.write(f"**Answer source:** {source_label}")

    with st.expander("Preview last answer", expanded=False):
        st.markdown(f"> {last['answer']}")

    rating = st.slider("Rating (0–5 stars)", min_value=0, max_value=5, value=5, step=1)
    comment = st.text_input(
        "Optional comment (especially useful if you select 0):",
        value="",
        key="rating_comment",
    )

    if st.button("Submit Rating"):
        username = st.session_state.username or "anonymous"
        append_ai_rating(
            username=username,
            source=last["source"],
            kb_id=last["kb_id"],
            question=last["question"],
            answer=last["answer"],
            rating=rating,
            comment=comment,
        )

        # If rating 0 AND source is KB → flag for manager review
        if rating == 0 and last["source"] == "kb" and last["kb_id"]:
            append_kb_flag(
                kb_id=last["kb_id"],
                flagged_by=username,
                rating=rating,
                comment=comment or "Flagged as outrageous by user.",
            )
            st.success(
                "Rating saved. This local KB answer was rated 0 and flagged for manager review."
            )
        else:
            st.success("Thank you! Your rating has been saved.")


def main():
    st.set_page_config(
        page_title="AI Restaurant – AI Chat",
        page_icon="🤖",
        layout="wide",
    )
    init_session()
    render_header()

    col1, col2 = st.columns([2, 1])
    with col1:
        render_chat_panel()

    with col2:
        st.markdown("#### User Info")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        st.markdown("---")
        render_rating_panel()

        # Debug info – you can remove for final submission
        st.markdown("---")
        st.markdown("#### Debug Info (temporary)")
        st.write(f"HF Token Loaded: {HF_API_TOKEN is not None}")
        st.write(f"Model Selected: {HF_MODEL}")
        st.write(f"API URL: {HF_API_URL}")

        st.markdown("---")
        st.info(
            "Design notes:\n"
            "- UC20: Local KB is used first; if no match, an external LLM is called.\n"
            "- UC21: Every answer can be rated 0–5; rating 0 on a **local KB** answer "
            "also flags it for manager review (kb_flags.csv)."
        )

    st.markdown("---")
    st.caption(
        "Implements UC20 & UC21: hybrid local + LLM chat, plus rating and flagging."
    )


if __name__ == "__main__":
    main()
