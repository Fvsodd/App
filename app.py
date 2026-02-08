import re
import sqlite3
import textwrap
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

DB_PATH = "marketplace.db"


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
                ("student1", "pass123", "student", "ИТ", "2"),
                ("teacher1", "pass123", "teacher", "Инженерия", "-"),
                ("admin1", "admin123", "admin", "Администрация", "-"),
            ],
        )

    # По требованию: оставляем только одно приложение — Конспектатор.
    cur.execute("SELECT id FROM users WHERE username='admin1'")
    admin_id = cur.fetchone()["id"]
    cur.execute("DELETE FROM apps")
    cur.execute(
        """
        INSERT INTO apps(name,description,category,author_id,status,downloads,created_at)
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            "Конспектатор",
            "Умное сокращение учебных текстов: создаёт структурированный конспект лекции.",
            "Учебные инструменты",
            admin_id,
            "approved",
            0,
            datetime.utcnow().isoformat(),
        ),
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


class UniversityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Университетский маркетплейс")
        self.geometry("1260x760")
        self.minsize(1080, 680)

        self.current_user = None
        self.content_frame = None
        self.market_tree = None
        self.profile_text = None
        self.admin_tree = None
        self.ai_output = None

        self.search_var = tk.StringVar()
        self.ai_faculty = tk.StringVar()
        self.ai_course = tk.StringVar()
        self.ai_interests = tk.StringVar()

        self.conspect_length_var = tk.StringVar(value="Средний")
        self.conspect_style_var = tk.StringVar(value="Для понимания")
        self.conspect_status_var = tk.StringVar(value="Готово к работе")
        self.conspect_input = None
        self.conspect_output = None
        self.conspect_btn = None

        self._build_login()

    def clear_root(self):
        for ch in self.winfo_children():
            ch.destroy()

    def _is_conspect_installed(self):
        if not self.current_user:
            return False
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM apps WHERE name='Конспектатор' LIMIT 1")
        app_row = cur.fetchone()
        if not app_row:
            conn.close()
            return False
        cur.execute("SELECT 1 FROM installs WHERE user_id=? AND app_id=?", (self.current_user["id"], app_row["id"]))
        ok = cur.fetchone() is not None
        conn.close()
        return ok

    def _build_login(self):
        self.clear_root()
        frame = ttk.Frame(self, padding=36)
        frame.pack(fill="both", expand=True)

        box = ttk.Frame(frame, padding=24)
        box.pack(expand=True)

        ttk.Label(box, text="Университетский маркетплейс", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(box, text="Внутренняя демо-система для студентов, преподавателей и администрации.", foreground="#444").pack(anchor="w", pady=(4, 18))

        form = ttk.Frame(box)
        form.pack(anchor="w")
        ttk.Label(form, text="Логин", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Пароль", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
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
                messagebox.showerror("Ошибка входа", "Неверный логин или пароль")
                return
            self.current_user = row
            self._build_dashboard()

        ttk.Button(box, text="Войти", command=do_login).pack(anchor="w", pady=(14, 6))
        ttk.Label(box, text="Демо-аккаунты: student1/pass123, teacher1/pass123, admin1/admin123", foreground="#666").pack(anchor="w")

    def _build_dashboard(self):
        self.clear_root()
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main, padding=(12, 10))
        header.pack(fill="x")
        ttk.Label(header, text="Университетский маркетплейс — Бета", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Label(header, text=f"{self.current_user['username']} ({self.current_user['role']})", foreground="#444").pack(side="right", padx=8)
        ttk.Button(header, text="Выйти", command=self._logout).pack(side="right")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        nav = ttk.Frame(body, width=240, padding=10)
        nav.pack(side="left", fill="y")
        self.content_frame = ttk.Frame(body, padding=12)
        self.content_frame.pack(side="left", fill="both", expand=True)

        ttk.Label(nav, text="Разделы", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

        nav_items = [
            ("Маркетплейс", self.show_marketplace),
            ("AI-навигатор", self.show_ai_navigator),
            ("Профиль", self.show_profile),
        ]

        if self._is_conspect_installed() or self.current_user["role"] in ("teacher", "admin"):
            nav_items.append(("Конспектатор", self.show_conspectator))
        else:
            nav_items.append(("Конспектатор (доступен после установки)", lambda: messagebox.showinfo("Информация", "Установите «Конспектатор» в разделе «Маркетплейс")))

        if self.current_user["role"] == "admin":
            nav_items.append(("Панель администратора", self.show_admin_panel))

        for txt, fn in nav_items:
            ttk.Button(nav, text=txt, command=fn, width=30).pack(anchor="w", pady=4)

        self._show_intro_card()
        self.show_marketplace()

    def _show_intro_card(self):
        card = ttk.Frame(self.content_frame, padding=10)
        card.pack(fill="x", pady=(0, 10))
        ttk.Label(card, text="Что сделать сначала", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(card, text="1) Установите Конспектатор в Маркетплейсе  2) Откройте Конспектатор  3) Создайте конспект", foreground="#555").pack(anchor="w", pady=(2, 0))

    def _clear_content(self):
        for ch in self.content_frame.winfo_children():
            ch.destroy()
        self._show_intro_card()

    def _logout(self):
        self.current_user = None
        self._build_login()

    def show_marketplace(self):
        self._clear_content()

        bar = ttk.Frame(self.content_frame)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Маркетплейс", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 12))
        ttk.Label(bar, text="Поиск:").pack(side="left")
        ttk.Entry(bar, textvariable=self.search_var, width=34).pack(side="left", padx=(6, 8))
        ttk.Button(bar, text="Найти", command=self._refresh_marketplace).pack(side="left")
        ttk.Button(bar, text="Установить выбранное", command=self._install_selected).pack(side="left", padx=6)

        self.market_tree = ttk.Treeview(self.content_frame, columns=("id", "name", "description", "category", "downloads"), show="headings", height=15)
        for col, txt, w in [
            ("id", "ID", 50),
            ("name", "Приложение", 210),
            ("description", "Описание", 520),
            ("category", "Категория", 170),
            ("downloads", "Установок", 95),
        ]:
            self.market_tree.heading(col, text=txt)
            self.market_tree.column(col, width=w, anchor="w")
        self.market_tree.pack(fill="both", expand=True)

        self._refresh_marketplace()

    def _refresh_marketplace(self):
        for r in self.market_tree.get_children():
            self.market_tree.delete(r)

        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, category, downloads FROM apps WHERE status='approved' ORDER BY id")
        rows = cur.fetchall()
        conn.close()

        q = self.search_var.get().strip().lower()
        for r in rows:
            hay = f"{r['name']} {r['description']} {r['category']}".lower()
            if q and q not in hay:
                continue
            self.market_tree.insert("", "end", values=(r["id"], r["name"], r["description"], r["category"], r["downloads"]))

    def _install_selected(self):
        sel = self.market_tree.selection()
        if not sel:
            messagebox.showwarning("Установка", "Сначала выберите приложение")
            return

        app_id = int(self.market_tree.item(sel[0], "values")[0])
        app_name = self.market_tree.item(sel[0], "values")[1]

        conn = db_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO installs(user_id, app_id, installed_at) VALUES(?,?,?)", (self.current_user["id"], app_id, datetime.utcnow().isoformat()))
        cur.execute("UPDATE apps SET downloads = downloads + 1 WHERE id=?", (app_id,))
        conn.commit()
        conn.close()

        self._refresh_marketplace()
        messagebox.showinfo("Установка", f"«{app_name}» установлено (симуляция).")

        # После установки Конспектатор появляется в навигации там же, где сейчас.
        if app_name == "Конспектатор":
            self._build_dashboard()
            self.show_conspectator()

    def show_ai_navigator(self):
        self._clear_content()

        ttk.Label(self.content_frame, text="AI-навигатор", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self.content_frame, text="Подбор рекомендаций по профилю и интересам.", foreground="#555").pack(anchor="w", pady=(2, 10))

        form = ttk.Frame(self.content_frame)
        form.pack(fill="x")

        ttk.Label(form, text="Факультет").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.ai_faculty, width=24).grid(row=0, column=1, padx=8)
        ttk.Label(form, text="Курс").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.ai_course, width=10).grid(row=0, column=3, padx=8)
        ttk.Label(form, text="Интересы").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form, textvariable=self.ai_interests, width=62).grid(row=1, column=1, columnspan=3, sticky="w", padx=8)

        if not self.ai_faculty.get().strip():
            self.ai_faculty.set(self.current_user["faculty"] or "Общий")
        if not self.ai_course.get().strip():
            self.ai_course.set(self.current_user["course"] or "-")

        ttk.Button(self.content_frame, text="Получить рекомендации", command=self._generate_ai).pack(anchor="w", pady=8)

        self.ai_output = tk.Text(self.content_frame, height=18, wrap="word")
        self.ai_output.pack(fill="both", expand=True)
        self.ai_output.insert("1.0", "Введите интересы и нажмите «Получить рекомендации».")

    def _generate_ai(self):
        faculty = self.ai_faculty.get().strip() or "Общий"
        course = self.ai_course.get().strip() or "-"
        interests = self.ai_interests.get().strip()

        lines = [
            f"Профиль: факультет «{faculty}», курс {course}.",
            "",
            "Рекомендуем установить:",
            "- Конспектатор — для быстрого повторения лекций и подготовки к занятиям.",
            "",
            "Навыки для развития:",
            "- Структурирование учебного материала",
            "- Формулирование кратких тезисов",
            "- Подготовка к экзамену по ключевым пунктам",
            "",
            f"С учётом интересов («{interests or 'не указаны'}») лучше использовать режим «Для экзамена» или «Для понимания».",
        ]
        self.ai_output.delete("1.0", "end")
        self.ai_output.insert("1.0", "\n".join(lines))

    def show_profile(self):
        self._clear_content()
        ttk.Label(self.content_frame, text="Профиль и портфолио", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.profile_text = tk.Text(self.content_frame, height=24, wrap="word")
        self.profile_text.pack(fill="both", expand=True, pady=(8, 0))

        conn = db_conn()
        cur = conn.cursor()
        uid = self.current_user["id"]
        cur.execute(
            """
            SELECT apps.name, installs.installed_at
            FROM installs JOIN apps ON apps.id=installs.app_id
            WHERE installs.user_id=? ORDER BY installs.installed_at DESC
            """,
            (uid,),
        )
        installed = cur.fetchall()
        conn.close()

        score = min(100, len(installed) * 25)
        lines = [
            f"Пользователь: {self.current_user['username']} ({self.current_user['role']})",
            f"Факультет: {self.current_user['faculty']} | Курс: {self.current_user['course']}",
            "",
            f"Установленные приложения ({len(installed)}):",
        ]
        lines.extend([f"- {r['name']} (установлено: {r['installed_at']})" for r in installed])
        lines.extend(["", f"Статистика портфолио:", f"- Индекс активности: {score}/100"])
        self.profile_text.insert("1.0", "\n".join(lines))

    def show_admin_panel(self):
        self._clear_content()
        ttk.Label(self.content_frame, text="Панель администратора", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.admin_tree = ttk.Treeview(self.content_frame, columns=("id", "name", "status", "downloads"), show="headings", height=12)
        for col, txt, w in [
            ("id", "ID", 60),
            ("name", "Приложение", 260),
            ("status", "Статус", 120),
            ("downloads", "Установок", 120),
        ]:
            self.admin_tree.heading(col, text=txt)
            self.admin_tree.column(col, width=w, anchor="w")
        self.admin_tree.pack(fill="both", expand=True, pady=(8, 8))

        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, status, downloads FROM apps ORDER BY id")
        for a in cur.fetchall():
            self.admin_tree.insert("", "end", values=(a["id"], a["name"], a["status"], a["downloads"]))
        cur.execute("SELECT COUNT(*) c FROM installs")
        installs = cur.fetchone()["c"]
        conn.close()

        ttk.Label(self.content_frame, text=f"Общая статистика: установок в системе — {installs}").pack(anchor="w")

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
    app = UniversityApp()
    app.mainloop()


if __name__ == "__main__":
    main()
