import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import random
import re

# Biblioteki do obsługi plików
import pypdf
from docx import Document
from odf import text, teletype
from odf.opendocument import load

# --- LOKALNE BIBLIOTEKI NLP ---
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import nltk

# --- LOKALNA BIBLIOTEKA DLA FISZEK ---
import spacy
import spacy.cli 

# --- IMPORT DLA LLM (Model GGUF/llama.cpp) ---
from llama_cpp import Llama 

# --- USTAWIENIA WYGLĄDU ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- GLOBALNE ZMIENNE LLM ---
# Ścieżka do modelu GGUF
MODEL_PATH = "qwen2.5-1.5b-instruct-q4_k_m.gguf" 
_llama_model = None

# --- GLOBALNE ZMIENNE NLP ---
SPACY_MODELS = {
    "polish": "pl_core_news_sm",
    "english": "en_core_web_sm"
}
_loaded_spacy_models = {}

def load_llm():
    """Ładuje globalny model Llama GGUF do pamięci, jeśli nie jest załadowany."""
    global _llama_model
    if _llama_model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Nie znaleziono pliku modelu LLM: {MODEL_PATH}. Upewnij się, że plik jest w folderze aplikacji.")

        print(f"Ładowanie modelu LLM ({MODEL_PATH})... Może to potrwać.")
        _llama_model = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=-1,  
            # Bezpieczne okno kontekstu dla małych modeli
            n_ctx=4096, 
            verbose=False,
            chat_format="llama-3"
        )
        print("Model LLM załadowany pomyślnie.")
    return _llama_model


def generate_llm_summary(raw_text, language):
    """Generuje podsumowanie za pomocą modelu LLM Z FORMATOWANIEM MARKDOWN."""
    try:
        llm = load_llm()
    except Exception as e:
        print(f"Błąd ładowania LLM. Aplikacja przejdzie na LSA: {e}")
        return None

    # Bezpieczna granica dla 4096 tokenów w języku polskim.
    max_chars = 10000 
    
    # Dodanie komunikatu ostrzegawczego, jeśli tekst został obcięty
    if len(raw_text) > max_chars:
        print(f"Ostrzeżenie: Tekst wejściowy (długość: {len(raw_text)}) został obcięty do pierwszych {max_chars} znaków, aby zmieścić się w oknie kontekstu LLM (4096 tokenów).")
        raw_text = raw_text[:max_chars]
        
    user_prompt = f"Oto tekst do podsumowania:\n\n---\n{raw_text}" 

    # UTRZYMANIE SYSTEM PROMPT Z MARKDOWNEM DLA CZYSTEGO ZAPISU DO PLIKU .TXT
    if language == "polish":
        system_prompt = (
            "Jesteś polskim ekspertem w dziedzinie edukacji. Podsumuj cały tekst, który otrzymasz, "
            "w maksymalnie 10 najważniejszych punktach. "
            "***Używaj numerowanych list Markdown (1., 2., 3., etc.). Użyj znaku '##' dla nagłówka 'Podsumowanie'. "
            "Pogrub KLUCZOWE słowa lub nazwy używając PODWÓJNYCH GWIAZDEK Markdown (**słowo**). "
            "Odpowiedź MUSI ZAWIERAĆ znaczniki Markdown.***"
        )
        model_name = "Qwen2.5-1.5B-Instruct"
    else:
        system_prompt = (
            "You are an expert educational assistant. Summarize the entire text you receive into a maximum of 10 key points. "
            "***Use numbered Markdown lists (1., 2., 3., etc.). Use the '##' sign for the header 'Summary'. "
            "Bold KEYWORDS or names using DOUBLE ASTERISKS Markdown (**word**). "
            "The response MUST CONTAIN Markdown markers.***"
        )
        model_name = "Qwen2.5-1.5B-Instruct"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=512, 
            temperature=0.5, 
            stream=False,
        )
        
        summary = output['choices'][0]['message']['content'].strip()
        
        # Zapewnienie, że zaczyna się od nagłówka
        if not summary.startswith('## '):
             summary = '## Podsumowanie\n\n' + summary
             
        # Zapewnienie, że po nagłówku jest pusta linia
        summary = re.sub(r'(## [^\n]+)([^\n\s])', r'\1\n\n\2', summary)

        return summary
        
    except Exception as e:
        print(f"Błąd podczas generowania podsumowania przez LLM: {e}")
        return None


def get_spacy_nlp(language):
    """Zwraca załadowany model spaCy. Automatycznie pobiera model, jeśli go brakuje."""
    if language not in SPACY_MODELS:
        raise ValueError(f"Nieobsługiwany język: {language}")
        
    if language not in _loaded_spacy_models:
        model_name = SPACY_MODELS[language]
        try:
            _loaded_spacy_models[language] = spacy.load(model_name)
        except OSError:
            print(f"Brak modelu {model_name}. Rozpoczynam pobieranie...")
            spacy.cli.download(model_name)
            _loaded_spacy_models[language] = spacy.load(model_name)
            
    return _loaded_spacy_models[language]

def generate_cloze_flashcards(text, language):
    """Generuje fiszki metodą Cloze Deletion (luki w tekście) za pomocą spaCy."""
    # Obcinam tekst dla SpaCy do pierwszych 50 000 znaków
    # To pozwala generować fiszki z większej części dokumentu niż LLM
    text = text[:50000]
    
    try:
        nlp = get_spacy_nlp(language)
    except Exception as e:
        print(f"Błąd krytyczny ładowania spaCy: {e}")
        return []

    doc = nlp(text)
    flashcards = []
    
    # Używamy tej samej logiki POS (części mowy)
    if language == "polish":
        target_pos = ["NOUN", "PROPN", "ADJ", "VERB"]  
    else: 
        target_pos = ["NOUN", "PROPN", "ADJ"]

    for sent in doc.sents:
        keywords = [token for token in sent if token.pos_ in target_pos and len(token.text) > 3 and not token.is_punct and not token.like_num and token.i > 0]
        
        if not keywords or len(flashcards) >= 20: 
            continue
            
        target_word = random.choice(keywords)
        
        # Próba maskowania z użyciem różnych strategii (uwzględnianie wielkości liter i spójności)
        question = re.sub(r'\b' + re.escape(target_word.text) + r'\b', "______", sent.text, count=1)
        
        if question == sent.text:
             question = re.sub(r'\b' + re.escape(target_word.text.lower()) + r'\b', "______", sent.text, count=1)
             
        if question == sent.text:
            question = re.sub(r'\b' + re.escape(target_word.text) + r'\b', "______", sent.text, count=1, flags=re.IGNORECASE)

        answer = target_word.text
        
        if question != sent.text:
            flashcards.append({"question": question, "answer": answer})
        
    return flashcards

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
            print(f"Błąd odczytu pliku: {e}")
            return None
            
def cleanup_markdown_for_save(text):
    """Usuwa znaczniki Markdown dla zapisu do czystego pliku .txt."""
    # 1. Usuń nagłówki (np. ## Tytuł -> Tytuł)
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE) 
    # 2. Usuń pogrubienia/kursywy (np. **słowo** -> słowo)
    text = re.sub(r'(\*\*|\*|--|~~)', '', text) 
    # 3. Usuń listy uporządkowane/nieuporządkowane (np. 1. -> )
    text = re.sub(r'^\s*(\d+\.|\-|\*)\s*', '', text, flags=re.MULTILINE) 
    # 4. Nadmiarowe puste linie
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class EduApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja okna
        self.title("EduGenius - Lokalny Asystent Nauki")
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Zmienne stanu
        self.flashcards_data = []
        self.summary_text = "" # To pole teraz przechowuje tekst z Markdownem
        self.current_card_index = 0
        self.user_answers = [] 
        self.is_card_flipped = False
        self.language = "polish" 
        
        # Utworzenie czcionek
        self.header_font = ctk.CTkFont(family="Roboto", size=18, weight="bold")
        self.bold_font = ctk.CTkFont(family="Roboto", size=14, weight="bold")
        self.body_font = ctk.CTkFont(family="Roboto", size=14, weight="normal")

        # Pobieranie zasobów NLTK
        for resource in ['punkt', 'punkt_tab']:
            try:
                nltk.data.find(f'tokenizers/{resource}')
            except LookupError:
                try:
                    # Dodano warunek, aby uniknąć zbędnych pobrań po pierwszej próbie
                    if os.getenv('NLTK_DOWNLOAD_ATTEMPT', '0') == '0':
                         nltk.download(resource)
                         os.environ['NLTK_DOWNLOAD_ATTEMPT'] = '1'
                except Exception as e:
                    print(f"Nie można pobrać zasobu NLTK {resource}: {e}")

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

    def set_language(self, lang):
        self.language = lang
        
    def show_frame(self, container_class):
        frame = self.frames[container_class]
        frame.tkraise()

    def process_file(self, file_path):
        self.show_frame(LoadingView)
        thread = threading.Thread(target=self._process_file_thread, args=(file_path,))
        thread.start()

    def _process_file_thread(self, file_path):
        raw_text = None
        try:
            # 1. Wyciągnij tekst
            raw_text = FileProcessor.extract_text(file_path)
            if not raw_text or len(raw_text.strip()) < 10:
                self.after(0, lambda: messagebox.showerror("Błąd", "Nie udało się odczytać pliku lub jest pusty."))
                self.after(0, lambda: self.show_frame(UploadView))
                return

            # 2. Analiza (LLM) - PIERWSZA PRÓBA
            LANGUAGE = self.language
            
            llm_summary = generate_llm_summary(raw_text, LANGUAGE)
            
            if llm_summary:
                self.summary_text = llm_summary
            else:
                # 2.a LOKALNA ANALIZA (SUMY) - FALLBACK JEŚLI LLM ZAWIEDZIE
                print("LLM zawiódł lub nie jest dostępny. Używam lokalnej metody LSA (SUMY).")
                
                SENTENCES_COUNT = 10 
                sumy_language = 'english' if LANGUAGE == 'english' else 'polish'

                parser = PlaintextParser.from_string(raw_text, Tokenizer(sumy_language))
                
                try:
                    stemmer = Stemmer(sumy_language)
                except LookupError:
                    print(f"Ostrzeżenie: Stemmer dla '{sumy_language}' niedostępny. Używam fallback.")
                    stemmer = Stemmer("english")

                summarizer = LsaSummarizer(stemmer)
                
                try:
                    summarizer.stop_words = get_stop_words(sumy_language)
                except LookupError:
                    print(f"Ostrzeżenie: Stop-words dla '{sumy_language}' niedostępne. Używam fallback (English/Empty).")
                    try:
                        summarizer.stop_words = get_stop_words("english")
                    except LookupError:
                        summarizer.stop_words = [] 

                summary_result = summarizer(parser.document, SENTENCES_COUNT)
                final_summary = "\n\n".join([str(sentence) for sentence in summary_result])
                
                # Dodajemy nagłówek i formatowanie Markdown dla spójności
                header_text = f"## Podsumowanie - Metoda LSA (Lokalna, {LANGUAGE.upper()})"
                self.summary_text = f"{header_text}\n\n{final_summary}"
                
            # 3. Fiszki (SpaCy)
            self.flashcards_data = generate_cloze_flashcards(raw_text, LANGUAGE)
            
            # Reset gry
            self.current_card_index = 0
            self.user_answers = []

            self.after(0, self.setup_main_view)

        except Exception as e:
            print(f"Błąd przetwarzania: {e}")
            self.after(0, lambda: messagebox.showerror("Błąd krytyczny", f"Wystąpił błąd podczas analizy: {e}"))
            self.after(0, lambda: self.show_frame(UploadView))

    def setup_main_view(self):
        main_view = self.frames[MainAppView]
        main_view.update_summary(self.summary_text)
        main_view.load_flashcard() 
        self.show_frame(MainAppView)

    def save_to_txt(self):
        if not self.summary_text:
            return
        
        # UŻYWAMY NOWEJ FUNKCJI DO CZYSZCZENIA Z MARKDOWN DLA PLIKU .TXT
        cleaned_summary_text = cleanup_markdown_for_save(self.summary_text)

        full_content = f"*** EDUGENIUS NOTATKA - Język: {self.language.upper()} ***\n\n"
        full_content += cleaned_summary_text
        full_content += "\n\n*** FISZKI ***\n"
        
        if self.flashcards_data:
            for i, card in enumerate(self.flashcards_data):
                full_content += f"Pytanie {i+1}: {card['question']}\n"
                full_content += f"Odpowiedź {i+1}: {card['answer']}\n---\n"
        else:
             full_content += "Brak wygenerowanych fiszek.\n"

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Plik tekstowy", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            messagebox.showinfo("Sukces", "Notatka zapisana w pliku .txt!")

# --- WIDOKI (UI) ---

class UploadView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.center_frame, text="EduGenius - Lokalny Asystent Nauki", font=("Roboto Medium", 30))
        self.label.pack(pady=20)
        
        self.lang_label = ctk.CTkLabel(self.center_frame, text="Wybierz język pliku:", font=("Roboto", 16))
        self.lang_label.pack(pady=(0, 5))
        
        self.lang_var = ctk.StringVar(value=self.controller.language)
        self.lang_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.lang_frame.pack(pady=(0, 20))
        
        self.pl_btn = ctk.CTkButton(self.lang_frame, text="Polski", width=100, command=lambda: self.set_lang_and_style("polish"))
        self.pl_btn.pack(side="left", padx=10)
        self.en_btn = ctk.CTkButton(self.lang_frame, text="English", width=100, command=lambda: self.set_lang_and_style("english"))
        self.en_btn.pack(side="left", padx=10)
        
        self.set_lang_and_style(self.controller.language) 

        self.drop_btn = ctk.CTkButton(
            self.center_frame,
            text="Wybierz plik do analizy\n(.txt, .pdf, .docx, .odt)",
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

    def set_lang_and_style(self, lang):
        self.controller.set_language(lang)
        active_color = "#1f538d"
        inactive_color = "#2B2B2B"
        
        self.pl_btn.configure(fg_color=active_color if lang == "polish" else inactive_color)
        self.en_btn.configure(fg_color=active_color if lang == "english" else inactive_color)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Dokumenty", "*.txt *.pdf *.docx *.odt")])
        if file_path:
            self.controller.process_file(file_path)

class LoadingView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.label = ctk.CTkLabel(self.center_frame, text="Analiza i generowanie notatek...", font=("Roboto", 20))
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

        self.tab_summary = self.tabview.add("1. Podsumowanie")
        self.tab_flashcards = self.tabview.add("2. Fiszki (Tryb Nauki)")

        # Podsumowanie UI
        # Używamy domyślnej czcionki dla ciała tekstu
        self.summary_textbox = ctk.CTkTextbox(self.tab_summary, font=self.controller.body_font, wrap="word")
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.save_btn = ctk.CTkButton(self.tab_summary, text="Pobierz pełną notatkę (.txt)", command=self.controller.save_to_txt)
        self.save_btn.pack(pady=10)
        self.back_to_upload_btn = ctk.CTkButton(self.tab_summary, text="Powrót do pierwszego widoku", command=lambda: self.controller.show_frame(UploadView))
        self.back_to_upload_btn.pack(pady=10)

        # FISZKI UI
        self.card_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="#1f538d", corner_radius=30, width=600, height=400)
        self.card_frame.pack(pady=40, padx=40, fill="both", expand=True)
        self.card_frame.bind("<Button-1>", self.flip_card)

        self.card_label = ctk.CTkLabel(self.card_frame, text="Wgraj plik, aby wygenerować fiszki", font=("Roboto", 24), wraplength=500, text_color="white")
        self.card_label.place(relx=0.5, rely=0.5, anchor="center")
        self.card_label.bind("<Button-1>", self.flip_card)

        self.hint_label = ctk.CTkLabel(self.card_frame, text="", font=("Roboto", 12), text_color="gray")
        self.hint_label.place(relx=0.5, rely=0.9, anchor="center")

        self.btns_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="transparent")
        self.btns_frame.pack(pady=20)
        self.btn_know = ctk.CTkButton(self.btns_frame, text="Wiem :)", fg_color="green", hover_color="darkgreen", command=lambda: self.answer_card(True))
        self.btn_know.pack(side="left", padx=20)
        self.btn_dont_know = ctk.CTkButton(self.btns_frame, text="Nie wiem :(", fg_color="red", hover_color="darkred", command=lambda: self.answer_card(False))
        self.btn_dont_know.pack(side="right", padx=20)

        self.result_label = ctk.CTkLabel(self.tab_flashcards, text="", font=("Roboto", 16))
        self.result_label.pack(pady=10)

        # Przycisk powrotu do pierwszego widoku
        self.back_btn = ctk.CTkButton(self, text="Powrót do pierwszego widoku", command=lambda: self.controller.show_frame(UploadView))
        self.back_btn.pack(pady=10)

    def update_summary(self, markdown_text):
        """
        Wstawia tekst do CTkTextbox, usuwając pogrubienia (**) i nagłówki (##),
        ale zachowując nową linię, aby tekst był bardziej czytelny.
        
        Uwaga: CTkTextbox nie obsługuje tagów Tkinter do zmiany czcionek dla fragmentów tekstu.
        
        """
        self.summary_textbox.delete("0.0", "end")
        
        # 1. Usuń **pogrubienia** -> zostaje sam tekst
        # 2. Usuń ## nagłówki -> zostaje sam tekst (zmieniamy też na duże litery dla wyróżnienia)
        
        cleaned_for_display = []
        for line in markdown_text.split('\n'):
            line_content = line
            
            # Usuń ## i zmień na DUŻE LITERY dla nagłówka
            if line_content.startswith('## '):
                line_content = line_content[3:].upper()
            
            # Usuń **pogrubienia**
            line_content = re.sub(r'\*\*(.*?)\*\*', r'\1', line_content)
            
            cleaned_for_display.append(line_content)
            
        final_text = "\n".join(cleaned_for_display).strip()
        
        self.summary_textbox.insert("0.0", final_text)


    def load_flashcard(self):
        # ... (Metoda bez zmian) ...
        if not self.controller.flashcards_data:
            self.card_label.configure(text="Brak fiszek. Wgraj plik, aby wygenerować.")
            self.btn_know.configure(state="disabled")
            self.btn_dont_know.configure(state="disabled")
            self.result_label.configure(text="")
            return

        if self.controller.current_card_index >= len(self.controller.flashcards_data):
            self.controller.show_frame(SummaryResultView)
            return

        card = self.controller.flashcards_data[self.controller.current_card_index]
        self.card_label.configure(text=card['question'])
        self.hint_label.configure(text=f"Karta {self.controller.current_card_index + 1} z {len(self.controller.flashcards_data)} | Kliknij, aby odkryć")
        self.controller.is_card_flipped = False
        self.btn_know.configure(state="normal")
        self.btn_dont_know.configure(state="normal")
        self.result_label.configure(text="")

    def flip_card(self, event):
        # ... (Metoda bez zmian) ...
        if not self.controller.flashcards_data:
            return

        card = self.controller.flashcards_data[self.controller.current_card_index]
        if not self.controller.is_card_flipped:
            self.card_label.configure(text=card['answer'])
            self.hint_label.configure(text="Odpowiedź: (Kliknij, aby wrócić do pytania)")
            self.controller.is_card_flipped = True
            self.card_frame.configure(fg_color="gray")
        else:
            self.card_label.configure(text=card['question'])
            self.hint_label.configure(text="Kliknij, aby odkryć")
            self.controller.is_card_flipped = False
            self.card_frame.configure(fg_color="#1f538d")

    def answer_card(self, knew_it):
        # ... (Metoda bez zmian) ...
        if self.controller.current_card_index < len(self.controller.flashcards_data):
            self.controller.user_answers.append(knew_it)
            
            feedback = "Dobrze! Przechodzimy dalej." if knew_it else "Następnym razem! Przechodzimy dalej."
            self.result_label.configure(text=feedback)
            
            # Odkryj na chwilę odpowiedź
            card = self.controller.flashcards_data[self.controller.current_card_index]
            self.card_label.configure(text=card['answer'])
            self.hint_label.configure(text="ODPOWIEDŹ")
            
            # Przejście do następnej karty po krótkim opóźnieniu
            self.controller.current_card_index += 1
            self.controller.after(700, self.load_flashcard)


class SummaryResultView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.result_frame, text="KONIEC SESJI NAUKI!", font=("Roboto Medium", 30))
        self.label.pack(pady=20)

        self.score_label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto", 20))
        self.score_label.pack(pady=10)

        self.restart_btn = ctk.CTkButton(self.result_frame, text="Powrót do głównego widoku", command=self.back_to_main)
        self.restart_btn.pack(pady=30)

        self.upload_btn = ctk.CTkButton(self.result_frame, text="Powrót do pierwszego widoku", command=lambda: self.controller.show_frame(UploadView))
        self.upload_btn.pack(pady=10)
        
    def tkraise(self, *args, **kwargs):
        self.update_results()
        super().tkraise(*args, **kwargs)

    def update_results(self):
        total = len(self.controller.user_answers)
        known = sum(self.controller.user_answers)
        
        if total == 0:
            self.score_label.configure(text="Nie udzielono żadnych odpowiedzi.")
            return

        score_text = f"Zapamiętałeś/aś: {known} z {total} ({known/total*100:.1f}%)"
        self.score_label.configure(text=score_text)

    def back_to_main(self):
        self.controller.show_frame(MainAppView)
        self.controller.current_card_index = 0
        self.controller.user_answers = []
        # Ustawienie fiszek na pierwszej karcie
        self.controller.frames[MainAppView].load_flashcard()

if __name__ == "__main__":
    app = EduApp()
    app.mainloop()