"""Verifica que as perguntas congeladas nao foram alteradas.

Duas camadas:
  1. hash recalculado vs. hash registado em .hashes.json  (consistencia interna)
  2. hash_perguntas vs. hash no tag de congelamento       (ancora externa)

O hash_completo PODE diferir do tag: as respostas sao verificadas depois.
O hash_perguntas NAO pode diferir. Se diferir, o pre-registo perdeu valor.
"""
import json
import subprocess
import sys
from pathlib import Path

from lexgraph.benchmark.schema import Questao
from lexgraph.benchmark.congelar import hash_perguntas, hash_completo

TAG = "freeze-perguntas-v1"
FICHEIRO = Path("data/golden_dataset/questoes_v1.jsonl")
REGISTO = Path("data/golden_dataset/questoes_v1.hashes.json")


def carregar(p):
    return [Questao(**json.loads(l))
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def hashes_no_tag():
    r = subprocess.run(["git", "show", f"{TAG}:{REGISTO.as_posix()}"],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def main():
    qs = carregar(FICHEIRO)
    hp, hc = hash_perguntas(qs), hash_completo(qs)
    reg = json.loads(REGISTO.read_text(encoding="utf-8"))
    try:
        congelado = hashes_no_tag()
    except subprocess.CalledProcessError:
        print(f"ERRO: tag {TAG} nao encontrada. Corre: git fetch --tags")
        return 1

    erros = []
    if hp != reg["hash_perguntas"]:
        erros.append("hash_perguntas nao bate com .hashes.json")
    if hp != congelado["hash_perguntas"]:
        erros.append(f"PERGUNTAS ALTERADAS desde {TAG}: "
                     f"{congelado['hash_perguntas'][:12]} -> {hp[:12]}")
    if hc != reg["hash_completo"]:
        erros.append("hash_completo nao bate com .hashes.json (corre o seed)")

    print(f"hash_perguntas : {hp}")
    print(f"hash_completo  : {hc}")
    print(f"respostas mudaram desde o freeze: "
          f"{'sim (esperado apos verificacao)' if hc != congelado['hash_completo'] else 'nao'}")
    for e in erros:
        print("ERRO:", e)
    if erros:
        return 1
    print("Congelamento intacto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
