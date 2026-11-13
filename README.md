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
