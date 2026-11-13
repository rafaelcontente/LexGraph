"""
Diagnóstico: O que o grafo sabe sobre uma pergunta específica?
"""
from rdflib import Graph, Namespace

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")
EX = Namespace("https://lexgraph.dev/data/")

GRAPH_FILE = "data/graph/corpus_real.ttl"

def main():
    g = Graph()
    g.parse(GRAPH_FILE, format="turtle")
    print(f"Grafo carregado: {len(g)} triplos\n")
    
    # 1. Quantos artigos temos?
    q1 = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    PREFIX ai: <https://lexgraph.dev/ns/aiact#>
    SELECT (COUNT(?u) AS ?n) WHERE { ?u a ai:Artigo . }
    """
    for r in g.query(q1):
        print(f"📊 Total de artigos no grafo: {r.n}")
    
    # 2. O Artigo 6 existe?
    q2 = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?u ?texto WHERE {
        ?u a <https://lexgraph.dev/ns/aiact#Artigo> .
        ?u lg:rotulo ?rotulo .
        FILTER(CONTAINS(?rotulo, "Artigo 6"))
        ?u lg:temVersao ?v .
        ?v lg:texto ?texto .
    } LIMIT 1
    """
    print("\n🔍 Artigo 6:")
    found = False
    for r in g.query(q2):
        found = True
        print(f"  URI: {r.u}")
        print(f"  Texto (primeiros 200 chars): {str(r.texto)[:200]}...")
    if not found:
        print("  ❌ Artigo 6 não encontrado no grafo!")
    
    # 3. Que datas de vigência/aplicação temos?
    q3 = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?u ?rotulo ?data WHERE {
        ?u lg:temVersao ?v .
        ?v lg:vigenciaInicio ?data .
        ?u lg:rotulo ?rotulo .
    } LIMIT 10
    """
    print("\n📅 Datas de vigência no grafo:")
    for r in g.query(q3):
        print(f"  {r.rotulo}: {r.data}")
    
    # 4. O grafo tem alguma menção a "Anexo III"?
    q4 = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?u ?rotulo WHERE {
        ?u lg:temVersao ?v .
        ?v lg:texto ?texto .
        FILTER(CONTAINS(LCASE(?texto), "anexo iii"))
        ?u lg:rotulo ?rotulo .
    } LIMIT 5
    """
    print("\n📎 Menções a 'Anexo III':")
    found = False
    for r in g.query(q4):
        found = True
        print(f"  {r.rotulo}")
    if not found:
        print("  ❌ Nenhuma menção a 'Anexo III' encontrada!")

if __name__ == "__main__":
    main()
