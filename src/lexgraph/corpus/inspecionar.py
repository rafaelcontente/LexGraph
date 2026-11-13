"""Diagnostico da estrutura HTML do EUR-Lex. So le, nao escreve.

Objetivo: descobrir a convencao de markup real antes de escrever o parser,
e responder a pergunta aberta 'o art. 113.o esta na consolidada?'.
"""
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

RAW = Path(__file__).resolve().parents[3] / "data" / "raw"
DATAS = ["2 de dezembro de 2027", "2 de agosto de 2028",
         "27 de julho de 2026", "2 de agosto de 2026",
         "2 de fevereiro de 2025", "2 de dezembro de 2026"]


def inspecionar(f: Path) -> None:
    soup = BeautifulSoup(f.read_bytes(), "lxml")
    print(f"\n{'='*70}\n{f.name}  ({f.stat().st_size:,} bytes)\n{'='*70}")

    classes = Counter()
    for el in soup.find_all(True):
        c = " ".join(el.get("class", [])) or "(sem classe)"
        classes[(el.name, c)] += 1
    print("\n-- 12 combinacoes (tag, classe) mais frequentes --")
    for (tag, c), n in classes.most_common(12):
        print(f"{n:6d}  <{tag} class='{c}'>")

    arts = [el for el in soup.find_all(True)
            if el.get_text(strip=True).startswith("Artigo ")
            and len(el.get_text(strip=True)) < 40]
    print(f"\n-- candidatos a titulo de artigo: {len(arts)} --")
    for el in arts[:6]:
        print(f"  <{el.name} class='{' '.join(el.get('class', []))}' "
              f"id='{el.get('id', '')}'> {el.get_text(strip=True)!r}")

    print("\n-- Artigo 113.o --")
    hits = [el for el in arts if "113" in el.get_text()]
    if hits:
        for el in hits:
            print(f"  ENCONTRADO id='{el.get('id', '')}': {el.get_text(strip=True)!r}")
    else:
        print("  NAO encontrado entre os titulos.")

    texto = soup.get_text(" ", strip=True)
    print("\n-- contagem de datas-chave no texto completo --")
    for d in DATAS:
        print(f"  {texto.count(d):4d}  {d!r}")


if __name__ == "__main__":
    ficheiros = sorted(RAW.glob("*.html"))
    if not ficheiros:
        print("Nenhum HTML em data/raw/. Corre primeiro: python -m lexgraph.corpus.descarregar")
    for f in ficheiros:
        inspecionar(f)
