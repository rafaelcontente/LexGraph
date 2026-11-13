"""
TESTE DE REGRESSÃO: O grafo não deve conter versões sobrepostas da mesma unidade.

CAUSA: O script de ingestão processava múltiplos documentos (ex: original e consolidado) 
e criava múltiplas versões para o mesmo `unidade_id` (ex: art_1_v_20240801 e art_1_v_20260727) 
sem definir `vigenciaFim`, violando a regra SHACL de não sobreposição.

COMPORTAMENTO ESPERADO: O processo de ingestão deve deduplicar, mantendo apenas a 
versão com a `vigenciaInicio` mais recente para cada `unidade_id`.

REFERÊNCIA: Issue #45 - Deduplicação inteligente na ingestão para garantir conformidade SHACL.
"""
import pytest
from pathlib import Path
from rdflib import Graph, Namespace

LG = Namespace("https://lexgraph.dev/ns/core#")
GRAPH_FILE = Path("data/graph/corpus_real.ttl")

@pytest.mark.skipif(not GRAPH_FILE.exists(), reason="Grafo real ainda não foi gerado. Corre a ingestão primeiro.")
def test_nenhuma_sobreposicao_de_versoes():
    """Verifica a query SHACL exata que estava a falhar."""
    g = Graph()
    g.parse(GRAPH_FILE, format="turtle")
    
    query_sobreposicao = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT $this ?v1 ?v2 WHERE {
        $this lg:temVersao ?v1, ?v2 .
        FILTER(?v1 != ?v2)
        ?v1 lg:vigenciaInicio ?i1 .
        ?v2 lg:vigenciaInicio ?i2 .
        FILTER(?i1 < ?i2)
        OPTIONAL { ?v1 lg:vigenciaFim ?f1 }
        FILTER(!BOUND(?f1) || ?i2 < ?f1)
    }
    """
    resultados = list(g.query(query_sobreposicao))
    
    assert len(resultados) == 0, (
        f"Bug de regressão: Detectadas {len(resultados)} sobreposições de versões. "
        f"Exemplo: {resultados[0] if resultados else 'N/A'}. "
        "A ingestão deve manter apenas a versão mais recente."
    )

def test_zero_duplicados_mesma_data():
    """Garante que não há unidades com >1 versão na mesma data exata."""
    if not GRAPH_FILE.exists():
        pytest.skip("Grafo não existe")
        
    g = Graph()
    g.parse(GRAPH_FILE, format="turtle")
    
    query_duplicados = """
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?u (COUNT(?v) AS ?n) WHERE {
        ?u lg:temVersao ?v .
        ?v lg:vigenciaInicio ?data .
    } GROUP BY ?u HAVING (COUNT(?v) > 1)
    """
    duplicados = list(g.query(query_duplicados))
    
    assert len(duplicados) == 0, f"Bug de regressão: Detectados {len(duplicados)} nós com versões duplicadas na mesma data."
