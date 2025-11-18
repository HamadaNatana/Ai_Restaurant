import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import csv
from datetime import datetime
import threading
import json
from urllib import request, error as urlerror

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_CSV = DATA_DIR / "knowledge_base.csv"
KB_FLAGS_CSV = DATA_DIR / "kb_flags.csv"


# -------------------------------------------------------------
# DATA LAYER (UC20 / UC21)
# -------------------------------------------------------------

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_knowledge_base():
    items = []
    if KB_CSV.exists():
        with open(KB_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(row)
    return items


def find_local_answer(question: str):
    """
    Fuzzy search for UC20 – local KB lookup.
    """
    q = question.lower().strip().strip("?")

    for row in load_knowledge_base():
        kbq = row["question"].lower().strip().strip("?")
        if kbq in q or q in kbq:
            return row

    return None


def append_flag(kb_id: str, flagged_by: str, rating: int, comment: str):
    """
    UC21 – store a 0/'outrageous' rating for manager review.
    """
    exists = KB_FLAGS_CSV.exists()
    with open(KB_FLAGS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["kb_id", "flagged_by", "rating", "comment", "created_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not exists:
            writer.writeheader()

        writer.writerow({
            "kb_id": kb_id,
            "flagged_by": flagged_by,
            "rating": rating,
            "comment": comment,
            "created_at": _now()
        })


# -------------------------------------------------------------
# REAL OLLAMA CALL VIA HTTP (NO python 'ollama' PACKAGE)
# -------------------------------------------------------------

def _ollama_chat_http(question: str, model: str = "llama3.2") -> str:
    """
    Call Ollama's HTTP /api/chat endpoint using only standard library.
    Requires Ollama server running locally with the given model pulled.
    """
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=60) as resp:
            resp_data = resp.read().decode("utf-8")
            obj = json.loads(resp_data)
            msg = obj.get("message", {})
            content = msg.get("content", "").strip()
            if not content:
                return "(LLM returned an empty response.)"
            return content
    except urlerror.URLError as e:
        return f"(LLM HTTP Error: {e})"
    except Exception as e:
        return f"(LLM Error: {e})"


def ask_external_llm_async(question: str, callback):
    """
    Run Ollama HTTP call in a background thread, then call `callback(answer)`.
    """

    def worker():
        answer = _ollama_chat_http(question)
        callback(answer)

    threading.Thread(target=worker, daemon=True).start()


# -------------------------------------------------------------
# GUI: AI CHAT (UC20 + UC21) – Beautified
# -------------------------------------------------------------

class AiChatScreen(tk.Frame):
    """
    UC20 – AI Customer Service Chat (local KB + LLM)
    UC21 – Rating Local KB Answers (0–5, with flagging at 0)
    """

    def __init__(self, master, user):
        super().__init__(master, bg="#f3f4f6")  # light gray app background
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self.last_answer_source = None   # "local" or "llm"
        self.last_kb_id = None           # id of last local KB answer

        self._build_ui()

    # ---------------------------------------------------------
    # UI LAYOUT
    # ---------------------------------------------------------

    def _build_ui(self):
        # TOP APP BAR (like a web app header)
        appbar = tk.Frame(self, bg="#111827", height=54)
        appbar.pack(fill="x", side="top")

        tk.Label(
            appbar,
            text="AI Restaurant Order & Delivery System",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#111827",
            anchor="w"
        ).pack(side="left", padx=(16, 8))

        tk.Label(
            appbar,
            text="AI Customer Service",
            font=("Segoe UI", 11),
            fg="#9ca3af",
            bg="#111827",
        ).pack(side="left")

        # MAIN CONTENT WRAPPER
        content = tk.Frame(self, bg="#f3f4f6")
        content.pack(fill="both", expand=True, padx=18, pady=18)

        # CARD CONTAINER (like a panel on a website)
        card = tk.Frame(content, bg="white", bd=0, highlightthickness=1, highlightbackground="#e5e7eb")
        card.pack(fill="both", expand=True)

        # Card header
        header = tk.Frame(card, bg="white")
        header.pack(fill="x", pady=(12, 4), padx=16)

        tk.Label(
            header,
            text="AI Customer Service",
            font=("Segoe UI", 18, "bold"),
            fg="#111827",
            bg="white"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Chat about menu items, orders, VIP rules, allergies, and more.",
            font=("Segoe UI", 10),
            fg="#6b7280",
            bg="white"
        ).pack(anchor="w", pady=(2, 0))

        # Divider line
        tk.Frame(card, bg="#e5e7eb", height=1).pack(fill="x", pady=(8, 4))

        # CHAT + INPUT AREA
        center = tk.Frame(card, bg="white")
        center.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        # Chat frame
        chat_frame = tk.Frame(center, bg="#f9fafb", bd=0, relief="flat")
        chat_frame.pack(fill="both", expand=True)

        self.text_area = tk.Text(
            chat_frame,
            wrap="word",
            state="disabled",
            bg="#f9fafb",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            borderwidth=0
        )
        self.text_area.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(chat_frame, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)

        # Configure tags for "bubble" styles
        # User bubble (right-aligned feel via left margins)
        self.text_area.tag_config(
            "user_name",
            foreground="#1d4ed8",
            font=("Segoe UI", 9, "bold")
        )
        self.text_area.tag_config(
            "user_msg",
            background="#dbeafe",
            foreground="#111827",
            lmargin1=220,
            lmargin2=220,
            rmargin=10,
            spacing1=2,
            spacing3=8,
            font=("Segoe UI", 10)
        )

        # Local KB bubble
        self.text_area.tag_config(
            "kb_name",
            foreground="#15803d",
            font=("Segoe UI", 9, "bold")
        )
        self.text_area.tag_config(
            "kb_msg",
            background="#dcfce7",
            foreground="#111827",
            lmargin1=10,
            lmargin2=10,
            rmargin=140,
            spacing1=2,
            spacing3=8,
            font=("Segoe UI", 10)
        )

        # LLM bubble
        self.text_area.tag_config(
            "llm_name",
            foreground="#6d28d9",
            font=("Segoe UI", 9, "bold")
        )
        self.text_area.tag_config(
            "llm_msg",
            background="#ede9fe",
            foreground="#111827",
            lmargin1=10,
            lmargin2=10,
            rmargin=140,
            spacing1=2,
            spacing3=8,
            font=("Segoe UI", 10)
        )

        # System/info messages
        self.text_area.tag_config(
            "system_msg",
            foreground="#9ca3af",
            font=("Segoe UI", 9, "italic"),
            spacing1=2,
            spacing3=6
        )

        # INPUT + SEND ROW
        input_frame = tk.Frame(center, bg="white")
        input_frame.pack(fill="x", pady=(8, 0))

        self.entry_var = tk.StringVar()
        entry = tk.Entry(
            input_frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 11),
            relief="solid",
            borderwidth=1
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=4)
        entry.bind("<Return>", lambda e: self._send())

        send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Segoe UI", 10, "bold"),
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            relief="flat",
            padx=16,
            pady=4,
            command=self._send
        )
        send_btn.pack(side="right")

        # RATING + BACK ROW
        footer_controls = tk.Frame(card, bg="#f9fafb")
        footer_controls.pack(fill="x", padx=16, pady=(4, 6))

        rating_frame = tk.Frame(footer_controls, bg="#f9fafb")
        rating_frame.pack(side="left", pady=4)

        tk.Label(
            rating_frame,
            text="Rate last LOCAL answer (0–5):",
            font=("Segoe UI", 9),
            bg="#f9fafb",
            fg="#4b5563"
        ).pack(side="left", padx=(0, 4))

        self.rating_var = tk.IntVar(value=5)
        for v in range(6):
            tk.Radiobutton(
                rating_frame,
                text=str(v),
                variable=self.rating_var,
                value=v,
                bg="#f9fafb",
                font=("Segoe UI", 9),
                highlightthickness=0
            ).pack(side="left")

        rate_btn = tk.Button(
            rating_frame,
            text="Submit",
            font=("Segoe UI", 9),
            bg="#e5e7eb",
            fg="#111827",
            activebackground="#d1d5db",
            activeforeground="#111827",
            relief="flat",
            padx=10,
            pady=2,
            command=self._submit_rating
        )
        rate_btn.pack(side="left", padx=(6, 0))

        back_btn = tk.Button(
            footer_controls,
            text="Back to Dashboard",
            font=("Segoe UI", 9),
            bg="white",
            fg="#111827",
            activebackground="#e5e7eb",
            activeforeground="#111827",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=2,
            command=self._back
        )
        back_btn.pack(side="right", pady=4)

        # STATUS BAR (inside card bottom)
        self.status_label = tk.Label(
            card,
            text="",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="white",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=16, pady=(0, 10))

        # Initial system prompt
        self._append_system(
            "Hello! Ask me anything about the restaurant, menu, VIP rules, "
            "delivery, or allergy information."
        )

    # ---------------------------------------------------------
    # APPEND HELPERS – "Bubble" style messages
    # ---------------------------------------------------------

    def _append_system(self, msg: str):
        self.text_area.config(state="normal")
        self.text_area.insert("end", msg + "\n", ("system_msg",))
        self.text_area.insert("end", "\n")
        self.text_area.config(state="disabled")
        self.text_area.see("end")

    def _append_user(self, msg: str):
        self.text_area.config(state="normal")
        self.text_area.insert("end", f"{self.user['username']} (You)\n", ("user_name",))
        self.text_area.insert("end", msg + "\n\n", ("user_msg",))
        self.text_area.config(state="disabled")
        self.text_area.see("end")

    def _append_kb(self, msg: str):
        self.text_area.config(state="normal")
        self.text_area.insert("end", "AI (Local Knowledge Base)\n", ("kb_name",))
        self.text_area.insert("end", msg + "\n\n", ("kb_msg",))
        self.text_area.config(state="disabled")
        self.text_area.see("end")

    def _append_llm_typing(self, full_text: str, index: int = 0):
        """
        Typing animation for LLM answer: prints one character at a time.
        """
        if index == 0:
            self.text_area.config(state="normal")
            self.text_area.insert("end", "AI (External LLM – llama3.2)\n", ("llm_name",))
            self.text_area.insert("end", "", ("llm_msg",))
            self.text_area.config(state="disabled")

        if index >= len(full_text):
            self.text_area.config(state="disabled")
            self.text_area.see("end")
            return

        self.text_area.config(state="normal")
        self.text_area.insert("end", full_text[index], ("llm_msg",))
        self.text_area.config(state="disabled")
        self.text_area.see("end")

        # Typing speed (ms)
        self.after(15, lambda: self._append_llm_typing(full_text, index + 1))

    def _set_status(self, text: str):
        self.status_label.config(text=text)

    # ---------------------------------------------------------
    # CHAT LOGIC
    # ---------------------------------------------------------

    def _send(self):
        question = self.entry_var.get().strip()
        if not question:
            return

        self.entry_var.set("")
        self._append_user(question)

        kb = find_local_answer(question)

        if kb:
            # Local KB path
            self.last_answer_source = "local"
            self.last_kb_id = kb["kb_id"]

            self._append_kb(kb["answer"])
            self._append_system("You can now rate this local answer 0–5.")
            self._set_status("")
        else:
            # External LLM path via Ollama HTTP
            self.last_answer_source = "llm"
            self.last_kb_id = None

            self._set_status("AI is thinking via llama3.2…")

            def on_llm_answer(text):
                self.after(0, lambda: self._finish_llm_answer(text))

            ask_external_llm_async(question, on_llm_answer)

    def _finish_llm_answer(self, text: str):
        self._set_status("")
        self._append_llm_typing(text)

    # ---------------------------------------------------------
    # RATING LOGIC (UC21)
    # ---------------------------------------------------------

    def _submit_rating(self):
        rating = self.rating_var.get()

        if self.last_answer_source != "local":
            messagebox.showinfo(
                "Rating",
                "You can only rate LOCAL knowledge base answers (not LLM replies)."
            )
            return

        if not self.last_kb_id:
            messagebox.showinfo("Rating", "No KB answer is available for rating.")
            return

        if rating == 0:
            append_flag(
                kb_id=self.last_kb_id,
                flagged_by=self.user["username"],
                rating=0,
                comment="Flagged as outrageous by user."
            )
            messagebox.showinfo(
                "Flagged",
                "This local answer was rated 0 and flagged for the manager to review."
            )
        else:
            messagebox.showinfo(
                "Rating Submitted",
                f"Thanks! You rated this local answer {rating}/5."
            )

    # ---------------------------------------------------------
    # NAVIGATION
    # ---------------------------------------------------------

    def _back(self):
        from customer_gui import CustomerScreen
        self.destroy()
        CustomerScreen(self.master, self.user)
