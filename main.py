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

# --- CENTRALNY SŁOWNIK TŁUMACZEŃ (L10N) ---
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
        "hint_click_to_flip": "Karta {current} z {total} | Kliknij kartę, aby odkryć odpowiedź.",
        "hint_flipped": "Odpowiedź: (Kliknij kartę, aby wrócić do pytania)",
        "btn_know": "Wiem :)",
        "btn_dont_know": "Nie wiem :(",
        "feedback_know": "Dobrze! Przechodzimy dalej.",
        "feedback_dont_know": "Następnym razem! Przechodzimy dalej.",
        "result_header": "KONIEC SESJI NAUKI!",
        "result_no_answers": "Nie udzielono żadnych odpowiedzi.",
        "result_score": "Zapamiętałeś/aś: {known} z {total} ({percent:.1f}%)",
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
        "hint_click_to_flip": "Card {current} of {total} | Click the card to reveal the answer.",
        "hint_flipped": "Answer: (Click the card to go back to the question)",
        "btn_know": "I know :)",
        "btn_dont_know": "I don't know :(",
        "feedback_know": "Correct! Moving on.",
        "feedback_dont_know": "Maybe next time! Moving on.",
        "result_header": "END OF STUDY SESSION!",
        "result_no_answers": "No answers provided.",
        "result_score": "You remembered: {known} out of {total} ({percent:.1f}%)",
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

# --- ZDEFINIOWANE LIMIT ZNAKÓW DLA OBU PROCESÓW ---
MAX_CHARS_LIMIT = 10000 

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

def get_safe_text_fragment(raw_text, max_chars):
    """Obcina tekst do maksymalnej liczby znaków, ucinając po ostatniej pełnej kropce."""
    if len(raw_text) <= max_chars:
        return raw_text
    
    truncated = raw_text[:max_chars]
    
    # Znajdź ostatnią kropkę, znak zapytania lub wykrzyknik
    last_sentence_end = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
    
    # Ucinamy tylko jeśli jest blisko końca (np. w ostatnich 10% limitu)
    if last_sentence_end > max_chars * 0.9: 
        # Zapewnia, że fragment kończy się na pełnym zdaniu
        return truncated[:last_sentence_end + 1]
    else:
        # Jeśli nie znaleziono kropki blisko końca, po prostu używamy obciętego
        return truncated
        
def generate_llm_summary(raw_text, language):
    """Generuje podsumowanie za pomocą modelu LLM. Fragment 1."""
    try:
        llm = load_llm()
    except Exception as e:
        print(f"Błąd ładowania LLM. Aplikacja przejdzie na LSA: {e}")
        return None

    # Bezpieczne obcięcie tekstu wejściowego
    text_fragment = get_safe_text_fragment(raw_text, MAX_CHARS_LIMIT)
        
    user_prompt = f"Oto tekst do podsumowania:\n\n---\n{text_fragment}" 

    # Poprawiony Prompt systemowy
    if language == "polish":
        system_prompt = (
            "Jesteś polskim ekspertem w dziedzinie edukacji. Podsumuj ten tekst "
            "w maksymalnie 10 najważniejszych punktach. "
            "***Nigdy nie używaj fraz wstępnych takich jak 'Oto podsumowanie', 'PODSUMOWANIE' itp. ZACZNIJ OD RAZU od pierwszego punktu na liście.*** "
            "Używaj numerowanych list Markdown (1., 2., 3., etc.). "
            "Pogrub KLUCZOWE słowa lub nazwy używając PODWÓJNYCH GWIAZDEK Markdown (**słowo**). "
            "Odpowiedź MUSI ZAWIERAĆ znaczniki Markdown i NIGDY nie zawierać tekstu spoza listy. Nie używaj nagłówka."
        )
    else:
        system_prompt = (
            "You are an expert educational assistant. Summarize this text "
            "into a maximum of 10 key points. "
            "***Never use introductory phrases like 'Here is the summary' or 'SUMMARY'. START IMMEDIATELY with the first point on the list.*** "
            "Use numbered Markdown lists (1., 2., 3., etc.). "
            "Bold KEYWORDS or names using DOUBLE ASTERISKS Markdown (**word**). "
            "The response MUST CONTAIN Markdown markers and NEVER contain text outside the list. Do not use a header."
        )

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
    """Generuje fiszki metodą Cloze Deletion (luki w tekście) za pomocą spaCy. Ograniczenie do 10000 znaków. FRAGMENT 2"""
    
    # Bezpieczne obcięcie tekstu dla SpaCy do 10 000 znaków
    text_fragment = get_safe_text_fragment(text, MAX_CHARS_LIMIT)
    
    try:
        nlp = get_spacy_nlp(language)
    except Exception as e:
        print(f"Błąd krytyczny ładowania spaCy: {e}")
        return []

    doc = nlp(text_fragment)
    flashcards = []
    
    if language == "polish":
        target_pos = ["NOUN", "PROPN", "ADJ", "VERB"]  
    else: 
        target_pos = ["NOUN", "PROPN", "ADJ"]

    for sent in doc.sents:
        keywords = [token for token in sent if token.pos_ in target_pos and len(token.text) > 3 and not token.is_punct and not token.like_num and token.i > 0]
        
        if not keywords or len(flashcards) >= 20: 
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


def clean_llm_summary(summary_text, language):
    """
    Usuwa wszelkie czatowe i błędy formatowania generowane przez LLM.
    Zostawia tylko listę punktów i dodaje dynamiczny nagłówek na górze.
    """
    if not summary_text:
        return ""
        
    # Usuwanie nagłówka '## Podsumowanie' (który model miał nie generować)
    cleaned = re.sub(r'^\s*#+\s*(Podsumowanie|Summary)\s*\n*', '', summary_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # REGEX do usunięcia fraz w stylu "Ograniczono do 10 punktów i oznaczono jako 1.0"
    chat_phrases_to_remove = [
        r'Oto\s+najważniejsze\s+informacje\s+o\s+.*:\s*', 
        r'(Przepływy|Wymiar)\s*:\s*.*[\n\s]*',             
        r'Ograniczono\s+do\s+10\s+punktów.*',
        r'Dodatkowe\s+informacje:\s*',
        r'Zaczynamy\s+od\s+razu\s+od\s+punktów\s*.*',
        r'\-\s*CustomTkinter:\s*Ograniczono\s+masz\s+czatowe\s+rzeczy\s*', 
        
        # --- POPRAWKA: USUWANIE BŁĘDNYCH NAGŁÓWKÓW I SEPARATORÓW ---
        r'^\s*SUMMARY\s*\n*', 
        r'^\s*\-{5,}\s*\n*',  
    ]
    
    for phrase in chat_phrases_to_remove:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
    # Usunięcie nadmiarowych myślników (listy nieuporządkowane, które mogą się pojawić)
    cleaned = re.sub(r'^\s*\-\s*', '', cleaned, flags=re.MULTILINE)
    
    # Oczyszczenie nadmiarowych pustych linii
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
    # Wymuszenie nagłówka, którego oczekuje użytkownik (dynamiczne)
    header = L10N[language]["summary_header"]
    return f"{header}\n\n{cleaned}".strip()

class EduApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Zmienne stanu
        self.flashcards_data = []
        self.summary_text = "" 
        self.current_card_index = 0
        self.user_answers = [] 
        self.is_card_flipped = False
        self.language = "polish" # Domyślny język
        
        # Konfiguracja okna (tytuł zmieniany w set_language)
        self.title(L10N[self.language]["app_title"])
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
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
        """Ustawia język aplikacji i wymusza aktualizację wszystkich widoków."""
        if self.language != lang:
            self.language = lang
            self.title(L10N[self.language]["app_title"])
            
            # Wymuszenie aktualizacji języka w wszystkich utworzonych widokach
            for frame in self.frames.values():
                if hasattr(frame, 'update_language'):
                    frame.update_language()
        
    def show_frame(self, container_class):
        # 1. Znajdź obecną ramkę i ją ukryj
        old_frame = None
        for frame in self.frames.values():
            if frame.winfo_ismapped(): 
                old_frame = frame
                break
        
        # 2. Jeśli opuszczamy LoadingView, zatrzymaj animację.
        if old_frame and isinstance(old_frame, LoadingView):
             old_frame.on_hide()
        
        # 3. Pokaż nową ramkę (tkraise automatycznie wywoła tkraise w LoadingView)
        frame = self.frames[container_class]
        frame.tkraise()
        
    def reset_state_and_show_upload(self):
        """Resetuje cały stan analizy i przełącza do widoku wgrywania pliku."""
        # 1. Reset stanu aplikacji
        self.flashcards_data = []
        self.summary_text = ""
        self.current_card_index = 0
        self.user_answers = []
        
        # 2. Reset widoków MainApp, aby usunąć stare dane i komunikat "flashcard_empty"
        main_view = self.frames[MainAppView]
        main_view.update_summary("") 
        main_view.load_flashcard() 
        
        # 3. Pokaż widok wgrywania
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
            # 1. Wyciągnij tekst
            raw_text = FileProcessor.extract_text(file_path)
            if not raw_text or len(raw_text.strip()) < 10:
                self.after(0, lambda: messagebox.showerror("Błąd", texts["error_file_read"]))
                self.after(0, lambda: self.show_frame(UploadView))
                return

            # --- FRAGMENT 1: PODSUMOWANIE (LLM lub FALLBACK LSA) ---
            llm_summary = generate_llm_summary(raw_text, LANGUAGE)
            
            if llm_summary:
                # Oczyszczamy tekst z czatowych fraz i dodajemy nagłówek w poprawnym języku
                self.summary_text = clean_llm_summary(llm_summary, LANGUAGE)
            else:
                # LOKALNA ANALIZA (SUMY) - FALLBACK JEŚLI LLM ZAWIEDZIE
                print("LLM zawiódł lub nie jest dostępny. Używam lokalnej metody LSA (SUMY).")
                
                SENTENCES_COUNT = 10 
                sumy_language = 'english' if LANGUAGE == 'english' else 'polish'

                # FALLBACK RÓWNIEŻ UŻYWA OGRANICZONEGO TEKSTU (10k znaków po pełnym zdaniu)
                fallback_text = get_safe_text_fragment(raw_text, MAX_CHARS_LIMIT)
                
                parser = PlaintextParser.from_string(fallback_text, Tokenizer(sumy_language))
                
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
                
                # Dodajemy nagłówek dla Fallback
                header_text = texts["summary_header"] + f" - LSA ({LANGUAGE.upper()})"
                self.summary_text = f"{header_text}\n\n{final_summary}"
                
            # --- FRAGMENT 2: FISZKI (SpaCy) ---
            self.flashcards_data = generate_cloze_flashcards(raw_text, LANGUAGE)
            
            # Reset gry
            self.current_card_index = 0
            self.user_answers = []

            self.after(0, self.setup_main_view)

        except Exception as e:
            print(f"Błąd przetwarzania: {e}")
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

        # UŻYWAMY FUNKCJI DO CZYSZCZENIA Z MARKDOWN DLA PLIKU .TXT
        cleaned_summary_text = cleanup_markdown_for_save(self.summary_text)

        # Dynamiczne teksty dla pliku .txt
        header_prefix = texts["note_prefix"]
        flashcards_header = texts["flashcards_header_txt"]
        no_flashcards = texts["no_flashcards_txt"]
        question_txt = texts["question_txt"]
        answer_txt = texts["answer_txt"]


        full_content = f"*** {header_prefix} - Language: {self.language.upper()} ***\n\n"
        full_content += cleaned_summary_text
        full_content += f"\n\n*** {flashcards_header} ***\n"
        
        if self.flashcards_data:
            for i, card in enumerate(self.flashcards_data):
                full_content += f"{question_txt} {i+1}: {card['question']}\n"
                full_content += f"{answer_txt} {i+1}: {card['answer']}\n---\n"
        else:
             full_content += no_flashcards + "\n"

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Plik tekstowy", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            messagebox.showinfo(texts["success_save"], texts["success_save_msg"])

# --- WIDOKI (UI) ---

class UploadView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto Medium", 30))
        self.label.pack(pady=20)
        
        self.lang_label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto", 16))
        self.lang_label.pack(pady=(0, 5))
        
        self.lang_var = ctk.StringVar(value=self.controller.language)
        self.lang_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.lang_frame.pack(pady=(0, 20))
        
        self.pl_btn = ctk.CTkButton(self.lang_frame, text="Polski", width=100, command=lambda: self.set_lang_and_style("polish"))
        self.pl_btn.pack(side="left", padx=10)
        self.en_btn = ctk.CTkButton(self.lang_frame, text="English", width=100, command=lambda: self.set_lang_and_style("english"))
        self.en_btn.pack(side="left", padx=10)

        # Inicjalizacja przycisku wyboru pliku
        self.drop_btn = ctk.CTkButton(
            self.center_frame,
            text="",
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
        
        self.set_lang_and_style(self.controller.language)
        self.update_language() 

    def set_lang_and_style(self, lang):
        self.controller.set_language(lang)
        active_color = "#1f538d"
        inactive_color = "#2B2B2B"
        
        # Stylizacja przycisków języka (aktywny/nieaktywny)
        self.pl_btn.configure(fg_color=active_color if lang == "polish" else inactive_color)
        self.en_btn.configure(fg_color=active_color if lang == "english" else inactive_color)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Dokumenty", "*.txt *.pdf *.docx *.odt")])
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
        # Zwiększono interwał z 1500ms do 2500ms
        self.phrase_interval_ms = 2500 
        
        # Nowe zmienne do zarządzania kolejką fraz
        self.phrases_queue = []
        self.all_phrases = []

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.label = ctk.CTkLabel(self.center_frame, text="", font=("Roboto", 20))
        self.label.pack(pady=20)
        
        # Wstępne załadowanie fraz
        self.update_language()

    def update_language(self):
        """Ładuje frazy dla nowego języka i czyści kolejkę."""
        texts = L10N[self.controller.language]
        new_phrases = texts.get("loading_phrases", [texts["loading_text"]])
        
        # Ładujemy wszystkie frazy i czyścimy kolejkę
        self.all_phrases = list(new_phrases)
        self.phrases_queue = [] 

    def start_loading_animation(self):
        """Rozpoczyna cykliczną zmianę fraz ładowania, wykorzystując wszystkie frazy z listy, zanim się powtórzą."""
        texts = L10N[self.controller.language]

        if not self.phrases_queue:
            # Jeśli kolejka jest pusta, resetujemy ją, mieszając frazy.
            if self.all_phrases:
                self.phrases_queue = list(self.all_phrases)
            else:
                # Fallback, jeśli lista fraz jest pusta (użycie domyślnego komunikatu)
                self.phrases_queue = [texts["loading_text"]]
                
            random.shuffle(self.phrases_queue)
            
        # Pobieramy pierwszą frazę z kolejki i ją usuwamy
        new_phrase = self.phrases_queue.pop(0)
        
        self.label.configure(text=new_phrase)
        
        # Zaplanowanie kolejnej zmiany po określonym interwale
        self.animation_job = self.after(self.phrase_interval_ms, self.start_loading_animation)

    def stop_loading_animation(self):
        """Zatrzymuje cykliczną zmianę fraz ładowania."""
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
            
    def tkraise(self, *args, **kwargs):
        """Uruchamia animację po wyświetleniu widoku."""
        # Zapewnienie, że stary job jest anulowany przed rozpoczęciem nowego
        self.stop_loading_animation() 
        self.start_loading_animation()
        super().tkraise(*args, **kwargs)
        
    def on_hide(self):
        """Zatrzymuje animację, gdy widok jest ukrywany."""
        self.stop_loading_animation()


class MainAppView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.tabview = ctk.CTkTabview(self, width=850, height=650)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)

        # Używamy dynamicznych kluczy opartych na języku od początku
        texts = L10N[self.controller.language]
        initial_summary_name = texts["tab_summary"]
        initial_flashcards_name = texts["tab_flashcards"]
        
        # Zmienna do śledzenia aktualnych kluczy (tłumaczone nazwy)
        self.current_tab_names = [initial_summary_name, initial_flashcards_name]
        
        # Tworzymy zakładki za pomocą początkowych, już przetłumaczonych nazw
        # Te nazwy stają się kluczami w tabview._tab_dict
        self.tab_summary = self.tabview.add(initial_summary_name)
        self.tab_flashcards = self.tabview.add(initial_flashcards_name)

        # Podsumowanie UI
        self.summary_textbox = ctk.CTkTextbox(self.tab_summary, font=self.controller.body_font, wrap="word") 
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ramka na przyciski w zakładce Podsumowanie
        self.summary_btns_frame = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        self.summary_btns_frame.pack(pady=10)
        
        self.save_btn = ctk.CTkButton(self.summary_btns_frame, text="", command=self.controller.save_to_txt)
        self.save_btn.pack(side="left", padx=10)
        
        # NAPRAWIONY PRZYCISK: Używa nowej metody resetującej stan
        self.back_to_upload_btn = ctk.CTkButton(self.summary_btns_frame, text="", command=self.controller.reset_state_and_show_upload)
        self.back_to_upload_btn.pack(side="left", padx=10)

        # FISZKI UI
        self.card_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="#1f538d", corner_radius=30, width=600, height=400)
        self.card_frame.pack(pady=(40, 10), padx=40, fill="both", expand=True)
        self.card_frame.bind("<Button-1>", self.flip_card)

        self.card_label = ctk.CTkLabel(self.card_frame, text="", font=("Roboto", 24), wraplength=500, text_color="white")
        self.card_label.place(relx=0.5, rely=0.5, anchor="center")
        self.card_label.bind("<Button-1>", self.flip_card)

        self.hint_label = ctk.CTkLabel(self.tab_flashcards, text="", font=("Roboto", 14), text_color="white")
        self.hint_label.pack(pady=(0, 20)) 

        self.btns_frame = ctk.CTkFrame(self.tab_flashcards, fg_color="transparent")
        self.btns_frame.pack(pady=10)
        self.btn_know = ctk.CTkButton(self.btns_frame, text="", fg_color="green", hover_color="darkgreen", command=lambda: self.answer_card(True))
        self.btn_know.pack(side="left", padx=20)
        self.btn_dont_know = ctk.CTkButton(self.btns_frame, text="", fg_color="red", hover_color="darkred", command=lambda: self.answer_card(False))
        self.btn_dont_know.pack(side="right", padx=20)

        self.result_label = ctk.CTkLabel(self.tab_flashcards, text="", font=("Roboto", 16))
        self.result_label.pack(pady=10)

        self.update_language() # Początkowe ustawienie języka

    def update_language(self):
        lang = self.controller.language
        texts = L10N[lang]
        
        # Tłumaczone wartości dla przycisków
        new_summary_name = texts["tab_summary"]
        new_flashcards_name = texts["tab_flashcards"]
        new_values = [new_summary_name, new_flashcards_name]
        
        # 1. Zapisz nazwę aktualnej zakładki i stare nazwy kluczy
        current_active_tab_name = self.tabview._current_name 
        old_tab_names = self.current_tab_names # Stare klucze (np. ['1. Podsumowanie', '2. Fiszki...'])

        # 2. Zaktualizuj WYŚWIETLANY tekst w CTkSegmentedButton
        try:
            self.tabview._segmented_button.configure(values=new_values)
        except Exception:
            try:
                self.tabview._segmented_button.set_values(new_values)
            except Exception as e:
                print(f"Błąd aktualizacji tekstu w CTkTabview: {e}")
                pass 

        # 3. Zaktualizuj KLUCZE WEWNĘTRZNE w CTkTabview (unikanie KeyError)
        
        # Mapa: Stary_Klucz -> Nowy_Klucz
        old_to_new_map = dict(zip(old_tab_names, new_values))
        
        # 3.1. Przetwórz _tab_dict - Mapowanie nowego tekstu na istniejące ramki
        new_tab_dict = {}
        for old_key in old_tab_names:
            if old_key in self.tabview._tab_dict:
                new_key = old_to_new_map.get(old_key)
                if new_key:
                    new_tab_dict[new_key] = self.tabview._tab_dict[old_key]
        
        # Wewnętrzne słowniki CTkTabview muszą zostać zastąpione
        self.tabview._tab_dict = new_tab_dict
        self.tabview._name_list = new_values
        
        # AKTUALIZUJEMY NASZĄ ZMIENNĄ ŚLEDZĄCĄ (nowe klucze do kolejnej aktualizacji)
        self.current_tab_names = new_values 

        # 4. Wymuś ponowne ustawienie aktywnej zakładki
        new_active_name = new_summary_name # Domyślne ustawienie
        if current_active_tab_name in old_to_new_map:
             # Jeśli stara nazwa była w mapowaniu, użyjemy jej nowego odpowiednika
             new_active_name = old_to_new_map[current_active_tab_name]
             
        try:
            self.tabview.set(new_active_name)
        except ValueError:
            # W razie błędu, spróbuj ustawić na domyślne (summary)
            try:
                self.tabview.set(new_summary_name)
            except ValueError:
                pass 

        # 5. Aktualizacja pozostałych widżetów
        self.save_btn.configure(text=texts["save_btn"])
        self.back_to_upload_btn.configure(text=texts["back_to_upload_btn"])
        self.btn_know.configure(text=texts["btn_know"])
        self.btn_dont_know.configure(text=texts["btn_dont_know"])
        
        # Jeśli jesteśmy w trybie fiszek, przeładuj kartę, aby zaktualizować tekst (lub pusty komunikat)
        self.load_flashcard()


    def update_summary(self, markdown_text):
        """
        Wstawia tekst do CTkTextbox, usuwając formatowanie Markdown.
        """
        self.summary_textbox.delete("0.0", "end")
        
        if not markdown_text:
            self.summary_textbox.insert("0.0", L10N[self.controller.language]["flashcard_empty"])
            return

        cleaned_for_display = []
        for line in markdown_text.split('\n'):
            line_content = line
            
            # 1. Usuń **pogrubienia**
            line_content = re.sub(r'\*\*(.*?)\*\*', r'\1', line_content)
            
            # 2. Traktowanie nagłówka (##) - Zmieniamy na DUŻE LITERY i dodajemy separator
            if line_content.startswith('## '):
                line_content = '\n' + line_content[3:].upper() + '\n' + ('-' * 30)
            
            # 3. Usuń resztki formatowania listy (np. myślniki), zostaw numerację i treść
            if re.match(r'^\s*\d+\.\s*', line_content):
                line_content = re.sub(r'^\s*(\d+\.\s*)', r'\1', line_content) # Zostaw numerację
            else:
                 line_content = re.sub(r'^(\s*[\-\*]\s*)', '', line_content) # Usuń inne znaczniki listy
                 
            line_content = line_content.strip()

            if line_content: # Dodawaj tylko niepuste linie
                cleaned_for_display.append(line_content)
            
        final_text = "\n".join(cleaned_for_display).strip()
        
        if not final_text:
             final_text = L10N[self.controller.language]["summary_error"]
             
        self.summary_textbox.insert("0.0", final_text)


    def load_flashcard(self):
        lang = self.controller.language
        texts = L10N[lang]
        
        if not self.controller.flashcards_data:
            # Wyświetla komunikat o braku fiszek
            self.card_label.configure(text=texts["flashcard_empty"])
            self.hint_label.configure(text="") 
            self.btn_know.configure(state="disabled")
            self.btn_dont_know.configure(state="disabled")
            self.result_label.configure(text="")
            return

        if self.controller.current_card_index >= len(self.controller.flashcards_data):
            # Przekierowuje do ekranu wyników tylko, gdy fiszki są załadowane i wszystkie karty zostały wyświetlone.
            self.controller.show_frame(SummaryResultView)
            return

        card = self.controller.flashcards_data[self.controller.current_card_index]
        self.card_label.configure(text=card['question'])
        self.hint_label.configure(text=texts["hint_click_to_flip"].format(
            current=self.controller.current_card_index + 1,
            total=len(self.controller.flashcards_data)
        ))
        self.controller.is_card_flipped = False
        self.card_frame.configure(fg_color="#1f538d") 
        self.btn_know.configure(state="normal")
        self.btn_dont_know.configure(state="normal")
        self.result_label.configure(text="")

    def flip_card(self, event):
        if not self.controller.flashcards_data:
            return

        lang = self.controller.language
        texts = L10N[lang]
        card = self.controller.flashcards_data[self.controller.current_card_index]
        
        if not self.controller.is_card_flipped:
            self.card_label.configure(text=card['answer'])
            self.hint_label.configure(text=texts["hint_flipped"])
            self.controller.is_card_flipped = True
            self.card_frame.configure(fg_color="gray")
        else:
            self.card_label.configure(text=card['question'])
            self.hint_label.configure(text=texts["hint_click_to_flip"].format(
                current=self.controller.current_card_index + 1,
                total=len(self.controller.flashcards_data)
            ))
            self.controller.is_card_flipped = False
            self.card_frame.configure(fg_color="#1f538d")

    def answer_card(self, knew_it):
        if self.controller.current_card_index < len(self.controller.flashcards_data):
            self.controller.user_answers.append(knew_it)
            
            lang = self.controller.language
            texts = L10N[lang]
            
            feedback = texts["feedback_know"] if knew_it else texts["feedback_dont_know"]
            self.result_label.configure(text=feedback)
            
            # Odkryj na chwilę odpowiedź
            card = self.controller.flashcards_data[self.controller.current_card_index]
            self.card_label.configure(text=card['answer'])
            self.hint_label.configure(text=texts["answer_txt"].upper())
            
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

        self.label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto Medium", 30))
        self.label.pack(pady=20)

        self.score_label = ctk.CTkLabel(self.result_frame, text="", font=("Roboto", 20))
        self.score_label.pack(pady=10)

        self.restart_btn = ctk.CTkButton(self.result_frame, text="", command=self.back_to_main)
        self.restart_btn.pack(pady=30)

        # NAPRAWIONY PRZYCISK: Używa nowej metody resetującej stan
        self.upload_btn = ctk.CTkButton(self.result_frame, text="", command=self.controller.reset_state_and_show_upload)
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
        # Ustawienie fiszek na pierwszej karcie
        self.controller.frames[MainAppView].load_flashcard()

if __name__ == "__main__":
    app = EduApp()
    app.mainloop()