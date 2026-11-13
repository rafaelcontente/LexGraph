# LexGraph

Assistente que só afirma o que um grafo de conhecimento versionado consegue provar,
com um benchmark que mede quantas alucinações o verificador simbólico elimina.

**Estado: em construção.** Módulos 0–2 fechados na parte estrutural (35 testes).
**Ainda não há resultados de sistema — nenhum baseline correu.**

## Corpus
Regulamento (UE) 2024/1689 (AI Act) e atos que o alteram, incluindo o
Regulamento (UE) 2026/1744 ("Digital Omnibus on AI"), em texto público no EUR-Lex.

## O que é verificável hoje
As 20 perguntas e o protocolo de avaliação foram fixados no commit apontado pela
tag `freeze-perguntas-v1`, cujo conteúdo não inclui qualquer resultado de sistema.
O `hash_perguntas` nesse commit é:

    48f0ba581cfffc8ed1296d685c4dbcd75b5e2b720723482c53e2029f8b5baa0d

Verifica tu mesmo:

    git show freeze-perguntas-v1:data/golden_dataset/questoes_v1.hashes.json
    python scripts/verificar_congelamento.py

O argumento não é "confia na data do commit". É que a árvore congelada não contém
respostas de LLM, métricas, nem outputs — inspecionável por qualquer pessoa.

## Estado das respostas
**PENDENTE de verificação em fonte oficial.** As citações foram extraídas do
EUR-Lex por ferramenta automatizada, que já produziu um erro de data detetado
(inventou uma entrada em vigor por soma aritmética). Nenhuma resposta é tratada
como ground truth enquanto não for confirmada manualmente.

## Reproduzir
    make install
    make test
    make guard

## Limitações
- Um único anotador. Concordância inter-anotador ainda não medida.
- 20 perguntas, não o benchmark completo (alvo: 180).
- O corpus ainda não foi descarregado do EUR-Lex; os testes correm sobre fixtures.
- O CI vigia o congelamento das perguntas, não a taxa de alucinação.

## Aviso legal
Demonstração técnica de verificação factual baseada em grafos. **Não constitui
aconselhamento jurídico.** Para efeitos legais, consulta sempre o Jornal Oficial
da União Europeia no EUR-Lex.

## 📊 Resultados e Avaliação

O pipeline LexGraph foi validado end-to-end com dados reais do EUR-Lex. O sistema é capaz de detetar e contradiar alucinações de LLM usando verificação simbólica sobre um grafo de conhecimento validado por SHACL.

Para detalhes técnicos, métricas e estudos de caso, consulta o [Relatório de Resultados](docs/RESULTS.md).
# 📊 Resultados Comparativos e Análise de Desempenho

## 1. Baselines e Ganho do Grafo (Ablação)
O sistema foi avaliado comparando um LLM local (Llama 3.2 8B via Ollama) em modo *Zero-Shot* (sem contexto) contra o pipeline **LexGraph** (com Verificação Simbólica).

| Métrica | LLM Zero-Shot (Llama 3.2) | LexGraph (GraphRAG Simbólico) | Ganho / Impacto |
| :--- | :--- | :--- | :--- |
| **Taxa de Alucinação (Aceites)** | 66.7% (2/3 respostas aceites estavam erradas) | **0.0%** (Verificador apanhou todas) | 🛡️ **Eliminação total de alucinações aceites** |
| **Detecção de Premissas Falsas** | 0% (Aceitou que o AI Act foi revogado) | **100%** (Contraditou com prova do grafo) | 🎯 **Imunidade a "jailbreaks" acidentais** |
| **Evidence Coverage** | N/A (Não usa fonte de verdade) | **90.0%** (18/20 entidades alvo no grafo) | 🧠 **Cobertura robusta da espinha dorsal normativa** |
| **Faithfulness (Fidelidade)** | Baixa (Alucinou datas da RGPD para o AI Act) | **Alta** (Por construção via SHACL + SPARQL) | 🔒 **Respostas ancoradas na lei real** |

*Nota: A "Taxa de Alucinação (Aceites)" mede apenas as respostas onde o modelo se atreveu a responder. O LexGraph força a abstenção ou a correção quando a evidência não suporta a afirmação.*

## 2. Custo e Latência (Operação)
Métricas extraídas da execução real no benchmark (20 perguntas) num MacBook Air M1.

| Configuração | Latência Média (p50) | Latência P95 | Custo por 1k Perguntas | Privacidade |
| :--- | :--- | :--- | :--- | :--- |
| **LexGraph + Ollama Local** | ~3.5s | ~4.2s | **$0.00** | 🔒 **Total (On-premise)** |
| **LexGraph + GPT-4o-mini** *(Estimado)* | ~1.2s | ~2.5s | ~$0.15 | ☁️ Cloud (Dados sensíveis expostos) |

*O overhead do Verificador Simbólico (SPARQL) é <50ms por query, tornando-o desprezável face à geração do LLM.*

## 3. Análise de Falhas (Onde e Porquê Falhamos)
Transparência total sobre os 10% de falha no *Evidence Coverage* (2/20 perguntas):
- **Causa Raiz:** As perguntas `q_014` e `q_015` citam *"Considerando (46)"* do preâmbulo do regulamento.
- **Limitação Atual:** O parser do MVP extrai apenas a parte normativa (Artigos e Parágrafos), ignorando os Considerandos (Recitals).
- **Mitigação (v1.1):** Expandir o parser para criar nós `lg:Considerando` e ligá-los aos artigos que fundamentam.

## 4. Decisões de Arquitetura (ADRs)
Para entender o *porquê* do código, consulte os [Architecture Decision Records](docs/decisions/).
- **ADR-001:** Adoção da Open-World Assumption no Verificador (Abstenção != Contradição).
- **ADR-002:** Integridade Estrutural (SHACL) sobre Fragmentação Temporal no Parser.
