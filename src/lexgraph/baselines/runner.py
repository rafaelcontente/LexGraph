from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from lexgraph.benchmark.schema import Questao, Estado, Particao
from lexgraph.baselines.providers import criar_provider
from lexgraph.baselines.avaliar import julgar

GOLDEN = Path("data/golden_dataset/questoes_v1.jsonl")
OUT_DIR = Path("data/evals")
PARTICOES_PERMITIDAS = {Particao.DEV, Particao.CALIBRACAO}

def carregar_questoes() -> list[Questao]:
    return [Questao(**json.loads(l)) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]

def prompt_para(q: Questao) -> str:
    return q.pergunta

def correr(provider_nome: str, *, particao: Particao | None = None, limit: int | None = None, model: str = "gpt-4o-mini") -> dict:
    provider = criar_provider(provider_nome, model=model)
    questoes = carregar_questoes()
    nao_verif = [q.id for q in questoes if q.estado is not Estado.VERIFICADO]
    if nao_verif:
        print(f"⚠️  {len(nao_verif)} questoes nao verificadas serao ignoradas.")
    questoes = [q for q in questoes if q.estado is Estado.VERIFICADO]
    if particao is Particao.TESTE:
        raise RuntimeError("🚫 Particao 'teste' esta SELADA. Nao corre baselines aqui. Ver pre-registo §7.")
    if particao:
        questoes = [q for q in questoes if q.particao is particao]
    if limit:
        questoes = questoes[:limit]
    
    resultados = []
    for q in questoes:
        resp = provider.generate(prompt_para(q))
        j = julgar(q, resp.texto)
        
        # CORREÇÃO: Incluir premissa_declarada e procura_negativa para o verificador
        resultados.append({
            "id": q.id, 
            "categoria": q.categoria.value, 
            "particao": q.particao.value, 
            "pos_cutoff": q.pos_cutoff, 
            "pergunta": q.pergunta, 
            "premissa_declarada": getattr(q, "premissa_declarada", None),
            "procura_negativa": getattr(q, "procura_negativa", None),
            "resposta_esperada": q.resposta_esperada, 
            "resposta_llm": resp.texto, 
            "modelo": resp.modelo, 
            "latencia_ms": resp.latencia_ms, 
            "tokens_estimados": resp.tokens_estimados, 
            "erro_provider": resp.erro, 
            "status": j.status, 
            "avaliavel": j.avaliavel, 
            "motivo": j.motivo, 
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")
        })
        
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    destino = OUT_DIR / f"baseline_{provider_nome}.jsonl"
    with destino.open("w", encoding="utf-8") as fh:
        for r in resultados:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"destino": str(destino), "resultados": resultados}

def metricas(resultados: list[dict]) -> dict:
    avaliadas = [r for r in resultados if r["avaliavel"]]
    pendentes = [r for r in resultados if not r["avaliavel"]]
    n = len(resultados)
    a = len(avaliadas)
    aceites = [r for r in avaliadas if r["status"] in ("correta", "errada")]
    alucinadas = [r for r in aceites if r["status"] == "errada"]
    cont = Counter(r["status"] for r in avaliadas)
    return {
        "total_questoes": n, 
        "avaliadas": a, 
        "pendentes_verificador": len(pendentes), 
        "corretas": cont["correta"], 
        "erradas_alucinacao": cont["errada"], 
        "abstencoes": cont["abstencoes"], 
        "taxa_alucinacao_aceites": (round(len(alucinadas)/len(aceites), 3) if aceites else None), 
        "cobertura": round(a / n, 3) if n else None, 
        "taxa_correcao_global": round(cont["correta"] / n, 3) if n else None
    }

def resumo_por_categoria(resultados: list[dict]) -> dict:
    out: dict = {}
    for r in resultados:
        c = r["categoria"]
        out.setdefault(c, Counter())
        out[c][r["status"]] += 1
    return {c: dict(v) for c, v in out.items()}
