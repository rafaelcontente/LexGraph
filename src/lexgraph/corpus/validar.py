# src/lexgraph/corpus/validar.py
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Problema:
    codigo: str
    detalhe: str
    gravidade: str = "erro"      # erro | aviso


def validar_corpus(registos: list) -> list[Problema]:
    probs: list[Problema] = []
    por_unidade = defaultdict(list)
    ids = set()

    for r in registos:
        if r.expressao_id in ids:
            probs.append(Problema("DUP_EXPR", r.expressao_id))
        ids.add(r.expressao_id)
        por_unidade[r.unidade_id].append(r)

    conhecidos = {r.unidade_id for r in registos}

    for r in registos:
        if r.parent_id and r.parent_id not in conhecidos:
            probs.append(Problema("PARENT_ORFAO", f"{r.unidade_id} → {r.parent_id}"))

    for uid, versoes in por_unidade.items():
        vs = sorted(versoes, key=lambda v: v.vigencia.inicio)
        for a, b in zip(vs, vs[1:]):
            if a.vigencia.fim is None:
                probs.append(Problema("VERSAO_ABERTA_SOBREPOSTA", uid))
            elif a.vigencia.fim > b.vigencia.inicio:
                probs.append(Problema("Sobreposicao", f"{uid}: {a.expressao_id} / {b.expressao_id}"))
            elif a.vigencia.fim < b.vigencia.inicio:
                probs.append(Problema("LACUNA_VIGENCIA", uid, "aviso"))

    return probs