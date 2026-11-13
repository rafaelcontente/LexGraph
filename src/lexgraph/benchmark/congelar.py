"""Congelamento em duas fases e particao estratificada deterministica."""
from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from .schema import Particao, Questao

CAMPOS_PERGUNTA = ("id", "categoria", "pergunta", "dificuldade", "pos_cutoff", "particao")


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_perguntas(questoes: list[Questao]) -> str:
    """So o enunciado e metadados. NAO inclui respostas."""
    payload = [
        {k: getattr(q, k).value if hasattr(getattr(q, k), "value") else getattr(q, k)
         for k in CAMPOS_PERGUNTA}
        for q in sorted(questoes, key=lambda q: q.id)
    ]
    return _sha(_canon(payload))


def hash_completo(questoes: list[Questao]) -> str:
    """Tudo, incluindo respostas esperadas e citacoes."""
    payload = [q.model_dump(mode="json") for q in sorted(questoes, key=lambda q: q.id)]
    return _sha(_canon(payload))


def escrever(questoes: list[Questao], destino: Path) -> dict[str, str]:
    linhas = [_canon(q.model_dump(mode="json"))
              for q in sorted(questoes, key=lambda q: q.id)]
    conteudo = ("\n".join(linhas) + "\n").encode("utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    hashes = {
        "ficheiro": hashlib.sha256(conteudo).hexdigest(),
        "hash_perguntas": hash_perguntas(questoes),
        "hash_completo": hash_completo(questoes),
    }
    destino.with_suffix(".hashes.json").write_text(
        json.dumps(hashes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return hashes


def partir(questoes: list[Questao], seed: int = 42,
           pesos: dict[Particao, float] | None = None) -> list[Questao]:
    """Estratificado por (categoria, dificuldade, pos_cutoff). Deterministico."""
    pesos = pesos or {Particao.DEV: 0.33, Particao.CALIBRACAO: 0.28,
                      Particao.TESTE: 0.39}
    estratos: dict[tuple, list[Questao]] = defaultdict(list)
    for q in questoes:
        if q.pos_cutoff:
            estratos[("cutoff",)].append(q)
        else:
            estratos[(q.categoria.value, q.dificuldade)].append(q)

    rng = random.Random(seed)
    resultado: list[Questao] = []
    for chave, grupo in sorted(estratos.items(), key=lambda kv: str(kv[0])):
        ids = sorted(q.id for q in grupo)
        rng.shuffle(ids)
        n = len(ids)
        n_dev = round(n * pesos[Particao.DEV])
        n_cal = round(n * pesos[Particao.CALIBRACAO])
        destino = {}
        for i, qid in enumerate(ids):
            if chave == ("cutoff",):
                destino[qid] = Particao.CONTAMINACAO
            elif i < n_dev:
                destino[qid] = Particao.DEV
            elif i < n_dev + n_cal:
                destino[qid] = Particao.CALIBRACAO
            else:
                destino[qid] = Particao.TESTE
        for q in grupo:
            resultado.append(q.model_copy(update={"particao": destino[q.id]}))
    return sorted(resultado, key=lambda q: q.id)
