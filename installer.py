import sys
import subprocess
import os
import urllib.request
from typing import List

PACKAGES: List[str] = [
    "customtkinter", "pypdf", "python-docx", "odfpy==1.4.1", 
    "sumy", "nltk", "spacy", "packaging", 
    "llama-cpp-python", "tqdm", "requests"
]
SPACY_MODELS: List[str] = ['pl_core_news_sm', 'en_core_web_sm']
GGUF_URL: str = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
GGUF_FILENAME: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf"

def run_pip(args: List[str], step_name: str) -> bool:
    """Uruchamia Pip w subprocessie."""
    try:
        print(f"\n--- Rozpoczynam: {step_name} ---")
        subprocess.run([sys.executable, "-m", "pip"] + args, check=True, stdout=sys.stdout, stderr=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[BLAD KRYTYCZNY] {step_name} nie powiodl sie. Szczegoly ponizej.", file=sys.stderr)
        print(e, file=sys.stderr)
        return False

def download_file(url: str, filename: str):
    """Pobiera plik z URL, pokazując postęp."""
    try:
        from tqdm import tqdm
        print(f"Pobieram model LLM ({filename}) [~1 GB]...")

        def hook(t):
            last_b = [0]
            def inner(b=1, bsize=1, tsize=None):
                if tsize is not None:
                    t.total = tsize
                t.update((b - last_b[0]) * bsize)
                last_b[0] = b
            return inner

        with tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1) as t:
            urllib.request.urlretrieve(url, filename, reporthook=hook(t))
        print("Model LLM pobrany pomyslnie.")
        return True
    except Exception as e:
        print(f"\n[BLAD KRYTYCZNY] Nie udalo sie pobrac modelu LLM. Sprawdz polaczenie internetowe.", file=sys.stderr)
        print(e, file=sys.stderr)
        return False

def main():
    if not run_pip(["install", "--upgrade", "pip"], "Aktualizacja PIP"): return 1
    
    print("\n[2/4] Instalacja glownych bibliotek i silnika llama-cpp-python...")
    pip_args = ["install"] + PACKAGES + ["--prefer-binary", "--extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cpu"]
    if not run_pip(pip_args, "Instalacja bibliotek"): return 1
    
    print("\n[3/4] Pobieram modele jezykowe SpaCy...")
    for model in SPACY_MODELS:
        print(f"Pobieram model SpaCy: {model}...")
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", model, "-q"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"BŁĄD podczas pobierania modelu SpaCy: {model}.", file=sys.stderr)
            return 1

    print("\n[3/4] Pobieram pakiety NLTK...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        print("Pakiety NLTK pobrane pomyślnie.")
    except Exception as e:
        print(f"BŁĄD podczas pobierania NLTK: {e}", file=sys.stderr)
        return 1
        
    print("\n[4/4] Pobieranie modelu LLM...")
    if os.path.exists(GGUF_FILENAME):
        print("Model LLM juz istnieje. Pomijam pobieranie.")
    elif not download_file(GGUF_URL, GGUF_FILENAME):
        return 1

    print("\n===========================================================")
    print("INSTALACJA ZAKONCZONA POMYSLNIE!")
    print("Uruchom program wpisujac: python main.py")
    print("===========================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())