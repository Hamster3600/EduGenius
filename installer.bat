@echo off
chcp 65001 >nul
echo ===========================================================
echo   ROZPOCZYNAM INSTALACJE EDUGENIUS
echo ===========================================================

echo.
echo [KROK 0] Sprawdzam, czy zainstalowany jest Python 3.14...

py -3.14 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.14 nie zostal znaleziony.
    echo Probuje pobrac i zainstalowac automatycznie przez winget...
    echo.
    
    winget install Python.Python.3.14 --accept-package-agreements --accept-source-agreements --silent
    
    if %errorlevel% neq 0 (
        echo.
        echo [BLAD] Nie udalo sie zainstalowac Pythona 3.14 przez winget.
        echo Sprobuj zainstalowac go recznie ze strony python.org
        pause
        exit /b 1
    )
    
    echo.
    echo ===========================================================
    echo Python 3.14 zostal pomyslnie zainstalowany!
    echo UWAGA: System zaktualizowal zmienne srodowiskowe.
    echo MUSISZ ZAMKNAC TO OKNO I URUCHOMIC SKRYPT PONOWNIE!
    echo ===========================================================
    pause
    exit /b 0
) else (
    echo Znaleziono Pythona 3.14. Przechodze do dalszej instalacji.
)

echo.
echo [KROK 1] Uruchamiam skrypt instalacyjny Pythona...
py -3.14 installer.py

if %errorlevel% neq 0 (
    echo.
    echo [BLAD KRYTYCZNY] Instalacja przez skrypt Python zawiodla.
    pause
    exit /b 1
)

echo.
echo ===========================================================
echo   KONIEC
echo ===========================================================
pause
exit /b 0