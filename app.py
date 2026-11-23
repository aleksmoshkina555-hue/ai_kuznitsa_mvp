import threading
import tkinter as tk
from tkinter import ttk, messagebox
from mock_db import CORP_SOURCES
from agent import process_corporate_query


class CorpAgentApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CorpKnowledgeAgent — ИИ-агент поиска по документам и почте (ИИкузница)")
        self.root.geometry("1150x740")
        self.root.configure(bg="#f8fafc")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f8fafc")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#f8fafc", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#f8fafc", foreground="#0f172a", font=("Segoe UI", 15, "bold"))
        style.configure("Sub.TLabel", background="#f8fafc", foreground="#475569", font=("Segoe UI", 9))

        self.setup_hotkeys()
        self.create_widgets()

    def setup_hotkeys(self):
        def handle_ctrl_key(event):
            widget = event.widget
            if not isinstance(widget, (tk.Entry, tk.Text)):
                return None

            if event.keycode == 67:
                widget.event_generate("<<Copy>>")
                return "break"
            elif event.keycode == 86:
                widget.event_generate("<<Paste>>")
                return "break"
            elif event.keycode == 88:
                widget.event_generate("<<Cut>>")
                return "break"
            elif event.keycode == 65:
                if isinstance(widget, tk.Entry):
                    widget.select_range(0, "end")
                    widget.icursor("end")
                elif isinstance(widget, tk.Text):
                    widget.tag_add("sel", "1.0", "end")
                return "break"
            return None

        self.root.bind_all("<Control-KeyPress>", handle_ctrl_key)

    def create_widgets(self):
        header_frame = ttk.Frame(self.root, padding=(15, 10))
        header_frame.pack(fill="x")

        title_container = ttk.Frame(header_frame)
        title_container.pack(side="left")
        ttk.Label(title_container, text="CorpKnowledgeAgent — Поиск по документам и почте", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_container, text="Локальный контур (On-Premise) | Контроль актуальности норм | Экономия до 300 ч/мес", style="Sub.TLabel").pack(anchor="w")

        workspace_frame = ttk.Frame(self.root, padding=(15, 5))
        workspace_frame.pack(fill="both", expand=True)

        sidebar = ttk.Frame(workspace_frame, width=360)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="База знаний (Источники RAG)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        sources_list = tk.Text(sidebar, bg="#ffffff", fg="#1e293b", font=("Segoe UI", 9), wrap="word", relief="solid", borderwidth=1, padx=8, pady=8)
        sources_list.pack(fill="both", expand=True)
        for source in CORP_SOURCES:
            status_text = "ДЕЙСТВУЕТ" if source["status"] == "Действует" else "УСТАРЕЛ"
            sources_list.insert("end", f"{source['source_type']} [{status_text}]\n{source['title']} ({source['date']})\nОтв.: {source['owner']}\n{'-'*42}\n")
        sources_list.config(state="disabled")

        content_area = ttk.Frame(workspace_frame)
        content_area.pack(side="left", fill="both", expand=True)

        email_form = ttk.Frame(content_area, style="Card.TFrame", padding=12)
        email_form.pack(fill="x", pady=(0, 10))

        meta_row = ttk.Frame(email_form, style="Card.TFrame")
        meta_row.pack(fill="x", pady=(0, 6))
        ttk.Label(meta_row, text="От кого:", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.sender_input = tk.Entry(meta_row, font=("Segoe UI", 10), bg="#f8fafc", relief="solid", borderwidth=1, width=32)
        self.sender_input.pack(side="left", padx=(6, 15))

        ttk.Label(meta_row, text="Тема:", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.subject_input = tk.Entry(meta_row, font=("Segoe UI", 10), bg="#f8fafc", relief="solid", borderwidth=1)
        self.subject_input.pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(email_form, text="Текст вопроса / письма:", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.message_input = tk.Text(email_form, height=4, font=("Segoe UI", 10), bg="#f8fafc", relief="solid", borderwidth=1, wrap="word", padx=6, pady=4)
        self.message_input.pack(fill="x", pady=(4, 8))

        controls_row = ttk.Frame(email_form, style="Card.TFrame")
        controls_row.pack(fill="x")
        self.search_button = tk.Button(
            controls_row, text="Найти ответ и подготовить письмо", bg="#2563eb", fg="white",
            disabledforeground="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6, cursor="hand2",
            command=self.on_search_click
        )
        self.search_button.pack(side="left")

        self.status_text = ttk.Label(controls_row, text="Готов к работе", style="Card.TLabel", foreground="#64748b")
        self.status_text.pack(side="left", padx=12)

        self.warning_banner = tk.Label(content_area, text="", font=("Segoe UI", 10, "bold"), wraplength=720, justify="left", padx=10, pady=8)

        results_container = ttk.Frame(content_area)
        results_container.pack(fill="both", expand=True)

        answer_panel = ttk.Frame(results_container, style="Card.TFrame", padding=10)
        answer_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(answer_panel, text="Найденный ответ и источники", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.answer_output = tk.Text(answer_panel, font=("Segoe UI", 10), bg="#f0fdf4", fg="#14532d", relief="solid", borderwidth=1, wrap="word", padx=8, pady=8)
        self.answer_output.pack(fill="both", expand=True, pady=(6, 0))

        draft_panel = ttk.Frame(results_container, style="Card.TFrame", padding=10)
        draft_panel.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Label(draft_panel, text="Черновик ответа (Human-in-the-Loop)", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.assignee_label = ttk.Label(draft_panel, text="Ответственный: —", style="Card.TLabel", foreground="#2563eb", font=("Segoe UI", 9, "bold"))
        self.assignee_label.pack(anchor="w", pady=(2, 4))

        self.draft_output = tk.Text(draft_panel, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a", relief="solid", borderwidth=1, wrap="word", padx=8, pady=8)
        self.draft_output.pack(fill="both", expand=True, pady=(0, 8))

        send_button = tk.Button(
            draft_panel, text="Подтвердить и отправить по почте", bg="#16a34a", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=6, cursor="hand2",
            command=self.send_email
        )
        send_button.pack(fill="x")

        footer_panel = ttk.Frame(content_area, style="Card.TFrame", padding=8)
        footer_panel.pack(fill="x", pady=(8, 0))
        self.metrics_text = ttk.Label(footer_panel, text="Метрики: время — | токены — | стоимость 0.00 ₽", style="Card.TLabel", font=("Segoe UI", 9, "bold"))
        self.metrics_text.pack(anchor="w")
        self.trace_text = ttk.Label(footer_panel, text="Трассировка: ожидание запуска...", style="Card.TLabel", foreground="#475569", font=("Segoe UI", 9))
        self.trace_text.pack(anchor="w", pady=(2, 0))

    def on_search_click(self):
        sender = self.sender_input.get().strip()
        subject = self.subject_input.get().strip()
        body = self.message_input.get("1.0", "end").strip()

        self.search_button.config(state="disabled", text="Агент ищет...")
        self.status_text.config(text="Проверка регламентов и генерация ответа...", foreground="#ffffff")
        self.warning_banner.pack_forget()

        threading.Thread(target=self.process_in_background, args=(sender, subject, body), daemon=True).start()

    def process_in_background(self, sender, subject, body):
        try:
            result = process_corporate_query(sender, subject, body)
            self.root.after(0, lambda: self.show_result(result))
        except Exception as exc:
            error_details = str(exc)
            self.root.after(0, lambda: self.show_error(error_details))

    def show_error(self, error_text: str):
        self.search_button.config(state="normal", text="Найти ответ и подготовить письмо")
        self.status_text.config(text="Ошибка подключения к Ollama", foreground="#dc2626")
        messagebox.showerror(
            "Локальная модель не отвечает",
            f"Не удалось связаться с Ollama (модель qwen2.5:1.5b).\n\n"
            f"1. Убедитесь, что Ollama запущена в трее.\n"
            f"2. Проверьте, что модель докачалась командой: ollama pull qwen2.5:1.5b\n\nДетали: {error_text}"
        )

    def show_result(self, result: dict):
        self.search_button.config(state="normal", text="Найти ответ и подготовить письмо")
        self.status_text.config(text="Готово!", foreground="#16a34a")
        self.answer_output.delete("1.0", "end")
        self.draft_output.delete("1.0", "end")

        if result.get("blocked"):
            self.warning_banner.config(
                text=f"ЗАБЛОКИРОВАНО СИСТЕМОЙ БЕЗОПАСНОСТИ: {result['reason']}",
                bg="#fee2e2", fg="#991b1b"
            )
            self.warning_banner.pack(fill="x", before=self.answer_output.master.master, pady=(0, 8))
            self.answer_output.insert("1.0", "Запрос отклонен фильтром безопасности. Утечка корпоративных документов предотвращена.")
            self.assignee_label.config(text="Ответственный: Служба ИБ")
            self.metrics_text.config(text="Метрики: время 0.00 сек | токены 0 | стоимость 0.00 ₽")
        else:
            if result.get("outdated_docs"):
                outdated = result["outdated_docs"][0]
                self.warning_banner.config(
                    text=f"ВНИМАНИЕ: Обнаружен устаревший документ «{outdated['title']}» ({outdated['date']}) — исключен из ответа, применена норма 2026 года.",
                    bg="#fef3c7", fg="#92400e"
                )
                self.warning_banner.pack(fill="x", before=self.answer_output.master.master, pady=(0, 8))

            formatted_sources = "\n".join([f"- {doc['source_type']} {doc['title']} (от {doc['date']})" for doc in result["active_docs"]])
            full_answer = f"{result['answer']}\n\n--- Проверенные источники ---\n{formatted_sources}" if formatted_sources else result["answer"]
            self.answer_output.insert("1.0", full_answer)
            self.assignee_label.config(text=f"Ответственный: {result['responsible']}")
            self.draft_output.insert("1.0", result["email_draft"])
            self.metrics_text.config(
                text=f"Метрики: время поиска {result['latency']} сек (экономия ~45 мин) | токены {result['tokens']} | стоимость 0.00 ₽"
            )
            self.trace_text.config(text="Трассировка: " + "  ->  ".join(result["logs"]))

    def send_email(self):
        recipient = self.sender_input.get().strip()
        messagebox.showinfo(
            "Письмо отправлено",
            f"Ответ успешно отправлен адресату:\n{recipient}\n\nОбращение закрыто в системе."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = CorpAgentApp(root)
    root.mainloop()
