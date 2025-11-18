import csv
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# CSV Paths
USERS_CSV = DATA_DIR / "users.csv"
TOPICS_CSV = DATA_DIR / "discussion_topics.csv"
POSTS_CSV = DATA_DIR / "discussion_posts.csv"


# -------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


# -------------------------------------------------------------
# USERS
# -------------------------------------------------------------

def load_users():
    users = []
    for row in _read_csv(USERS_CSV):
        users.append({
            "user_id": row["user_id"],
            "username": row["username"],
            "password": row["password"],
            "role": row["role"],  # CUSTOMER, VIP, CHEF, DELIVERY, MANAGER
            "status": row.get("status", "ACTIVE"),
            "warnings": int(row.get("warnings", "0") or 0),
            "deposit": float(row.get("deposit", "0") or 0.0),
            "total_spent": float(row.get("total_spent", "0") or 0.0),
            "num_orders": int(row.get("num_orders", "0") or 0),
            "blacklisted": (row.get("blacklisted", "False") == "True"),
        })
    return users


def save_users(users):
    fieldnames = [
        "user_id", "username", "password", "role", "status",
        "warnings", "deposit", "total_spent", "num_orders", "blacklisted"
    ]
    rows = []
    for u in users:
        row = u.copy()
        row["blacklisted"] = "True" if u.get("blacklisted") else "False"
        rows.append(row)
    _write_csv(USERS_CSV, rows, fieldnames)


def get_user_by_username(username):
    for user in load_users():
        if user["username"] == username:
            return user
    return None


def authenticate(username, password):
    user = get_user_by_username(username)
    if (
        user
        and user["password"] == password
        and user["status"] == "ACTIVE"
        and not user["blacklisted"]
    ):
        return user
    return None


def deposit_money(username, amount):
    if amount <= 0:
        raise ValueError("Deposit must be positive.")

    users = load_users()
    for u in users:
        if u["username"] == username:
            u["deposit"] = round(u["deposit"] + amount, 2)
            save_users(users)
            return u

    raise ValueError("User not found.")


# -------------------------------------------------------------
# DISCUSSION BOARD: TOPICS
# -------------------------------------------------------------

def load_topics():
    topics = []
    for row in _read_csv(TOPICS_CSV):
        topics.append({
            "topic_id": row["topic_id"],
            "title": row["title"],
            "category": row.get("category", "general").lower(),
            "topic_ref_id": row.get("topic_ref_id", ""),
            "author_username": row["author_username"],
            "created_at": row.get("created_at", _now()),
            "last_activity_at": row.get("last_activity_at", _now()),
            "is_locked": row.get("is_locked", "False"),
        })
    return topics


def save_topics(topics):
    fieldnames = [
        "topic_id", "title", "category", "topic_ref_id",
        "author_username", "created_at", "last_activity_at", "is_locked"
    ]
    _write_csv(TOPICS_CSV, topics, fieldnames)


def sort_topics_by_activity(topics):
    return sorted(
        topics,
        key=lambda t: t["last_activity_at"],
        reverse=True
    )


# -------------------------------------------------------------
# DISCUSSION BOARD: POSTS
# -------------------------------------------------------------

def load_posts(topic_id):
    posts = []
    for row in _read_csv(POSTS_CSV):
        if row["topic_id"] == str(topic_id):
            posts.append({
                "post_id": row["post_id"],
                "topic_id": row["topic_id"],
                "author_username": row["author_username"],
                "content": row["content"],
                "created_at": row.get("created_at", _now()),
            })
    return posts


def load_all_posts():
    posts = []
    for row in _read_csv(POSTS_CSV):
        posts.append({
            "post_id": row["post_id"],
            "topic_id": row["topic_id"],
            "author_username": row["author_username"],
            "content": row["content"],
            "created_at": row.get("created_at", _now()),
        })
    return posts


def save_posts(posts):
    fieldnames = ["post_id", "topic_id", "author_username", "content", "created_at"]
    _write_csv(POSTS_CSV, posts, fieldnames)


def add_post(topic_id, author_username, content):
    posts = load_all_posts()
    new_id = 1 + max([int(p["post_id"]) for p in posts], default=0)
    now = _now()

    posts.append({
        "post_id": str(new_id),
        "topic_id": str(topic_id),
        "author_username": author_username,
        "content": content,
        "created_at": now,
    })

    save_posts(posts)

    # Update topic last activity
    topics = load_topics()
    for t in topics:
        if t["topic_id"] == str(topic_id):
            t["last_activity_at"] = now
    save_topics(topics)
