"""
Parser real do corpus EUR-Lex — Versão Estruturalmente Segura (SHACL-Compliant).
Garante 1 versão por unidade, usando a data base do documento, evitando sobreposições.
"""
from __future__ import annotations

import re
import warnings
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from lexgraph.corpus.schema import RegistoCorpus, TipoUnidade, Vigencia, Aplicacao, Fonte, Lineage

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

RE_ARTIGO = re.compile(r"^\s*(?:Artigo|Article)\s+([0-9]+[A-Za-z]?\.?)\b", re.IGNORECASE)
RE_PARAGRAFO = re.compile(r"^\s*([0-9]+)\.\s+")

def extrair_numero_artigo(texto: str) -> Optional[str]:
    m = RE_ARTIGO.match(texto)
    if not m:
        return None
    ref = m.group(1).strip().replace(".", "").replace("º", "").replace("°", "")
    if ref[-1:].lower() == "o" and ref[:-1].isdigit():
        return ref[:-1]
    if len(ref) > 1 and ref[-1].isalpha() and ref[:-1].isdigit():
        return f"{ref[:-1]}-{ref[-1].upper()}"
    return ref

def extrair_numero_paragrafo(texto: str) -> Optional[str]:
    m = RE_PARAGRAFO.match(texto)
    return m.group(1) if m else None

def _get_base_date(celex: str) -> str:
    """Retorna a data base da versão do documento, garantindo consistência temporal."""
    if "02024R1689-20260727" in celex:
        return "2026-07-27"  # Versão consolidada
    elif "32026R1744" in celex:
        return "2026-07-27"  # Regulamento Omnibus
    else:
        return "2024-08-01"  # Regulamento AI Act original

def _fonte(celex: str, url: str) -> Fonte:
    return Fonte(
        ato_id=f"reg_{celex[1:5]}_{celex[5:]}" if celex[0] == "3" else f"cons_{celex[1:]}",
        celex=celex,
        eli=f"https://eur-lex.europa.eu/eli/reg/{celex[1:5]}/{celex[5:]}/oj",
        url_oficial=url,
        lingua="PT",
    )

def _lineage(fonte_hash: str) -> Lineage:
    return Lineage(
        pipeline_versao="0.2.0",
        metodo_extracao="lxml",
        fonte_hash=fonte_hash,
        extractor_versao="bs4+lxml",
    )

def parse_html(html: str, celex: str, url: str, fonte_hash: str) -> list[RegistoCorpus]:
    soup = BeautifulSoup(html, "lxml")
    registos: list[RegistoCorpus] = []
    
    artigo_atual_num: Optional[str] = None
    paragrafo_atual_num: Optional[str] = None
    
    # Data consistente para todo o documento
    data_base = _get_base_date(celex)
    data_obj = datetime.strptime(data_base, "%Y-%m-%d").date()
    
    for el in soup.find_all(["p", "div"]):
        texto_cru = el.get_text(separator=" ", strip=True)
        if not texto_cru:
            continue

        if RE_ARTIGO.match(texto_cru):
            num = extrair_numero_artigo(texto_cru)
            if num:
                artigo_atual_num = num
                paragrafo_atual_num = None
                uid = f"art_{num.lower()}"
                
                registos.append(RegistoCorpus(
                    unidade_id=uid,
                    tipo=TipoUnidade.ARTIGO,
                    parent_id=None,
                    ordem=len(registos),
                    rotulo=f"Artigo {num}.º",
                    texto=texto_cru,
                    vigencia=Vigencia(inicio=data_obj, fim=None),
                    aplicacao=Aplicacao(inicio=data_obj),
                    fonte=_fonte(celex, url),
                    lineage=_lineage(fonte_hash),
                ))
            continue

        if artigo_atual_num and RE_PARAGRAFO.match(texto_cru):
            num_par = extrair_numero_paragrafo(texto_cru)
            if num_par:
                paragrafo_atual_num = num_par
                uid = f"art_{artigo_atual_num.lower()}_par_{num_par}"
                
                registos.append(RegistoCorpus(
                    unidade_id=uid,
                    tipo=TipoUnidade.NUMERO,
                    parent_id=f"art_{artigo_atual_num.lower()}",
                    ordem=len(registos),
                    rotulo=f"Art. {artigo_atual_num}.º, n.º {num_par}",
                    texto=texto_cru,
                    vigencia=Vigencia(inicio=data_obj, fim=None),
                    aplicacao=Aplicacao(inicio=data_obj),
                    fonte=_fonte(celex, url),
                    lineage=_lineage(fonte_hash),
                ))
            continue

    n_artigos = sum(1 for r in registos if r.tipo is TipoUnidade.ARTIGO)
    if n_artigos == 0:
        raise ValueError(f"Parser falhou: 0 artigos encontrados em {celex}.")

    return registos
