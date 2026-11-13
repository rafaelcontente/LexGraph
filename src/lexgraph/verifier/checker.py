"""
Verificador Simbólico (Módulo 5) - Versão Robusta.
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

def _normalizar(texto: str) -> str:
    """Remove acentos e lowercases para comparação robusta."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

RE_DATA_PT = re.compile(r"\b(\d{1,2})\s+de\s+([a-zà-ú]+)\s+de\s+(\d{4})\b", re.IGNORECASE)
_MESES = {"janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,
          "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}

def _extrair_datas_iso(texto: str) -> list[str]:
    datas = []
    for m in RE_DATA_PT.finditer(texto):
        mes = _MESES.get(m.group(2).lower())
        if mes:
            datas.append(f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}")
    return list(set(datas))

def _contem_texto_no_grafo(grafo: Graph, celex: str, termo: str) -> list[str]:
    """Procura um termo no texto das versões de um ato. Retorna trechos encontrados."""
    termo_norm = _normalizar(termo)
    # Procuramos qualquer substring de 4+ chars do termo normalizado
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
            if len(encontrados) >= 3:
                break
    return encontrados

def verificar(questao: dict, resposta_llm: str, grafo: Graph) -> ResultadoVerificacao:
    categoria = questao.get("categoria", "")
    premissa = questao.get("premissa_declarada", "")
    resposta_norm = _normalizar(resposta_llm)
    premissa_norm = _normalizar(premissa)

    # 1. Fora do Corpus
    if categoria == "fora_corpus":
        recusas = ["nao tenho informacao", "nao sei", "desconhec", "fora do ambito", "nao posso responder"]
        if any(r in resposta_norm for r in recusas) or len(resposta_llm.strip()) < 20:
            return ResultadoVerificacao("ABSTENCAO_CORRETA", "Modelo absteve-se corretamente.")
        return ResultadoVerificacao("CONTRADITA", f"Alucinação fora do corpus: '{resposta_llm[:50]}...'")

    # 2. Premissa Falsa
    if categoria == "premissa_falsa":
        # O LLM rejeitou a premissa?
        palavras_rejeicao = ["premissa e falsa", "premissa falsa", "incorreto", "nao e verdade", 
                             "nao foi revogado", "foi alterado", "nao se aplica", "nao e exigida"]
        if any(p in resposta_norm for p in palavras_rejeicao):
            return ResultadoVerificacao("SUPORTADA", "Modelo rejeitou corretamente a premissa falsa.")
        
        # O LLM aceitou a premissa. Verificar contra o grafo.
        # Estratégia: procurar termos-chave da premissa no grafo do ato relevante
        celex_alvo = "32024R1689"  # AI Act base
        
        # Extrair termos significativos da premissa (palavras > 4 chars)
        termos = [t for t in premissa_norm.split() if len(t) > 4 and t not in 
                  ("regulamento", "digital", "omnibus", "sistemas", "aplicacao", "prazo", "disposicoes")]
        
        if not termos:
            return ResultadoVerificacao("NAO_VERIFICAVEL", "Premissa sem termos verificáveis.")
        
        # Verificar se o termo principal existe no grafo
        termo_principal = termos[0]
        encontrados = _contem_texto_no_grafo(grafo, celex_alvo, termo_principal)
        
        if not encontrados:
            # O termo da premissa não existe no grafo → premissa falsa confirmada
            return ResultadoVerificacao(
                "CONTRADITA",
                f"Premissa contém '{termo_principal}' que não foi encontrado no ato {celex_alvo}.",
                evidencia_grafo=f"Termo '{termo_principal}' ausente no grafo"
            )
        
        # Se encontrou, verificar contexto (ex: "revogado" vs "alterado")
        if "revog" in premissa_norm:
            revog_encontrado = _contem_texto_no_grafo(grafo, celex_alvo, "revog")
            if not revog_encontrado:
                alterado = _contem_texto_no_grafo(grafo, celex_alvo, "alterad")
                ev = alterado[0] if alterado else "Ato mantém-se em vigor."
                return ResultadoVerificacao(
                    "CONTRADITA",
                    f"Premissa alega revogação, mas o grafo não contém 'revog'. Evidência: '{ev[:80]}...'",
                    evidencia_grafo=ev
                )
        
        return ResultadoVerificacao("NAO_VERIFICAVEL", "Premissa parcialmente suportada, verificação inconclusiva.")

    # 3. Temporal / Data
    if categoria == "temporal" or questao.get("tipo_resposta") == "data":
        datas_resposta = _extrair_datas_iso(resposta_llm)
        if not datas_resposta:
            return ResultadoVerificacao("NAO_VERIFICAVEL", "Nenhuma data na resposta.")
        
        query = """
        PREFIX lg: <https://lexgraph.dev/ns/core#>
        SELECT ?data WHERE { ?s lg:vigenciaInicio ?data . }
        """
        datas_no_grafo = set()
        for row in grafo.query(query):
            if row.data:
                datas_no_grafo.add(str(row.data))
                
        datas_encontradas = [d for d in datas_resposta if d in datas_no_grafo]
        
        if datas_encontradas:
            return ResultadoVerificacao("SUPORTADA", f"Data {datas_encontradas[0]} no grafo.", evidencia_grafo=datas_encontradas[0])
        return ResultadoVerificacao(
            "CONTRADITA", 
            f"Datas {datas_resposta} não no grafo. Exemplos: {sorted(datas_no_grafo)[:3]}",
            evidencia_grafo=str(sorted(datas_no_grafo)[:3])
        )

    # 4. Negação
    if categoria == "negacao":
        esperado = (questao.get("resposta_esperada") or "").lower()
        if "nao" in resposta_norm[:10] and esperado == "nao":
            return ResultadoVerificacao("SUPORTADA", "Negação correta.")
        if "sim" in resposta_norm[:10] and esperado == "sim":
            return ResultadoVerificacao("SUPORTADA", "Afirmação correta.")
        return ResultadoVerificacao("CONTRADITA", f"Resposta '{resposta_llm[:30]}' não alinha com esperado '{esperado}'.")

    # 5. Factual simples
    if categoria == "factual_simples":
        esperado = (questao.get("resposta_esperada") or "").lower()
        if esperado in resposta_norm:
            return ResultadoVerificacao("SUPORTADA", "Resposta contém informação esperada.")
        return ResultadoVerificacao("CONTRADITA", f"Resposta não contém '{esperado[:30]}'.")

    return ResultadoVerificacao("NAO_VERIFICAVEL", "Categoria não suportada.")
