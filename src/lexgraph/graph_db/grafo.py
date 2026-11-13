"""Carregamento, validação SHACL e promoção de estado (maker-checker)."""
from __future__ import annotations
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, URIRef

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")
EX = Namespace("https://lexgraph.dev/data/")

RAIZ = Path(__file__).resolve().parents[3]
ONTOLOGIA = RAIZ / "ontology" / "schema.ttl"
SHAPES = RAIZ / "ontology" / "shapes.shacl"


def carregar(*ficheiros: Path) -> Graph:
    g = Graph()
    for f in ficheiros:
        g.parse(Path(f), format="turtle")
    return g


def validar_shacl(dados: Graph, shapes: Graph | None = None,
                  ontologia: Graph | None = None) -> tuple[bool, str]:
    """Devolve (conforma, relatório legível). Inferência RDFS é obrigatória."""
    shapes = shapes if shapes is not None else carregar(SHAPES)
    ontologia = ontologia if ontologia is not None else carregar(ONTOLOGIA)
    conforma, _rg, texto = validate(
        dados, shacl_graph=shapes, ont_graph=ontologia,
        inference="rdfs", advanced=True, abort_on_first=False, debug=False,
    )
    return bool(conforma), texto


def promover_para_revisto(g: Graph, no: URIRef, revisor: URIRef) -> None:
    """O ato de revisão humana. Só depois disto o triplo é consultável como prova."""
    g.remove((no, LG.estadoVerificacao, None))
    g.add((no, LG.estadoVerificacao, AI.Revisto))
    g.add((no, LG.revistoPor, revisor))
