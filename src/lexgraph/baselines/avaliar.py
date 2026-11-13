from __future__ import annotations
import re
from dataclasses import dataclass

RE_DATA = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_DATA_PT = re.compile(r"\b(\d{1,2})\s+de\s+([a-zà-ú]+)\s+de\s+(\d{4})\b", re.IGNORECASE)
_MESES = {"janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
RE_ABSTENCAO = re.compile(r"(nao tenho informacao|nao sei|desconhec|nao posso responder|nao esta disponivel|sem dados|unable|dont know|i cannot)", re.IGNORECASE)
RE_PREMISSA_FALSA = re.compile(r"(premissa e falsa|premissa falsa|nao e verdade|incorreto|esta errado|falsa|nao foi revogado|nao e exigida|nao se aplica)", re.IGNORECASE)

def _datas_na_resposta(texto: str) -> set[str]:
    out: set[str] = set()
    for m in RE_DATA.finditer(texto):
        out.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    for m in RE_DATA_PT.finditer(texto):
        mes = _MESES.get(m.group(2).lower())
        if mes:
            out.add(f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}")
    return out

def _tokens_chave(texto: str) -> set[str]:
    t = texto.lower()
    chaves = set(re.findall(r"\b\d{4}\b", t))
    if "1689" in t: chaves.add("1689")
    if "1744" in t: chaves.add("1744")
    if "alterad" in t: chaves.add("alterado")
    if "revogad" in t: chaves.add("revogado")
    return chaves

@dataclass
class Julgamento:
    id: str
    status: str
    avaliavel: bool
    motivo: str

def julgar(q, resposta: str) -> Julgamento:
    if q.estado.value != "verificado":
        return Julgamento(q.id, "pendente", False, "questao nao verificada")
    if q.categoria.value == "fora_corpus":
        if RE_ABSTENCAO.search(resposta):
            return Julgamento(q.id, "correta", True, "abstencao adequada")
        return Julgamento(q.id, "errada", True, "respondeu a materia fora do corpus")
    if q.categoria.value == "premissa_falsa":
        if RE_PREMISSA_FALSA.search(resposta):
            return Julgamento(q.id, "correta", True, "identificou premissa falsa")
        return Julgamento(q.id, "errada", True, "aceitou a premissa falsa")
    if q.categoria.value == "negacao":
        esperado = (q.resposta_esperada or "").lower()
        if RE_ABSTENCAO.search(resposta):
            return Julgamento(q.id, "abstencoes", True, "abstencao")
        inicio = resposta.strip().lower()
        if inicio.startswith(esperado):
            return Julgamento(q.id, "correta", True, f"resposta '{esperado}'")
        if "nao" in inicio[:6] and esperado == "nao":
            return Julgamento(q.id, "correta", True, "negacao")
        if "sim" in inicio[:6] and esperado == "sim":
            return Julgamento(q.id, "correta", True, "afirmacao")
        return Julgamento(q.id, "errada", True, "sim/nao nao corresponde")
    if q.tipo_resposta == "data" or q.categoria.value == "temporal":
        esperado = (q.resposta_esperada or "").strip()
        datas = _datas_na_resposta(resposta)
        if not datas:
            return Julgamento(q.id, "abstencoes", True, "sem data na resposta")
        if esperado in datas:
            return Julgamento(q.id, "correta", True, f"data {esperado} presente")
        return Julgamento(q.id, "errada", True, f"datas {sorted(datas)} != esperada {esperado}")
    if q.tipo_resposta == "texto_curto":
        esperado = (q.resposta_esperada or "").lower()
        chaves_resp = _tokens_chave(resposta)
        chaves_exp = _tokens_chave(esperado)
        if chaves_exp and chaves_exp <= chaves_resp:
            return Julgamento(q.id, "correta", True, "tokens-chave presentes")
        return Julgamento(q.id, "errada", True, "tokens-chave ausentes")
    return Julgamento(q.id, "pendente", False, f"requer verificador (cat={q.categoria.value})")
