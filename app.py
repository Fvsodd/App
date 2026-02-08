import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from collections import Counter
import math

DB_PATH = "marketplace.db"

CATEGORIES = ["education", "programming", "design", "ai tools", "utilities"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            faculty TEXT,
            course INTEGER
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            screenshots TEXT,
            status TEXT NOT NULL DEFAULT 'approved',
            downloads INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(author_id) REFERENCES users(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS installs (
            user_id INTEGER NOT NULL,
            app_id INTEGER NOT NULL,
            installed_at TEXT NOT NULL,
            PRIMARY KEY(user_id, app_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(app_id) REFERENCES apps(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            app_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(app_id) REFERENCES apps(id)
        )
        """
    )

    cur.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()["c"] == 0:
        seed_users = [
            ("student1", "pass123", "student", "IT", 2),
            ("student2", "pass123", "student", "Architecture", 3),
            ("teacher1", "pass123", "teacher", "IT", None),
            ("admin1", "admin123", "admin", "Administration", None),
        ]
        cur.executemany(
            "INSERT INTO users(username,password,role,faculty,course) VALUES(?,?,?,?,?)",
            seed_users,
        )

    cur.execute("SELECT COUNT(*) as c FROM apps")
    if cur.fetchone()["c"] == 0:
        cur.execute("SELECT id, username FROM users")
        users = {row["username"]: row["id"] for row in cur.fetchall()}
        seed_apps = [
            (
                "Python Lab Assistant",
                "Interactive programming helper for first-year coding courses.",
                "programming",
                users["student1"],
                "python_lab.png",
                "approved",
                32,
            ),
            (
                "Arch Sketch Toolkit",
                "Tools for architecture concept sketches and quick annotations.",
                "design",
                users["student2"],
                "arch_tool.png",
                "approved",
                18,
            ),
            (
                "AI Report Summarizer",
                "Summarize long educational reports and articles using AI prompts.",
                "ai tools",
                users["student1"],
                "ai_report.png",
                "approved",
                26,
            ),
            (
                "Campus Planner",
                "Simple utility to plan study schedule and deadlines.",
                "utilities",
                users["student2"],
                "planner.png",
                "approved",
                40,
            ),
        ]
        cur.executemany(
            """
            INSERT INTO apps(name,description,category,author_id,screenshots,status,downloads,created_at)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            [row + (datetime.utcnow().isoformat(),) for row in seed_apps],
        )

    conn.commit()
    conn.close()


def tokenize(text):
    return [w.lower().strip(".,!?()[]{}\"'") for w in text.split() if w.strip()]


def semantic_score(query, text):
    synonyms = {
        "architecture": ["design", "sketch", "modeling", "cad"],
        "project": ["assignment", "course", "task"],
        "ai": ["ml", "machine", "intelligence"],
        "coding": ["programming", "python", "developer"],
        "study": ["education", "learning", "course"],
    }

    q_tokens = tokenize(query)
    expanded = []
    for token in q_tokens:
        expanded.append(token)
        expanded.extend(synonyms.get(token, []))

    doc_tokens = tokenize(text)
    q_count = Counter(expanded)
    d_count = Counter(doc_tokens)

    all_terms = set(q_count) | set(d_count)
    q_vec = [q_count[t] for t in all_terms]
    d_vec = [d_count[t] for t in all_terms]

    dot = sum(a * b for a, b in zip(q_vec, d_vec))
    q_norm = math.sqrt(sum(a * a for a in q_vec))
    d_norm = math.sqrt(sum(b * b for b in d_vec))
    if q_norm == 0 or d_norm == 0:
        return 0.0
    return dot / (q_norm * d_norm)


class MarketplaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zhetisu University AI Marketplace MVP")
        self.geometry("1180x760")
        self.current_user = None

        self.login_frame = None
        self.main_frame = None
        self.notebook = None

        self.market_tree = None
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="all")
        self.details_text = None

        self.ai_faculty = tk.StringVar()
        self.ai_course = tk.StringVar()
        self.ai_interest = tk.StringVar()
        self.ai_output = None

        self.upload_name = tk.StringVar()
        self.upload_category = tk.StringVar(value=CATEGORIES[0])
        self.upload_desc = tk.StringVar()
        self.upload_screen = tk.StringVar()

        self.portfolio_text = None

        self.teacher_text = None
        self.admin_tree = None

        self.build_login_ui()

    def build_login_ui(self):
        if self.main_frame:
            self.main_frame.destroy()

        self.login_frame = ttk.Frame(self, padding=24)
        self.login_frame.pack(fill="both", expand=True)

        ttk.Label(self.login_frame, text="Zhetisu University AI Marketplace", font=("Segoe UI", 20, "bold")).pack(pady=(10, 20))
        ttk.Label(self.login_frame, text="Internal desktop MVP", font=("Segoe UI", 12)).pack(pady=(0, 20))

        form = ttk.Frame(self.login_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w", padx=5, pady=8)
        username_entry = ttk.Entry(form, width=30)
        username_entry.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", padx=5, pady=8)
        password_entry = ttk.Entry(form, show="*", width=30)
        password_entry.grid(row=1, column=1, padx=5)

        def submit_login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password),
            )
            user = cur.fetchone()
            conn.close()
            if user:
                self.current_user = user
                self.build_main_ui()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")

        ttk.Button(self.login_frame, text="Login", command=submit_login).pack(pady=12)
        ttk.Label(
            self.login_frame,
            text="Demo users: student1/pass123, teacher1/pass123, admin1/admin123",
            foreground="#666",
        ).pack(pady=(8, 0))

    def build_main_ui(self):
        self.login_frame.destroy()
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill="both", expand=True)

        top = ttk.Frame(self.main_frame)
        top.pack(fill="x")
        ttk.Label(
            top,
            text=f"Logged in as {self.current_user['username']} ({self.current_user['role']})",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")
        ttk.Button(top, text="Logout", command=self.logout).pack(side="right")

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        self.add_marketplace_tab()
        self.add_ai_tab()

        if self.current_user["role"] == "student":
            self.add_upload_tab()
            self.add_portfolio_tab()
        elif self.current_user["role"] == "teacher":
            self.add_teacher_tab()
        elif self.current_user["role"] == "admin":
            self.add_admin_tab()

    def logout(self):
        self.current_user = None
        self.main_frame.destroy()
        self.build_login_ui()

    def add_marketplace_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Marketplace")

        controls = ttk.Frame(frame, padding=8)
        controls.pack(fill="x")

        ttk.Label(controls, text="Search:").pack(side="left")
        search_entry = ttk.Entry(controls, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)

        ttk.Label(controls, text="Category:").pack(side="left", padx=(10, 3))
        cat_menu = ttk.Combobox(controls, textvariable=self.category_var, values=["all"] + CATEGORIES, state="readonly", width=15)
        cat_menu.pack(side="left")

        ttk.Button(controls, text="Find", command=self.refresh_marketplace).pack(side="left", padx=8)
        ttk.Button(controls, text="Install Selected", command=self.install_selected).pack(side="left", padx=8)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True)

        self.market_tree = ttk.Treeview(body, columns=("id", "name", "category", "author", "downloads"), show="headings")
        for col, title in [
            ("id", "ID"),
            ("name", "Application"),
            ("category", "Category"),
            ("author", "Author"),
            ("downloads", "Downloads"),
        ]:
            self.market_tree.heading(col, text=title)
            self.market_tree.column(col, width=120 if col != "name" else 300)
        self.market_tree.pack(side="left", fill="both", expand=True)
        self.market_tree.bind("<<TreeviewSelect>>", lambda _: self.render_app_details())

        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        self.details_text = tk.Text(frame, height=8, wrap="word")
        self.details_text.pack(fill="x", padx=8, pady=8)

        self.refresh_marketplace()

    def refresh_marketplace(self):
        for row in self.market_tree.get_children():
            self.market_tree.delete(row)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT apps.id, apps.name, apps.description, apps.category, apps.downloads, apps.screenshots,
                   users.username AS author
            FROM apps
            JOIN users ON apps.author_id = users.id
            WHERE apps.status='approved'
            """
        )
        rows = cur.fetchall()
        conn.close()

        query = self.search_var.get().strip().lower()
        category = self.category_var.get().strip().lower()

        ranked = []
        for r in rows:
            if category and category != "all" and r["category"] != category:
                continue
            combined = f"{r['name']} {r['description']} {r['category']}"
            score = semantic_score(query, combined) if query else 1.0
            if not query or query in combined.lower() or score > 0.08:
                ranked.append((score, r))

        ranked.sort(key=lambda x: (x[0], x[1]["downloads"]), reverse=True)
        for _, r in ranked:
            self.market_tree.insert("", "end", values=(r["id"], r["name"], r["category"], r["author"], r["downloads"]))

    def selected_app_id(self):
        selected = self.market_tree.selection()
        if not selected:
            return None
        values = self.market_tree.item(selected[0], "values")
        return int(values[0])

    def render_app_details(self):
        app_id = self.selected_app_id()
        if not app_id:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT apps.*, users.username as author
            FROM apps JOIN users ON users.id=apps.author_id
            WHERE apps.id=?
            """,
            (app_id,),
        )
        app = cur.fetchone()
        conn.close()

        self.details_text.delete("1.0", "end")
        detail = (
            f"Name: {app['name']}\n"
            f"Category: {app['category']}\n"
            f"Author: {app['author']}\n"
            f"Downloads: {app['downloads']}\n"
            f"Screenshots: {app['screenshots'] or 'N/A'}\n\n"
            f"Description:\n{app['description']}"
        )
        self.details_text.insert("1.0", detail)

    def install_selected(self):
        app_id = self.selected_app_id()
        if not app_id:
            messagebox.showwarning("Install", "Select an application first")
            return
        if self.current_user["role"] != "student":
            messagebox.showinfo("Install", "Mock install is available for student role only in MVP")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO installs(user_id, app_id, installed_at) VALUES(?,?,?)",
            (self.current_user["id"], app_id, datetime.utcnow().isoformat()),
        )
        cur.execute("UPDATE apps SET downloads = downloads + 1 WHERE id=?", (app_id,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Install", "Mock install completed. App added to portfolio.")
        self.refresh_marketplace()
        if self.current_user["role"] == "student" and self.portfolio_text:
            self.refresh_portfolio()

    def add_ai_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="AI Navigator")

        form = ttk.Frame(frame, padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="Faculty:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.ai_faculty, width=25).grid(row=0, column=1, padx=6)
        ttk.Label(form, text="Course:").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.ai_course, width=10).grid(row=0, column=3, padx=6)
        ttk.Label(form, text="Interests:").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Entry(form, textvariable=self.ai_interest, width=60).grid(row=1, column=1, columnspan=3, padx=6, sticky="w")

        ttk.Button(form, text="Generate Recommendations", command=self.run_ai_navigator).grid(row=2, column=0, columnspan=2, pady=8, sticky="w")

        self.ai_output = tk.Text(frame, wrap="word")
        self.ai_output.pack(fill="both", expand=True, padx=10, pady=10)

    def run_ai_navigator(self):
        faculty = self.ai_faculty.get().strip() or (self.current_user["faculty"] or "general")
        course = self.ai_course.get().strip() or (self.current_user["course"] if self.current_user["course"] else "N/A")
        interests = self.ai_interest.get().strip().lower()

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description, category, downloads FROM apps WHERE status='approved'"
        )
        apps = cur.fetchall()

        scored = []
        for app in apps:
            text = f"{app['name']} {app['description']} {app['category']}"
            score = semantic_score(f"{faculty} {interests}", text)
            score += app["downloads"] / 1000
            scored.append((score, app))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [a for _, a in scored[:3]]

        category_focus = "programming"
        if "arch" in faculty.lower() or "design" in interests:
            category_focus = "design"
        elif "ai" in interests or "data" in interests:
            category_focus = "ai tools"
        elif "edu" in interests or "study" in interests:
            category_focus = "education"

        project_idea = {
            "programming": "build a grading assistant plugin that checks code style and gives hints",
            "design": "create an AI-assisted architecture visualization and feedback tool",
            "ai tools": "develop a local AI note summarizer for university research papers",
            "education": "make a smart study planner for course milestones and exam prep",
            "utilities": "build a campus productivity launcher with timetable integration",
        }[category_focus]

        rec_lines = [
            f"You are a {faculty} student (course {course}).",
            "Recommended applications to install now:",
        ]
        rec_lines.extend([f"- {a['name']} ({a['category']})" for a in top])
        rec_lines.append("\nSkills to develop:")
        if category_focus == "programming":
            rec_lines.extend(["- Python and API integration", "- Testing and debugging", "- UI/UX for desktop tools"])
        elif category_focus == "design":
            rec_lines.extend(["- Visualization workflow", "- Human-centered design", "- Tool prototyping"])
        elif category_focus == "ai tools":
            rec_lines.extend(["- Prompt engineering", "- Data preprocessing", "- Model evaluation basics"])
        else:
            rec_lines.extend(["- Product thinking", "- Data literacy", "- Communication and documentation"])

        rec_lines.append(f"\nApplication idea for your portfolio: {project_idea}.")
        rec_lines.append("This recommendation is generated using profile + semantic marketplace matching.")

        self.ai_output.delete("1.0", "end")
        self.ai_output.insert("1.0", "\n".join(rec_lines))
        conn.close()

    def add_upload_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Upload Application")

        form = ttk.Frame(frame, padding=12)
        form.pack(fill="x")

        ttk.Label(form, text="App Name:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.upload_name, width=45).grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Category:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(form, textvariable=self.upload_category, values=CATEGORIES, state="readonly", width=20).grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.upload_desc, width=70).grid(row=2, column=1, sticky="w")

        ttk.Label(form, text="Screenshot Path (optional):").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.upload_screen, width=45).grid(row=3, column=1, sticky="w")

        ttk.Button(form, text="Submit for Approval", command=self.submit_app).grid(row=4, column=0, columnspan=2, pady=10, sticky="w")

        ttk.Label(
            frame,
            text="Uploaded applications are visible after admin approval.",
            foreground="#555",
        ).pack(anchor="w", padx=12)

    def submit_app(self):
        name = self.upload_name.get().strip()
        desc = self.upload_desc.get().strip()
        category = self.upload_category.get().strip()
        screen = self.upload_screen.get().strip()

        if not name or not desc:
            messagebox.showwarning("Upload", "Name and description are required")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO apps(name,description,category,author_id,screenshots,status,downloads,created_at)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                name,
                desc,
                category,
                self.current_user["id"],
                screen,
                "pending",
                0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Upload", "Application submitted for admin review")
        self.upload_name.set("")
        self.upload_desc.set("")
        self.upload_screen.set("")

    def add_portfolio_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="My Portfolio")

        ttk.Button(frame, text="Refresh Portfolio", command=self.refresh_portfolio).pack(anchor="w", padx=8, pady=8)
        self.portfolio_text = tk.Text(frame, wrap="word")
        self.portfolio_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.refresh_portfolio()

    def refresh_portfolio(self):
        conn = get_connection()
        cur = conn.cursor()

        uid = self.current_user["id"]

        cur.execute(
            """
            SELECT apps.name, apps.category, installs.installed_at
            FROM installs
            JOIN apps ON apps.id = installs.app_id
            WHERE installs.user_id=?
            ORDER BY installs.installed_at DESC
            """,
            (uid,),
        )
        installed = cur.fetchall()

        cur.execute(
            """
            SELECT name, status, downloads
            FROM apps
            WHERE author_id=?
            ORDER BY created_at DESC
            """,
            (uid,),
        )
        published = cur.fetchall()

        cur.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE user_id=?",
            (uid,),
        )
        review_count = cur.fetchone()["c"]

        total_downloads = sum(row["downloads"] for row in published)
        usefulness_score = min(100, len(installed) * 12 + len(published) * 15 + review_count * 4 + total_downloads // 3)

        lines = [
            f"Student: {self.current_user['username']}",
            f"Faculty: {self.current_user['faculty']}",
            "",
            f"Installed apps ({len(installed)}):",
        ]
        for row in installed:
            lines.append(f"- {row['name']} [{row['category']}] installed at {row['installed_at']}")

        lines.append(f"\nPublished apps ({len(published)}):")
        for row in published:
            lines.append(f"- {row['name']} | status: {row['status']} | downloads: {row['downloads']}")

        lines.extend(
            [
                "",
                f"Total downloads of your projects: {total_downloads}",
                f"Reviews written: {review_count}",
                f"AI usefulness score: {usefulness_score}/100",
                "Portfolio score combines usage, publications, and project impact.",
            ]
        )

        self.portfolio_text.delete("1.0", "end")
        self.portfolio_text.insert("1.0", "\n".join(lines))
        conn.close()

    def add_teacher_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Teacher Dashboard")

        ttk.Button(frame, text="Refresh Dashboard", command=self.refresh_teacher_dashboard).pack(anchor="w", padx=8, pady=8)
        self.teacher_text = tk.Text(frame, wrap="word")
        self.teacher_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.refresh_teacher_dashboard()

    def refresh_teacher_dashboard(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT apps.name, apps.downloads, users.username as author
            FROM apps JOIN users ON users.id=apps.author_id
            WHERE apps.status='approved'
            ORDER BY apps.downloads DESC
            LIMIT 5
            """
        )
        popular = cur.fetchall()

        cur.execute(
            """
            SELECT users.username, SUM(apps.downloads) as total
            FROM apps JOIN users ON users.id=apps.author_id
            WHERE users.role='student'
            GROUP BY users.username
            ORDER BY total DESC
            LIMIT 5
            """
        )
        top_students = cur.fetchall()

        cur.execute("SELECT COUNT(*) as c FROM installs")
        installs_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM apps WHERE status='approved'")
        app_count = cur.fetchone()["c"]

        lines = ["Teacher Dashboard (MVP)", "", "Most used applications:"]
        for row in popular:
            lines.append(f"- {row['name']} by {row['author']} ({row['downloads']} downloads)")

        lines.append("\nTop student projects (by cumulative downloads):")
        for row in top_students:
            lines.append(f"- {row['username']}: {row['total']} total downloads")

        lines.extend(
            [
                "",
                f"Usage statistics: {installs_count} installations made by students.",
                f"Approved apps in marketplace: {app_count}.",
            ]
        )

        self.teacher_text.delete("1.0", "end")
        self.teacher_text.insert("1.0", "\n".join(lines))
        conn.close()

    def add_admin_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Admin Panel")

        controls = ttk.Frame(frame, padding=8)
        controls.pack(fill="x")
        ttk.Button(controls, text="Refresh", command=self.refresh_admin_queue).pack(side="left")
        ttk.Button(controls, text="Approve Selected", command=lambda: self.update_selected_app_status("approved")).pack(side="left", padx=6)
        ttk.Button(controls, text="Reject Selected", command=lambda: self.update_selected_app_status("rejected")).pack(side="left", padx=6)

        self.admin_tree = ttk.Treeview(frame, columns=("id", "name", "author", "category", "status"), show="headings")
        for col in ["id", "name", "author", "category", "status"]:
            self.admin_tree.heading(col, text=col.title())
            self.admin_tree.column(col, width=180 if col == "name" else 120)
        self.admin_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.refresh_admin_queue()

    def refresh_admin_queue(self):
        for row in self.admin_tree.get_children():
            self.admin_tree.delete(row)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT apps.id, apps.name, apps.category, apps.status, users.username as author
            FROM apps JOIN users ON users.id=apps.author_id
            ORDER BY apps.status='pending' DESC, apps.created_at DESC
            """
        )
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.admin_tree.insert("", "end", values=(row["id"], row["name"], row["author"], row["category"], row["status"]))

    def update_selected_app_status(self, status):
        selected = self.admin_tree.selection()
        if not selected:
            messagebox.showwarning("Admin", "Select an application")
            return

        values = self.admin_tree.item(selected[0], "values")
        app_id = int(values[0])

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE apps SET status=? WHERE id=?", (status, app_id))
        conn.commit()
        conn.close()

        self.refresh_admin_queue()
        self.refresh_marketplace()
        messagebox.showinfo("Admin", f"Application {status}")


if __name__ == "__main__":
    init_db()
    app = MarketplaceApp()
    app.mainloop()
