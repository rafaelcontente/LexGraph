from datetime import date
import pytest
from pydantic import ValidationError

from lexgraph.benchmark.schema import (
    Categoria, Evidencia, Estado, Particao, Questao, exigir_verificadas,
)
from lexgraph.benchmark.congelar import hash_perguntas, hash_completo

EV = Evidencia(celex="32026R1744", localizador="Art. 1.o, ponto 40",
               citacao_literal="texto oficial", url="https://eur-lex.europa.eu/")

BASE = dict(id="q_001", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="facil",
            pos_cutoff=True, particao=Particao.DEV, tipo_resposta="texto_curto",
            resposta_esperada="x", pergunta="Qual e o ato alterador?", evidencias=(EV,))


def test_pendente_bloqueia_benchmark():
    q = Questao(**BASE)
    with pytest.raises(RuntimeError, match="nao verificadas"):
        exigir_verificadas([q], Particao.DEV)


def test_verificado_exige_revisor():
    with pytest.raises(ValidationError, match="verificado_por"):
        Questao(**{**BASE, "estado": Estado.VERIFICADO})


def test_verificado_com_revisor_passa():
    q = Questao(**{**BASE, "estado": Estado.VERIFICADO,
                   "verificado_por": "Rafael", "verificado_em": date(2026, 11, 14)})
    exigir_verificadas([q], Particao.DEV)


def test_temporal_exige_asof():
    with pytest.raises(ValidationError, match="asof"):
        Questao(**{**BASE, "categoria": Categoria.TEMPORAL})


def test_fora_corpus_nao_tem_resposta():
    with pytest.raises(ValidationError):
        Questao(**{**BASE, "categoria": Categoria.FORA_CORPUS})


def test_negacao_exige_procura():
    with pytest.raises(ValidationError, match="procura_negativa"):
        Questao(**{**BASE, "categoria": Categoria.NEGACAO})


def test_premissa_falsa_exige_declaracao():
    with pytest.raises(ValidationError, match="premissa_declarada"):
        Questao(**{**BASE, "categoria": Categoria.PREMISSA_FALSA})


def test_hash_perguntas_ignora_respostas():
    a = Questao(**BASE)
    b = Questao(**{**BASE, "resposta_esperada": "OUTRA", "estado": Estado.VERIFICADO,
                   "verificado_por": "Rafael", "verificado_em": date(2026, 11, 14)})
    assert hash_perguntas([a]) == hash_perguntas([b])
    assert hash_completo([a]) != hash_completo([b])


def test_hash_perguntas_muda_se_pergunta_muda():
    a = Questao(**BASE)
    b = Questao(**{**BASE, "pergunta": "Pergunta diferente sobre o mesmo tema?"})
    assert hash_perguntas([a]) != hash_perguntas([b])


def test_placeholder_bloqueia_verificacao():
    ev = Evidencia(celex="32024R1689", localizador="Art. 113.o [A CONFIRMAR]",
                   citacao_literal="[A PREENCHER AMANHA]",
                   url="https://eur-lex.europa.eu/")
    with pytest.raises(ValidationError, match="placeholder"):
        Questao(**{**BASE, "evidencias": (ev,), "estado": Estado.VERIFICADO,
                   "verificado_por": "Rafael", "verificado_em": date(2026, 11, 14)})
