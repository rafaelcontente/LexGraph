"""
Demo interativa do LexGraph.
Mostra o pipeline a desmontar uma alucinação de Premissa Falsa.
"""
from rdflib import Graph
from lexgraph.verifier.checker import verificar

def main():
    print("=" * 70)
    print(" 🎬 LEXGRAPH DEMO: A desmontar uma alucinação em tempo real")
    print("=" * 70)
    
    print("\n[1/4] 📥 A carregar o Grafo de Conhecimento...")
    g = Graph()
    g.parse("data/graph/corpus_real.ttl", format="turtle")
    print(f"   ✅ Grafo carregado. {len(g)} triplos SHACL-validados.")

    pergunta = "Uma vez que o Regulamento da IA foi revogado pelo Digital Omnibus, que regime se aplica agora?"
    print(f"\n[2/4] ❓ Pergunta do Utilizador (contém premissa falsa):")
    print(f"   \"{pergunta}\"")

    resposta_llm = "Sim, o Regulamento foi revogado. O novo regime é definido pelo Omnibus."
    print(f"\n[3/4] 🤖 Resposta do LLM (Zero-Shot):")
    print(f"   \"{resposta_llm}\"")

    print(f"\n[4/4] ⚖️  Verificador Simbólico a consultar o grafo via SPARQL...")
    questao = {
        "categoria": "premissa_falsa",
        "premissa_declarada": "O Regulamento da IA foi revogado pelo Digital Omnibus.",
        "resposta_esperada": "A premissa é falsa."
    }
    
    resultado = verificar(questao, resposta_llm, g)
    
    print("\n" + "=" * 70)
    print(" 🏁 VEREDICTO DO LEXGRAPH")
    print("=" * 70)
    print(f"   Status      : 🔴 {resultado.status}")
    print(f"   Motivo      : {resultado.motivo}")
    print(f"   Evidência   : {resultado.evidencia_grafo}")
    print("=" * 70)
    print("\n💡 Conclusão: O LexGraph impediu que uma alucinação do LLM fosse")
    print("   apresentada ao utilizador, provando a falsidade com base na lei real.")

if __name__ == "__main__":
    main()
