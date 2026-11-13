import argparse
import json
from lexgraph.baselines.runner import correr, metricas, resumo_por_categoria
from lexgraph.benchmark.schema import Particao

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="mock", choices=["mock", "openai"], help="mock = deterministico (default); openai = chamada real")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--particao", default=None, choices=["dev", "calibracao", "teste", "contaminacao"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    part = Particao(args.particao) if args.particao else None
    print(f"🚀 Baseline provider={args.provider} particao={args.particao or 'todas'}")
    res = correr(args.provider, particao=part, limit=args.limit, model=args.model)
    m = metricas(res["resultados"])
    por_cat = resumo_por_categoria(res["resultados"])
    print("\n" + "=" * 60)
    print("METRICAS (pre-registo §5)")
    print("=" * 60)
    for k, v in m.items():
        print(f"  {k:<28} {v}")
    print("\n" + "=" * 60)
    print("POR CATEGORIA")
    print("=" * 60)
    for c, d in por_cat.items():
        print(f"  {c:<20} {d}")
    print(f"\n💾 Guardado em {res['destino']}")
    if m["pendentes_verificador"]:
        print(f"⚠️  {m['pendentes_verificador']} questoes ficam para o verificador simbolico (Modulo 5).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
