@echo off
setlocal enabledelayedexpansion

REM Nazwa pliku do logowania bledow
set "ERROR_LOG=installer_error.log"

REM Funkcja do sprawdzania bledu i przekierowania do trap
:check_error
if %errorlevel% neq 0 (
    echo.
    echo Wystapil blad. Analiza logu bledow...
    goto :error_trap
)
goto :eof

REM --- Funkcja obslugi bledow ---
:error_trap
echo.
echo ===========================================================
echo WYNIK: BLAD
echo Instalacja przerwana - cos poszlo nie tak.
echo -----------------------------------------------------------
echo SZCZEGOLY OSTATNIEGO BLEDU (pip/curl):
echo -----------------------------------------------------------

REM Wyswietl log bledu, jesli istnieje
if exist "%ERROR_LOG%" (
    type "%ERROR_LOG%"
    del "%ERROR_LOG%"
) else (
    echo Brak szczegolowego logu bledow (lub blad wystapil przed komendami pip/curl).
)

echo -----------------------------------------------------------
echo Sprawdz komunikaty powyzej i sprobuj instalacji recznej (zobacz README.md).
echo ===========================================================
echo.
pause
exit /b 1

REM --- Komunikat powitalny ---
echo.
echo EduGenius - Witamy w automatycznym instalatorze
echo ===========================================================

REM --- Sprawdzenie pliku main.py ---
if not exist "main.py" (
    echo BLAD: Nie ma pliku main.py w tym folderze!
    echo Przenies sie do folderu z aplikacja i uruchom ponownie.
    goto :error_trap
)

REM --- Weryfikacja Pythona (i Pip) ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo BLAD: Python nie jest zainstalowany lub nie jest w zmiennej PATH.
    goto :error_trap
)

REM --- INSTALACJA GLOWNYCH BIBLIOTEK (Bez kompilacji) ---
echo Instaluje biblioteki Pythona (etap 1/2)...

pip install --upgrade pip 2> "%ERROR_LOG%"
call :check_error

pip install \
    customtkinter \
    pypdf \
    python-docx \
    "odfpy==1.4.1" \
    sumy \
    nltk \
    spacy \
    packaging \
    --no-cache-dir 2> "%ERROR_LOG%"
call :check_error


REM --- INSTALACJA LLAMA-CPP-PYTHON (Wymaga kompilatora) ---
echo.
echo Instaluje llama-cpp-python (etap 2/2 - moze potrwac dluzej)...
pip install llama-cpp-python --no-cache-dir 2> "%ERROR_LOG%"
if %errorlevel% neq 0 (
    echo.
    echo -----------------------------------------------------------
    echo OSTRZEZENIE: Instalacja llama-cpp-python zawiodla.
    echo Ten pakiet CZĘSTO wymaga narzedzi kompilacji (np. Visual Studio Build Tools).
    echo Aplikacja uruchomi sie, ale bedzie uzywac wolniejszego podsumowania LSA.
    echo Szczegoly bledu kompilacji:
    type "%ERROR_LOG%" 2>nul
    del "%ERROR_LOG%" 2>nul
    echo -----------------------------------------------------------
) else (
    del "%ERROR_LOG%" 2>nul
)


REM --- Pobieranie modeli spaCy i NLTK ---
echo.
echo Pobieram modele jezykowe (Spacy i NLTK)...

REM Spacy: Użycie -q by ograniczyć spam w logu i -m by nie ładować spaCy jako modułu

echo Instaluje model Spacy: pl_core_news_sm...
python -m spacy download pl_core_news_sm -q
echo Instaluje model Spacy: en_core_web_sm...
python -m spacy download en_core_web_sm -q

REM -- NLTK --
echo Instaluje pakiety NLTK...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"


REM --- Pobieranie modelu LLM ---
set "MODEL=qwen2.5-1.5b-instruct-q4_k_m.gguf"
set "URL=https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/%MODEL%"

echo.
if not exist "!MODEL!" (
    echo Pobieram model "!MODEL!" (~1 GB)...
    
    REM Uzywamy CURL do pobierania. Flaga -f (fail) jest kluczowa dla errorlevel.
    curl -f -L -o "!MODEL!" "!URL!" -# 2> "%ERROR_LOG%"
    
    if %errorlevel% neq 0 (
        echo.
        echo BLAD: Pobieranie modelu LLM za pomoca curl nie powiodlo sie.
        echo Sprawdz polaczenie internetowe lub pobierz plik recznie (link w README.md).
        goto :error_trap
    )
    del "%ERROR_LOG%" 2>nul
    
) else (
    echo Model juz jest zainstalowany.
)

REM --- Komunikat koncowy ---
echo.
echo WYNIK: POWODZENIE
echo ===========================================================
echo WSZYSTKO GOTOWE!
echo Dla uruchomienia: "python main.py"
echo ===========================================================
echo.
pause

endlocal
exit /b 0