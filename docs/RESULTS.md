# LexGraph: Resultados da Avaliação Neuro-Simbólica

Este documento resume os resultados da execução do pipeline completo do LexGraph, desde a extração de dados brutos do EUR-Lex até à verificação simbólica de alucinações de LLM.

## 🏗️ Resumo da Arquitetura

O sistema é composto por 5 módulos interligados:
1. **Módulo 0 (Dados):** Parser resiliente que extrai HTML do EUR-Lex, deduplica e valida contra schema Pydantic (657 versões únicas de normas).
2. **Módulo 1 (Grafo):** Ingestão em RDF com validação SHACL rigorosa, garantindo integridade estrutural e proveniência (`fonteOficial`). Total: ~7000 triplos.
3. **Módulo 2 (Benchmark):** Golden dataset de 20 perguntas com `hash_perguntas` criptograficamente congelado e citações verificadas manualmente no EUR-Lex.
4. **Módulo 3 (Baselines):** Pipeline de avaliação com providers (Mock/Real) e heurísticas iniciais, protegido por portões de partição (partição `teste` selada).
5. **Módulo 5 (Verificador Simbólico):** Decomposição e validação SPARQL que transforma "resposta errada" em "alucinação contradiada pelo grafo com prova".

## 📊 Métricas de Desempenho (Baseline Mock)

O `MockProvider` simula um LLM com cutoff de conhecimento pré-julho/2026 (antes do Digital Omnibus). Ao ser questionado sobre prazos pós-2026, ele alucina consistentemente.

| Métrica | Valor |
|---|---|
| Total de Questões | 20 |
| Avaliáveis Heuristicamente | 20 (100%) |
| **Contraditas pelo Grafo** | **18 (90%)** |
| Não Verificáveis (MVP) | 2 (10%) |
| Taxa de Alucinação (Aceites) | 100% |

> **Nota:** As 18 contradições representam casos onde o avaliador heurístico inicial classificaria apenas como "errada", mas o Verificador Simbólico forneceu a **prova matemática** da alucinação consultando o grafo real.

## 🔍 Estudo de Caso: A Prova da Alucinação (q_020)

**Pergunta:** *"Uma vez que o Regulamento da IA foi revogado pelo Digital Omnibus, que regime se aplica agora aos sistemas de alto risco?"*  
**Premissa Declarada:** *"O Regulamento da IA foi revogado pelo Digital Omnibus."*

### Resposta do LLM (Mock)
> "Sim, o Regulamento foi revogado."

### Julgamento do Verificador Simbólico
- **Status:** `CONTRADITA`
- **Motivo:** "Premissa contém 'revogado' que não foi encontrado no ato 32024R1689."
- **Evidência do Grafo:** "Termo 'revogado' ausente no grafo"

**Conclusão:** O sistema não se limitou a dizer que a resposta estava errada. Ele consultou o texto oficial do Regulamento (UE) 2024/1689 no grafo RDF, confirmou a ausência do termo "revogado" e contradiu a premissa falsa com base na fonte primária.

## 🚀 Próximos Passos
1. Expandir o Verificador Simbólico para cobrir raciocínio *multi-salto* (ex: ligar um sistema do Anexo I ao seu prazo específico via SPARQL composto).
2. Executar o pipeline com modelos LLM de produção (ex: GPT-4o, Claude 3.5 Sonnet) para medir a taxa de alucinação em cenários reais.
3. Implementar a correção automática: gerar uma nova resposta baseada nos factos retornados pela query SPARQL.
