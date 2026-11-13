from datetime import date
import pytest
from rdflib import Graph, Literal
from rdflib.namespace import XSD

from lexgraph.graph_db.grafo import (
    LG, AI, EX, carregar, validar_shacl, promover_para_revisto, ONTOLOGIA,
)
from lexgraph.graph_db import consultas as C

H = "a" * 64

FIXTURE = f"""
@prefix lg: <https://lexgraph.dev/ns/core#> .
@prefix ai: <https://lexgraph.dev/ns/aiact#> .
@prefix ex: <https://lexgraph.dev/data/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:reg_2024_1689 a lg:RecursoJuridico .
ex:reg_2026_1744 a lg:RecursoJuridico .
ex:revisor_humano a lg:Agente .
ex:conjunto_anx_iii a ai:ConjuntoNormativo .

ex:art_113 a ai:Artigo ; lg:temVersao ex:art_113_v1, ex:art_113_v2 ;
    lg:remetePara ex:art_3 .
ex:art_6 a ai:Artigo ; lg:temVersao ex:art_6_v1 ; lg:remetePara ex:art_113 .
ex:art_3 a ai:Artigo ; lg:temVersao ex:art_3_v1 .

ex:art_113_v1 a lg:VersaoUnidade ; lg:versaoDe ex:art_113 ;
    lg:vigenciaInicio "2024-08-01"^^xsd:date ; lg:vigenciaFim "2026-07-27"^^xsd:date ;
    lg:texto "original" ; lg:textoHash "{H}" ; lg:fonteOficial ex:reg_2024_1689 .
ex:art_113_v2 a lg:VersaoUnidade ; lg:versaoDe ex:art_113 ;
    lg:vigenciaInicio "2026-07-27"^^xsd:date ;
    lg:texto "consolidado" ; lg:textoHash "{H}" ; lg:fonteOficial ex:reg_2026_1744 .
ex:art_6_v1 a lg:VersaoUnidade ; lg:versaoDe ex:art_6 ;
    lg:vigenciaInicio "2024-08-01"^^xsd:date ;
    lg:texto "art 6" ; lg:textoHash "{H}" ; lg:fonteOficial ex:reg_2024_1689 .
ex:art_3_v1 a lg:VersaoUnidade ; lg:versaoDe ex:art_3 ;
    lg:vigenciaInicio "2024-08-01"^^xsd:date ;
    lg:texto "definicoes" ; lg:textoHash "{H}" ; lg:fonteOficial ex:reg_2024_1689 .

ex:prazo_iii_v1 a ai:Prazo ; ai:tipoPrazo ai:PrazoAplicacao ;
    ai:dataPrazo "2026-08-02"^^xsd:date ; ai:regeAplicacaoDe ex:conjunto_anx_iii ;
    lg:fonteNormativa ex:art_113_v1 ;
    lg:vigenciaInicio "2024-08-01"^^xsd:date ; lg:vigenciaFim "2026-07-27"^^xsd:date ;
    lg:estadoVerificacao ai:Candidato .
ex:prazo_iii_v2 a ai:Prazo ; ai:tipoPrazo ai:PrazoAplicacao ;
    ai:dataPrazo "2027-12-02"^^xsd:date ; ai:regeAplicacaoDe ex:conjunto_anx_iii ;
    lg:fonteNormativa ex:art_113_v2 ;
    lg:vigenciaInicio "2026-07-27"^^xsd:date ;
    lg:estadoVerificacao ai:Candidato .

ex:alt_001 a lg:Alteracao ; lg:tipoAlteracao ai:Prorrogacao ;
    lg:atoAlterador ex:reg_2026_1744 ; lg:altera ex:art_113 ;
    lg:versaoAnterior ex:art_113_v1 ; lg:versaoNova ex:art_113_v2 ;
    lg:dataEfeito "2026-07-27"^^xsd:date .
"""


@pytest.fixture
def g():
    return Graph().parse(data=FIXTURE, format="turtle")


@pytest.fixture
def g_revisto(g):
    for p in (EX.prazo_iii_v1, EX.prazo_iii_v2):
        promover_para_revisto(g, p, EX.revisor_humano)
    return g


# ---- Teste 1: grafo válido passa; violação injetada é detetada ---------

def test_grafo_valido_passa(g):
    ok, rel = validar_shacl(g)
    assert ok, rel


def test_remissao_para_artigo_inexistente(g):
    g.add((EX.art_6, LG.remetePara, EX.art_999))   # não existe
    ok, rel = validar_shacl(g)
    assert not ok and "inexistente" in rel


def test_prazo_sem_data(g):
    g.remove((EX.prazo_iii_v2, AI.dataPrazo, None))
    ok, _ = validar_shacl(g)
    assert not ok


def test_norma_sem_fonte_normativa(g):
    g.add((EX.obrig_1, AI.Obrigacao, None)) if False else None
    g.add((EX.obrig_1, LG.estadoVerificacao, AI.Candidato))
    from rdflib import RDF
    g.add((EX.obrig_1, RDF.type, AI.Obrigacao))     # sem lg:fonteNormativa
    ok, rel = validar_shacl(g)
    assert not ok and "origem" in rel


def test_sobreposicao_temporal(g):
    g.add((EX.art_113_v2, LG.vigenciaInicio,
           Literal("2026-07-26", datatype=XSD.date)))
    g.remove((EX.art_113_v2, LG.vigenciaInicio,
              Literal("2026-07-27", datatype=XSD.date)))
    ok, rel = validar_shacl(g)
    assert not ok and "sobrepostas" in rel


def test_revisto_sem_revisor(g):
    g.add((EX.prazo_iii_v2, LG.estadoVerificacao, AI.Revisto))
    ok, rel = validar_shacl(g)
    assert not ok and "revistoPor" in rel


# ---- Portão maker-checker ---------------------------------------------

def test_candidato_nao_e_consultavel(g):
    assert C.prazo_em_vigor(g, EX.conjunto_anx_iii, date(2026, 9, 1)) == []


def test_revisto_ja_e_consultavel(g_revisto):
    assert C.prazo_em_vigor(g_revisto, EX.conjunto_anx_iii, date(2026, 9, 1)) \
        == ["2027-12-02"]


# ---- Teste 3: as cinco queries de controlo -----------------------------

def test_asof_antes_da_alteracao(g_revisto):
    assert C.prazo_em_vigor(g_revisto, EX.conjunto_anx_iii, date(2026, 6, 1)) \
        == ["2026-08-02"]


def test_asof_depois_da_alteracao(g_revisto):
    assert C.prazo_em_vigor(g_revisto, EX.conjunto_anx_iii, date(2026, 9, 1)) \
        == ["2027-12-02"]


def test_asof_no_dia_exato_da_alteracao(g_revisto):
    # intervalo semiaberto: 2026-07-27 já pertence à versão nova
    assert C.prazo_em_vigor(g_revisto, EX.conjunto_anx_iii, date(2026, 7, 27)) \
        == ["2027-12-02"]


def test_diff_entre_versoes(g_revisto):
    assert C.diff_prazos(g_revisto) == [("2026-08-02", "2027-12-02", "2026-07-27")]


def test_prazos_alterados_pelo_omnibus(g_revisto):
    assert C.prazos_por_ato(g_revisto, EX.reg_2026_1744) == ["2027-12-02"]


def test_remissao_dois_saltos(g_revisto):
    assert (str(EX.art_6), str(EX.art_3)) in C.dois_saltos(g_revisto)