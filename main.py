import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import random
import re
from tkinter import ttk 
import math
import time

import pypdf
from docx import Document
from odf import text, teletype
from odf.opendocument import load

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import nltk

import spacy
import spacy.cli 

from llama_cpp import Llama 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

L10N = {
    "polish": {
        "app_title": "EduGenius - Lokalny Asystent Nauki",
        "upload_header": "EduGenius - Lokalny Asystent Nauki",
        "lang_select": "Wybierz język pliku:",
        "file_select_btn": "Wybierz plik do analizy\n(.txt, .pdf, .docx, .odt)",
        "loading_text": "Analiza i generowanie notatek...",
        "loading_phrases": [
            "Analizuję strukturę pliku...", 
            "Wyodrębniam kluczowe fragmenty tekstu...",
            "Przygotowuję kontekst dla modelu LLM...",
            "Generuję podsumowanie eksperckie...",
            "Wykonuję analizę semantyczną...",
            "Wyszukuję definicje i terminy...",
            "Tworzę listę najważniejszych pojęć...",
            "Sprawdzam spójność logiczną notatek...",
            "Opracowuję pytania i luki w tekście...",
            "Generuję fiszki metodą Cloze Deletion...",
            "Filtruję mniej istotne dane...",
            "Optymalizuję notatki do nauki...",
            "Uruchamiam proces NLP (Natural Language Processing)...",
            "Wgrywam dane do pamięci podręcznej...",
            "Przygotowuję interfejs użytkownika...",
            "Kończę przetwarzanie... Ostatnie szlify...",
            "Kalibruję algorytmy...",
            "Analizuję czasowniki i rzeczowniki (SpaCy)...",
            "Sortuję fiszki według priorytetu...",
            "Czekam na odpowiedź z lokalnego modelu...",
            "Porządkuję dane wyjściowe...",
            "Ustawiam tabulatory...",
        ],
        "tab_summary": "1. Podsumowanie",
        "tab_flashcards": "2. Fiszki (Tryb Nauki)",
        "save_btn": "Pobierz pełną notatkę (.txt)",
        "back_to_upload_btn": "Powrót do wczytywania pliku",
        "flashcard_empty": "Wgraj plik, aby wygenerować fiszki",
        "hint_click_to_flip": "Karta {current} z {total} | kliknij kartę, żeby odkryć odpowiedź.",
        "hint_flipped": "Odpowiedź {current} z {total} | kliknij kartę, żeby wrócić do pytania",
        "btn_know": "Wiem :)",
        "btn_dont_know": "Nie wiem :(",
        "feedback_know": "Dobrze! Przechodzimy dalej.",
        "feedback_dont_know": "Następnym razem! Przechodzimy dalej.",
        "result_header": "KONIEC SESJI NAUKI!",
        "result_no_answers": "Nie udzielono żadnych odpowiedzi.",
        "result_score": "zapamiętałeś/aś: {known} z {total} ({percent:.1f}%)",
        "restart_btn": "Powrót do trybu nauki",
        "error_file_read": "Nie udało się odczytać pliku lub jest pusty.",
        "error_critical": "Wystąpił błąd krytyczny podczas analizy: {error}",
        "success_save": "Sukces",
        "success_save_msg": "Notatka zapisana w pliku .txt!",
        "summary_header": "## Podsumowanie",
        "summary_error": "Błąd formatowania: Podsumowanie jest puste.",
        "note_prefix": "EDUGENIUS NOTATKA",
        "flashcards_header_txt": "FISZKI",
        "no_flashcards_txt": "Brak wygenerowanych fiszek.",
        "question_txt": "Pytanie",
        "answer_txt": "Odpowiedź"
    },
    "english": {
        "app_title": "EduGenius - Local Study Assistant",
        "upload_header": "EduGenius - Local Study Assistant",
        "lang_select": "Select file language:",
        "file_select_btn": "Select file for analysis\n(.txt, .pdf, .docx, .odt)",
        "loading_text": "Analyzing and generating notes...",
        "loading_phrases": [
            "Analyzing file structure...",
            "Extracting key text fragments...",
            "Preparing context for the LLM model...",
            "Generating expert summary...",
            "Performing semantic analysis...",
            "Searching for definitions and terms...",
            "Creating a list of most important concepts...",
            "Checking the logical consistency of notes...",
            "Developing questions and cloze deletions...",
            "Generating flashcards using Cloze Deletion...",
            "Filtering less essential data...",
            "Optimizing notes for study...",
            "Running NLP (Natural Language Processing) process...",
            "Loading data to cache...",
            "Preparing user interface...",
            "Finalizing processing... Last touches...",
            "Calibrating algorithms...",
            "Analyzing verbs and nouns (SpaCy)...",
            "Sorting flashcards by priority...",
            "Waiting for response from the local model...",
            "Arranging output data...",
            "Setting up tabs...",
        ],
        "tab_summary": "1. Summary",
        "tab_flashcards": "2. Flashcards (Study Mode)",
        "save_btn": "Download full note (.txt)",
        "back_to_upload_btn": "Back to file upload",
        "flashcard_empty": "Upload a file to generate flashcards",
        "hint_click_to_flip": "Card {current} of {total} | click the card to reveal the answer.",
        "hint_flipped": "Answer {current} of {total} | click the card to go back to the question",
        "btn_know": "I know :)",
        "btn_dont_know": "I don't know :(",
        "feedback_know": "Correct! Moving on.",
        "feedback_dont_know": "Maybe next time! Moving on.",
        "result_header": "END OF STUDY SESSION!",
        "result_no_answers": "No answers provided.",
        "result_score": "you remembered: {known} out of {total} ({percent:.1f}%)",
        "restart_btn": "Back to study mode",
        "error_file_read": "Could not read the file or is empty.",
        "error_critical": "A critical error occurred during analysis: {error}",
        "success_save": "Success",
        "success_save_msg": "Note saved to .txt file!",
        "summary_header": "## Summary",
        "summary_error": "Formatting error: Summary is empty.",
        "note_prefix": "EDUGENIUS NOTE",
        "flashcards_header_txt": "FLASHCARDS",
        "no_flashcards_txt": "No flashcards generated.",
        "question_txt": "Question",
        "answer_txt": "Answer"
    }
}


MODEL_PATH = "qwen2.5-1.5b-instruct-q4_k_m.gguf" 
_llama_model = None

SPACY_MODELS = {
    "polish": "pl_core_news_sm",
    "english": "en_core_web_sm"
}
_loaded_spacy_models = {}

MAX_CHARS_LIMIT = 10000 
MAX_FLASHCARDS = 50 


def load_llm():
    global _llama_model
    if _llama_model is None:
        if not os.path.exists(MODEL_PATH):
            return None 

        try:
            _llama_model = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=-1,  
                n_ctx=4096, 
                verbose=False,
                chat_format="llama-3"
            )
        except Exception as e:
            _llama_model = None 
            
    return _llama_model

def get_safe_text_fragment(raw_text, max_chars):
    if len(raw_text) <= max_chars:
        return raw_text
    
    truncated = raw_text[:max_chars]
    
    last_sentence_end = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
    
    if last_sentence_end > max_chars * 0.9: 
        return truncated[:last_sentence_end + 1]
    else:
        return truncated
        
def generate_llm_summary(raw_text, language):
    llm = load_llm()
    if llm is None:
        return None 
        
    try:
        text_fragment = get_safe_text_fragment(raw_text, MAX_CHARS_LIMIT)
            
        user_prompt = f"oto tekst do podsumowania:\n\n---\n{text_fragment}" 

        if language == "polish":
            system_prompt = (
                "jesteś polskim ekspertem w dziedzinie edukacji. podsumuj ten tekst "
                "w maksymalnie 10 najważniejszych punktach. "
                "***nigdy nie używaj fraz wstępnych takich jak 'oto podsumowanie', 'podsumowanie' itp. zacznij od razu od pierwszego punktu na liście.*** "
                "używaj numerowanych list markdown (1., 2., 3., etc.). "
                "pogrub kluczowe słowa lub nazwy używając podwójnych gwiazdek markdown (**słowo**). "
                "odpowiedź musi zawierać znaczniki markdown i nigdy nie zawierać tekstu spoza listy. nie używaj nagłówka."
            )
        else:
            system_prompt = (
                "you are an expert educational assistant. summarize this text "
                "into a maximum of 10 key points. "
                "***never use introductory phrases like 'here is the summary' or 'summary'. start immediately with the first point on the list.*** "
                "use numbered markdown lists (1., 2., 3., etc.). "
                "bold keywords or names using double asterisks markdown (**word**). "
                "the response must contain markdown markers and never contain text outside the list. do not use a header."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=512, 
            temperature=0.5, 
            stream=False,
        )
        
        summary = output['choices'][0]['message']['content'].strip()
        
        return summary
        
    except Exception as e:
        return None


def get_spacy_nlp(language):
    if language not in SPACY_MODELS:
        raise ValueError(f"nieobsługiwany język: {language}")
        
    if language not in _loaded_spacy_models:
        model_name = SPACY_MODELS[language]
        try:
            _loaded_spacy_models[language] = spacy.load(model_name)
        except OSError:
            spacy.cli.download(model_name)
            _loaded_spacy_models[language] = spacy.load(model_name)
            
    return _loaded_spacy_models[language]

def generate_cloze_flashcards(text, language):
    
    text_fragment = get_safe_text_fragment(text, MAX_CHARS_LIMIT)
    
    try:
        nlp = get_spacy_nlp(language)
    except Exception as e:
        return []

    doc = nlp(text_fragment)
    flashcards = []
    
    if language == "polish":
        target_pos = ["NOUN", "PROPN", "ADJ", "VERB"]  
    else: 
        target_pos = ["NOUN", "PROPN", "ADJ"]

    for sent in doc.sents:
        if len(sent.text) < 15:
            continue
            
        keywords = [token for token in sent if token.pos_ in target_pos and len(token.text) > 3 and not token.is_punct and not token.like_num and token.i > 0]
        
        if not keywords or len(flashcards) >= MAX_FLASHCARDS: 
            continue
            
        target_word = random.choice(keywords)
        
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
            return None
            
def cleanup_markdown_for_save(text):
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE) 
    text = re.sub(r'(\*\*|\*|--|~~)', '', text) 
    text = re.sub(r'^\s*(\d+\.|\-|\*)\s*', '', text, flags=re.MULTILINE) 
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def clean_llm_summary(summary_text, language):
    if not summary_text:
        return ""
        
    cleaned = re.sub(r'^\s*#+\s*(Podsumowanie|Summary)\s*\n*', '', summary_text, flags=re.IGNORECASE | re.MULTILINE)
    
    chat_phrases_to_remove = [
        r'Oto\s+najważniejsze\s+informacje\s+o\s+.*:\s*', 
        r'(Przepływy|Wymiar)\s*:\s*.*[\n\s]*',             
        r'Ograniczono\s+do\s+10\s+punktów.*',
        r'Dodatkowe\s+informacje:\s*',
        r'Zaczynamy\s+od\s+razu\s+od\s+punktów\s*.*',
        r'\-\s*CustomTkinter:\s*Ograniczono\s+masz\s+czatowe\s+rzeczy\s*', 
        
        r'^\s*SUMMARY\s*\n*', 
        r'^\s*\-{5,}\s*\n*',  
    ]
    
    for phrase in chat_phrases_to_remove:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
    cleaned = re.sub(r'^\s*\-\s*', '', cleaned, flags=re.MULTILINE)
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
    header = L10N[language]["summary_header"]
    return f"{header}\n\n{cleaned}".strip()

class EduApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.flashcards_data = []
        self.summary_text = "" 
        self.current_card_index = 0
        self.user_answers = [] 
        self.is_card_flipped = False
        self.language = "polish" 
        
        self.title(L10N[self.language]["app_title"])
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.header_font = ctk.CTkFont(family="Roboto", size=18, weight="bold")
        self.bold_font = ctk.CTkFont(family="Roboto", size=14, weight="bold")
        self.body_font = ctk.CTkFont(family="Roboto", size=14, weight="normal")

        for resource in ['punkt', 'punkt_tab']:
            try:
                nltk.data.find(f'tokenizers/{resource}')
            except LookupError:
                try:
                    if os.getenv('NLTK_DOWNLOAD_ATTEMPT', '0') == '0':
                         nltk.download(resource)
                         os.environ['NLTK_DOWNLOAD_ATTEMPT'] = '1'
                except Exception as e:
                    pass

        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (UploadView, LoadingView, MainAppView, SummaryResultView): 
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(UploadView)

    def set_language(self, lang):
        if self.language != lang:
            self.language = lang
            self.title(L10N[self.language]["app_title"])
            
            for frame in self.frames.values():
                if hasattr(frame, 'update_language'):
                    frame.update_language()
        
    def show_frame(self, container_class):
        old_frame = None
        for frame in self.frames.values():
            if frame.winfo_ismapped(): 
                old_frame = frame
                break
        
        if old_frame and isinstance(old_frame, LoadingView):
             old_frame.on_hide()
        
        frame = self.frames[container_class]
        frame.tkraise()
        
    def reset_state_and_show_upload(self):
        self.flashcards_data = []
        self.summary_text = ""
        self.current_card_index = 0
        self.user_answers = []
        
        main_view = self.frames[MainAppView]
        main_view.update_summary("") 
        main_view.load_flashcard(animate=False) 
        
        self.show_frame(UploadView)

    def process_file(self, file_path):
        self.show_frame(LoadingView)
        thread = threading.Thread(target=self._process_file_thread, args=(file_path,))
        thread.start()

    def _process_file_thread(self, file_path):
        raw_text = None
        LANGUAGE = self.language
        texts = L10N[LANGUAGE]

        try:
            raw_text = FileProcessor.extract_text(file_path)
            if not raw_text or len(raw_text.strip()) < 10:
                self.after(0, lambda: messagebox.showerror("Błąd", texts["error_file_read"]))
                self.after(0, lambda: self.show_frame(UploadView))
                return

            llm_summary = generate_llm_summary(raw_text, LANGUAGE)
            
            if llm_summary:
                self.summary_text = clean_llm_summary(llm_summary, LANGUAGE)
            else:
                
                SENTENCES_COUNT = 10 
                sumy_language = 'english' if LANGUAGE == 'english' else 'polish'

                fallback_text = get_safe_text_fragment(raw_text, MAX_CHARS_LIMIT)
                
                parser = PlaintextParser.from_string(fallback_text, Tokenizer(sumy_language))
                
                try:
                    stemmer = Stemmer(sumy_language)
                except LookupError:
                    stemmer = Stemmer("english")

                summarizer = LsaSummarizer(stemmer)
                
                try:
                    summarizer.stop_words = get_stop_words(sumy_language)
                except LookupError:
                    try:
                        summarizer.stop_words = get_stop_words("english")
                    except LookupError:
                        summarizer.stop_words = [] 

                summary_result = summarizer(parser.document, SENTENCES_COUNT)
                final_summary = "\n\n".join([str(sentence) for sentence in summary_result])
                
                header_text = texts["summary_header"] + f" - lsa ({LANGUAGE.upper()})"
                self.summary_text = f"{header_text}\n\n{final_summary}"
                
            self.flashcards_data = generate_cloze_flashcards(raw_text, LANGUAGE)
            
            self.current_card_index = 0
            self.user_answers = []

            self.after(0, self.setup_main_view)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror(texts["error_critical"].split(":")[0], texts["error_critical"].format(error=e)))
            self.after(0, lambda: self.show_frame(UploadView))

    def setup_main_view(self):
        main_view = self.frames[MainAppView]
        main_view.update_summary(self.summary_text)
        main_view.load_flashcard() 
        self.show_frame(MainAppView)

    def save_to_txt(self):
        if not self.summary_text:
            return
        
        LANGUAGE = self.language
        texts = L10N[LANGUAGE]

        cleaned_summary_text = cleanup_markdown_for_save(self.summary_text)

        header_prefix = texts["note_prefix"]
        flashcards_header = texts["flashcards_header_txt"]
        no_flashcards = texts["no_flashcards_txt"]
        question_txt = texts["question_txt"]
        answer_txt = texts["answer_txt"]


        full_content = f"*** {header_prefix} - language: {self.language.upper()} ***\n\n"
        full_content += cleaned_summary_text
        full_content += f"\n\n*** {flashcards_header} ***\n"
        
        if self.flashcards_data:
            for i, card in enumerate(self.flashcards_data):
                full_content += f"{question_txt} {i+1}: {card['question']}\n"
                full_content += f"{answer_txt} {i+1}: {card['answer']}\n---\n"
        else:
             full_content += no_flashcards + "\n"

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("plik tekstowy", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            messagebox.showinfo(texts["success_save"], texts["success_save_msg"])

class UploadView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto medium", 30))
        self.label.pack(pady=20)
        
        self.lang_label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto", 16))
        self.lang_label.pack(pady=(0, 5))
        
        self.lang_var = ctk.StringVar(value=self.controller.language)
        self.lang_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.lang_frame.pack(pady=(0, 20))
        
        self.pl_btn = ctk.CTkButton(self.lang_frame, text="polski", width=100, command=lambda: self.set_lang_and_style("polish"))
        self.pl_btn.pack(side="left", padx=10)
        self.en_btn = ctk.CTkButton(self.lang_frame, text="english", width=100, command=lambda: self.set_lang_and_style("english"))
        self.en_btn.pack(side="left", padx=10)

        self.drop_btn = ctk.CTkButton(
            self.center_frame,
            text="",
            font=("Roboto", 18),
            width=400,
            height=200,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            border_width=2,
            border_color="#1f538d",
            corner_radius=20,
            command=self.select_file
        )
        self.drop_btn.pack(pady=20)
        
        self.set_lang_and_style(self.controller.language)
        self.update_language() 

    def set_lang_and_style(self, lang):
        self.controller.set_language(lang)
        active_color = "#1f538d"
        inactive_color = "#2b2b2b"
        
        self.pl_btn.configure(fg_color=active_color if lang == "polish" else inactive_color)
        self.en_btn.configure(fg_color=active_color if lang == "english" else inactive_color)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("dokumenty", "*.txt *.pdf *.docx *.odt")])
        if file_path:
            self.controller.process_file(file_path)

    def update_language(self):
        lang = self.controller.language
        texts = L10N[lang]
        self.label.configure(text=texts["upload_header"])
        self.lang_label.configure(text=texts["lang_select"])
        self.drop_btn.configure(text=texts["file_select_btn"])


class LoadingView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.animation_job = None 
        self.phrase_interval_ms = 2500 
        
        self.phrases_queue = []
        self.all_phrases = []

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto", 20))
        self.label.pack(pady=20)
        
        self.update_language()

    def update_language(self):
        texts = L10N[self.controller.language]
        new_phrases = texts.get("loading_phrases", [texts["loading_text"]])
        
        self.all_phrases = list(new_phrases)
        self.phrases_queue = [] 

    def start_loading_animation(self):
        texts = L10N[self.controller.language]

        if not self.phrases_queue:
            if self.all_phrases:
                self.phrases_queue = list(self.all_phrases)
            else:
                self.phrases_queue = [texts["loading_text"]]
                
            random.shuffle(self.phrases_queue)
            
        new_phrase = self.phrases_queue.pop(0)
        
        self.label.configure(text=new_phrase)
        
        self.animation_job = self.after(self.phrase_interval_ms, self.start_loading_animation)

    def stop_loading_animation(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
            
    def tkraise(self, *args, **kwargs):
        self.stop_loading_animation() 
        self.start_loading_animation()
        super().tkraise(*args, **kwargs)
        
    def on_hide(self):
        self.stop_loading_animation()


class MainAppView(ctk.CTkFrame):
    FADE_TIME_MS = 250
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.card_fade_job = None
        
        self.tabview = ctk.CTkTabview(self, width=850, height=650)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)

        texts = L10N[self.controller.language]
        initial_summary_name = texts["tab_summary"]
        initial_flashcards_name = texts["tab_flashcards"]
        
        self.current_tab_names = [initial_summary_name, initial_flashcards_name]
        
        self.tab_summary = self.tabview.add(initial_summary_name)
        self.tab_flashcards = self.tabview.add(initial_flashcards_name)

        self.summary_textbox = ctk.CTkTextbox(self.tab_summary, font=self.controller.body_font, wrap="word") 
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.summary_btns_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        self.summary_btns_frame.pack(pady=10)
        
        self.save_btn = ctk.CTkButton(self.summary_btns_frame, text="", command=self.controller.save_to_txt)
        self.save_btn.pack(side="left", padx=10)
        
        self.back_to_upload_btn = ctk.CTkButton(self.summary_btns_frame, text="", command=self.controller.reset_state_and_show_upload)
        self.back_to_upload_btn.pack(side="left", padx=10)

        self.card_container = ctk.CTkFrame(self.tab_flashcards, fg_color="transparent")
        self.card_container.pack(pady=(40, 10), padx=40, fill="both", expand=True)
        self.card_container.grid_rowconfigure(0, weight=1)
        self.card_container.grid_columnconfigure(0, weight=1)
        
        self.card_frame = ctk.CTkFrame(self.card_container, fg_color="#1f538d", corner_radius=30)
        self.card_frame.pack(fill="both", expand=True, padx=40, pady=40) 
        self.card_frame.bind("<Button-1>", self.flip_card)

        self.card_label = ctk.CTkLabel(self.card_frame, text="", font=("Roboto", 24), wraplength=500, text_color="white")
        self.card_label.place(relx=0.5, rely=0.5, anchor="center")
        self.card_label.bind("<Button-1>", self.flip_card)
        
        self.hint_label = ctk.CTkLabel(self.tab_flashcards, text="", font=("Roboto", 14), text_color="white")
        self.hint_label.pack(pady=(0, 20)) 

        self.btns_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="transparent")
        self.btns_frame.pack(pady=10)
        
        self.btn_know = ctk.CTkButton(self.btns_frame, text="", fg_color="green", hover_color="darkgreen", command=lambda: self.answer_card(True))
        self.btn_dont_know = ctk.CTkButton(self.btns_frame, text="", fg_color="red", hover_color="darkred", command=lambda: self.answer_card(False))
        
        self.btn_know.pack(side="left", padx=20)
        self.btn_dont_know.pack(side="right", padx=20)

        self.result_label = ctk.CTkLabel(self.tab_flashcards, text="", font=("Roboto", 16))
        self.result_label.pack(pady=10)

        self.update_language(is_initial_call=True) 

    def _hide_answer_buttons(self):
        self.btn_know.pack_forget()
        self.btn_dont_know.pack_forget()

    def _show_answer_buttons(self):
        self.btn_know.pack(side="left", padx=20)
        self.btn_dont_know.pack(side="right", padx=20)
        self.btn_know.configure(state="normal")
        self.btn_dont_know.configure(state="normal")
        

    def update_language(self, is_initial_call=False):
        lang = self.controller.language
        texts = L10N[lang]
        
        new_summary_name = texts["tab_summary"]
        new_flashcards_name = texts["tab_flashcards"]
        new_values = [new_summary_name, new_flashcards_name]
        
        current_active_tab_name = self.tabview._current_name 
        old_tab_names = self.current_tab_names 

        try:
            self.tabview._segmented_button.configure(values=new_values)
        except Exception:
            try:
                self.tabview._segmented_button.set_values(new_values)
            except Exception as e:
                pass 

        old_to_new_map = dict(zip(old_tab_names, new_values))
        
        new_tab_dict = {}
        for old_key in old_tab_names:
            if old_key in self.tabview._tab_dict:
                new_key = old_to_new_map.get(old_key)
                if new_key:
                    new_tab_dict[new_key] = self.tabview._tab_dict[old_key]
        
        self.tabview._tab_dict = new_tab_dict
        self.tabview._name_list = new_values
        
        self.current_tab_names = new_values 

        new_active_name = new_summary_name 
        if current_active_tab_name in old_to_new_map:
             new_active_name = old_to_new_map[current_active_tab_name]
             
        try:
            self.tabview.set(new_active_name)
        except ValueError:
            try:
                self.tabview.set(new_summary_name)
            except ValueError:
                pass 

        self.save_btn.configure(text=texts["save_btn"])
        self.back_to_upload_btn.configure(text=texts["back_to_upload_btn"])
        self.btn_know.configure(text=texts["btn_know"])
        self.btn_dont_know.configure(text=texts["btn_dont_know"])
        
        if not is_initial_call:
            self.load_flashcard(animate=False)


    def update_summary(self, markdown_text):
        self.summary_textbox.delete("0.0", "end")
        
        if not markdown_text:
            self.summary_textbox.insert("0.0", L10N[self.controller.language]["flashcard_empty"])
            return

        cleaned_for_display = []
        for line in markdown_text.split('\n'):
            line_content = line
            
            line_content = re.sub(r'\*\*(.*?)\*\*', r'\1', line_content)
            
            if line_content.startswith('## '):
                line_content = '\n' + line_content[3:].upper() + '\n' + ('-' * 30)
            
            if re.match(r'^\s*\d+\.\s*', line_content):
                line_content = re.sub(r'^\s*(\d+\.\s*)', r'\1', line_content) 
            else:
                 line_content = re.sub(r'^(\s*[\-\*]\s*)', '', line_content) 
                 
            line_content = line_content.strip()

            if line_content: 
                cleaned_for_display.append(line_content)
            
        final_text = "\n".join(cleaned_for_display).strip()
        
        if not final_text:
             final_text = L10N[self.controller.language]["summary_error"]
             
        self.summary_textbox.insert("0.0", final_text)


    def load_flashcard(self, animate=True):
        lang = self.controller.language
        texts = L10N[lang]
        
        if self.controller.current_card_index >= len(self.controller.flashcards_data):
            self.controller.show_frame(SummaryResultView)
            return
            
        if not self.controller.flashcards_data:
            self.card_label.configure(text=texts["flashcard_empty"], text_color="white")
            self.hint_label.configure(text="") 
            self.btn_know.configure(state="disabled")
            self.btn_dont_know.configure(state="disabled")
            self.result_label.configure(text="")
            self.card_frame.configure(fg_color="#1f538d")
            return

        self.result_label.configure(text="")

        if animate:
            self._fade_card_text(start_alpha=1.0, end_alpha=0.0, callback=self._load_card_content)
        else:
            self._load_card_content()
            
    def _load_card_content(self):
        lang = self.controller.language
        texts = L10N[lang]
        card = self.controller.flashcards_data[self.controller.current_card_index]

        self.card_label.configure(text=card['question'], text_color="white")
        self.hint_label.configure(text=texts["hint_click_to_flip"].format(
            current=self.controller.current_card_index + 1,
            total=len(self.controller.flashcards_data)
        ))
        self.controller.is_card_flipped = False
        self.card_frame.configure(fg_color="#1f538d") 
        
        # ZMIANA: Ustawienie przycisków na 'normal' po załadowaniu pytania
        self.btn_know.configure(state="normal")
        self.btn_dont_know.configure(state="normal")

        self._fade_card_text(start_alpha=0.0, end_alpha=1.0, callback=None)

    def _fade_card_text(self, start_alpha, end_alpha, callback=None):
        
        if self.card_fade_job:
            self.controller.after_cancel(self.card_fade_job)
            self.card_fade_job = None

        start_time = time.time() * 1000
        ANIMATION_STEP_MS = 10 
        
        CARD_BG_R, CARD_BG_G, CARD_BG_B = 31, 83, 141
        TEXT_R, TEXT_G, TEXT_B = 255, 255, 255
        
        def run_animation():
            nonlocal start_time
            current_time = time.time() * 1000
            time_elapsed = current_time - start_time
            
            progress = min(1.0, time_elapsed / self.FADE_TIME_MS)
            
            eased_progress = 0.5 * (1 - math.cos(progress * math.pi))
            
            visibility = start_alpha + (end_alpha - start_alpha) * eased_progress
            
            r = int(CARD_BG_R + (TEXT_R - CARD_BG_R) * visibility)
            g = int(CARD_BG_G + (TEXT_G - CARD_BG_G) * visibility)
            b = int(CARD_BG_B + (TEXT_B - CARD_BG_B) * visibility)
            
            current_color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.card_label.configure(text_color=current_color)
            
            if progress >= 1.0:
                final_color = "white" if end_alpha == 1.0 else f'#{CARD_BG_R:02x}{CARD_BG_G:02x}{CARD_BG_B:02x}'
                self.card_label.configure(text_color=final_color)
                
                if callback:
                    callback()
            else:
                self.card_fade_job = self.controller.after(ANIMATION_STEP_MS, run_animation) 

        run_animation()


    def flip_card(self, event):
        if not self.controller.flashcards_data:
            return

        if self.card_fade_job:
            self.controller.after_cancel(self.card_fade_job)
            self.card_fade_job = None

        lang = self.controller.language
        texts = L10N[lang]
        card = self.controller.flashcards_data[self.controller.current_card_index]
        
        if not self.controller.is_card_flipped:
            self.card_label.configure(text=card['answer'], text_color="white")
            self.hint_label.configure(text=texts["hint_flipped"])
            self.hint_label.configure(text=texts["hint_flipped"].format(
                current=self.controller.current_card_index + 1,
                total=len(self.controller.flashcards_data)
            ))
            self.controller.is_card_flipped = True
            self.card_frame.configure(fg_color="#454545") 
            
            # Przyciski już są aktywne, ale upewniamy się, że ich stan jest zachowany
            self.btn_know.configure(state="normal")
            self.btn_dont_know.configure(state="normal")
        else:
            self.card_label.configure(text=card['question'], text_color="white")
            self.hint_label.configure(text=texts["hint_click_to_flip"].format(
                current=self.controller.current_card_index + 1,
                total=len(self.controller.flashcards_data)
            ))
            self.controller.is_card_flipped = False
            self.card_frame.configure(fg_color="#1f538d")
            
            # Przyciski pozostają aktywne
            self.btn_know.configure(state="normal")
            self.btn_dont_know.configure(state="normal")


    def answer_card(self, knew_it):
        if self.controller.current_card_index < len(self.controller.flashcards_data):
            # ZMIANA: Usunięcie sprawdzenia 'if not self.controller.is_card_flipped:'
            
            self.controller.user_answers.append(knew_it)
            
            lang = self.controller.language
            texts = L10N[lang]
            
            feedback = texts["feedback_know"] if knew_it else texts["feedback_dont_know"]
            self.result_label.configure(text=feedback)
            
            self.btn_know.configure(state="disabled")
            self.btn_dont_know.configure(state="disabled")
            
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

        self.label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto medium", 30))
        self.label.pack(pady=20)

        self.score_label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto", 20))
        self.score_label.pack(pady=10)

        self.restart_btn = ctk.CTkButton(self.result_frame, text="", command=self.back_to_main)
        self.restart_btn.pack(pady=30)

        self.upload_btn = ctk.CTkButton(
            self.result_frame, 
            text="", 
            command=self.controller.reset_state_and_show_upload,
            fg_color="#2e2e2e",
            hover_color="#3e3e3e"
        )
        self.upload_btn.pack(pady=10)
        
        self.update_language()
        
    def tkraise(self, *args, **kwargs):
        self.update_results()
        super().tkraise(*args, **kwargs)

    def update_language(self):
        lang = self.controller.language
        texts = L10N[lang]
        self.label.configure(text=texts["result_header"])
        self.restart_btn.configure(text=texts["restart_btn"])
        self.upload_btn.configure(text=texts["back_to_upload_btn"])
        self.update_results() 

    def update_results(self):
        lang = self.controller.language
        texts = L10N[lang]
        total = len(self.controller.user_answers)
        known = sum(self.controller.user_answers)
        
        if total == 0:
            self.score_label.configure(text=texts["result_no_answers"])
            return

        score_text = texts["result_score"].format(
            known=known,
            total=total,
            percent=known/total*100
        )
        self.score_label.configure(text=score_text)

    def back_to_main(self):
        self.controller.show_frame(MainAppView)
        self.controller.current_card_index = 0
        self.controller.user_answers = []
        self.controller.frames[MainAppView].load_flashcard()

if __name__ == "__main__":
    app = EduApp()
    app.mainloop()