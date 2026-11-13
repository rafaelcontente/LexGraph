"""Diagnostico: porque e que a procura de texto falha nos HTML do EUR-Lex."""
import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from lexgraph.corpus.canonical import normalizar_texto

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
RAW = Path("data/raw")
DATAS = ["2 de dezembro de 2027", "2 de agosto de 2028", "2 de agosto de 2026"]

for f in sorted(RAW.glob("*.html")):
    soup = BeautifulSoup(f.read_bytes(), "lxml")
    cru = soup.get_text(" ", strip=True)
    limpo = normalizar_texto(cru)

    print(f"\n{'='*66}\n{f.name}\n{'='*66}")
    print("idioma (contagem normalizada):",
          {p: limpo.count(p) for p in ("Artigo", "Article", "Artikel")})
    print(f"NBSP no texto cru: {cru.count(chr(160))}")
    print(f"'Artigo '  cru={cru.count('Artigo ')}  normalizado={limpo.count('Artigo ')}")

    tits = soup.select("p.oj-ti-art")
    print(f"\ntitulos <p class=oj-ti-art>: {len(tits)}")
    for el in tits[:3]:
        print("   repr cru:", repr(el.get_text()))
        print("   repr limpo:", repr(normalizar_texto(el.get_text())))

    print("\nprocura por '113' em nos curtos:")
    n = 0
    for el in soup.find_all(string=re.compile("113")):
        s = normalizar_texto(str(el))
        if len(s) < 60:
            print(f"   {s!r}  <- <{el.parent.name} class={el.parent.get('class')}>")
            n += 1
            if n >= 3:
                break
    if n == 0:
        print("   nenhum no curto contem '113'")

    print("\ndatas:")
    for d in DATAS:
        print(f"   {d!r}: cru={cru.count(d)}  normalizado={limpo.count(d)}")
