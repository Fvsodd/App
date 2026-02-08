import re
import sqlite3
import textwrap
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

DB_PATH = "marketplace.db"
CATEGORIES = ["Education", "Programming", "Design", "AI Tools", "Utilities"]


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            faculty TEXT,
            course TEXT
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

    cur.execute("SELECT COUNT(*) c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO users(username,password,role,faculty,course) VALUES(?,?,?,?,?)",
            [
                ("student1", "pass123", "student", "IT", "2"),
                ("student2", "pass123", "student", "Architecture", "3"),
                ("teacher1", "pass123", "teacher", "Engineering", "-"),
                ("admin1", "admin123", "admin", "Administration", "-"),
            ],
        )

    cur.execute("SELECT COUNT(*) c FROM apps")
    if cur.fetchone()["c"] == 0:
        cur.execute("SELECT id, username FROM users")
        ids = {r["username"]: r["id"] for r in cur.fetchall()}
        now = datetime.utcnow().isoformat()
        cur.executemany(
            """
            INSERT INTO apps(name,description,category,author_id,status,downloads,created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            [
                (
                    "Python Lab Assistant",
                    "Practice helper for programming labs and assignments.",
                    "Programming",
                    ids["student1"],
                    "approved",
                    31,
                    now,
                ),
                (
                    "Campus Planner",
                    "Utility for weekly study planning and deadline tracking.",
                    "Utilities",
                    ids["student2"],
                    "approved",
                    46,
                    now,
                ),
                (
                    "Arch Sketch Toolkit",
                    "Quick sketch and reference toolkit for architecture projects.",
                    "Design",
                    ids["student2"],
                    "approved",
                    19,
                    now,
                ),
                (
                    "AI Report Summarizer",
                    "Summarizes long course reports into concise notes.",
                    "AI Tools",
                    ids["student1"],
                    "approved",
                    24,
                    now,
                ),
            ],
        )

    conn.commit()
    conn.close()


class KonspektEngine:
    STOP_WORDS = {
        "и", "в", "во", "на", "с", "со", "по", "к", "ко", "о", "об", "от", "до", "за", "из", "у",
        "а", "но", "или", "ли", "же", "бы", "это", "этот", "эта", "эти", "как", "что", "чтобы",
        "для", "при", "так", "не", "ни", "то", "его", "ее", "их", "мы", "вы", "они", "он", "она",
    }

    @staticmethod
    def split_sentences(text: str):
        text = re.sub(r"\s+", " ", text.strip())
        if not text:
            return []
        return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]

    @staticmethod
    def sentence_score(sentence: str):
        words = re.findall(r"[А-Яа-яA-Za-zЁё\-]+", sentence.lower())
        if not words:
            return 0
        score = 0
        for w in words:
            if len(w) >= 7:
                score += 2
            elif len(w) >= 5:
                score += 1
            if w not in KonspektEngine.STOP_WORDS:
                score += 0.3
        if any(ch.isdigit() for ch in sentence):
            score += 1
        if ":" in sentence or ";" in sentence:
            score += 0.8
        return score

    @staticmethod
    def choose_count(total: int, length_mode: str):
        if total == 0:
            return 0
        if length_mode == "Короткий":
            return max(3, min(6, total // 4 if total > 8 else total))
        if length_mode == "Средний":
            return max(5, min(10, total // 2 if total > 10 else total))
        return max(8, min(16, int(total * 0.75) if total > 12 else total))

    @staticmethod
    def generate(text: str, length_mode: str, style_mode: str):
        sents = KonspektEngine.split_sentences(text)
        if not sents:
            return "Пожалуйста, вставьте текст для конспектирования."

        scored = [(i, s, KonspektEngine.sentence_score(s)) for i, s in enumerate(sents)]
        chosen = sorted(scored, key=lambda x: x[2], reverse=True)[:KonspektEngine.choose_count(len(sents), length_mode)]
        chosen = [s for _, s, _ in sorted(chosen, key=lambda x: x[0])]

        lines = ["КОНСПЕКТ", "=" * 55, ""]
        if style_mode == "Для экзамена":
            lines.append("Что важно запомнить:")
            for i, s in enumerate(chosen[:8], 1):
                lines.append(f"{i}) {s}")
        elif style_mode == "Для понимания":
            lines.append("Логика материала:")
            if chosen:
                lines.append(f"• Главная идея: {chosen[0]}")
            for s in chosen[1:6]:
                lines.append(f"• Ключевой момент: {s}")
            if len(chosen) > 1:
                lines.append(f"• Вывод: {chosen[-1]}")
        else:
            lines.append("Краткие тезисы:")
            for s in chosen[:10]:
                lines.append(f"• {s}")

        wrapped = []
        for line in lines:
            if line.startswith("•") or line[:2].isdigit() or line.endswith(":") or line.startswith("="):
                wrapped.append(line)
            else:
                wrapped.extend(textwrap.wrap(line, width=92) if line else [""])
        return "\n".join(wrapped)


class UniversityMarketplaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zhetisu University Marketplace Beta")
        self.geometry("1280x780")
        self.minsize(1100, 700)

        self.current_user = None
        self.content_frame = None

        self.market_tree = None
        self.profile_text = None
        self.admin_tree = None
        self.ai_output = None

        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All")
        self.ai_faculty = tk.StringVar()
        self.ai_course = tk.StringVar()
        self.ai_interests = tk.StringVar()

        self.upload_name = tk.StringVar()
        self.upload_cat = tk.StringVar(value=CATEGORIES[0])
        self.upload_desc = tk.StringVar()

        self.conspect_length_var = tk.StringVar(value="Средний")
        self.conspect_style_var = tk.StringVar(value="Для понимания")
        self.conspect_status_var = tk.StringVar(value="Готово к работе")
        self.conspect_input = None
        self.conspect_output = None
        self.conspect_btn = None

        self._build_login()

    def clear_root(self):
        for child in self.winfo_children():
            child.destroy()

    def _build_login(self):
        self.clear_root()
        frame = ttk.Frame(self, padding=36)
        frame.pack(fill="both", expand=True)

        box = ttk.Frame(frame, padding=24)
        box.pack(expand=True)

        ttk.Label(box, text="Zhetisu University Marketplace", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        ttk.Label(
            box,
            text="Internal beta application for students, teachers and administration.",
            font=("Segoe UI", 11),
            foreground="#444",
        ).pack(anchor="w", pady=(4, 18))

        form = ttk.Frame(box)
        form.pack(anchor="w")
        ttk.Label(form, text="Username", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Password", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        username_entry = ttk.Entry(form, width=32)
        password_entry = ttk.Entry(form, width=32, show="*")
        username_entry.grid(row=0, column=1, padx=10)
        password_entry.grid(row=1, column=1, padx=10)

        def do_login():
            conn = db_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username_entry.get().strip(), password_entry.get().strip()),
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Login failed", "Invalid username or password")
                return
            self.current_user = row
            self._build_dashboard()

        ttk.Button(box, text="Login", command=do_login).pack(anchor="w", pady=(14, 6))
        ttk.Label(
            box,
            text="Demo accounts: student1/pass123, teacher1/pass123, admin1/admin123",
            foreground="#666",
        ).pack(anchor="w")

    def _build_dashboard(self):
        self.clear_root()

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Zhetisu University Marketplace — Beta Demo",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")
        ttk.Label(header, text=f"{self.current_user['username']} ({self.current_user['role']})", foreground="#444").pack(side="right", padx=8)
        ttk.Button(header, text="Logout", command=self._logout).pack(side="right")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        nav = ttk.Frame(body, width=230, padding=10)
        nav.pack(side="left", fill="y")
        self.content_frame = ttk.Frame(body, padding=12)
        self.content_frame.pack(side="left", fill="both", expand=True)

        ttk.Label(nav, text="Navigation", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))
        nav_items = [
            ("Marketplace", self.show_marketplace),
            ("AI Navigator", self.show_ai_navigator),
            ("Profile", self.show_profile),
            ("Конспектатор", self.show_conspectator),
        ]
        if self.current_user["role"] == "admin":
            nav_items.append(("Admin Panel", self.show_admin_panel))

        for text, fn in nav_items:
            ttk.Button(nav, text=text, command=fn, width=24).pack(anchor="w", pady=4)

        if self.current_user["role"] == "student":
            ttk.Separator(nav, orient="horizontal").pack(fill="x", pady=10)
            ttk.Label(nav, text="Student Action", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
            ttk.Button(nav, text="Submit New App", command=self._student_submit_dialog, width=24).pack(anchor="w")

        self._show_intro_card()
        self.show_marketplace()

    def _show_intro_card(self):
        card = ttk.Frame(self.content_frame, padding=10)
        card.pack(fill="x", pady=(0, 10))
        ttk.Label(card, text="What to do now", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(
            card,
            text="1) Browse Marketplace  2) Try AI Navigator  3) Open Profile  4) Use Конспектатор.",
            foreground="#555",
        ).pack(anchor="w", pady=(2, 0))

    def _clear_content(self):
        for child in self.content_frame.winfo_children():
            child.destroy()
        self._show_intro_card()

    def _logout(self):
        self.current_user = None
        self._build_login()

    def show_marketplace(self):
        self._clear_content()
        filter_box = ttk.Frame(self.content_frame)
        filter_box.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_box, text="Marketplace", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 12))
        ttk.Label(filter_box, text="Search:").pack(side="left")
        ttk.Entry(filter_box, textvariable=self.search_var, width=28).pack(side="left", padx=(4, 8))
        ttk.Label(filter_box, text="Category:").pack(side="left")
        ttk.Combobox(filter_box, textvariable=self.category_var, values=["All"] + CATEGORIES, state="readonly", width=15).pack(side="left", padx=(4, 8))
        ttk.Button(filter_box, text="Apply", command=self._refresh_marketplace).pack(side="left")
        ttk.Button(filter_box, text="Install Selected", command=self._install_selected).pack(side="left", padx=6)

        self.market_tree = ttk.Treeview(
            self.content_frame,
            columns=("id", "name", "category", "author", "downloads", "status"),
            show="headings",
            height=16,
        )
        for col, txt, w in [
            ("id", "ID", 45),
            ("name", "Application", 320),
            ("category", "Category", 130),
            ("author", "Author", 130),
            ("downloads", "Downloads", 90),
            ("status", "Status", 90),
        ]:
            self.market_tree.heading(col, text=txt)
            self.market_tree.column(col, width=w, anchor="w")
        self.market_tree.pack(fill="both", expand=True)

        self._refresh_marketplace()

    def _refresh_marketplace(self):
        for row in self.market_tree.get_children():
            self.market_tree.delete(row)

        conn = db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT apps.id, apps.name, apps.description, apps.category, apps.downloads, apps.status,
                   users.username author
            FROM apps JOIN users ON users.id=apps.author_id
            ORDER BY apps.downloads DESC, apps.name
            """
        )
        rows = cur.fetchall()
        conn.close()

        q = self.search_var.get().strip().lower()
        cat = self.category_var.get().strip()

        for r in rows:
            if self.current_user["role"] != "admin" and r["status"] != "approved":
                continue
            if cat and cat != "All" and r["category"] != cat:
                continue
            hay = f"{r['name']} {r['description']} {r['category']} {r['author']}".lower()
            if q and q not in hay:
                continue
            self.market_tree.insert("", "end", values=(r["id"], r["name"], r["category"], r["author"], r["downloads"], r["status"]))

    def _install_selected(self):
        sel = self.market_tree.selection()
        if not sel:
            messagebox.showwarning("Install", "Please select an application first")
            return
        if self.current_user["role"] != "student":
            messagebox.showinfo("Install", "Install action is enabled for student role in this beta")
            return

        app_id = int(self.market_tree.item(sel[0], "values")[0])
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO installs(user_id, app_id, installed_at) VALUES(?,?,?)", (self.current_user["id"], app_id, datetime.utcnow().isoformat()))
        cur.execute("UPDATE apps SET downloads=downloads+1 WHERE id=?", (app_id,))
        conn.commit()
        conn.close()

        self._refresh_marketplace()
        messagebox.showinfo("Install", "Application installed (simulated).")

    def show_ai_navigator(self):
        self._clear_content()

        ttk.Label(self.content_frame, text="AI Navigator", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self.content_frame, text="Get personalized recommendations for apps, skills, and project ideas.", foreground="#555").pack(anchor="w", pady=(2, 10))

        form = ttk.Frame(self.content_frame)
        form.pack(fill="x")

        ttk.Label(form, text="Faculty").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.ai_faculty, width=24).grid(row=0, column=1, padx=8)
        ttk.Label(form, text="Course").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.ai_course, width=10).grid(row=0, column=3, padx=8)
        ttk.Label(form, text="Interests").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.ai_interests, width=62).grid(row=1, column=1, columnspan=3, sticky="w", padx=8)

        if not self.ai_faculty.get().strip():
            self.ai_faculty.set(self.current_user["faculty"] or "General")
        if not self.ai_course.get().strip():
            self.ai_course.set(self.current_user["course"] or "-")

        ttk.Button(self.content_frame, text="Get recommendations", command=self._generate_ai_recommendations).pack(anchor="w", pady=8)

        self.ai_output = tk.Text(self.content_frame, height=18, wrap="word")
        self.ai_output.pack(fill="both", expand=True)
        self.ai_output.insert("1.0", "AI Navigator is ready. Enter interests and click Get recommendations.")

    def _generate_ai_recommendations(self):
        faculty = self.ai_faculty.get().strip() or "General"
        course = self.ai_course.get().strip() or "-"
        interests = self.ai_interests.get().strip().lower()

        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT name, category, description, downloads FROM apps WHERE status='approved'")
        apps = cur.fetchall()
        conn.close()

        def score(app):
            base = app["downloads"] / 100
            text = f"{app['name']} {app['description']} {app['category']}".lower()
            words = [w for w in interests.split() if w]
            hits = sum(1 for w in words if w in text)
            return base + hits

        top = sorted(apps, key=score, reverse=True)[:3]
        focus = "software tooling"
        idea = "Create a study helper app for your faculty with deadline reminders."
        skills = ["Product thinking", "Data organization", "User-centered design"]
        if "arch" in faculty.lower() or "design" in interests:
            focus = "design and visualization"
            idea = "Build an architecture concept review assistant with annotation support."
            skills = ["Visualization workflow", "Design critique", "Rapid prototyping"]
        elif "it" in faculty.lower() or "code" in interests or "python" in interests:
            focus = "programming and automation"
            idea = "Develop a code quality helper for student assignments."
            skills = ["Python automation", "Testing basics", "API integration"]
        elif "ai" in interests or "data" in interests:
            focus = "AI-supported productivity"
            idea = "Create a local AI note summarizer for research readings."
            skills = ["Prompt design", "Data preprocessing", "Model evaluation"]

        lines = [f"Student profile summary: {faculty} faculty, course {course}.", "", "Recommended applications:"]
        for app in top:
            lines.append(f"- {app['name']} ({app['category']}) — useful for {focus}.")
        lines.extend(["", "Skills to develop next:", *[f"- {s}" for s in skills], "", f"Portfolio project idea: {idea}"])

        self.ai_output.delete("1.0", "end")
        self.ai_output.insert("1.0", "\n".join(lines))

    def show_profile(self):
        self._clear_content()
        ttk.Label(self.content_frame, text="Profile & Portfolio", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.profile_text = tk.Text(self.content_frame, height=24, wrap="word")
        self.profile_text.pack(fill="both", expand=True, pady=(8, 0))

        conn = db_conn()
        cur = conn.cursor()
        uid = self.current_user["id"]
        cur.execute(
            """
            SELECT apps.name, apps.category, installs.installed_at
            FROM installs JOIN apps ON apps.id=installs.app_id
            WHERE installs.user_id=? ORDER BY installs.installed_at DESC
            """,
            (uid,),
        )
        installed = cur.fetchall()
        cur.execute("SELECT name, status, downloads FROM apps WHERE author_id=? ORDER BY created_at DESC", (uid,))
        published = cur.fetchall()
        conn.close()

        total_downloads = sum(r["downloads"] for r in published)
        portfolio_score = min(100, len(installed) * 15 + len(published) * 12 + total_downloads // 3)

        lines = [
            f"User: {self.current_user['username']} ({self.current_user['role']})",
            f"Faculty: {self.current_user['faculty']} | Course: {self.current_user['course']}",
            "",
            f"Installed apps ({len(installed)}):",
        ]
        lines.extend([f"- {r['name']} [{r['category']}] installed at {r['installed_at']}" for r in installed])
        lines.append("")
        lines.append(f"Published apps ({len(published)}):")
        lines.extend([f"- {r['name']} | status: {r['status']} | downloads: {r['downloads']}" for r in published])
        lines.extend(["", "Portfolio statistics:", f"- Total downloads of your apps: {total_downloads}", f"- Portfolio score: {portfolio_score}/100"])

        self.profile_text.insert("1.0", "\n".join(lines))

    def show_admin_panel(self):
        self._clear_content()
        ttk.Label(self.content_frame, text="Admin Panel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self.content_frame, text="Moderate applications and view system-level statistics.", foreground="#555").pack(anchor="w", pady=(2, 8))

        controls = ttk.Frame(self.content_frame)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Approve", command=lambda: self._change_app_status("approved")).pack(side="left")
        ttk.Button(controls, text="Reject", command=lambda: self._change_app_status("rejected")).pack(side="left", padx=6)
        ttk.Button(controls, text="Refresh", command=self._refresh_admin_apps).pack(side="left", padx=6)

        self.admin_tree = ttk.Treeview(self.content_frame, columns=("id", "name", "author", "category", "status", "downloads"), show="headings", height=13)
        for col, txt, w in [
            ("id", "ID", 45),
            ("name", "Application", 280),
            ("author", "Author", 120),
            ("category", "Category", 120),
            ("status", "Status", 100),
            ("downloads", "Downloads", 90),
        ]:
            self.admin_tree.heading(col, text=txt)
            self.admin_tree.column(col, width=w, anchor="w")
        self.admin_tree.pack(fill="both", expand=True)

        stats = ttk.Frame(self.content_frame, padding=(0, 10, 0, 0))
        stats.pack(fill="x")
        self.admin_stats_label = ttk.Label(stats, text="")
        self.admin_stats_label.pack(anchor="w")
        self._refresh_admin_apps()

    def _refresh_admin_apps(self):
        for row in self.admin_tree.get_children():
            self.admin_tree.delete(row)

        conn = db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT apps.id, apps.name, apps.category, apps.status, apps.downloads, users.username author
            FROM apps JOIN users ON users.id=apps.author_id
            ORDER BY CASE apps.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, apps.created_at DESC
            """
        )
        apps = cur.fetchall()
        for a in apps:
            self.admin_tree.insert("", "end", values=(a["id"], a["name"], a["author"], a["category"], a["status"], a["downloads"]))

        cur.execute("SELECT COUNT(*) c FROM apps WHERE status='pending'")
        pending = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) c FROM installs")
        installs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) c FROM apps")
        total_apps = cur.fetchone()["c"]
        conn.close()

        self.admin_stats_label.config(text=f"Statistics: total apps={total_apps} | pending approval={pending} | total installs={installs}")

    def _change_app_status(self, status):
        sel = self.admin_tree.selection()
        if not sel:
            messagebox.showwarning("Admin", "Please select an application")
            return
        app_id = int(self.admin_tree.item(sel[0], "values")[0])
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE apps SET status=? WHERE id=?", (status, app_id))
        conn.commit()
        conn.close()
        self._refresh_admin_apps()
        messagebox.showinfo("Admin", f"Application marked as {status}.")

    def _student_submit_dialog(self):
        if self.current_user["role"] != "student":
            return

        dlg = tk.Toplevel(self)
        dlg.title("Submit Application")
        dlg.geometry("540x320")
        dlg.transient(self)
        dlg.grab_set()

        root = ttk.Frame(dlg, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Submit New Application", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(root, text="Submitted apps require admin approval before appearing in marketplace.", foreground="#555").pack(anchor="w", pady=(2, 10))

        form = ttk.Frame(root)
        form.pack(fill="x")
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.upload_name, width=46).grid(row=0, column=1, padx=8)
        ttk.Label(form, text="Category").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.upload_cat, values=CATEGORIES, state="readonly", width=20).grid(row=1, column=1, sticky="w", padx=8)
        ttk.Label(form, text="Description").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.upload_desc, width=60).grid(row=2, column=1, padx=8)

        def submit():
            name = self.upload_name.get().strip()
            cat = self.upload_cat.get().strip()
            desc = self.upload_desc.get().strip()
            if not name or not desc:
                messagebox.showwarning("Submit", "Name and description are required")
                return
            conn = db_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO apps(name,description,category,author_id,status,downloads,created_at) VALUES(?,?,?,?,?,?,?)",
                (name, desc, cat, self.current_user["id"], "pending", 0, datetime.utcnow().isoformat()),
            )
            conn.commit()
            conn.close()
            self.upload_name.set("")
            self.upload_desc.set("")
            self.upload_cat.set(CATEGORIES[0])
            dlg.destroy()
            self._refresh_marketplace()
            messagebox.showinfo("Submit", "Application submitted for admin review")

        btn_row = ttk.Frame(root)
        btn_row.pack(anchor="e", pady=14)
        ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(side="right")
        ttk.Button(btn_row, text="Submit", command=submit).pack(side="right", padx=8)

    # ---------- Integrated Conspectator ----------
    def show_conspectator(self):
        self._clear_content()

        ttk.Label(self.content_frame, text="📚 Конспектатор — умное сокращение учебных текстов", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(self.content_frame, text="Вставьте текст лекции или учебного материала — мы сделаем краткий конспект", foreground="#444").pack(anchor="w", pady=(4, 10))

        controls = ttk.Frame(self.content_frame)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Длина:").pack(side="left")
        ttk.Combobox(controls, textvariable=self.conspect_length_var, values=["Короткий", "Средний", "Подробный"], state="readonly", width=12).pack(side="left", padx=(5, 15))
        ttk.Label(controls, text="Стиль:").pack(side="left")
        ttk.Combobox(controls, textvariable=self.conspect_style_var, values=["Для экзамена", "Для понимания", "Краткие тезисы"], state="readonly", width=18).pack(side="left", padx=(5, 15))
        ttk.Label(controls, textvariable=self.conspect_status_var, foreground="#355e3b").pack(side="left", padx=10)

        main = ttk.Frame(self.content_frame)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        center = ttk.Frame(main, width=180)
        center.pack(side="left", fill="y", padx=12)
        center.pack_propagate(False)
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Текст для обработки", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
        self.conspect_input = tk.Text(left, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        self.conspect_input.pack(fill="both", expand=True)

        ttk.Label(right, text="Готовый конспект", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
        self.conspect_output = tk.Text(right, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        self.conspect_output.pack(fill="both", expand=True)

        self.conspect_btn = ttk.Button(center, text="✨ Создать конспект", command=self._generate_conspect, width=20)
        self.conspect_btn.pack(pady=(60, 10))
        ttk.Button(center, text="Копировать", command=self._copy_conspect, width=20).pack(pady=8)
        ttk.Button(center, text="Сохранить .txt", command=self._save_conspect, width=20).pack(pady=4)

    def _generate_conspect(self):
        source = self.conspect_input.get("1.0", "end").strip()
        if not source:
            messagebox.showwarning("Нет текста", "Пожалуйста, вставьте текст перед созданием конспекта.")
            return
        self.conspect_status_var.set("Обработка текста...")
        self.conspect_btn.config(state="disabled")
        self.update_idletasks()
        self.after(250, lambda: self._finish_conspect(source))

    def _finish_conspect(self, source):
        result = KonspektEngine.generate(source, self.conspect_length_var.get(), self.conspect_style_var.get())
        self.conspect_output.delete("1.0", "end")
        self.conspect_output.insert("1.0", result)
        self.conspect_btn.config(state="normal")
        self.conspect_status_var.set("Готово: конспект создан")

    def _copy_conspect(self):
        text = self.conspect_output.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Пусто", "Сначала создайте конспект, затем копируйте.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.conspect_status_var.set("Конспект скопирован")

    def _save_conspect(self):
        text = self.conspect_output.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Пусто", "Сначала создайте конспект, затем сохраните файл.")
            return
        path = filedialog.asksaveasfilename(title="Сохранить конспект", defaultextension=".txt", filetypes=[("Текстовый файл", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.conspect_status_var.set(f"Сохранено: {path}")
        except OSError:
            messagebox.showerror("Ошибка", "Не удалось сохранить файл.")


def main():
    init_db()
    app = UniversityMarketplaceApp()
    app.mainloop()


if __name__ == "__main__":
    main()
