import pytest
from lexgraph.baselines.providers import MockProvider, criar_provider
from lexgraph.baselines.avaliar import julgar, _datas_na_resposta
from lexgraph.benchmark.schema import Categoria, Evidencia, Estado, Particao, Questao

EV = Evidencia(celex="32026R1744", localizador="Art. 1.o", citacao_literal="texto oficial", url="https://eur-lex.europa.eu/")

def _q(**kw):
    # Base válida para uma pergunta TEMPORAL (o caso mais comum nos testes)
    base = {
        "id": "q_001",
        "categoria": Categoria.TEMPORAL,
        "dificuldade": "media",
        "pos_cutoff": True,
        "particao": Particao.DEV,
        "tipo_resposta": "data",
        "resposta_esperada": "2027-12-02",
        "asof": "2026-09-01",
        "pergunta": "Qual a data de aplicacao do Anexo III?",
        "evidencias": (EV,),
        "estado": Estado.VERIFICADO,
        "verificado_por": "Rafael",
        "verificado_em": "2026-11-13"
    }
    base.update(kw)
    
    # Regra do schema: asof só se aplica a perguntas temporais
    if base.get("categoria") != Categoria.TEMPORAL:
        base.pop("asof", None)
        
    # Regra do schema: fora_corpus exige resposta_esperada=None e tipo_resposta="sem_resposta"
    if base.get("categoria") == Categoria.FORA_CORPUS:
        base["resposta_esperada"] = None
        base["tipo_resposta"] = "sem_resposta"
        
    return Questao(**base)

def test_mock_deterministico():
    p = MockProvider()
    a = p.generate("data de aplicacao do anexo iii")
    b = p.generate("data de aplicacao do anexo iii")
    assert a.texto == b.texto

def test_datas_extraidas():
    assert "2027-12-02" in _datas_na_resposta("aplica a 2 de dezembro de 2027")
    assert "2026-08-02" in _datas_na_resposta("a partir de 2026-08-02")

def test_temporal_errada_mock():
    r = julgar(_q(), "2 de agosto de 2026")
    assert r.status == "errada"

def test_temporal_correta():
    r = julgar(_q(), "2 de dezembro de 2027")
    assert r.status == "correta"

def test_fora_corpus_abstencao_correta():
    q = _q(categoria=Categoria.FORA_CORPUS, procura_negativa="ausencia confirmada")
    assert julgar(q, "Nao tenho informacao sobre isso.").status == "correta"
    assert julgar(q, "A coima foi 15 milhoes.").status == "errada"

def test_premissa_falsa_rejeitada():
    q = _q(categoria=Categoria.PREMISSA_FALSA, tipo_resposta="texto_curto", premissa_declarada="foi revogado", resposta_esperada="A premissa e falsa")
    assert julgar(q, "A premissa e falsa, foi alterado nao revogado.").status == "correta"

def test_multi_salto_fica_pendente():
    q = _q(categoria=Categoria.MULTI_SALTO, tipo_resposta="lista", resposta_esperada="x")
    j = julgar(q, "resposta qualquer")
    assert j.status == "pendente" and j.avaliavel is False

def test_portao_bloqueia_particao_teste():
    from lexgraph.baselines.runner import correr
    with pytest.raises(RuntimeError, match="SELADA"):
        correr("mock", particao=Particao.TESTE)

def test_metricas_conjunto_anti_gaming():
    from lexgraph.baselines.runner import metricas
    res = [
        {"avaliavel": True, "status": "correta", "categoria": "temporal"}, 
        {"avaliavel": True, "status": "errada", "categoria": "temporal"}, 
        {"avaliavel": False, "status": "pendente", "categoria": "multi_salto"}
    ]
    m = metricas(res)
    assert m["cobertura"] == round(2/3, 3)
    assert m["taxa_alucinacao_aceites"] == 0.5
    assert m["pendentes_verificador"] == 1
