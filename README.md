# 🧠 EduGenius - Lokalny Asystent Nauki z LLM

## 📖 Wyjaśnienie Projektu

EduGenius to w pełni lokalna aplikacja desktopowa (CustomTkinter) do automatycznego generowania notatek i interaktywnych fiszek z dokumentów (TXT, PDF, DOCX, ODT). Wykorzystuje lokalny model LLM (za pomocą llama-cpp-python) oraz zaawansowane biblioteki NLP (SpaCy, Sumy) do ekstrakcji i porządkowania wiedzy.

## 🌟 Kluczowe Funkcje

- **Obsługa Formatów**: Analiza plików .txt, .pdf, .docx, i .odt.
- **Podsumowanie LLM**: Generowanie zwięzłego podsumowania za pomocą lekkiego lokalnego modelu Qwen2.5-1.5B-Instruct-Q4_K_M.gguf.
- **Fiszki Cloze Deletion**: Automatyczne tworzenie interaktywnych fiszek (luki w tekście) na podstawie kluczowych terminów (za pomocą SpaCy).
- **Tryb Nauki**: Interaktywny widok fiszek z funkcją śledzenia postępów.


## 🚀 Instalacja Automatyczna

Dla szybkiej instalacji użyj gotowych skryptów instalacyjnych:

### Windows

Uruchom plik `installer.bat` jako administrator (kliknij prawym przyciskiem myszy i wybierz "Uruchom jako administrator").

### Linux/macOS

W terminalu przejdź do folderu projektu i uruchom:

```
bash
chmod +x installer.sh
./installer.sh
```

## 🔧 Instalacja Ręczna (Krok po Kroku)

Instalacji ręcznej zaleca się używać tylko w tedy kiedy automatyczna zawiedzie.

### 1. Wymagania wstępne

- **Python**: Zainstalowany w wersji 3.9 - 3.11. Upewnij się, że dodano go do PATH podczas instalacji.

### 2. Procedura instalacji

Otwórz terminal (CMD, PowerShell, lub Terminal) i przejdź do głównego folderu projektu.

#### Krok 2.1: Instalacja Bibliotek Python

Zainstaluj wszystkie wymagane pakiety:

```
bash
# Aktualizacja PIP
python -m pip install --upgrade pip

# Instalacja wszystkich bibliotek z pliku requirements.txt
python -m pip install -r requirements.txt --no-cache-dir
```


#### Krok 2.2: Ostateczna Instalacja Silnika LLM (llama-cpp-python)

Ten krok jest kluczowy dla uruchomienia AI. Wybierz odpowiednią komendę dla Twojego sprzętu.

**A. Instalacja standardowa (dla nowoczesnych CPU z AVX2):**

```
bash
python -m pip install llama-cpp-python
```

**B. Jeśli jest błąd ładowania LLM / brak AVX2:**

Jeśli po uruchomieniu aplikacji zobaczysz błąd, że LLM nie działa, to Twoje CPU nie wspiera AVX2. Przez co nie możesz korzystać z AI do podsumowania oraz fiszek.

#### Krok 2.3: Pobieranie Modeli Językowych (NLP)

Pobierz modele SpaCy (dla fiszek) oraz pakiety NLTK (dla podsumowań LSA):

```
bash
# Modele SpaCy
python -m spacy download pl_core_news_sm
python -m spacy download en_core_web_sm

# Pakiety NLTK (dla Stemmera i Stop-words)
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('snowball_data');"
```

#### Krok 2.4: Pobieranie Modelu LLM (plik GGUF, ~1 GB)

Pobierz plik modelu AI do głównego katalogu projektu. Musi on mieć nazwę: [`qwen2.5-1.5b-instruct-q4_k_m.gguf`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf).

```
bash
# Najprostsza komenda dla Windows/Linux/macOS
curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Te skrypty automatycznie zainstalują wszystkie biblioteki, modele językowe i pobierą model LLM. Jeśli instalacja automatyczna się nie powiedzie, skorzystaj z instalacji ręcznej powyżej.

## ▶️ Uruchomienie Aplikacji

Uruchom plik `main.py` z konsoli:

```
bash
python main.py
```

## Privacy Policy

Politykę Prywatności dla EduGenius znajdziesz pod adresem [https://hamster3600.github.io/EduGenius/LICENSE](https://github.com/Hamster3600/EduGenius/blob/main/LICENSE). 
