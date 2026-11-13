"""Inventario de artigos + contexto literal de datas-chave. So le, nao escreve."""
import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from lexgraph.corpus.canonical import normalizar_texto

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
RAW = Path("data/raw")

SELETORES = ["p.oj-ti-art", "p.stitle-article-norm", ".ti-art"]
RE_ART = re.compile(r"^«?Artigo\s+(\d+)(?:\.o|º|°)?(?:-([A-Z]))?")
DATAS = ["2 de dezembro de 2027", "2 de agosto de 2028", "2 de agosto de 2027",
         "2 de agosto de 2026", "2 de fevereiro de 2025",
         "2 de dezembro de 2026", "27 de julho de 2026"]


def titulos(soup):
    for sel in SELETORES:
        els = soup.select(sel)
        if els:
            return sel, els
    return None, []


for f in sorted(RAW.glob("*.html")):
    soup = BeautifulSoup(f.read_bytes(), "lxml")
    sel, els = titulos(soup)
    print(f"\n{'='*72}\n{f.name}\nseletor={sel}  titulos={len(els)}\n{'='*72}")

    nums = []
    for el in els:
        m = RE_ART.match(normalizar_texto(el.get_text()))
        if m:
            nums.append(m.group(1) + (f"-{m.group(2)}" if m.group(2) else ""))
    print("numeros:", ", ".join(nums) if nums else "(nenhum reconhecido)")

    alvo = [el for el in els
            if normalizar_texto(el.get_text()).startswith("Artigo 113")]
    print("\n--- Artigo 113 ---")
    if alvo:
        el = alvo[0]
        partes = [normalizar_texto(el.get_text())]
        for sib in el.find_next_siblings():
            t = normalizar_texto(sib.get_text())
            if RE_ART.match(t) and not t.startswith("Artigo 113"):
                break
            if t:
                partes.append(t)
            if len(partes) > 25:
                break
        if len(partes) < 2 and el.parent is not None:
            partes = [normalizar_texto(el.parent.get_text())[:3000]]
        print("\n".join(partes))
    else:
        print("NAO encontrado entre os titulos.")

    texto = normalizar_texto(soup.get_text(" ", strip=True))
    print("\n--- contexto das datas ---")
    for d in DATAS:
        pos = [m.start() for m in re.finditer(re.escape(d), texto)]
        print(f"\n{d!r}: {len(pos)} ocorrencias")
        for p in pos[:6]:
            print("   ..." + texto[max(0, p - 200):p + 130] + "...")
