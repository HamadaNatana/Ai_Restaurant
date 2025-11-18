import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime
from data import (
    load_topics, save_topics, sort_topics_by_activity,
    load_posts, add_post, load_all_posts
)


class DiscussionBoardScreen(tk.Frame):
    """
    UC16 – Start / participate in discussion boards on chefs, dishes, delivery,
    matching the SRS exactly with timestamps, locking, sorting, and modern layout.
    """

    def __init__(self, master, user):
        super().__init__(master, bg="#f7f7f7")
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self.topics = sort_topics_by_activity(load_topics())
        self._build_ui()

    # -----------------------------------------------------------
    # UI LAYOUT
    # -----------------------------------------------------------

    def _build_ui(self):
        header = tk.Frame(self, bg="#f7f7f7")
        header.pack(fill="x", pady=10)

        tk.Label(header, text="Community Discussion Board",
                 font=("Arial", 22, "bold"), bg="#f7f7f7").pack()

        main = tk.Frame(self, bg="#f7f7f7")
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # ------------- LEFT PANEL: TOPIC LIST --------------
        left = tk.Frame(main, bg="#ffffff", bd=2, relief="groove")
        left.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left, text="Topics", font=("Arial", 16, "bold"),
                 bg="#ffffff").pack(pady=10)

        columns = ("title", "category", "author", "time")
        self.topic_tree = ttk.Treeview(left, columns=columns, show="headings", height=20)

        self.topic_tree.heading("title", text="Title")
        self.topic_tree.heading("category", text="Category")
        self.topic_tree.heading("author", text="Author")
        self.topic_tree.heading("time", text="Last Active")

        self.topic_tree.column("title", width=180)
        self.topic_tree.column("category", width=90)
        self.topic_tree.column("author", width=110)
        self.topic_tree.column("time", width=130)

        self.topic_tree.pack(fill="y", expand=True)
        self.topic_tree.bind("<<TreeviewSelect>>", self._on_topic_select)

        # New topic button
        tk.Button(left, text="New Topic", width=20,
                  command=self._new_topic).pack(pady=10)

        self._refresh_topics()

        # ------------- RIGHT PANEL: POSTS VIEWER --------------
        right = tk.Frame(main, bg="#ffffff", bd=2, relief="groove")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Thread Posts", font=("Arial", 16, "bold"),
                 bg="#ffffff").pack(pady=10)

        self.post_area = tk.Text(right, height=25, wrap="word",
                                 bg="#fafafa", font=("Arial", 11), state="disabled")
        self.post_area.pack(fill="both", expand=True, padx=10)

        # Reply section
        bottom = tk.Frame(right, bg="#ffffff")
        bottom.pack(fill="x", pady=10)

        tk.Button(bottom, text="Reply to Thread",
                  command=self._reply).pack(pady=5)

        tk.Button(self, text="Back to Dashboard",
                  command=self._back).pack(pady=10)

    # -----------------------------------------------------------
    # TOPIC MANAGEMENT
    # -----------------------------------------------------------

    def _refresh_topics(self):
        for row in self.topic_tree.get_children():
            self.topic_tree.delete(row)

        for t in self.topics:
            last = t["last_activity_at"]
            self.topic_tree.insert(
                "",
                tk.END,
                iid=t["topic_id"],
                values=(t["title"], t["category"],
                        t["author_username"], last)
            )

    def _on_topic_select(self, event=None):
        sel = self.topic_tree.focus()
        if not sel:
            return

        posts = load_posts(sel)

        self.post_area.config(state="normal")
        self.post_area.delete("1.0", tk.END)

        for p in posts:
            created = p.get("created_at", "")
            self.post_area.insert(
                tk.END,
                f"{p['author_username']}  ({created})\n"
                f"{p['content']}\n"
                f"{'-'*50}\n\n"
            )

        self.post_area.config(state="disabled")

    def _require_post_permission(self):
        if self.user["role"] not in ("CUSTOMER", "VIP"):
            messagebox.showerror(
                "Not Allowed",
                "Only Registered/VIP customers can post in discussions."
            )
            return False
        return True

    def _new_topic(self):
        if not self._require_post_permission():
            return

        title = simpledialog.askstring("New Topic", "Enter topic title:")
        if not title:
            return

        category = simpledialog.askstring(
            "Category",
            "Enter category (chef/dish/delivery/general):"
        )
        if not category:
            category = "general"

        topic_ref_id = simpledialog.askstring(
            "Reference ID (Optional)",
            "For dish/chef/delivery topics, enter the ID (optional):"
        ) or ""

        new_id = 1 + max([int(t["topic_id"]) for t in self.topics], default=0)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_topic = {
            "topic_id": str(new_id),
            "title": title,
            "category": category.lower(),
            "topic_ref_id": topic_ref_id,
            "author_username": self.user["username"],
            "created_at": now,
            "last_activity_at": now,
            "is_locked": "False",
        }

        self.topics.append(new_topic)
        save_topics(self.topics)

        first_post = simpledialog.askstring(
            "Opening Message", "Write your opening message:"
        )
        if first_post:
            add_post(new_id, self.user["username"], first_post)

        self.topics = sort_topics_by_activity(load_topics())
        self._refresh_topics()

    def _reply(self):
        if not self._require_post_permission():
            return

        sel = self.topic_tree.focus()
        if not sel:
            messagebox.showerror("Error", "Select a topic first.")
            return

        # Check locked
        for t in self.topics:
            if t["topic_id"] == sel and t["is_locked"] == "True":
                messagebox.showwarning(
                    "Locked Thread",
                    "This thread is locked by the manager."
                )
                return

        content = simpledialog.askstring("Reply", "Enter your reply:")
        if not content:
            return

        add_post(sel, self.user["username"], content)

        self.topics = sort_topics_by_activity(load_topics())
        self._refresh_topics()
        self._on_topic_select()

    def _back(self):
        from customer_gui import CustomerScreen
        self.destroy()
        CustomerScreen(self.master, self.user)
