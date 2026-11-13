import json
from pathlib import Path

MOCK_FILE = Path("data/evals/baseline_mock_verified.jsonl")
OLLAMA_FILE = Path("data/evals/baseline_openai_verified.jsonl")

def load_data(filepath):
    if not filepath.exists(): return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}

def main():
    mock_data = load_data(MOCK_FILE)
    ollama_data = load_data(OLLAMA_FILE)
    
    # Vamos ver as 5 perguntas que o Ollama respondeu
    ids_alvo = list(ollama_data.keys())[:5]
    
    print("=" * 90)
    print(" 📊 COMPARAÇÃO REAL: MOCK vs. LLAMA 3.2 (LOCAL) + VERIFICADOR SIMBÓLICO")
    print("=" * 90)
    
    for q_id in ids_alvo:
        if q_id not in mock_data: continue
        m, o = mock_data[q_id], ollama_data[q_id]
        
        print(f"\n🔹 {q_id.upper()} | Categoria: {m['categoria']}")
        print(f"Pergunta: {m['pergunta'][:70]}...")
        print("-" * 90)
        
        print(f"🤖 MOCK (Determinístico):")
        print(f"   Resposta : {m['resposta_llm'][:100]}")
        print(f"   Verif.   : [{m['verificacao_status']}] {m['verificacao_motivo']}")
        
        print(f"\n🦙 LLAMA 3.2 (Real, Local):")
        if o.get("erro_provider"):
            print(f"   Resposta : [ERRO] {o['erro_provider']}")
        else:
            print(f"   Resposta : {o['resposta_llm'][:100]}")
        print(f"   Verif.   : [{o['verificacao_status']}] {o['verificacao_motivo']}")
        print("=" * 90)

if __name__ == "__main__":
    main()
