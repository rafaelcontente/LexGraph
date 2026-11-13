"""
Ingestão do Corpus Real no Grafo RDF (Módulo 1, Fase 2).
Lê o JSONL estruturado e gera triplos RDF válidos pelo nosso schema/SHACL.
"""
import hashlib
import json
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

from lexgraph.graph_db.grafo import validar_shacl, ONTOLOGIA, SHAPES

LG = Namespace("https://lexgraph.dev/ns/core#")
AI = Namespace("https://lexgraph.dev/ns/aiact#")
EX = Namespace("https://lexgraph.dev/data/")

INTERIM = Path("data/interim/corpus_v1.jsonl")
GRAPH_OUT = Path("data/graph/corpus_real.ttl")


def uri(uid: str) -> URIRef:
    return EX[uid.replace(".", "_").replace("-", "_")]


def main():
    if not INTERIM.exists():
        print(f"❌ Ficheiro não encontrado: {INTERIM}")
        print("Corre primeiro: python scripts/run_parser.py")
        return

    with open(INTERIM, "r", encoding="utf-8") as f:
        registos = [json.loads(line) for line in f if line.strip()]

    print(f"📥 Lidos {len(registos)} registos de {INTERIM}")

    # 1. Deduplicação: manter a versão com o texto mais longo
    versoes = {}
    atos_info = {} # Para rastrear os atos (celex, url)
    
    for r in registos:
        uid = r["unidade_id"]
        vig_inicio = r.get("vigencia", {}).get("inicio", "2024-08-01")
        data_safe = vig_inicio.replace("-", "")
        v_uri_str = f"{uid}_v_{data_safe}"
        
        texto = r.get("texto", "")
        celex = r.get("fonte", {}).get("celex", "UNKNOWN")
        url = r.get("fonte", {}).get("url_oficial", "")
        
        atos_info[celex] = url
        
        if v_uri_str in versoes:
            if len(texto) > len(versoes[v_uri_str]["texto"]):
                versoes[v_uri_str]["texto"] = texto
                versoes[v_uri_str]["tipo"] = r.get("tipo", "ARTIGO").upper()
                versoes[v_uri_str]["parent_id"] = r.get("parent_id")
                versoes[v_uri_str]["celex"] = celex
        else:
            versoes[v_uri_str] = {
                "uid": uid,
                "tipo": r.get("tipo", "ARTIGO").upper(),
                "parent_id": r.get("parent_id"),
                "texto": texto,
                "vig_inicio": vig_inicio,
                "celex": celex
            }

    print(f"✅ Deduplicados: {len(registos)} -> {len(versoes)} versões únicas")

    # 2. Construção do Grafo
    g = Graph()
    g.bind("lg", LG)
    g.bind("ai", AI)
    g.bind("ex", EX)

    unidades_criadas = set()
    atos_criados = set()

    for v_str, dados in versoes.items():
        uid = dados["uid"]
        u_uri = uri(uid)
        tipo = dados["tipo"]
        vig_inicio = dados["vig_inicio"]
        texto = dados["texto"]
        parent_id = dados["parent_id"]
        celex = dados["celex"]
        
        data_safe = vig_inicio.replace("-", "")
        v_uri = URIRef(f"{u_uri}_v_{data_safe}")
        ato_uri = EX[f"ato_{celex}"]

        # Criar o nó do Ato (RecursoJuridico) se ainda não existir
        if celex not in atos_criados:
            g.add((ato_uri, RDF.type, LG.RecursoJuridico))
            g.add((ato_uri, LG.celex, Literal(celex)))
            if atos_info.get(celex):
                g.add((ato_uri, LG.urlOficial, URIRef(atos_info[celex])))
            atos_criados.add(celex)

        # Criar a Unidade Normativa (se ainda não existir)
        if uid not in unidades_criadas:
            if tipo == "ARTIGO":
                g.add((u_uri, RDF.type, AI.Artigo))
            elif tipo in ("PARAGRAFO", "NUMERO"):
                g.add((u_uri, RDF.type, AI.Numero))
            else:
                g.add((u_uri, RDF.type, LG.UnidadeNormativa))
            unidades_criadas.add(uid)

        # Criar a Versão da Unidade
        g.add((v_uri, RDF.type, LG.VersaoUnidade))
        g.add((v_uri, LG.versaoDe, u_uri))
        g.add((u_uri, LG.temVersao, v_uri))
        
        # Propriedades da Versão
        g.add((v_uri, LG.texto, Literal(texto)))
        
        # Hash do texto (obrigatório pelo SHACL)
        texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        g.add((v_uri, LG.textoHash, Literal(texto_hash)))
        
        g.add((v_uri, LG.vigenciaInicio, Literal(vig_inicio, datatype=XSD.date)))
        
        # CORREÇÃO: Ligar a versão à fonte oficial (obrigatório pelo SHACL)
        g.add((v_uri, LG.fonteOficial, ato_uri))
        
        # Estado (Maker-Checker: tudo o que entra do parser é Candidato)
        g.add((v_uri, LG.estadoVerificacao, AI.Candidato))

        # Hierarquia (parentesco entre unidades)
        if parent_id:
            p_uri = uri(parent_id)
            if parent_id not in unidades_criadas:
                g.add((p_uri, RDF.type, LG.UnidadeNormativa))
                unidades_criadas.add(parent_id)
            
            g.add((p_uri, LG.temParte, u_uri))
            g.add((u_uri, LG.parteDe, p_uri))

    # 3. Guardar grafo
    GRAPH_OUT.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=GRAPH_OUT, format="turtle")
    print(f"✅ Grafo gerado: {GRAPH_OUT} ({len(g)} triplos)")

    # 4. Validar com SHACL
    print("🔍 A validar com SHACL...")
    ok, rel = validar_shacl(g)
    if ok:
        print("🎉 Validação SHACL passou com sucesso! O grafo real está pronto.")
    else:
        print("⚠️  Aviso de validação SHACL:")
        print(rel[:1500])
        print("\n... (continua no relatório completo se necessário)")


if __name__ == "__main__":
    main()
