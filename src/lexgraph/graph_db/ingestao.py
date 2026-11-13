"""
Ingestão do Corpus Real no Grafo RDF (Módulo 1, Fase 2).
Lê o JSONL estruturado e gera triplos RDF válidos pelo nosso schema/SHACL.
Garante que cada unidade tenha apenas a sua versão mais recente, evitando sobreposições SHACL.
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

    # 1. Deduplicação Inteligente: manter APENAS a versão mais recente de cada unidade
    # Isto resolve as violações SHACL de "versões sobrepostas"
    versoes_mais_recentes = {}
    
    for r in registos:
        uid = r["unidade_id"]
        vig_inicio = r.get("vigencia", {}).get("inicio", "2024-08-01")
        
        if uid not in versoes_mais_recentes:
            versoes_mais_recentes[uid] = r
        else:
            # Comparar datas: manter a mais recente
            data_atual = versoes_mais_recentes[uid].get("vigencia", {}).get("inicio", "2024-08-01")
            if vig_inicio > data_atual:
                versoes_mais_recentes[uid] = r

    print(f"✅ Deduplicados: {len(registos)} -> {len(versoes_mais_recentes)} versões únicas (mais recentes)")

    # 2. Construção do Grafo
    g = Graph()
    g.bind("lg", LG)
    g.bind("ai", AI)
    g.bind("ex", EX)

    atos_criados = set()

    for uid, r in versoes_mais_recentes.items():
        u_uri = uri(uid)
        tipo = r.get("tipo", "ARTIGO").upper()
        vig_inicio = r.get("vigencia", {}).get("inicio", "2024-08-01")
        texto = r.get("texto", "")
        parent_id = r.get("parent_id")
        celex = r.get("fonte", {}).get("celex", "UNKNOWN")
        url = r.get("fonte", {}).get("url_oficial", "")
        
        data_safe = vig_inicio.replace("-", "")
        v_uri = URIRef(f"{u_uri}_v_{data_safe}")
        ato_uri = EX[f"ato_{celex}"]

        # Criar o nó do Ato (RecursoJuridico) se ainda não existir
        if celex not in atos_criados:
            g.add((ato_uri, RDF.type, LG.RecursoJuridico))
            g.add((ato_uri, LG.celex, Literal(celex)))
            if url:
                g.add((ato_uri, LG.urlOficial, URIRef(url)))
            atos_criados.add(celex)

        # Criar a Unidade Normativa
        if tipo == "ARTIGO":
            g.add((u_uri, RDF.type, AI.Artigo))
        elif tipo in ("PARAGRAFO", "NUMERO"):
            g.add((u_uri, RDF.type, AI.Numero))
        else:
            g.add((u_uri, RDF.type, LG.UnidadeNormativa))

        # Criar a Versão da Unidade (apenas uma por unidade, a mais recente)
        g.add((v_uri, RDF.type, LG.VersaoUnidade))
        g.add((v_uri, LG.versaoDe, u_uri))
        g.add((u_uri, LG.temVersao, v_uri))
        
        # Propriedades da Versão
        g.add((v_uri, LG.texto, Literal(texto)))
        
        # Hash do texto (obrigatório pelo SHACL)
        texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        g.add((v_uri, LG.textoHash, Literal(texto_hash)))
        
        g.add((v_uri, LG.vigenciaInicio, Literal(vig_inicio, datatype=XSD.date)))
        
        # Ligar a versão à fonte oficial (obrigatório pelo SHACL)
        g.add((v_uri, LG.fonteOficial, ato_uri))
        
        # Estado (Maker-Checker: tudo o que entra do parser é Candidato)
        g.add((v_uri, LG.estadoVerificacao, AI.Candidato))

        # Hierarquia (parentesco entre unidades)
        if parent_id:
            p_uri = uri(parent_id)
            # Garantir que o pai existe como UnidadeNormativa
            if (p_uri, RDF.type, None) not in g:
                g.add((p_uri, RDF.type, LG.UnidadeNormativa))
            
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
        print("🎉 Validação SHACL passou com sucesso! O grafo real está pronto e estruturalmente perfeito.")
    else:
        print("⚠️  Aviso de validação SHACL:")
        print(rel[:1500])
        print("\n... (continua no relatório completo se necessário)")


if __name__ == "__main__":
    main()
