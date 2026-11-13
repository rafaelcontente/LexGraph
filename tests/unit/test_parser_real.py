"""Testes do parser real contra os HTMLs descarregados."""
import json
from pathlib import Path

import pytest

from lexgraph.corpus.parser import parse_html, extrair_numero_artigo, extrair_numero_paragrafo
from lexgraph.corpus.schema import TipoUnidade

RAW = Path("data/raw")


@pytest.fixture(scope="module")
def html_original():
    f = RAW / "reg_2024_1689_original.html"
    if not f.exists():
        pytest.skip("HTML original não descarregado — corre python -m lexgraph.corpus.descarregar")
    return f.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def html_omnibus():
    f = RAW / "reg_2026_1744.html"
    if not f.exists():
        pytest.skip("HTML omnibus não descarregado")
    return f.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def html_consolidado():
    f = RAW / "reg_2024_1689_cons_20260727.html"
    if not f.exists():
        pytest.skip("HTML consolidado não descarregado")
    return f.read_text(encoding="utf-8")


# --- Testes unitários das funções auxiliares ---

def test_extrair_numero_artigo_simples():
    assert extrair_numero_artigo("Artigo 113.o") == "113"
    assert extrair_numero_artigo("Artigo 5.º") == "5"
    assert extrair_numero_artigo("Article 42") == "42"


def test_extrair_numero_artigo_com_letra():
    assert extrair_numero_artigo("Artigo 113A") == "113-A"


def test_extrair_numero_paragrafo():
    assert extrair_numero_paragrafo("1. O presente regulamento...") == "1"
    assert extrair_numero_paragrafo("10. Sem prejuízo...") == "10"
    assert extrair_numero_paragrafo("texto sem número") is None


# --- Testes de integração com HTML real ---

def test_parser_extrai_113_artigos_do_original(html_original):
    registos = parse_html(html_original, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    artigos = [r for r in registos if r.tipo is TipoUnidade.ARTIGO]
    assert len(artigos) >= 113, f"Esperado >=113 artigos, obtido {len(artigos)}"


def test_parser_extrai_artigo_113(html_original):
    registos = parse_html(html_original, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    art_113 = [r for r in registos if r.unidade_id == "art_113"]
    assert len(art_113) == 1, f"Esperado 1 art_113, obtido {len(art_113)}"
    assert "Entrada em vigor" in art_113[0].texto or "aplicação" in art_113[0].texto.lower()


def test_parser_extrai_paragrafos_do_artigo_113(html_original):
    registos = parse_html(html_original, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    pars_113 = [r for r in registos if r.unidade_id.startswith("art_113_par_")]
    assert len(pars_113) >= 3, f"Art. 113 deve ter >=3 parágrafos, obtido {len(pars_113)}"


def test_parser_omnibus_tem_menos_artigos(html_omnibus):
    """O Omnibus só altera — deve ter muito menos artigos que o regulamento base."""
    registos = parse_html(html_omnibus, "32026R1744", "https://eur-lex.europa.eu/", "a" * 64)
    artigos = [r for r in registos if r.tipo is TipoUnidade.ARTIGO]
    assert 5 <= len(artigos) <= 20, f"Omnibus deve ter poucos artigos, obtido {len(artigos)}"


def test_parser_funciona_no_consolidado(html_consolidado):
    """O parser deve funcionar mesmo com as classes CSS diferentes do consolidado."""
    registos = parse_html(html_consolidado, "02024R1689-20260727", "https://eur-lex.europa.eu/", "a" * 64)
    artigos = [r for r in registos if r.tipo is TipoUnidade.ARTIGO]
    # O consolidado tem 113 artigos base + alguns novos (ex: 113A, etc.)
    assert len(artigos) >= 113, f"Consolidado deve ter >=113 artigos, obtido {len(artigos)}"


def test_parser_preserva_texto_literal(html_original):
    """O campo texto deve conter a citação literal, não normalizada."""
    registos = parse_html(html_original, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    art_113 = next(r for r in registos if r.unidade_id == "art_113")
    # O texto deve conter "2 de agosto de 2026" literalmente
    assert "2 de agosto de 2026" in art_113.texto


def test_parser_schema_valido(html_original):
    """Todos os registos devem validar contra o schema Pydantic."""
    registos = parse_html(html_original, "32024R1689", "https://eur-lex.europa.eu/", "a" * 64)
    for r in registos:
        assert r.unidade_id
        assert r.tipo in TipoUnidade
        assert r.texto
        assert r.fonte.celex