# EduGenius - Lokalny Asystent Nauki z LLM

## Widok główny

![widok_główny](https://github.com/Hamster3600/EduGenius/blob/main/img/main_view.png)

## Podsumowanie

![podsumowanie](https://github.com/Hamster3600/EduGenius/blob/main/img/summary_view.png)

## Fiszki
![fiszki_pytanie](https://github.com/Hamster3600/EduGenius/blob/main/img/flashcard_1.png)
![fiszki_odpowiedź](https://github.com/Hamster3600/EduGenius/blob/main/img/flashcard_2.png)

## Wynik fiszek

![wynik_sesji_nauki](https://github.com/Hamster3600/EduGenius/blob/main/img/end_of_study_mode.png)

## Wyjaśnienie Projektu

EduGenius to w pełni lokalna aplikacja desktopowa zrobiona za pomocą biblioteki CustomTkinter do automatycznego generowania notatek i interaktywnych fiszek z dokumentów. Wykorzystuje lokalny model LLM za pomocą llama-cpp-python oraz zaawansowane biblioteki SpaCy i Sumy do skodensowania i porządkowania wiedzy.

## Kluczowe Funkcje

- **Obsługa Formatów**: Analiza plików .txt, .pdf, .docx, i .odt.
- **Podsumowanie LLM**: Generowanie zwięzłego podsumowania za pomocą lekkiego lokalnego modelu Qwen2.5-1.5B.
- **Fiszki Cloze Deletion**: Automatyczne tworzenie interaktywnych fiszek na podstawie kluczowych terminów.
- **Tryb Nauki**: Interaktywny widok fiszek z funkcją śledzenia postępów.

## Instalacja Automatyczna

Dla szybkiej instalacji użyj gotowych skryptów instalacyjnych:

  ### Windows
  
  Uruchom plik `installer.bat` jako administrator.
  
  ### Linux/macOS
  
  W terminalu przejdź do folderu projektu i uruchom:
  
  ```
  bash
  chmod +x installer.sh
  ./installer.sh
  ```

## Instalacja Ręczna

Instalacji ręcznej zaleca się używać tylko w tedy kiedy automatyczna zawiedzie.

  ### 1. Wymagania wstępne
  
  - **Python**: Zainstalowany w wersji 3.9 - 3.11. Upewnij się, że jest dodany do PATH.
  
  ### 2. Procedura instalacji
  
  Otwórz CMD, PowerShell lub Terminal i przejdź do folderu projektu.
  
  #### Krok 2.1: Instalacja Bibliotek Python
  
  Zainstaluj wszystkie wymagane pakiety:
  
  ```
  bash
  # aktualizacja pip
  python -m pip install --upgrade pip
  
  # instalacja wszystkich bibliotek z requirements.txt
  python -m pip install -r requirements.txt --no-cache-dir
  ```


#### 2.2: Instalacja Silnika llama

Ten krok jest kluczowy dla uruchomienia AI. Wybierz odpowiednią komendę dla Twojego sprzętu.

  **2.2.1 Instalacja standardowa (dla nowoczesnych CPU z AVX2):**
  
  ```
  bash
  python -m pip install llama-cpp-python
  ```
  
  **2.2.2 Jeśli jest błąd ładowania LLM / brak AVX2:**
  
  Jeśli po uruchomieniu aplikacji zobaczysz błąd że LLM nie działa, to Twoje CPU nie wspiera AVX2. Przez co nie możesz korzystać z AI, więc aplikacja skorzysta z fallback'u.
  
#### Krok 2.3: Pobieranie Modeli Językowych

Pobierz modele SpaCy oraz pakiety NLTK:

```
bash
# modele SpaCy
python -m spacy download pl_core_news_sm
python -m spacy download en_core_web_sm

# pakiety NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('snowball_data');"
```

#### Krok 2.4: Pobieranie Modelu LLM (plik GGUF, ~1 GB)

Pobierz plik modelu AI do głównego katalogu projektu. Musi on mieć nazwę: [`qwen2.5-1.5b-instruct-q4_k_m.gguf`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf).

```
bash
curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

## Uruchomienie Aplikacji

Uruchom plik `main.py` z konsoli:

```
bash
python3 main.py
```

## Privacy Policy

Politykę Prywatności dla EduGenius znajdziesz pod adresem [https://hamster3600.github.io/EduGenius/LICENSE](https://github.com/Hamster3600/EduGenius/blob/main/LICENSE). 
