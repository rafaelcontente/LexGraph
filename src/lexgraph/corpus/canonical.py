"""Normalização e serialização determinísticas. Sem isto o Teste 1 falha."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable

_WS = re.compile(r"\s+")


def normalizar_texto(t: str) -> str:
    """Mínimo e documentado. NÃO altera pontuação nem aspas.
    NFC + espaços não-separáveis → espaço + colapso de whitespace + strip.
    A comparação manual com o EUR-Lex (Teste 3) aplica esta mesma função.
    """
    t = unicodedata.normalize("NFC", t)
    t = t.replace("\u00a0", " ").replace("\u2007", " ").replace("\u202f", " ")
    t = t.replace("\u00ad", "")          # soft hyphen
    return _WS.sub(" ", t).strip()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_texto(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def escrever_jsonl(registos: Iterable, destino: Path) -> str:
    """Ordem total estável + JSON canónico + LF. Devolve o hash do ficheiro."""
    linhas = [
        canonical_json(r.model_dump(mode="json"))
        for r in sorted(registos, key=lambda r: (r.unidade_id, r.vigencia.inicio))
    ]
    conteudo = ("\n".join(linhas) + "\n").encode("utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    return hashlib.sha256(conteudo).hexdigest()