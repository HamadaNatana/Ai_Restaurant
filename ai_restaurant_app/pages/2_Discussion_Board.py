import csv
from datetime import datetime
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TOPICS_CSV = DATA_DIR / "discussion_topics.csv"
POSTS_CSV = DATA_DIR / "discussion_posts.csv"


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
    def key_func(t):
        return t.get("last_activity_at") or "1970-01-01 00:00:00"

    return sorted(topics, key=key_func, reverse=True)


# --------------------- UC16 Logic ---------------------------
def init_user():
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = "CUSTOMER"


def user_can_post():
    return st.session_state.role in ("CUSTOMER", "VIP")


def user_is_manager():
    return st.session_state.role == "MANAGER"


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
        "Only Registered/VIP customers can create topics / reply.\n\n"
        "Manager can lock/unlock topics."
    )


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
                locked = t["is_locked"] == "True"
                status = "🔒" if locked else "💬"
                st.write(
                    f"{status} **{t['title']}** "
                    f"(_{t['category']}_) by **{t['author_username']}**"
                )
                st.caption(
                    f"Created: {t['created_at']} | Last activity: {t['last_activity_at']}"
                )

        st.markdown("---")
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
                if not title.strip() or not opening_message.strip():
                    st.error("Title and opening message are required.")
                else:
                    topics = load_topics()
                    new_id = next_topic_id(topics)
                    now = now_str()
                    new_topic = {
                        "topic_id": new_id,
                        "title": title.strip(),
                        "category": category,
                        "topic_ref_id": topic_ref_id.strip(),
                        "author_username": st.session_state.username,
                        "created_at": now,
                        "last_activity_at": now,
                        "is_locked": "False",
                    }
                    topics.append(new_topic)
                    save_topics(topics)

                    all_posts = load_posts()
                    new_post = {
                        "post_id": next_post_id(all_posts),
                        "topic_id": new_id,
                        "author_username": st.session_state.username,
                        "content": opening_message.strip(),
                        "created_at": now,
                    }
                    all_posts.append(new_post)
                    save_posts(all_posts)

                    st.success("Topic created successfully. Scroll to the right to view.")
                    st.experimental_rerun()
        else:
            st.warning("Only Registered/VIP customers can create topics.")

    # -------- RIGHT: selected topic and replies ----------
    with col_right:
        st.markdown("### Thread View")

        topic_titles = [f"{t['topic_id']}: {t['title']}" for t in topics]
        selected_topic = None
        selected_topic_obj = None

        if topics:
            selected_topic = st.selectbox("Select a topic", topic_titles)
            if selected_topic:
                sel_id = selected_topic.split(":", 1)[0].strip()
                for t in topics:
                    if t["topic_id"] == sel_id:
                        selected_topic_obj = t
                        break

        if not selected_topic_obj:
            st.info("Select a topic from the dropdown to view posts.")
        else:
            locked = selected_topic_obj["is_locked"] == "True"
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
                topic_posts, key=lambda p: p["created_at"] or "1970-01-01 00:00:00"
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

            # Manager lock/unlock
            if user_is_manager():
                col_lock1, col_lock2 = st.columns(2)
                with col_lock1:
                    if st.button("🔒 Lock topic"):
                        selected_topic_obj["is_locked"] = "True"
                        selected_topic_obj["last_activity_at"] = now_str()
                        save_topics(topics)
                        st.success("Topic locked.")
                        st.experimental_rerun()
                with col_lock2:
                    if st.button("🔓 Unlock topic"):
                        selected_topic_obj["is_locked"] = "False"
                        save_topics(topics)
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
                        else:
                            all_posts = load_posts()
                            new_post = {
                                "post_id": next_post_id(all_posts),
                                "topic_id": selected_topic_obj["topic_id"],
                                "author_username": st.session_state.username,
                                "content": reply.strip(),
                                "created_at": now_str(),
                            }
                            all_posts.append(new_post)
                            save_posts(all_posts)

                            # Update last_activity_at
                            topics = load_topics()
                            for t in topics:
                                if t["topic_id"] == selected_topic_obj["topic_id"]:
                                    t["last_activity_at"] = now_str()
                            save_topics(topics)

                            st.success("Reply posted.")
                            st.experimental_rerun()

    st.markdown("---")
    st.caption(
        "Implements UC16: topics list, starting new topics, viewing threads, posting replies, and manager lock/unlock."
    )


if __name__ == "__main__":
    main()
