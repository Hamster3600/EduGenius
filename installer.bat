@echo off

echo ===========================================================
echo   ROZPOCZYNAM INSTALACJE EDUGENIUS
echo ===========================================================

python installer.py

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