"""
Runner do Verificador Simbólico (Módulo 5).
Lê um ficheiro de baseline e valida as respostas contra o grafo real.
"""
import argparse
import json
from pathlib import Path
from collections import Counter

from rdflib import Graph
from lexgraph.verifier.checker import verificar

BASELINE_DIR = Path("data/evals")
GRAPH_FILE = Path("data/graph/corpus_real.ttl")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="baseline_mock.jsonl", help="Ficheiro de baseline a verificar")
    args = ap.parse_args()

    input_file = BASELINE_DIR / args.input
    if not input_file.exists():
        print(f"❌ Ficheiro não encontrado: {input_file}")
        print("Corre primeiro: python scripts/run_baseline.py")
        return 1

    if not GRAPH_FILE.exists():
        print(f"❌ Grafo real não encontrado: {GRAPH_FILE}")
        print("Corre primeiro: python -m lexgraph.graph_db.ingestao")
        return 1

    print(f"📥 A carregar grafo real de {GRAPH_FILE}...")
    grafo = Graph()
    grafo.parse(GRAPH_FILE, format="turtle")
    print(f"✅ Grafo carregado com {len(grafo)} triplos.")

    print(f"🔍 A verificar {input_file}...")
    resultados_verificados = []
    estatisticas = Counter()

    with open(input_file, "r", encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            reg = json.loads(linha)
            
            # Executar verificação simbólica
            res_verif = verificar(reg, reg["resposta_llm"], grafo)
            
            reg["verificacao_status"] = res_verif.status
            reg["verificacao_motivo"] = res_verif.motivo
            reg["verificacao_evidencia"] = res_verif.evidencia_grafo
            
            resultados_verificados.append(reg)
            estatisticas[res_verif.status] += 1

    # Guardar resultados
    output_file = input_file.with_name(input_file.stem + "_verified.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for reg in resultados_verificados:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")

    print("\n" + "="*60)
    print("RESULTADOS DA VERIFICAÇÃO SIMBÓLICA")
    print("="*60)
    for status, count in estatisticas.items():
        print(f"  {status:<20} : {count}")
    print("="*60)
    print(f"💾 Resultados guardados em: {output_file}")
    
    # Destaque para o valor agregado
    if estatisticas["CONTRADITA"] > 0:
        print(f"\n🎯 SUCESSO: O verificador detetou {estatisticas['CONTRADITA']} alucinações que o avaliador heurístico inicial pode ter classificado apenas como 'errada', mas agora temos a prova simbólica (CONTRADITA pelo grafo).")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
