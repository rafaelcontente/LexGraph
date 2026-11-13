"""
TESTE DE REGRESSÃO: O parser deve extrair exatamente 113 artigos do AI Act base.

CAUSA: Alterações na lógica de extração de datas ou classes CSS faziam o parser 
ignorar artigos ou criar falsos positivos, alterando a contagem total.

COMPORTAMENTO ESPERADO: O parser deve retornar exatamente 113 registos do tipo 
ARTIGO para o CELEX 32024R1689, independentemente de menções de datas no texto.

REFERÊNCIA: Issue #38 - Estabilização do parser com lógica conservativa de datas.
"""
import pytest
from pathlib import Path
from lexgraph.corpus.parser import parse_html
from lexgraph.corpus.schema import TipoUnidade

RAW_FILE = Path("data/raw/reg_2024_1689_original.html")

@pytest.mark.skipif(not RAW_FILE.exists(), reason="Ficheiro HTML de teste não encontrado.")
def test_extrai_exatamente_113_artigos():
    html = RAW_FILE.read_text(encoding="utf-8")
    
    # O parser não deve falhar nem devolver 0 artigos
    registos = parse_html(html, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    
    artigos = [r for r in registos if r.tipo is TipoUnidade.ARTIGO]
    
    assert len(artigos) == 113, (
        f"Bug de regressão no parser: Esperados 113 artigos, obtidos {len(artigos)}. "
        "A lógica de deteção de títulos de artigos foi comprometida."
    )
