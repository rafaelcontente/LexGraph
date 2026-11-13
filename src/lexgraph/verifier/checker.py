"""
Verificador Simbólico (Módulo 5).
Valida respostas de LLM contra o grafo RDF real usando SPARQL.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal
from rdflib import Graph, Literal as RDFLiteral, Namespace
from rdflib.namespace import XSD

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")

StatusVerificacao = Literal["SUPORTADA", "CONTRADITA", "NAO_VERIFICAVEL", "ABSTENCAO_CORRETA"]

@dataclass
class ResultadoVerificacao:
    status: StatusVerificacao
    motivo: str
    evidencia_grafo: str | None = None

# Regex para extrair datas (reutilizado do avaliador)
RE_DATA_PT = re.compile(r"\b(\d{1,2})\s+de\s+([a-zà-ú]+)\s+de\s+(\d{4})\b", re.IGNORECASE)
_MESES = {"janeiro":1,"fevereiro":2,"marco":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12}

def _extrair_datas_iso(texto: str) -> list[str]:
    datas = []
    for m in RE_DATA_PT.finditer(texto):
        mes = _MESES.get(m.group(2).lower())
        if mes:
            datas.append(f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}")
    return list(set(datas))

def verificar(questao: dict, resposta_llm: str, grafo: Graph) -> ResultadoVerificacao:
    """
    Verifica uma resposta de LLM contra o grafo.
    questao: dicionário carregado do baseline JSONL.
    resposta_llm: texto gerado pelo modelo.
    grafo: instância rdflib.Graph com os dados reais.
    """
    categoria = questao.get("categoria", "")
    
    # 1. Verificação de Fora do Corpus (Abstenção)
    if categoria == "fora_corpus":
        # Heurística simples: se a resposta tiver mais de 20 caracteres e não for uma recusa clara, é alucinação
        recusas = ["não tenho informação", "não sei", "desconhec", "fora do âmbito"]
        if any(r in resposta_llm.lower() for r in recusas) or len(resposta_llm.strip()) < 15:
            return ResultadoVerificacao("ABSTENCAO_CORRETA", "Modelo absteve-se corretamente de matéria fora do corpus.")
        else:
            return ResultadoVerificacao("CONTRADITA", f"Modelo alucinou resposta fora do corpus: '{resposta_llm[:50]}...'")

    # 2. Verificação Temporal / Data
    if categoria == "temporal" or questao.get("tipo_resposta") == "data":
        datas_resposta = _extrair_datas_iso(resposta_llm)
        if not datas_resposta:
            return ResultadoVerificacao("NAO_VERIFICAVEL", "Nenhuma data identificada na resposta do LLM para verificar.")
        
        # Query SPARQL: procurar datas de vigência ou aplicação no grafo
        # Nota: simplificamos procurando qualquer data no grafo que corresponda à extraída
        query = """
        PREFIX lg: <https://lexgraph.dev/ns/core#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?data WHERE {
            ?s lg:vigenciaInicio ?data .
        }
        """
        # Para ser mais preciso, podíamos filtrar por ?s sendo a unidade da pergunta, 
        # mas para este MVP verificamos se a data existe *algures* no grafo como vigência.
        # Uma versão avançada ligaria a pergunta à unidade_id específica.
        
        datas_no_grafo = set()
        for row in grafo.query(query):
            if row.data:
                datas_no_grafo.add(str(row.data))
                
        # Verificar se alguma data da resposta está no grafo
        datas_encontradas = [d for d in datas_resposta if d in datas_no_grafo]
        
        if datas_encontradas:
            return ResultadoVerificacao(
                "SUPORTADA", 
                f"A data {datas_encontradas[0]} foi encontrada no grafo como data de vigência/aplicação.",
                evidencia_grafo=datas_encontradas[0]
            )
        else:
            return ResultadoVerificacao(
                "CONTRADITA", 
                f"As datas {datas_resposta} não foram encontradas no grafo. Datas no grafo: {sorted(list(datas_no_grafo)[:5])}..."
            )

    # 3. Fallback para outras categorias (MVP)
    return ResultadoVerificacao("NAO_VERIFICAVEL", "Categoria ainda não suportada pelo verificador simbólico MVP.")
