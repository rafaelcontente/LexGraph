"""
Verificador Simbólico (Módulo 5) - Versão Rigorosa (Open-World Assumption).
Separa estritamente: SUPORTADA, CONTRADITA, NAO_VERIFICAVEL, ABSTENCAO_CORRETA.
Impede que abstenções do LLM sejam classificadas como contradições.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal
from rdflib import Graph, Namespace

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")

StatusVerificacao = Literal["SUPORTADA", "CONTRADITA", "NAO_VERIFICAVEL", "ABSTENCAO_CORRETA"]

@dataclass
class ResultadoVerificacao:
    status: StatusVerificacao
    motivo: str
    evidencia_grafo: str | None = None

def _normalizar(texto: str | None) -> str:
    if texto is None:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

def _e_abstencao(resposta: str) -> bool:
    """Deteta se o LLM se absteve de fazer uma afirmação factual."""
    r = _normalizar(resposta)
    if len(r.strip()) < 15:
        return True
    indicadores = [
        "nao sei", "nao tenho informacao", "nao tenho informacoes",
        "nao consigo encontrar", "nao posso fornecer", "desculpe",
        "nao ha informacoes", "nao ha informacao", "nao e possivel determinar",
        "nao tenho certeza", "sem dados", "desconheco"
    ]
    return any(ind in r for ind in indicadores)

def _contem_texto_no_grafo(grafo: Graph, celex: str, termo: str) -> list[str]:
    termo_norm = _normalizar(termo)
    query = f"""
    PREFIX lg: <https://lexgraph.dev/ns/core#>
    SELECT ?texto WHERE {{
        ?v lg:versaoDe ?u .
        ?u lg:fonteOficial ?ato .
        ?ato lg:celex "{celex}" .
        ?v lg:texto ?texto .
    }}
    """
    encontrados = []
    for row in grafo.query(query):
        if _normalizar(str(row.texto)).find(termo_norm) != -1:
            encontrados.append(str(row.texto)[:150])
            if len(encontrados) >= 2:
                break
    return encontrados

def verificar(questao: dict, resposta_llm: str, grafo: Graph) -> ResultadoVerificacao:
    categoria = questao.get("categoria", "")
    premissa = questao.get("premissa_declarada")
    resposta_norm = _normalizar(resposta_llm)
    
    # ==========================================================
    # REGRA DE OURO: Abstenção nunca é contradição.
    # Se o LLM não fez afirmação, não pode ser contrariado.
    # ==========================================================
    if _e_abstencao(resposta_llm):
        if categoria == "fora_corpus":
            return ResultadoVerificacao("ABSTENCAO_CORRETA", "O modelo absteve-se corretamente de matéria fora do corpus.")
        return ResultadoVerificacao("NAO_VERIFICAVEL", "O modelo absteve-se de responder. Nenhuma afirmação foi feita para ser contrariada pelo grafo.")

    # ==========================================================
    # 1. Premissa Falsa
    # ==========================================================
    if categoria == "premissa_falsa":
        palavras_rejeicao = ["premissa e falsa", "premissa falsa", "incorreto", "nao e verdade", 
                             "nao foi revogado", "foi alterado", "nao se aplica", "nao e exigida"]
        if any(p in resposta_norm for p in palavras_rejeicao):
            return ResultadoVerificacao("SUPORTADA", "O modelo identificou e rejeitou corretamente a premissa falsa.")
        
        # Se chegou aqui, o LLM ACEITOU a premissa (fez uma afirmação positiva).
        # Agora sim, vamos ao grafo procurar a contradição.
        celex_alvo = "32024R1689"
        if "revog" in _normalizar(premissa):
            revog_encontrado = _contem_texto_no_grafo(grafo, celex_alvo, "revog")
            if not revog_encontrado:
                # O grafo não tem "revog". Vamos ver se tem "alterad" para dar contexto.
                alterado = _contem_texto_no_grafo(grafo, celex_alvo, "alterad")
                ev = alterado[0] if alterado else "O ato mantém-se em vigor sem menção de revogação."
                return ResultadoVerificacao(
                    "CONTRADITA",
                    f"O modelo aceitou a premissa de revogação, mas o grafo não contém evidência disso. Evidência de vigência: '{ev[:80]}...'",
                    evidencia_grafo=ev
                )
        return ResultadoVerificacao("NAO_VERIFICAVEL", "Premissa complexa, verificação inconclusiva com a heurística atual.")

    # ==========================================================
    # 2. Temporal / Data
    # ==========================================================
    if categoria == "temporal" or questao.get("tipo_resposta") == "data":
        # (Assumimos que a função de extração de datas já está definida como antes)
        # ... [Manter a lógica de extração de datas do código anterior aqui] ...
        # Para brevidade, vou usar uma versão simplificada da lógica anterior:
        datas_resposta = _extrair_datas_iso(resposta_llm) # Assumindo que esta função existe
        if not datas_resposta:
            return ResultadoVerificacao("NAO_VERIFICAVEL", "Nenhuma data clara na resposta para verificar.")
        
        query = "PREFIX lg: <https://lexgraph.dev/ns/core#> SELECT ?data WHERE { ?s lg:vigenciaInicio ?data . }"
        datas_no_grafo = set(str(row.data) for row in grafo.query(query) if row.data)
        
        datas_encontradas = [d for d in datas_resposta if d in datas_no_grafo]
        if datas_encontradas:
            return ResultadoVerificacao("SUPORTADA", f"Data {datas_encontradas[0]} confirmada no grafo.", evidencia_grafo=datas_encontradas[0])
        
        # CONTRADIÇÃO REAL: O LLM deu uma data, mas essa data NÃO é uma data de vigência no grafo.
        return ResultadoVerificacao(
            "CONTRADITA", 
            f"O modelo afirmou a data {datas_resposta[0]}, mas esta não corresponde a nenhuma data de vigência no grafo para este ato.",
            evidencia_grafo=f"Datas válidas no grafo (exemplo): {sorted(list(datas_no_grafo))[:3]}"
        )

    # ==========================================================
    # 3. Negação e Factual Simples
    # ==========================================================
    if categoria == "negacao":
        esperado = (questao.get("resposta_esperada") or "").lower()
        if "nao" in resposta_norm[:10] and esperado == "nao":
            return ResultadoVerificacao("SUPORTADA", "Negação correta.")
        if "sim" in resposta_norm[:10] and esperado == "sim":
            return ResultadoVerificacao("SUPORTADA", "Afirmação correta.")
        return ResultadoVerificacao("CONTRADITA", f"Afirmação do modelo não alinha com o facto esperado ('{esperado}').")

    if categoria == "factual_simples":
        esperado = (questao.get("resposta_esperada") or "").lower()
        if esperado in resposta_norm:
            return ResultadoVerificacao("SUPORTADA", "Informação confirmada.")
        return ResultadoVerificacao("CONTRADITA", "Informação não encontrada na resposta.")

    # ==========================================================
    # Fallback
    # ==========================================================
    return ResultadoVerificacao("NAO_VERIFICAVEL", "Categoria ou estrutura de resposta não suportada pelo verificador MVP.")

# Função auxiliar de datas (copiada da versão anterior para garantir que funciona)
RE_DATA_PT = re.compile(r"\b(\d{1,2})\s+de\s+([a-zà-ú]+)\s+de\s+(\d{4})\b", re.IGNORECASE)
_MESES = {"janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}
def _extrair_datas_iso(texto: str) -> list[str]:
    datas = []
    for m in RE_DATA_PT.finditer(texto):
        mes = _MESES.get(m.group(2).lower())
        if mes:
            datas.append(f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}")
    return list(set(datas))
