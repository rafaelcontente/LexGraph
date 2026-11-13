"""
Métricas de qualidade do grafo (Fase 1) - Versão Ajustada.
"""
import json
from pathlib import Path
from rdflib import Graph, Namespace

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")
EX = Namespace("https://lexgraph.dev/data/")

GRAPH_FILE = Path("data/graph/corpus_real.ttl")

def carregar_grafo():
    g = Graph()
    g.parse(GRAPH_FILE, format="turtle")
    return g

def medir_total_triplos(g): return len(g)
def medir_artigos(g): return int(list(g.query("PREFIX ai: <https://lexgraph.dev/ns/aiact#> SELECT (COUNT(?u) AS ?n) WHERE { ?u a ai:Artigo . }"))[0].n)
def medir_paragrafos(g): return int(list(g.query("PREFIX ai: <https://lexgraph.dev/ns/aiact#> SELECT (COUNT(?u) AS ?n) WHERE { ?u a ai:Numero . }"))[0].n)

def medir_entidades_chave(g):
    entidades_esperadas = ["art_6", "art_113", "art_1", "art_2", "art_6_par_1", "art_6_par_2", "art_113_par_1", "art_113_par_2", "art_113_par_3"]
    encontradas = sum(1 for uid in entidades_esperadas if (EX[uid], None, None) in g)
    return encontradas / len(entidades_esperadas), entidades_esperadas

def medir_cobertura_temporal(g):
    """Verifica se as datas críticas existem no grafo (em vigenciaInicio ou no texto)."""
    datas_criticas = ["2024-08-01", "2025-02-02", "2026-08-02", "2027-12-02", "2028-08-02"]
    
    # 1. Datas em vigenciaInicio
    q_inicio = "PREFIX lg: <https://lexgraph.dev/ns/core#> SELECT ?data WHERE { ?s lg:vigenciaInicio ?data . }"
    datas_inicio = {str(row.data) for row in g.query(q_inicio)}
    
    # 2. Datas no texto (para capturar prazos específicos mencionados)
    q_texto = "PREFIX lg: <https://lexgraph.dev/ns/core#> SELECT ?texto WHERE { ?s lg:texto ?texto . }"
    textos = [str(row.texto) for row in g.query(q_texto)]
    texto_completo = " ".join(textos)
    
    encontradas = []
    for d in datas_criticas:
        if d in datas_inicio or d in texto_completo:
            encontradas.append(d)
            
    return len(encontradas) / len(datas_criticas), encontradas, datas_inicio

def medir_remissoes_quebradas(g):
    q = "PREFIX lg: <https://lexgraph.dev/ns/core#> SELECT ?child ?parent WHERE { ?child lg:parteDe ?parent . }"
    total = 0
    quebradas = 0
    exemplos = []
    for row in g.query(q):
        total += 1
        if (row.parent, None, None) not in g:
            quebradas += 1
            if len(exemplos) < 5: exemplos.append(f"  ❌ {row.child} -> {row.parent}")
    return quebradas / total if total > 0 else 0, total, exemplos

def medir_duplicados(g):
    q = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?u (COUNT(?v) AS ?n) WHERE { ?u lg:temVersao ?v . ?v lg:vigenciaInicio ?data . } 
    GROUP BY ?u HAVING (COUNT(?v) > 1)
    """
    return len(list(g.query(q)))

def main():
    print("=" * 70)
    print(" 📊 RELATÓRIO DE QUALIDADE DO GRAFO (Fase 1 - Estruturalmente Seguro)")
    print("=" * 70)
    g = carregar_grafo()
    
    print(f"\n🔹 Volume:")
    print(f"   Total de triplos: {medir_total_triplos(g)}")
    print(f"   Artigos: {medir_artigos(g)}")
    print(f"   Parágrafos/Números: {medir_paragrafos(g)}")
    
    print(f"\n🔹 Recall de Entidades-Chave:")
    recall, entidades = medir_entidades_chave(g)
    print(f"   Recall: {recall:.1%} ({int(recall*len(entidades))}/{len(entidades)})")
    
    print(f"\n🔹 Cobertura Temporal (em vigenciaInicio ou texto):")
    cob, encontradas, datas_inicio = medir_cobertura_temporal(g)
    print(f"   Cobertura: {cob:.1%} ({len(encontradas)}/5)")
    print(f"   Encontradas: {encontradas}")
    
    print(f"\n🔹 Remissões Quebradas:")
    taxa, total, exemplos = medir_remissoes_quebradas(g)
    print(f"   Taxa: {taxa:.1%} ({int(taxa*total)}/{total})")
    
    print(f"\n🔹 Duplicados (unidades com >1 versão na mesma data):")
    print(f"   Total: {medir_duplicados(g)}")
    
    print("\n" + "=" * 70)
    if recall == 1.0 and medir_duplicados(g) == 0:
        print(" 🎉 GRAFO ESTRUTURALMENTE PERFEITO. Pronto para Fase 2 (Recuperação).")
    print("=" * 70)

if __name__ == "__main__":
    main()
