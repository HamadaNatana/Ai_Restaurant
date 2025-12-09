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
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

KB_CSV = DATA_DIR / "knowledge_base.csv"
KB_FLAGS_CSV = DATA_DIR / "kb_flags.csv"

# -------------------------------------------------
# Env & Hugging Face config
# -------------------------------------------------
load_dotenv(BASE_DIR / ".env") 

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" # changable models
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------
# Local Knowledge Base (UC20 part 1)
# -------------------------------------------------
def load_knowledge_base():
    """Return list of dict rows from local KB CSV."""
    items = []
    if not KB_CSV.exists():
        return items

    with open(KB_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items


def find_local_answer(question: str):
    """
    Fuzzy match based on SRS idea:
    - make both lower-case
    - strip trailing '?'
    - match if stored question is substring of user question or vice versa
    """
    q = question.lower().strip().strip("?")
    if not q:
        return None

    for row in load_knowledge_base():
        kbq = row["question"].lower().strip().strip("?")
        if kbq and (kbq in q or q in kbq):
            return row  # includes kb_id, question, answer
    return None


def append_kb_flag(kb_id: str, flagged_by: str, rating: int, comment: str):
    """
    UC21 – store a 0 rating (outrageous) for manager review in kb_flags.csv.
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


# -------------------------------------------------
# Hugging Face LLM (UC20 fallback)
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
    Call Hugging Face text-generation endpoint.
    """
    if not HF_API_TOKEN:
        return "(HF_API_TOKEN is not set. Put it in your .env file.)"

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

    except Exception as e:
        return f"(Hugging Face error: {e})"


# -------------------------------------------------
# Session helpers for chat state
# -------------------------------------------------
def init_session():
    # User identity from global app
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = "CUSTOMER"

    if "messages" not in st.session_state:
        st.session_state.messages = []  # list of {role, content, source}
    if "last_source" not in st.session_state:
        st.session_state.last_source = None  # "kb" or "llm"
    if "last_kb_id" not in st.session_state:
        st.session_state.last_kb_id = None


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
                UC20 – Local KB first, then LLM fallback &nbsp;&nbsp;|&nbsp;&nbsp;
                UC21 – Rating with 0-star flagging
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat():
    st.markdown("### Chat")

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

    user_input = st.chat_input(
        "Ask a question about menu, VIP, deposits, warnings, delivery, or allergies..."
    )
    if user_input:
        handle_user_question(user_input)


def handle_user_question(question: str):
    add_message("user", question, None)

    kb_row = find_local_answer(question)

    if kb_row:
        answer_text = kb_row["answer"]
        add_message("assistant", answer_text, "kb")
        st.session_state.last_source = "kb"
        st.session_state.last_kb_id = kb_row["kb_id"]
    else:
        history = st.session_state.messages
        answer_text = hf_chat(question, history)
        add_message("assistant", answer_text, "llm")
        st.session_state.last_source = "llm"
        st.session_state.last_kb_id = None


def render_rating():
    st.markdown("### Rate the Last Local Answer")

    if st.session_state.last_source != "kb":
        st.info(
            "The last answer did **not** come from the local knowledge base. "
            "Ratings are only stored for local KB answers."
        )
        return

    kb_id = st.session_state.last_kb_id
    if not kb_id:
        st.info("No local KB answer is currently selected for rating.")
        return

    st.write(
        "Please rate the **most recent local knowledge base answer** "
        "from 0 to 5 stars. Rating **0** will flag it as 'outrageous' "
        "for the manager to review."
    )

    rating = st.slider("Rating", min_value=0, max_value=5, value=5, step=1)
    comment = st.text_input(
        "Optional comment for the manager (especially if rating is 0):", value=""
    )

    if st.button("Submit Rating"):
        username = st.session_state.username or "anonymous"

        if rating == 0:
            append_kb_flag(
                kb_id=kb_id,
                flagged_by=username,
                rating=rating,
                comment=comment or "Flagged as outrageous by user.",
            )
            st.success(
                "This local answer was rated 0 and flagged for the manager to review."
            )
        else:
            st.success(f"Thank you! You rated this local answer {rating}/5.")


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
        render_chat()
    with col2:
        st.markdown("#### User Info")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        st.markdown("---")
        render_rating()

    st.markdown("---")
    st.caption(
        "Implements UC20 and UC21: local KB lookup, LLM fallback, and 0–5 rating with 0 as a manager flag."
    )

if __name__ == "__main__":
    main()
