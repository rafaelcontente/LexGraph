"""Verifica que as perguntas congeladas nao foram alteradas.

Duas camadas:
  1. hash recalculado vs. hash registado em .hashes.json  (consistencia interna)
  2. hash_perguntas vs. hash esperado hardcoded           (ancora do pre-registo)

O hash_completo PODE diferir do .hashes.json anterior: as respostas sao
verificadas depois. O hash_perguntas NAO pode diferir.
"""
import json
import sys
from pathlib import Path

from lexgraph.benchmark.schema import Questao
from lexgraph.benchmark.congelar import hash_perguntas, hash_completo

FICHEIRO = Path("data/golden_dataset/questoes_v1.jsonl")
REGISTO = Path("data/golden_dataset/questoes_v1.hashes.json")

# Hash oficial do pre-registo (atualizado quando as perguntas mudam
# legitimamente — p.ex. depois de confirmar citacoes no EUR-Lex).
# Se este valor mudar, o commit deve ter uma mensagem que explique porquê.
HASH_PERGUNTAS_ESPERADO = (
    "65c274ce96b0cdce2550d6f35fb04a0804181370af21e1f668429af2b64e3da0"
)


def carregar(p):
    return [Questao(**json.loads(l))
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    if not FICHEIRO.exists():
        print(f"ERRO: {FICHEIRO} nao existe. Corre scripts/seed_benchmark.py.")
        return 1
    if not REGISTO.exists():
        print(f"ERRO: {REGISTO} nao existe. Corre scripts/seed_benchmark.py.")
        return 1

    qs = carregar(FICHEIRO)
    hp, hc = hash_perguntas(qs), hash_completo(qs)
    reg = json.loads(REGISTO.read_text(encoding="utf-8"))

    erros = []
    if hp != reg["hash_perguntas"]:
        erros.append("hash_perguntas nao bate com .hashes.json")
    if hp != HASH_PERGUNTAS_ESPERADO:
        erros.append(
            f"PERGUNTAS ALTERADAS: esperado {HASH_PERGUNTAS_ESPERADO[:12]}..., "
            f"obtido {hp[:12]}..."
        )
    if hc != reg["hash_completo"]:
        erros.append("hash_completo nao bate com .hashes.json (corre o seed)")

    print(f"hash_perguntas : {hp}")
    print(f"hash_completo  : {hc}")
    print(f"hash esperado  : {HASH_PERGUNTAS_ESPERADO}")
    for e in erros:
        print("ERRO:", e)
    if erros:
        return 1
    print("Congelamento intacto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
