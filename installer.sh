#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#komunikat o błędzie
trap 'echo -e "\n${NC}WYNIK: ${RED}BŁĄD${NC}\n===========================================================\n Instalacja przerwana - coś poszło nie tak.\n Spróbuj jeszcze raz lub ręcznie zainstaluj brakujące rzeczy.\n===========================================================\n${NC}"; exit 1' ERR

#komunikat powitalny
echo -e "${BLUE}EduGenius${NC} - Witam w automatycznym installererze${NC}"
echo -e "${NC}===========================================================${NC}"

#sprawdzenie dir
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}BŁĄD: ${NC}Nie ma pliku main.py w tym folderze!${NC}"
    echo -e "${NC}Przenieś się do folderu z aplikacją i odpal jeszcze raz.${NC}"
    exit 1
fi

#pobieranie bibliotek
echo -e "${YELLOW}Instaluję biblioteki pythona...${NC}"
pip3 install --upgrade pip --break-system-packages 
pip3 install --break-system-packages \
    customtkinter \
    pypdf \
    python-docx \
    "odfpy==1.4.1" \
    sumy \
    nltk \
    spacy \
    llama-cpp-python \
    --no-cache-dir

# pobieranie stacy i nltk
echo -e "${YELLOW}Pobieram modele językowe...${NC}"
set +e
(python3 - <<EOF
    import nltk
    import sys
    import subprocess
    
    MODELS = ['pl_core_news_sm', 'en_core_web_sm']
    
    for model in MODELS:
        print(f"Pobieranie spaCy modelu: {model}...", file=sys.stderr)
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", model, "--break-system-packages"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            subprocess.run([sys.executable, "-m", "spacy", "download", model], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Pobieranie pakietów NLTK...", file=sys.stderr)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
EOF
) >/dev/null 2>&1 || true
set -e

#pobieranie modelu
MODEL="qwen2.5-1.5b-instruct-q4_k_m.gguf"
if [[ ! -f "$MODEL" ]]; then
    echo -e "${YELLOW}Pobieram model \"qwen2.5 1.5b\" (~1 GB)...${NC}"
    wget -q --show-progress \
    https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf \
    -O "$MODEL"
else
    echo -e "${GREEN}Model już jest zainstalowany.${NC}"
fi

# ostatni kommnunikat
echo ""
echo -e "${NC}WYNIK: ${GREEN}POWODZENIE${NC}"
echo "==========================================================="
echo " WSZYSTKO GOTOWE!"
echo " Dla uruchomienia: \"python3 main.py\""
echo "==========================================================="
echo -e "${NC}"

exit 0