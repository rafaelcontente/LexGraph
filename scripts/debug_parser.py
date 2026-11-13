"""Diagnostico: porque e que a procura de texto falha nos HTML do EUR-Lex."""
import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suprimir o aviso
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

html_path = Path("data/raw/reg_2024_1689_original.html")
if not html_path.exists():
    print("Ficheiro não encontrado. Corre primeiro o downloader.")
else:
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    
    p_tags = soup.find_all("p", class_=True)
    print(f"Total de tags <p> com classe encontradas: {len(p_tags)}")
    
    classes_vistas = set()
    for p in p_tags[:15]:
        classes = p.get("class", [])
        classes_vistas.update(classes)
        texto = p.get_text(strip=True)[:60]
        print(f"  Classes: {str(classes):<25} | Texto: {texto}")
    
    print(f"\nLista de classes únicas em <p>: {classes_vistas}")