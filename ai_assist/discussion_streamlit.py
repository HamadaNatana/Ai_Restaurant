import os
from pathlib import Path
from typing import Optional

import streamlit as st

# Optional dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return

# ---------------- Django setup ----------------

import django

BASE_DIR = Path(__file__).resolve().parent.parent  # project root

# TODO: CHANGE THIS to your actual project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant_project.settings")

try:
    django.setup()
except Exception as e:
    st.error(f"Django setup failed: {e}")

from django.utils import timezone
from ai_assist.models import DiscussionTopic, DiscussionPost
from accounts.models import Customer

load_dotenv(BASE_DIR / ".env")

ROLE_VISITOR = "VISITOR"
ROLE_CUSTOMER = "CUSTOMER"
ROLE_VIP = "VIP"
ROLE_MANAGER = "MANAGER"


# ---------------- User/role helpers ----------------

def init_user():
    """
    For the prototype, simulate a logged-in user.
    In real UC03, this would come from Django auth.
    """
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        # Change role manually in session for testing (CUSTOMER / VIP / MANAGER)
        st.session_state.role = ROLE_CUSTOMER


def user_can_post() -> bool:
    return st.session_state.role in (ROLE_CUSTOMER, ROLE_VIP)


def user_is_manager() -> bool:
    return st.session_state.role == ROLE_MANAGER


def get_customer_for_username(username: str) -> Optional[Customer]:
    try:
        cust = Customer.objects.filter(user__username=username).first()
        if not cust:
            cust = Customer.objects.filter(username=username).first()
        return cust
    except Exception:
        return None


# ---------------- UI helpers ----------------

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
        "Only Registered/VIP customers can create topics and replies.\n\n"
        "Managers can lock/unlock topics."
    )


# ---------------- Main ----------------

def main():
    st.set_page_config(
        page_title="AI Restaurant – Discussion Board",
        page_icon="💬",
        layout="wide",
    )
    init_user()
    render_header()
    render_sidebar_info()

    # Safely load data from DB
    try:
        topics = DiscussionTopic.objects.all().order_by("-last_activity_at")
    except Exception as e:
        st.error(f"Error loading topics from database: {e}")
        topics = DiscussionTopic.objects.none()

    try:
        posts = DiscussionPost.objects.all().order_by("created_at")
    except Exception as e:
        st.error(f"Error loading posts from database: {e}")
        posts = DiscussionPost.objects.none()

    col_left, col_right = st.columns([1.2, 2])

    # -------- LEFT: topics list + create topic ----------
    with col_left:
        st.markdown("### Topics")

        if not topics.exists():
            st.info("No topics yet. Be the first to start a discussion!")
        else:
            for t in topics:
                locked = t.is_locked
                status = "🔒" if locked else "💬"
                author_name = t.author.user.username if getattr(t.author, "user", None) else (
                    t.author.username if t.author else "Unknown"
                )
                st.write(
                    f"{status} **{t.title}** "
                    f"(_{t.category}_) by **{author_name}**"
                )
                st.caption(
                    f"Created: {t.created_at} | Last activity: {t.last_activity_at}"
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
                    author = get_customer_for_username(st.session_state.username)
                    now = timezone.now()
                    try:
                        new_topic = DiscussionTopic.objects.create(
                            title=title.strip(),
                            category=category,
                            topic_ref_id=topic_ref_id.strip() or None,
                            author=author,
                            is_locked=False,
                            last_activity_at=now,
                        )
                        DiscussionPost.objects.create(
                            topic=new_topic,
                            author=author,
                            content=opening_message.strip(),
                        )
                        st.success("Topic created successfully. Scroll to the right to view.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating topic: {e}")
        else:
            st.warning("Only Registered/VIP customers can create topics.")

    # -------- RIGHT: selected topic and replies ----------
    with col_right:
        st.markdown("### Thread View")

        topic_titles = [f"{t.pk}: {t.title}" for t in topics]
        selected_topic_obj: Optional[DiscussionTopic] = None

        if topic_titles:
            selected_text = st.selectbox("Select a topic", topic_titles)
            if selected_text:
                sel_id = selected_text.split(":", 1)[0].strip()
                try:
                    selected_topic_obj = DiscussionTopic.objects.filter(pk=sel_id).first()
                except Exception as e:
                    st.error(f"Error loading selected topic: {e}")
                    selected_topic_obj = None

        if not selected_topic_obj:
            st.info("Select a topic from the dropdown to view posts.")
        else:
            locked = selected_topic_obj.is_locked
            lock_status = "🔒 Locked" if locked else "✅ Open"
            author_name = (
                selected_topic_obj.author.user.username
                if getattr(selected_topic_obj.author, "user", None)
                else (selected_topic_obj.author.username if selected_topic_obj.author else "Unknown")
            )
            st.markdown(
                f"#### {selected_topic_obj.title}  "
                f"(_{selected_topic_obj.category}_) — {lock_status}"
            )
            st.caption(
                f"Topic ID: {selected_topic_obj.pk} | "
                f"Created by: {author_name} | "
                f"Last activity: {selected_topic_obj.last_activity_at}"
            )

            try:
                topic_posts = selected_topic_obj.posts.all().order_by("created_at")
            except Exception as e:
                st.error(f"Error loading posts for topic: {e}")
                topic_posts = DiscussionPost.objects.none()

            if not topic_posts.exists():
                st.info("No posts yet in this topic.")
            else:
                for p in topic_posts:
                    p_author = (
                        p.author.user.username
                        if getattr(p.author, "user", None)
                        else (p.author.username if p.author else "Unknown")
                    )
                    st.markdown(
                        f"**{p_author}**  "
                        f"<span style='font-size:11px;color:#6b7280;'>"
                        f"{p.created_at}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write(p.content)
                    st.markdown("---")

            # Manager lock/unlock
            if user_is_manager():
                col_lock1, col_lock2 = st.columns(2)
                with col_lock1:
                    if st.button("🔒 Lock topic"):
                        try:
                            selected_topic_obj.is_locked = True
                            selected_topic_obj.last_activity_at = timezone.now()
                            selected_topic_obj.save()
                            st.success("Topic locked.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error locking topic: {e}")
                with col_lock2:
                    if st.button("🔓 Unlock topic"):
                        try:
                            selected_topic_obj.is_locked = False
                            selected_topic_obj.save()
                            st.success("Topic unlocked.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error unlocking topic: {e}")

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
                            author = get_customer_for_username(st.session_state.username)
                            try:
                                DiscussionPost.objects.create(
                                    topic=selected_topic_obj,
                                    author=author,
                                    content=reply.strip(),
                                )
                                selected_topic_obj.last_activity_at = timezone.now()
                                selected_topic_obj.save()
                                st.success("Reply posted.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error posting reply: {e}")

    st.markdown("---")
    st.caption(
        "Implements UC16: topics list, starting new topics, viewing threads, posting replies, and manager lock/unlock using Django models."
    )


if __name__ == "__main__":
    main()
