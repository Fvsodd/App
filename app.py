import re
import textwrap
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# -----------------------------
# Логика конспектирования (офлайн)
# -----------------------------
class KonspektEngine:
    """Простой офлайн-движок для создания конспекта по правилам."""

    STOP_WORDS = {
        "и", "в", "во", "на", "с", "со", "по", "к", "ко", "о", "об", "от", "до", "за", "из", "у",
        "а", "но", "или", "ли", "же", "бы", "это", "этот", "эта", "эти", "как", "что", "чтобы",
        "для", "при", "так", "не", "ни", "то", "его", "ее", "их", "мы", "вы", "они", "он", "она",
    }

    KEYWORDS_HINTS = {
        "определ": "Определения",
        "формул": "Формулы и расчёты",
        "пример": "Примеры",
        "метод": "Методы",
        "этап": "Этапы",
        "причин": "Причины",
        "следств": "Следствия",
        "задач": "Задачи",
        "вывод": "Выводы",
        "итог": "Итоги",
        "функц": "Функции",
        "структур": "Структура",
        "процесс": "Процессы",
    }

    @staticmethod
    def split_sentences(text: str):
        text = re.sub(r"\s+", " ", text.strip())
        if not text:
            return []
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

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
    def extract_topics(text: str):
        words = re.findall(r"[А-Яа-яA-Za-zЁё\-]{5,}", text.lower())
        freq = {}
        for w in words:
            if w in KonspektEngine.STOP_WORDS:
                continue
            freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:6]
        return [w for w, _ in top]

    @staticmethod
    def detect_sections(text: str):
        text_low = text.lower()
        found = []
        for key, title in KonspektEngine.KEYWORDS_HINTS.items():
            if key in text_low and title not in found:
                found.append(title)
        return found[:5]

    @staticmethod
    def make_exam_block(selected_sentences):
        lines = ["Что важно запомнить к экзамену:"]
        for i, sent in enumerate(selected_sentences[:6], start=1):
            lines.append(f"{i}) {sent}")
        return "\n".join(lines)

    @staticmethod
    def make_understanding_block(selected_sentences):
        if not selected_sentences:
            return ""
        intro = selected_sentences[0]
        core = selected_sentences[1:4]
        end = selected_sentences[-1] if len(selected_sentences) > 1 else selected_sentences[0]

        block = [
            "Логика материала простыми словами:",
            f"• Главная идея: {intro}",
        ]
        for sent in core:
            block.append(f"• Ключевой момент: {sent}")
        block.append(f"• Вывод: {end}")
        return "\n".join(block)

    @staticmethod
    def make_thesis_block(selected_sentences):
        lines = ["Краткие тезисы:"]
        for sent in selected_sentences[:10]:
            lines.append(f"• {sent}")
        return "\n".join(lines)

    @staticmethod
    def generate(text: str, length_mode: str, style_mode: str):
        sentences = KonspektEngine.split_sentences(text)
        if not sentences:
            return "Пожалуйста, вставьте текст лекции или учебного материала."

        scored = [(idx, s, KonspektEngine.sentence_score(s)) for idx, s in enumerate(sentences)]
        scored_sorted = sorted(scored, key=lambda x: x[2], reverse=True)

        count = KonspektEngine.choose_count(len(sentences), length_mode)
        chosen = scored_sorted[:count]
        chosen = sorted(chosen, key=lambda x: x[0])
        selected_sentences = [s for _, s, _ in chosen]

        topics = KonspektEngine.extract_topics(text)
        sections = KonspektEngine.detect_sections(text)

        result = []
        result.append("КОНСПЕКТ")
        result.append("=" * 60)
        result.append("")

        result.append("Тема (по содержанию текста):")
        if topics:
            result.append("• " + ", ".join(topics[:4]).capitalize())
        else:
            result.append("• Учебный материал")
        result.append("")

        if sections:
            result.append("Разделы, которые выделены в материале:")
            for sec in sections:
                result.append(f"• {sec}")
            result.append("")

        if style_mode == "Для экзамена":
            result.append(KonspektEngine.make_exam_block(selected_sentences))
        elif style_mode == "Для понимания":
            result.append(KonspektEngine.make_understanding_block(selected_sentences))
        else:
            result.append(KonspektEngine.make_thesis_block(selected_sentences))

        result.append("")
        result.append("Краткий вывод:")
        result.append("• Материал сведен к ключевым идеям и удобен для повторения.")

        wrapped = []
        for line in result:
            if line.startswith("•") or line[:2].isdigit() or line.endswith(":") or line.startswith("="):
                wrapped.append(line)
            else:
                wrapped.extend(textwrap.wrap(line, width=88) if line else [""])

        return "\n".join(wrapped)


# -----------------------------
# Интерфейс приложения
# -----------------------------
class KonspektatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Конспектатор")
        self.geometry("1320x760")
        self.minsize(1100, 650)

        # Стили для аккуратного университетского интерфейса.
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("SubTitle.TLabel", font=("Segoe UI", 11))
        style.configure("BlockTitle.TLabel", font=("Segoe UI", 11, "bold"))

        self.length_var = tk.StringVar(value="Средний")
        self.style_var = tk.StringVar(value="Для понимания")
        self.status_var = tk.StringVar(value="Готово к работе")

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        # Верхняя часть: заголовок и подзаголовок.
        ttk.Label(
            root,
            text="📚 Конспектатор — умное сокращение учебных текстов",
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            root,
            text="Вставьте текст лекции или учебного материала — мы сделаем краткий конспект",
            style="SubTitle.TLabel",
            foreground="#444",
        ).pack(anchor="w", pady=(4, 14))

        # Панель настроек.
        controls = ttk.Frame(root)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Длина конспекта:", style="BlockTitle.TLabel").pack(side="left")
        length_combo = ttk.Combobox(
            controls,
            textvariable=self.length_var,
            values=["Короткий", "Средний", "Подробный"],
            width=14,
            state="readonly",
        )
        length_combo.pack(side="left", padx=(8, 22))

        ttk.Label(controls, text="Стиль:", style="BlockTitle.TLabel").pack(side="left")
        style_combo = ttk.Combobox(
            controls,
            textvariable=self.style_var,
            values=["Для экзамена", "Для понимания", "Краткие тезисы"],
            width=18,
            state="readonly",
        )
        style_combo.pack(side="left", padx=(8, 0))

        # Основная горизонтальная раскладка: слева ввод, центр кнопка, справа результат.
        main = ttk.Frame(root)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        center = ttk.Frame(main, width=190)
        center.pack(side="left", fill="y", padx=12)
        center.pack_propagate(False)

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Текст для обработки", style="BlockTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.input_text = tk.Text(left, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        self.input_text.pack(fill="both", expand=True)

        ttk.Label(right, text="Готовый конспект", style="BlockTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.output_text = tk.Text(right, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        self.output_text.pack(fill="both", expand=True)

        # Центральная зона действий.
        ttk.Label(center, text="Действие", style="BlockTitle.TLabel").pack(pady=(40, 12))
        self.main_button = ttk.Button(
            center,
            text="✨ Создать конспект",
            command=self.on_generate,
            width=20,
        )
        self.main_button.pack(pady=8)

        ttk.Button(center, text="Копировать", command=self.copy_output, width=20).pack(pady=(24, 8))
        ttk.Button(center, text="Сохранить .txt", command=self.save_output, width=20).pack(pady=4)

        # Нижняя строка статуса.
        status_bar = ttk.Frame(root)
        status_bar.pack(fill="x", pady=(10, 0))
        ttk.Label(status_bar, textvariable=self.status_var, foreground="#355e3b").pack(side="left")

    def on_generate(self):
        source = self.input_text.get("1.0", "end").strip()
        if not source:
            messagebox.showwarning("Нет текста", "Пожалуйста, вставьте текст перед созданием конспекта.")
            return

        # Имитация процесса обработки для понятного UX.
        self.status_var.set("Обработка текста...")
        self.main_button.config(state="disabled")
        self.update_idletasks()

        self.after(350, lambda: self._finish_generate(source))

    def _finish_generate(self, source):
        summary = KonspektEngine.generate(source, self.length_var.get(), self.style_var.get())
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", summary)

        self.main_button.config(state="normal")
        self.status_var.set("Готово: конспект создан")

    def copy_output(self):
        text = self.output_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Пусто", "Сначала создайте конспект, затем копируйте.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set("Конспект скопирован в буфер обмена")

    def save_output(self):
        text = self.output_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Пусто", "Сначала создайте конспект, затем сохраните файл.")
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить конспект",
            defaultextension=".txt",
            filetypes=[("Текстовый файл", "*.txt")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_var.set(f"Сохранено: {path}")
        except OSError:
            messagebox.showerror("Ошибка", "Не удалось сохранить файл.")


def main():
    app = KonspektatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
