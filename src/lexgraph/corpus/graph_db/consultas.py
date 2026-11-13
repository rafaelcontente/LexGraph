"""Consultas de controlo do Módulo 1. Parâmetros via initBindings."""
from datetime import date
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import XSD

P = """
PREFIX lg: <https://lexgraph.dev/ns/core#>
PREFIX ai: <https://lexgraph.dev/ns/aiact#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

Q_ASOF = P + """
SELECT ?data ?fonte WHERE {
  ?p a ai:Prazo ; ai:tipoPrazo ai:PrazoAplicacao ;
       ai:regeAplicacaoDe ?conjunto ; ai:dataPrazo ?data ;
       lg:vigenciaInicio ?ini ; lg:fonteNormativa ?fonte ;
       lg:estadoVerificacao ai:Revisto .
  FILTER(?ini <= ?asof)
  OPTIONAL { ?p lg:vigenciaFim ?fim }
  FILTER(!BOUND(?fim) || ?asof < ?fim)
}
"""

Q_DIFF = P + """
SELECT ?conjunto ?antes ?depois ?dataEfeito WHERE {
  ?alt lg:versaoAnterior ?va ; lg:versaoNova ?vn ; lg:dataEfeito ?dataEfeito .
  ?pa lg:fonteNormativa ?va ; ai:regeAplicacaoDe ?conjunto ; ai:dataPrazo ?antes .
  ?pn lg:fonteNormativa ?vn ; ai:regeAplicacaoDe ?conjunto ; ai:dataPrazo ?depois .
  FILTER(?antes != ?depois)
}
"""

Q_DOIS_SALTOS = P + """
SELECT ?origem ?intermedio ?destino WHERE {
  ?origem lg:remetePara ?intermedio .
  ?intermedio lg:remetePara ?destino .
  FILTER(?origem != ?destino)
}
"""

Q_POR_ATO = P + """
SELECT ?prazo ?data ?dataEfeito WHERE {
  ?alt lg:atoAlterador ?ato ; lg:versaoNova ?vn ; lg:dataEfeito ?dataEfeito .
  ?prazo lg:fonteNormativa ?vn ; ai:dataPrazo ?data .
}
"""


def _d(d: date) -> Literal:
    return Literal(d.isoformat(), datatype=XSD.date)


def prazo_em_vigor(g: Graph, conjunto: URIRef, asof: date) -> list[str]:
    rows = g.query(Q_ASOF, initBindings={"conjunto": conjunto, "asof": _d(asof)})
    return [str(r.data) for r in rows]


def diff_prazos(g: Graph) -> list[tuple]:
    return [(str(r.antes), str(r.depois), str(r.dataEfeito)) for r in g.query(Q_DIFF)]


def dois_saltos(g: Graph) -> list[tuple]:
    return [(str(r.origem), str(r.destino)) for r in g.query(Q_DOIS_SALTOS)]


def prazos_por_ato(g: Graph, ato: URIRef) -> list[str]:
    return [str(r.data) for r in g.query(Q_POR_ATO, initBindings={"ato": ato})]