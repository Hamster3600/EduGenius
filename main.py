import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import json
import requests  # Zamiast biblioteki openai

# Biblioteki do obsługi plików
import pypdf
from docx import Document
from odf import text, teletype
from odf.opendocument import load

# --- KONFIGURACJA API X.AI ---
API_KEY = "TU_WPISZ_SWOJ_KLUCZ_API"
API_URL = "https://api.x.ai/v1/chat/completions"

# --- USTAWIENIA WYGLĄDU ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FileProcessor:
    """Klasa odpowiedzialna za wyciąganie tekstu z plików."""
    @staticmethod
    def extract_text(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.pdf':
                reader = pypdf.PdfReader(file_path)
                text_content = ""
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
                return text_content
            elif ext == '.docx':
                doc = Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            elif ext == '.odt':
                doc = load(file_path)
                return "\n".join([teletype.extractText(node) for node in doc.getElementsByType(text.P)])
            else:
                return None
        except Exception as e:
            print(f"Błąd odczytu: {e}")
            return None

class EduApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja okna
        self.title("EduGenius - HackHeroes")
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Zmienne stanu
        self.flashcards_data = []
        self.summary_text = ""
        self.current_card_index = 0
        self.user_answers = [] 
        self.is_card_flipped = False

        # Kontener na widoki
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Inicjalizacja widoków
        self.frames = {}
        for F in (UploadView, LoadingView, MainAppView, SummaryResultView):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(UploadView)

    def show_frame(self, container_class):
        frame = self.frames[container_class]
        frame.tkraise()

    def process_file(self, file_path):
        self.show_frame(LoadingView)
        thread = threading.Thread(target=self._process_file_thread, args=(file_path,))
        thread.start()

    def _process_file_thread(self, file_path):
        # 1. Wyciągnij tekst
        raw_text = FileProcessor.extract_text(file_path)
        if not raw_text or len(raw_text.strip()) < 10:
            self.after(0, lambda: messagebox.showerror("Błąd", "Nie udało się odczytać pliku lub jest pusty."))
            self.after(0, lambda: self.show_frame(UploadView))
            return

        # Ograniczenie znaków
        raw_text = raw_text[:15000] 

        # 2. Wyślij do AI przez requests
        try:
            prompt = f"""
            Przeanalizuj poniższy tekst edukacyjny.
            Twoim zadaniem jest zwrócić TYLKO i WYŁĄCZNIE czysty kod JSON (bez formatowania markdown ```json).
            
            JSON musi mieć strukturę:
            {{
                "summary": "Tutaj napisz szczegółowe streszczenie tekstu w formacie Markdown (używaj nagłówków, punktorów).",
                "flashcards": [
                    {{"question": "Pytanie 1", "answer": "Odpowiedź 1"}},
                    {{"question": "Pytanie 2", "answer": "Odpowiedź 2"}},
                    {{"question": "Pytanie 3", "answer": "Odpowiedź 3"}},
                    {{"question": "Pytanie 4", "answer": "Odpowiedź 4"}},
                    {{"question": "Pytanie 5", "answer": "Odpowiedź 5"}}
                ]
            }}

            Oto tekst do analizy:
            {raw_text}
            """

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }

            payload = {
                "messages": [
                    {"role": "system", "content": "Jesteś pomocnym asystentem edukacyjnym. Zwracaj tylko JSON."},
                    {"role": "user", "content": prompt}
                ],
                "model": "grok-beta", # Model x.ai
                "stream": False,
                "temperature": 0.3
            }

            # Wykonanie zapytania HTTP (requests)
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status() # Sprawdza czy nie ma błędu HTTP (np. 401, 500)

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Czasami AI dodaje ```json na początku i ``` na końcu, musimy to wyczyścić
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")

            data = json.loads(content)

            self.summary_text = data.get("summary", "Brak podsumowania.")
            self.flashcards_data = data.get("flashcards", [])
            
            # Reset gry
            self.current_card_index = 0
            self.user_answers = []

            self.after(0, self.setup_main_view)

        except requests.exceptions.RequestException as e:
            print(f"Błąd sieci: {e}")
            self.after(0, lambda: messagebox.showerror("Błąd API", f"Problem z połączeniem do x.ai: {e}"))
            self.after(0, lambda: self.show_frame(UploadView))
        except json.JSONDecodeError as e:
            print(f"Błąd JSON: {e}")
            self.after(0, lambda: messagebox.showerror("Błąd danych", "Otrzymano niepoprawny format danych od AI."))
            self.after(0, lambda: self.show_frame(UploadView))
        except Exception as e:
            print(f"Inny błąd: {e}")
            self.after(0, lambda: messagebox.showerror("Błąd", f"Wystąpił nieoczekiwany błąd: {e}"))
            self.after(0, lambda: self.show_frame(UploadView))

    def setup_main_view(self):
        main_view = self.frames[MainAppView]
        main_view.update_summary(self.summary_text)
        main_view.load_flashcard()
        self.show_frame(MainAppView)

    def save_markdown(self):
        if not self.summary_text:
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.summary_text)
            messagebox.showinfo("Sukces", "Notatka zapisana!")

# --- WIDOKI (UI) - Pozostają bez zmian w logice ---

class UploadView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.center_frame, text="EduGenius", font=("Roboto Medium", 40))
        self.label.pack(pady=20)

        self.drop_btn = ctk.CTkButton(
            self.center_frame,
            text="Kliknij, aby wybrać plik\n(.txt, .pdf, .docx, .odt)",
            font=("Roboto", 18),
            width=400,
            height=200,
            fg_color="#2B2B2B",
            hover_color="#3A3A3A",
            border_width=2,
            border_color="#1f538d",
            corner_radius=20,
            command=self.select_file
        )
        self.drop_btn.pack(pady=20)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Dokumenty", "*.txt *.pdf *.docx *.odt")])
        if file_path:
            self.controller.process_file(file_path)

class LoadingView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.label = ctk.CTkLabel(self.center_frame, text="Przetwarzanie przez x.ai...", font=("Roboto", 20))
        self.label.pack(pady=20)
        self.progress = ctk.CTkProgressBar(self.center_frame, width=300, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start()

class MainAppView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.tabview = ctk.CTkTabview(self, width=850, height=650)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)

        self.tab_summary = self.tabview.add("Podsumowanie")
        self.tab_flashcards = self.tabview.add("Fiszki")

        # Podsumowanie
        self.summary_textbox = ctk.CTkTextbox(self.tab_summary, font=("Roboto", 14), wrap="word")
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.save_btn = ctk.CTkButton(self.tab_summary, text="Pobierz notatkę (.md)", command=self.controller.save_markdown)
        self.save_btn.pack(pady=10)

        # Fiszki
        self.card_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="#1f538d", corner_radius=30, width=600, height=400)
        self.card_frame.pack(pady=40, padx=40, fill="both", expand=True)
        self.card_frame.bind("<Button-1>", self.flip_card) 

        self.card_label = ctk.CTkLabel(self.card_frame, text="Pytanie", font=("Roboto", 24), wraplength=500, text_color="white")
        self.card_label.place(relx=0.5, rely=0.5, anchor="center")
        self.card_label.bind("<Button-1>", self.flip_card)

        self.hint_label = ctk.CTkLabel(self.card_frame, text="(Kliknij, aby odwrócić)", font=("Roboto", 12), text_color="gray")
        self.hint_label.place(relx=0.5, rely=0.9, anchor="center")

        self.btns_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="transparent")
        self.btns_frame.pack(pady=20)
        self.btn_know = ctk.CTkButton(self.btns_frame, text="Wiem :)", fg_color="green", hover_color="darkgreen", command=lambda: self.answer_card(True))
        self.btn_know.pack(side="left", padx=20)
        self.btn_dont_know = ctk.CTkButton(self.btns_frame, text="Nie wiem :(", fg_color="red", hover_color="darkred", command=lambda: self.answer_card(False))
        self.btn_dont_know.pack(side="right", padx=20)

    def update_summary(self, text):
        self.summary_textbox.delete("0.0", "end")
        self.summary_textbox.insert("0.0", text)

    def load_flashcard(self):
        idx = self.controller.current_card_index
        cards = self.controller.flashcards_data
        if idx < len(cards):
            self.controller.is_card_flipped = False
            self.card_frame.configure(fg_color="#1f538d") 
            self.card_label.configure(text=cards[idx]['question'])
        else:
            self.controller.show_frame(SummaryResultView)
            self.controller.frames[SummaryResultView].show_results()

    def flip_card(self, event=None):
        idx = self.controller.current_card_index
        cards = self.controller.flashcards_data
        if idx >= len(cards): return
        self.controller.is_card_flipped = not self.controller.is_card_flipped
        if self.controller.is_card_flipped:
            self.card_frame.configure(fg_color="#E67E22")
            self.card_label.configure(text=cards[idx]['answer'])
        else:
            self.card_frame.configure(fg_color="#1f538d")
            self.card_label.configure(text=cards[idx]['question'])

    def answer_card(self, known):
        idx = self.controller.current_card_index
        cards = self.controller.flashcards_data
        self.controller.user_answers.append({
            "question": cards[idx]['question'],
            "answer": cards[idx]['answer'],
            "known": known
        })
        self.controller.current_card_index += 1
        self.load_flashcard()

class SummaryResultView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title = ctk.CTkLabel(self, text="Podsumowanie Nauki", font=("Roboto Medium", 30))
        self.title.pack(pady=20)
        self.score_label = ctk.CTkLabel(self, text="", font=("Roboto", 24), text_color="#2CC985")
        self.score_label.pack(pady=10)
        self.results_frame = ctk.CTkScrollableFrame(self, width=800, height=500)
        self.results_frame.pack(pady=10, fill="both", expand=True)
        self.restart_btn = ctk.CTkButton(self, text="Wróć do startu", command=lambda: controller.show_frame(UploadView))
        self.restart_btn.pack(pady=20)

    def show_results(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        answers = self.controller.user_answers
        known_count = sum(1 for a in answers if a['known'])
        total = len(answers)
        self.score_label.configure(text=f"Twój wynik: {known_count} / {total}")
        for idx, item in enumerate(answers):
            row = ctk.CTkFrame(self.results_frame, fg_color="#2B2B2B" if idx % 2 == 0 else "#333333")
            row.pack(fill="x", pady=5, padx=5)
            status_color = "green" if item['known'] else "red"
            status_text = "✓ Wiedziałem" if item['known'] else "✗ Nie wiedziałem"
            q_lbl = ctk.CTkLabel(row, text=f"P: {item['question']}", font=("Roboto", 16, "bold"), anchor="w", justify="left")
            q_lbl.pack(fill="x", padx=10, pady=(10,0))
            a_lbl = ctk.CTkLabel(row, text=f"O: {item['answer']}", font=("Roboto", 14), anchor="w", justify="left", text_color="gray")
            a_lbl.pack(fill="x", padx=10, pady=(0, 10))
            stat_lbl = ctk.CTkLabel(row, text=status_text, text_color=status_color, font=("Roboto", 12, "bold"), anchor="e")
            stat_lbl.pack(fill="x", padx=10, pady=(0, 10))

if __name__ == "__main__":
    app = EduApp()
    app.mainloop()