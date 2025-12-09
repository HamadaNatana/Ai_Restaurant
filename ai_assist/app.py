import csv
from datetime import datetime
from pathlib import Path

import streamlit as st

# --------------------- Paths & Constants -------------------------

# app.py is inside: ai_assist/app.py → data is ai_assist/data
BASE_DIR = Path(__file__).resolve().parent      # ai_assist
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TOPICS_CSV = DATA_DIR / "discussion_topics.csv"
POSTS_CSV = DATA_DIR / "discussion_posts.csv"

# Role constants (aligns with SRS actors)
ROLE_VISITOR = "VISITOR"
ROLE_CUSTOMER = "CUSTOMER"         # Registered customer
ROLE_VIP = "VIP"                   # VIP customer
ROLE_MANAGER = "MANAGER"

LOCK_TRUE = "True"
LOCK_FALSE = "False"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------- Data helpers -------------------------

def load_topics():
    if not TOPICS_CSV.exists():
        return []
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_topics(topics):
    with open(TOPICS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "topic_id",
            "title",
            "category",
            "topic_ref_id",
            "author_username",
            "created_at",
            "last_activity_at",
            "is_locked",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in topics:
            writer.writerow(t)


def load_posts():
    if not POSTS_CSV.exists():
        return []
    with open(POSTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_posts(posts):
    with open(POSTS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["post_id", "topic_id", "author_username", "content", "created_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in posts:
            writer.writerow(p)


def next_topic_id(topics):
    if not topics:
        return "1"
    return str(max(int(t["topic_id"]) for t in topics) + 1)


def next_post_id(posts):
    if not posts:
        return "1"
    return str(max(int(p["post_id"]) for p in posts) + 1)


def sort_topics_by_activity(topics):
    """
    Sort topics by last_activity_at descending.
    Timestamps are ISO-like so string sort is OK, but we use a safe default.
    """
    def key_func(t):
        return t.get("last_activity_at") or "1970-01-01 00:00:00"

    return sorted(topics, key=key_func, reverse=True)


# --------------------- Role / Session helpers -------------------------

def init_user():
    """
    For the prototype, we use a demo user.
    In the real system, this would be set by the login page (UC03).
    """
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = ROLE_CUSTOMER  # acts as "Registered customer"


def user_can_post():
    """
    UC16 actors: Registered and VIP customers.
    Only these roles can create topics and replies.
    """
    return st.session_state.role in (ROLE_CUSTOMER, ROLE_VIP)


def user_is_manager():
    return st.session_state.role == ROLE_MANAGER


# --------------------- UC16 domain helpers -------------------------

def create_topic(title, category, topic_ref_id, opening_message, author_username):
    """
    UC16 – Start a New Topic.
    Creates a new topic row + first post (opening message).
    """
    topics = load_topics()
    posts = load_posts()

    new_topic_id = next_topic_id(topics)
    now = now_str()

    new_topic = {
        "topic_id": new_topic_id,
        "title": title.strip(),
        "category": category,
        "topic_ref_id": (topic_ref_id or "").strip(),
        "author_username": author_username,
        "created_at": now,
        "last_activity_at": now,
        "is_locked": LOCK_FALSE,
    }
    topics.append(new_topic)
    save_topics(topics)

    new_post = {
        "post_id": next_post_id(posts),
        "topic_id": new_topic_id,
        "author_username": author_username,
        "content": opening_message.strip(),
        "created_at": now,
    }
    posts.append(new_post)
    save_posts(posts)


def add_reply(topic_id, content, author_username):
    """
    UC16 – Reply to existing topic.
    Creates a new post and updates topic.last_activity_at.
    """
    posts = load_posts()
    topics = load_topics()

    now = now_str()

    new_post = {
        "post_id": next_post_id(posts),
        "topic_id": topic_id,
        "author_username": author_username,
        "content": content.strip(),
        "created_at": now,
    }
    posts.append(new_post)
    save_posts(posts)

    # Update last activity for this topic
    for t in topics:
        if t["topic_id"] == topic_id:
            t["last_activity_at"] = now
            break
    save_topics(topics)


def set_topic_lock(topic_id, lock_value: bool):
    """
    Manager-only helper to lock/unlock a topic.
    """
    topics = load_topics()
    now = now_str()
    for t in topics:
        if t["topic_id"] == topic_id:
            t["is_locked"] = LOCK_TRUE if lock_value else LOCK_FALSE
            # Lock/unlock counts as activity (optional but nice)
            t["last_activity_at"] = now
            break
    save_topics(topics)


# --------------------- UI helpers -------------------------

def render_header():
    st.markdown(
        """
        <div style="background-color:#111827;padding:10px 16px;border-radius:0 0 8px 8px;">
            <h2 style="color:white;margin:0;">Discussion Board</h2>
            <p style="color:#9ca3af;margin:2px 0 0 0;font-size:13px;">
                UC16 – Start / participate in discussion about chefs, dishes, and delivery
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_info():
    st.sidebar.subheader("Current User (demo)")
    st.sidebar.write(f"**Username:** {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    st.sidebar.info(
        "UC16 actors:\n"
        "- Registered Customer (CUSTOMER)\n"
        "- VIP (VIP)\n\n"
        "Only these can create topics / reply.\n"
        "Manager can lock/unlock topics."
    )


# --------------------- Main UC16 Screen -------------------------

def main():
    st.set_page_config(
        page_title="AI Restaurant – Discussion Board",
        page_icon="💬",
        layout="wide",
    )
    init_user()
    render_header()
    render_sidebar_info()

    topics = sort_topics_by_activity(load_topics())
    posts = load_posts()

    col_left, col_right = st.columns([1.2, 2])

    # -------- LEFT: topics list + create topic ----------
    with col_left:
        st.markdown("### Topics")

        if not topics:
            st.info("No topics yet. Be the first to start a discussion!")
        else:
            for t in topics:
                locked = t["is_locked"] == LOCK_TRUE
                status = "🔒" if locked else "💬"
                st.write(
                    f"{status} **{t['title']}** "
                    f"(_{t['category']}_) by **{t['author_username']}**"
                )
                st.caption(
                    f"Created: {t['created_at']} | Last activity: {t['last_activity_at']}"
                )

        st.markdown("---")

        # Start new topic (Registered/VIP only)
        if user_can_post():
            st.markdown("#### Start a New Topic")
            with st.form("new_topic_form"):
                title = st.text_input("Title")
                category = st.selectbox(
                    "Category",
                    ["chef", "dish", "delivery", "general"],
                    index=3,
                )
                topic_ref_id = st.text_input(
                    "Reference ID (optional, e.g., dish or chef ID)"
                )
                opening_message = st.text_area("Opening message")
                submitted = st.form_submit_button("Create Topic")

            if submitted:
                if not title.strip():
                    st.error("Title is required.")
                elif not opening_message.strip():
                    st.error("Opening message is required.")
                elif len(opening_message.strip()) < 5:
                    st.error("Opening message is too short. Please write a bit more.")
                else:
                    create_topic(
                        title=title,
                        category=category,
                        topic_ref_id=topic_ref_id,
                        opening_message=opening_message,
                        author_username=st.session_state.username,
                    )
                    st.success("Topic created successfully. Scroll to the right to view.")
                    st.experimental_rerun()
        else:
            st.warning("Only Registered/VIP customers can create topics.")

    # -------- RIGHT: selected topic and replies ----------
    with col_right:
        st.markdown("### Thread View")

        topic_titles = [f"{t['topic_id']}: {t['title']}" for t in topics]
        selected_topic_obj = None

        if topics:
            selected_label = st.selectbox("Select a topic", topic_titles)
            if selected_label:
                sel_id = selected_label.split(":", 1)[0].strip()
                for t in topics:
                    if t["topic_id"] == sel_id:
                        selected_topic_obj = t
                        break

        if not selected_topic_obj:
            st.info("Select a topic from the dropdown to view posts.")
        else:
            locked = selected_topic_obj["is_locked"] == LOCK_TRUE
            lock_status = "🔒 Locked" if locked else "✅ Open"
            st.markdown(
                f"#### {selected_topic_obj['title']}  "
                f"(_{selected_topic_obj['category']}_) — {lock_status}"
            )
            st.caption(
                f"Topic ID: {selected_topic_obj['topic_id']} | "
                f"Created by: {selected_topic_obj['author_username']} | "
                f"Last activity: {selected_topic_obj['last_activity_at']}"
            )

            topic_posts = [
                p for p in posts if p["topic_id"] == selected_topic_obj["topic_id"]
            ]
            topic_posts = sorted(
                topic_posts,
                key=lambda p: p["created_at"] or "1970-01-01 00:00:00",
            )

            if not topic_posts:
                st.info("No posts yet in this topic.")
            else:
                for p in topic_posts:
                    st.markdown(
                        f"**{p['author_username']}**  "
                        f"<span style='font-size:11px;color:#6b7280;'>"
                        f"{p['created_at']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write(p["content"])
                    st.markdown("---")

            # Manager lock/unlock (only show the relevant button)
            if user_is_manager():
                st.markdown("#### Manager Controls")
                if not locked:
                    if st.button("🔒 Lock topic"):
                        set_topic_lock(selected_topic_obj["topic_id"], True)
                        st.success("Topic locked.")
                        st.experimental_rerun()
                else:
                    if st.button("🔓 Unlock topic"):
                        set_topic_lock(selected_topic_obj["topic_id"], False)
                        st.success("Topic unlocked.")
                        st.experimental_rerun()

            # Reply form
            st.markdown("#### Reply to this topic")
            if locked:
                st.warning("This thread is locked by the manager. Replies are disabled.")
            else:
                if not user_can_post():
                    st.warning("Only Registered/VIP customers can reply.")
                else:
                    with st.form("reply_form"):
                        reply = st.text_area("Your reply")
                        send = st.form_submit_button("Post Reply")
                    if send:
                        if not reply.strip():
                            st.error("Reply cannot be empty.")
                        elif len(reply.strip()) < 2:
                            st.error("Reply is too short.")
                        else:
                            add_reply(
                                topic_id=selected_topic_obj["topic_id"],
                                content=reply,
                                author_username=st.session_state.username,
                            )
                            st.success("Reply posted.")
                            st.experimental_rerun()

    st.markdown("---")
    st.caption(
        "Implements UC16: list topics, start new topics (Registered/VIP), view threads, "
        "post replies, and manager lock/unlock."
    )


if __name__ == "__main__":
    main()
