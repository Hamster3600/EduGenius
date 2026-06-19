#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

trap 'echo -e "\n${NC}WYNIK: ${RED}BŁĄD${NC}\n===========================================================\n Instalacja przerwana - coś poszło nie tak.\n Spróbuj jeszcze raz lub ręcznie zainstaluj brakujące rzeczy.\n===========================================================\n${NC}"; exit 1' ERR

echo -e "${BLUE}EduGenius${NC} - Witam w automatycznym installerze"
echo -e "===========================================================${NC}"

if [[ ! -f "main.py" ]]; then
    echo -e "${RED}BŁĄD:${NC} Nie ma pliku main.py w tym folderze!"
    echo -e "${NC}Przenieś się do folderu z aplikacją i odpal jeszcze raz.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}BŁĄD:${NC} Python3 nie jest zainstalowany."
    echo -e "${NC}Zainstaluj go wpisując: ${YELLOW}sudo apt install python3${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}BŁĄD:${NC} Pip3 nie jest zainstalowany."
    echo -e "${NC}Zainstaluj go wpisując: ${YELLOW}sudo apt install python3-pip${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/4] Instaluję zależności systemowe (Tkinter i kompilatory C++)...${NC}"
sudo apt-get update -qq
sudo apt-get install -y python3-tk build-essential python3-dev

echo -e "${YELLOW}[2/4] Instaluję biblioteki Pythona...${NC}"
pip3 install --upgrade pip --break-system-packages 
pip3 install --break-system-packages \
    customtkinter \
    pypdf \
    python-docx \
    "odfpy==1.4.1" \
    tk \
    sumy \
    nltk \
    spacy \
    llama-cpp-python \
    tqdm \
    requests \
    packaging

echo -e "${YELLOW}[3/4] Pobieram modele językowe SpaCy...${NC}"
python3 -m spacy download pl_core_news_sm
python3 -m spacy download en_core_web_sm

echo -e "${YELLOW}Pobieram pakiety NLTK...${NC}"
python3 -m nltk.downloader punkt -q
python3 -m nltk.downloader punkt_tab -q

MODEL="qwen2.5-1.5b-instruct-q4_k_m.gguf"
if [[ ! -f "$MODEL" ]]; then
    echo -e "${YELLOW}[4/4] Pobieram model \"qwen2.5 1.5b\" (~1 GB)...${NC}"
    wget -q --show-progress \
    https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf \
    -O "$MODEL"
else
    echo -e "${GREEN}[4/4] Model LLM już jest pobrany. Pomijam.${NC}"
fi

echo ""
echo -e "${NC}WYNIK: ${GREEN}POWODZENIE${NC}"
echo "==========================================================="
echo " WSZYSTKO GOTOWE!"
echo " Dla uruchomienia wpisz: python3 main.py"
echo "==========================================================="
echo -e "${NC}"

exit 0