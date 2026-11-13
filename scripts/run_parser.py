"""
Parser de corpus — LexGraph v1 (Módulo 0, Fase 2).
data/raw/*.html  ->  data/interim/corpus_v1.jsonl
"""
import json
import sys
from pathlib import Path

from lexgraph.corpus.parser import parse_html
from lexgraph.corpus.canonical import sha256_texto

RAW = Path("data/raw")
OUT = Path("data/interim/corpus_v1.jsonl")

# Mapeamento manual: nome do ficheiro -> CELEX + URL oficial
ATOS = {
    "reg_2024_1689_original.html": {
        "celex": "32024R1689",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:32024R1689",
    },
    "reg_2024_1689_cons_20260727.html": {
        "celex": "02024R1689-20260727",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:02024R1689-20260727",
    },
    "reg_2026_1744.html": {
        "celex": "32026R1744",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=OJ:L_202601744",
    },
}


def main() -> int:
    ficheiros = sorted(RAW.glob("*.html"))
    if not ficheiros:
        print(f"✗ Sem HTML em {RAW}/. Corre primeiro: python -m lexgraph.corpus.descarregar", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    todos = []

    for f in ficheiros:
        info = ATOS.get(f.name)
        if not info:
            print(f"⚠ {f.name} não está no mapeamento ATOS — a ignorar", file=sys.stderr)
            continue
        
        html = f.read_text(encoding="utf-8", errors="replace")
        fonte_hash = sha256_texto(html)
        
        registos = parse_html(html, info["celex"], info["url"], fonte_hash)
        todos.extend(registos)
        print(f"  {info['celex']:<20} {len(registos):>5} registos")

    with OUT.open("w", encoding="utf-8") as fh:
        for r in todos:
            fh.write(r.model_dump_json() + "\n")

    print(f"\n✓ {len(todos)} registos em {OUT}")
    
    # Gate simples: pelo menos 100 artigos no original
    n_artigos = sum(1 for r in todos if r.tipo.value == "artigo" and "2024" in r.fonte.celex)
    if n_artigos < 100:
        print(f"✗ Gate falhou: esperado >=100 artigos no 2024/1689, obtido {n_artigos}", file=sys.stderr)
        return 2
    print(f"✓ Gate OK: {n_artigos} artigos no regulamento base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
