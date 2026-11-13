"""Gera o seed do golden dataset. Respostas PENDENTES de verificação humana."""
from pathlib import Path
from lexgraph.benchmark.schema import Categoria, Evidencia, Questao, Estado
from lexgraph.benchmark.congelar import escrever

URL_OMNI = "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=OJ:L_202601744"
URL_BASE = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"

# ── Blocos de evidência reutilizados ──────────────────────────────────
E_C = Evidencia(
    celex="32026R1744",
    localizador="Art. 1.º, ponto 40, al. b) → art. 113.º, 3.º parágrafo, al. c)",
    citacao_literal=(
        "c) O capítulo III, secções 1, 2 e 3, com exceção do artigo 6.o, n.o 5, "
        "é aplicável a partir de: i) 2 de dezembro de 2027, no que diz respeito "
        "aos sistemas de IA classificados como sendo de risco elevado nos termos "
        "do artigo 6.o, n.o 2, e do anexo III, e ii) 2 de agosto de 2028, no que "
        "diz respeito aos sistemas de IA classificados como sendo de risco elevado "
        "nos termos do artigo 6.o, n.o 1, e do anexo I;"
    ),
    url=URL_OMNI, unidade_id="art_113_par_3_al_c",
)
E_A = Evidencia(
    celex="32026R1744",
    localizador="Art. 1.º, ponto 40, al. a) → art. 113.º, 3.º parágrafo, al. a)",
    citacao_literal=(
        "a) Os capítulos I e II são aplicáveis a partir de 2 de fevereiro de 2025, "
        "com exceção do artigo 5.o, n.o 1, primeiro parágrafo, alíneas b-A) e b-B), "
        "e do artigo 5.o, n.os 1-A e 1-B, que são aplicáveis a partir de "
        "2 de dezembro de 2026;"
    ),
    url=URL_OMNI, unidade_id="art_113_par_3_al_a",
)
E_D = Evidencia(
    celex="32026R1744",
    localizador="Art. 1.º, ponto 40, al. c) → art. 113.º, 3.º parágrafo, al. d)",
    citacao_literal="d) Os artigos 102.o a 110.o são aplicáveis a partir de 27 de julho de 2026.",
    url=URL_OMNI, unidade_id="art_113_par_3_al_d",
)
E_VIG = Evidencia(
    celex="32026R1744",
    localizador="Considerando (46)",
    citacao_literal=(
        "o presente regulamento deverá entrar em vigor com caráter de urgência "
        "no terceiro dia seguinte ao da sua publicação no Jornal Oficial da União Europeia."
    ),
    url=URL_OMNI,
)
# ⚠️ A OBTENHER: texto original do art. 113.º (versão 2024). Sem isto,
# as perguntas "antes da alteração" não podem ser verificadas.
E_ORIG = Evidencia(
    celex="32024R1689",
    localizador="Art. 113.º, 3.º parágrafo [TEXTO ORIGINAL — A CONFIRMAR]",
    citacao_literal="[A PREENCHER AMANHÃ A PARTIR DO EUR-LEX]",
    url=URL_BASE, unidade_id="art_113",
)

Q = []
def add(**kw): Q.append(Questao(estado=Estado.PENDENTE, particao="dev", **kw))

# ── Bloco C: prazos de alto risco ─────────────────────────────────────
add(id="q_001", categoria=Categoria.TEMPORAL, dificuldade="media", pos_cutoff=True,
    asof="2026-09-01", tipo_resposta="data", resposta_esperada="2027-12-02",
    pergunta="A 1 de setembro de 2026, qual é a data de aplicação das obrigações do Capítulo III, secções 1 a 3, para sistemas de IA de alto risco classificados nos termos do artigo 6.º, n.º 2, e do Anexo III?",
    evidencias=(E_C,))
add(id="q_002", categoria=Categoria.TEMPORAL, dificuldade="dificil", pos_cutoff=True,
    asof="2026-07-27", tipo_resposta="data", resposta_esperada="2027-12-02",
    pergunta="No dia exato em que o Regulamento (UE) 2026/1744 entrou em vigor, qual passa a ser a data de aplicação referida no artigo 113.º, terceiro parágrafo, alínea c), subalínea i)?",
    evidencias=(E_C, E_VIG))
add(id="q_003", categoria=Categoria.TEMPORAL, dificuldade="dificil", pos_cutoff=False,
    asof="2026-06-01", tipo_resposta="data", resposta_esperada="2026-08-02",
    pergunta="A 1 de junho de 2026, qual era a data de aplicação prevista para as obrigações de alto risco do Anexo III?",
    evidencias=(E_ORIG,), notas="Requer texto original do art. 113.º.")
add(id="q_004", categoria=Categoria.MULTI_SALTO, dificuldade="dificil", pos_cutoff=True,
    tipo_resposta="data", resposta_esperada="2028-08-02",
    pergunta="Um sistema de IA de alto risco integrado num produto abrangido pelo Anexo I: a partir de que data se lhe aplicam as obrigações do Capítulo III, secções 1 a 3?",
    evidencias=(E_C,))
add(id="q_005", categoria=Categoria.NEGACAO, dificuldade="media", pos_cutoff=True,
    tipo_resposta="sim_nao", resposta_esperada="Não",
    pergunta="O artigo 6.º, n.º 5, está abrangido pela data de aplicação de 2 de dezembro de 2027 fixada no artigo 113.º, terceiro parágrafo, alínea c)?",
    procura_negativa="A al. c) contém a exceção expressa «com exceção do artigo 6.o, n.o 5». Confirmar que nenhuma outra disposição do ato alterador reintroduz o art. 6.º n.º 5 nesse âmbito.",
    evidencias=(E_C,))
add(id="q_006", categoria=Categoria.PREMISSA_FALSA, dificuldade="dificil", pos_cutoff=True,
    tipo_resposta="texto_curto",
    resposta_esperada="A premissa é falsa: o artigo 6.º, n.º 5, está expressamente excetuado do âmbito da alínea c).",
    premissa_declarada="Todas as disposições do Capítulo III, secções 1 a 3, sem exceção, passaram a aplicar-se a 2 de dezembro de 2027.",
    pergunta="Sabendo que todas as disposições do Capítulo III, secções 1 a 3, sem exceção, passaram a aplicar-se a 2 de dezembro de 2027, o que deve um fornecedor fazer ao abrigo do artigo 6.º, n.º 5, nessa data?",
    evidencias=(E_C,))
add(id="q_007", categoria=Categoria.PREMISSA_FALSA, dificuldade="media", pos_cutoff=True,
    tipo_resposta="texto_curto",
    resposta_esperada="A premissa é falsa: o Anexo III aplica-se a partir de 2 de dezembro de 2027; 2 de agosto de 2028 é a data do Anexo I.",
    premissa_declarada="O prazo de aplicação para sistemas de alto risco do Anexo III é 2 de agosto de 2028.",
    pergunta="Considerando que o prazo de aplicação para sistemas de alto risco do Anexo III é 2 de agosto de 2028, quantos meses de preparação restam a partir de janeiro de 2027?",
    evidencias=(E_C,))
add(id="q_008", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="facil", pos_cutoff=True,
    tipo_resposta="texto_curto", resposta_esperada="Regulamento (UE) 2026/1744",
    pergunta="Que ato alterou o artigo 113.º do Regulamento (UE) 2024/1689 no que respeita às datas de aplicação?",
    evidencias=(E_C,))

# ── Bloco A: capítulos I e II ─────────────────────────────────────────
add(id="q_009", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="facil", pos_cutoff=False,
    tipo_resposta="data", resposta_esperada="2025-02-02",
    pergunta="A partir de que data se aplicam, como regra geral, os Capítulos I e II do Regulamento da IA?",
    evidencias=(E_A,))
add(id="q_010", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="media", pos_cutoff=True,
    tipo_resposta="data", resposta_esperada="2026-12-02",
    pergunta="A partir de que data se aplicam o artigo 5.º, n.os 1-A e 1-B?",
    evidencias=(E_A,))
add(id="q_011", categoria=Categoria.PREMISSA_FALSA, dificuldade="media", pos_cutoff=True,
    tipo_resposta="texto_curto",
    resposta_esperada="A premissa é falsa: há exceções ao artigo 5.º que só se aplicam a partir de 2 de dezembro de 2026.",
    premissa_declarada="Os Capítulos I e II aplicam-se integralmente, sem exceções, desde 2 de fevereiro de 2025.",
    pergunta="Uma vez que os Capítulos I e II se aplicam integralmente, sem exceções, desde 2 de fevereiro de 2025, todas as proibições do artigo 5.º são exigíveis desde essa data?",
    evidencias=(E_A,))

# ── Bloco D: artigos 102.º a 110.º ────────────────────────────────────
add(id="q_012", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="media", pos_cutoff=True,
    tipo_resposta="data", resposta_esperada="2026-07-27",
    pergunta="A partir de que data se aplicam os artigos 102.º a 110.º do Regulamento da IA?",
    evidencias=(E_D,))
add(id="q_013", categoria=Categoria.TEMPORAL, dificuldade="media", pos_cutoff=True,
    asof="2026-07-26", tipo_resposta="sim_nao", resposta_esperada="Não",
    pergunta="A 26 de julho de 2026, os artigos 102.º a 110.º já se aplicavam?",
    evidencias=(E_D,))

# ── Bloco VIG: entrada em vigor ───────────────────────────────────────
add(id="q_014", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="media", pos_cutoff=True,
    tipo_resposta="texto_curto",
    resposta_esperada="No terceiro dia seguinte ao da sua publicação no Jornal Oficial da União Europeia.",
    pergunta="Qual é a regra de entrada em vigor estabelecida para o Regulamento (UE) 2026/1744?",
    evidencias=(E_VIG,))
add(id="q_015", categoria=Categoria.FACTUAL_SIMPLES, dificuldade="media", pos_cutoff=True,
    tipo_resposta="data", resposta_esperada="2026-07-27",
    pergunta="Em que data entrou em vigor o Regulamento (UE) 2026/1744?",
    evidencias=(E_VIG,),
    notas="A data não consta do articulado; exige confirmar a data de publicação no JO. NÃO aceitar data inferida por soma aritmética.")

# ── Fora do corpus: medem abstenção correta ───────────────────────────
add(id="q_016", categoria=Categoria.FORA_CORPUS, dificuldade="facil", pos_cutoff=False,
    tipo_resposta="sem_resposta", resposta_esperada=None,
    procura_negativa="O Regulamento não contém decisões de aplicação individual nem registos de coimas aplicadas. Confirmar por pesquisa de «coima» e «sanção» no articulado: existem normas sobre o regime, não sobre casos concretos.",
    pergunta="Qual o valor da coima aplicada pela autoridade portuguesa competente a uma empresa concreta ao abrigo do Regulamento da IA em 2026?")
add(id="q_017", categoria=Categoria.FORA_CORPUS, dificuldade="media", pos_cutoff=False,
    tipo_resposta="sem_resposta", resposta_esperada=None,
    procura_negativa="O Regulamento não contém estatísticas de registo nem dados de execução. Confirmar ausência de qualquer anexo com contagens de sistemas registados.",
    pergunta="Qual é a percentagem de sistemas de IA de alto risco já registados na base de dados da UE?")
add(id="q_018", categoria=Categoria.FORA_CORPUS, dificuldade="dificil", pos_cutoff=False,
    tipo_resposta="sem_resposta", resposta_esperada=None,
    procura_negativa="O Regulamento não classifica fornecedores individuais nem emite juízos sobre empresas nomeadas. Pesquisa por nomes de empresas no articulado e anexos: ausência total.",
    pergunta="A empresa X é considerada fornecedora de alto risco aos olhos do Regulamento da IA?")

# ── Negação sobre conteúdo não exigido ────────────────────────────────
add(id="q_019", categoria=Categoria.NEGACAO, dificuldade="dificil", pos_cutoff=False,
    tipo_resposta="sim_nao", resposta_esperada="Não",
    procura_negativa="Pesquisa de «ISO 9001» e «ISO/IEC 9001» no articulado e anexos do Regulamento e do ato alterador: confirmar ausência. O Regulamento remete para normas harmonizadas, não impõe certificação ISO 9001.",
    pergunta="O Regulamento da IA exige que os fornecedores de sistemas de alto risco obtenham certificação ISO 9001?",
    evidencias=(E_C,), notas="Evidência a substituir pelo resultado documentado da procura.")
add(id="q_020", categoria=Categoria.PREMISSA_FALSA, dificuldade="media", pos_cutoff=True,
    tipo_resposta="texto_curto",
    resposta_esperada="A premissa é falsa: o Regulamento (UE) 2024/1689 foi alterado, não revogado, pelo Regulamento (UE) 2026/1744.",
    premissa_declarada="O Regulamento da IA foi revogado pelo Digital Omnibus.",
    pergunta="Uma vez que o Regulamento da IA foi revogado pelo Digital Omnibus, que regime se aplica agora aos sistemas de alto risco?",
    evidencias=(E_C,))

if __name__ == "__main__":
    destino = Path("data/golden_dataset/questoes_v1.jsonl")
    print(escrever(Q, destino))
    print(f"{len(Q)} perguntas escritas. Estado: PENDENTE.")