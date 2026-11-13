"""Fase 1 do Modulo 0: descarregar atos do EUR-Lex e registar proveniencia.

NAO faz parse nem interpretacao. O HTML bruto e o snapshot imutavel.
O determinismo do pipeline mede-se de raw/ -> corpus, nao de rede -> raw/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[3]
RAW = RAIZ / "data" / "raw"
MANIFEST = RAW / "manifest.json"

UA = ("LexGraph/0.1 (projeto academico de verificacao factual; "
      "contacto: rafaelcontente120@gmail.com)")

# URLs: a forma OJ do 2026/1744 foi confirmada a devolver o texto do ato.
# As formas CELEX sao o padrao canonico do EUR-Lex; o downloader reporta
# status HTTP e contagem de 'Artigo' para tornar qualquer falha visivel.
ATOS = [
    {
        "ato_id": "reg_2024_1689_original",
        "celex": "32024R1689",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:32024R1689",
        "descricao": "Regulamento (UE) 2024/1689 - texto original (2024)",
    },
    {
        "ato_id": "reg_2024_1689_cons_20260727",
        "celex": "02024R1689-20260727",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:02024R1689-20260727",
        "descricao": "Texto consolidado apos o Digital Omnibus (2026-07-27)",
    },
    {
        "ato_id": "reg_2026_1744",
        "celex": "32026R1744",
        "url": "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=OJ:L_202601744",
        "descricao": "Regulamento (UE) 2026/1744 - Digital Omnibus on AI",
    },
]

LICENCA = ("(c) Uniao Europeia. Reutilizacao nos termos da Decisao 2011/833/CE, "
           "com atribuicao de fonte ao EUR-Lex e indicacao de alteracoes. "
           "Confirmar condicoes exatas no aviso legal do EUR-Lex.")


def obter(ato: dict, sessao: requests.Session, forcar: bool) -> dict:
    destino = RAW / f"{ato['ato_id']}.html"
    http = None

    if destino.exists() and not forcar:
        conteudo = destino.read_bytes()
        origem = "cache_local"
    else:
        r = sessao.get(ato["url"], timeout=90, allow_redirects=True)
        http = r.status_code
        r.raise_for_status()
        conteudo = r.content
        destino.write_bytes(conteudo)
        origem = "descarregado"

    texto = conteudo.decode("utf-8", errors="replace")
    n_artigos = texto.count("Artigo ")
    suspeito = len(conteudo) < 20_000 or n_artigos < 20

    return {
        **ato,
        "ficheiro": f"data/raw/{destino.name}",
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "http_status": http,
        "origem": origem,
        "url_final": None if http is None else str(r.url),
        "ocorrencias_artigo": n_artigos,
        "suspeito": suspeito,
        "descarregado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verificado_fonte_oficial": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true",
                    help="re-descarregar mesmo que exista cache local")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": UA, "Accept-Language": "pt"})

    registos = []
    for i, ato in enumerate(ATOS):
        try:
            reg = obter(ato, sessao, args.forcar)
        except requests.RequestException as e:
            print(f"FALHOU {ato['ato_id']}: {e}")
            registos.append({**ato, "erro": str(e), "suspeito": True})
            continue
        marca = "SUSPEITO" if reg["suspeito"] else "ok"
        print(f"[{marca}] {ato['ato_id']}: {reg['bytes']:,} bytes, "
              f"{reg['ocorrencias_artigo']} 'Artigo ', http={reg['http_status']}")
        registos.append(reg)
        if reg["origem"] == "descarregado" and i < len(ATOS) - 1:
            time.sleep(2)          # cortesia: nao martelar o servidor

    manifest = {
        "corpus_versao": "v1",
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "licenca": LICENCA,
        "nota": ("HTML bruto = snapshot imutavel. Determinismo mede-se "
                 "de raw/ para corpus_v1.jsonl, nao de rede para raw/."),
        "atos": registos,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"\nmanifest -> {MANIFEST}")
    return 1 if any(r.get("suspeito") for r in registos) else 0


if __name__ == "__main__":
    raise SystemExit(main())
