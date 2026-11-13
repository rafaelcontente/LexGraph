"""
TESTE DE REGRESSÃO: Abstenção do LLM não deve ser classificada como CONTRADITA.

CAUSA: O verificador aplicava a "Falácia do Mundo Fechado". Se o LLM dizia 
"Não sei", o verificador procurava a afirmação no grafo, não a encontrava, 
e marcava como CONTRADITA, penalizando o modelo por ser cauteloso.

COMPORTAMENTO ESPERADO: Se a resposta do LLM contiver indicadores de abstenção, 
o verificador deve retornar NAO_VERIFICAVEL (ou ABSTENCAO_CORRETA se for fora_corpus), 
NUNCA CONTRADITA.

REFERÊNCIA: Issue #42 - Correção da lógica de avaliação do verificador simbólico.
"""
import pytest
from rdflib import Graph, Namespace
from lexgraph.verifier.checker import verificar

LG = Namespace("https://lexgraph.dev/ns/core#")

@pytest.fixture
def grafo_vazio():
    """Grafo mínimo para testes rápidos, sem dependência de rede ou ficheiros grandes."""
    g = Graph()
    g.bind("lg", LG)
    return g

def test_abstencao_temporal_nao_e_contradicao(grafo_vazio):
    questao = {
        "categoria": "temporal",
        "tipo_resposta": "data",
        "pergunta": "Qual a data de aplicação?",
        "resposta_esperada": "2027-12-02"
    }
    # O LLM absteve-se
    resposta_llm = "Desculpe, não tenho informação suficiente para responder a essa pergunta específica."
    
    resultado = verificar(questao, resposta_llm, grafo_vazio)
    
    # REGRA DE OURO: Abstenção NUNCA pode ser CONTRADITA
    assert resultado.status != "CONTRADITA", "Bug de regressão: Abstenção classificada como contradição!"
    assert resultado.status == "NAO_VERIFICAVEL", f"Esperado NAO_VERIFICAVEL, obtido {resultado.status}"
    assert "absteve" in resultado.motivo.lower()

def test_abstencao_fora_corpus_e_correta(grafo_vazio):
    questao = {
        "categoria": "fora_corpus",
        "pergunta": "Qual a multa da Empresa X?",
        "resposta_esperada": None
    }
    resposta_llm = "Não tenho informações sobre a Empresa X no regulamento."
    
    resultado = verificar(questao, resposta_llm, grafo_vazio)
    
    assert resultado.status == "ABSTENCAO_CORRETA"
