import copy
from datetime import date
import pytest
from pydantic import ValidationError
from lexgraph.corpus.schema import RegistoCorpus
from lexgraph.corpus.canonical import escrever_jsonl
from lexgraph.corpus.validar import validar_corpus


@pytest.fixture
def base_dict():
    return {
        "unidade_id": "art_113", "tipo": "artigo", "parent_id": "cap_xii",
        "ordem": 113, "rotulo": "Artigo 113.º", "texto": "O presente regulamento…",
        "vigencia": {"inicio": "2024-08-01", "fim": "2026-07-27"},
        "aplicacao": {"inicio": "2024-08-01"},
        "fonte": {"ato_id": "reg_2024_1689", "celex": "32024R1689",
                  "eli": "http://data.europa.eu/eli/reg/2024/1689/oj",
                  "url_oficial": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"},
        "lineage": {"pipeline_versao": "0.1.0", "metodo_extracao": "docling",
                    "fonte_hash": "a" * 64},
    }


# ---- Teste 2: o schema rejeita registos inválidos ----------------------

def test_rejeita_sem_id(base_dict):
    del base_dict["unidade_id"]
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_sem_vigencia(base_dict):
    del base_dict["vigencia"]
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_tipo_invalido(base_dict):
    base_dict["tipo"] = "paragrafo"
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_tipo_incoerente_com_id(base_dict):
    base_dict["tipo"] = "considerando"          # ID é art_113
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_aplicacao_silenciosamente_nula(base_dict):
    base_dict["aplicacao"] = {}                 # nem data nem herança
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_intervalo_degenerado(base_dict):
    base_dict["vigencia"] = {"inicio": "2026-07-27", "fim": "2026-07-27"}
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)

def test_rejeita_campo_extra(base_dict):
    base_dict["interpretacao_llm"] = "alto risco"   # Módulo 0 não interpreta
    with pytest.raises(ValidationError):
        RegistoCorpus(**base_dict)


# ---- Teste 1: determinismo byte-a-byte ---------------------------------

def test_pipeline_determinista(base_dict, tmp_path):
    r = RegistoCorpus(**base_dict)
    h1 = escrever_jsonl([r], tmp_path / "a.jsonl")
    h2 = escrever_jsonl([r], tmp_path / "b.jsonl")
    assert h1 == h2
    assert (tmp_path / "a.jsonl").read_bytes() == (tmp_path / "b.jsonl").read_bytes()

def test_ordem_de_entrada_nao_afeta_hash(base_dict, tmp_path):
    d2 = copy.deepcopy(base_dict)
    d2["vigencia"] = {"inicio": "2026-07-27", "fim": None}
    d2["fonte"]["celex"] = "02024R1689-20260727"
    a, b = RegistoCorpus(**base_dict), RegistoCorpus(**d2)
    assert escrever_jsonl([a, b], tmp_path / "a.jsonl") == \
           escrever_jsonl([b, a], tmp_path / "b.jsonl")

def test_normalizacao_idempotente(base_dict):
    base_dict["texto"] = "  O\u00a0presente   regulamento\u00ad  "
    r = RegistoCorpus(**base_dict)
    assert r.texto == "O presente regulamento"
    assert RegistoCorpus(**{**base_dict, "texto": r.texto}).texto_hash == r.texto_hash


# ---- validação de conjunto ---------------------------------------------

def test_deteta_sobreposicao_de_vigencia(base_dict):
    d2 = copy.deepcopy(base_dict)
    d2["vigencia"] = {"inicio": "2026-07-26", "fim": None}   # um dia cedo demais
    d2["fonte"]["celex"] = "02024R1689-20260727"
    probs = validar_corpus([RegistoCorpus(**base_dict), RegistoCorpus(**d2)])
    assert any(p.codigo == "Sobreposicao" for p in probs)