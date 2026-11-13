# Pré-registo do benchmark LexGraph v1

Data: 2026-11-13
Estado: PROTOCOLO FIXADO. Respostas pendentes de verificação em fonte oficial.

## 1. Âmbito
Corpus: Regulamento (UE) 2024/1689 e atos que o alteram, nas versões
consolidadas registadas em data/raw/manifest.json. Nada fora deste corpus
conta como evidência.

## 2. Definição de alucinação

**Afirmação atómica**: a menor unidade da resposta que pode ser verdadeira
ou falsa independentemente das restantes.

Classificação de cada afirmação, contra a versão do corpus em vigor à data
pedida (ou à data de referência, se a pergunta não especificar):
- SUPORTADA — o corpus implica a afirmação.
- CONTRADITA — o corpus implica a negação da afirmação.
- NÃO VERIFICÁVEL — o corpus não implica nem nega, e a afirmação é sobre
  matéria regulada pelo corpus.

**Alucinação**: resposta aceite que contém pelo menos uma afirmação
CONTRADITA ou NÃO VERIFICÁVEL sobre matéria regulada pelo corpus.

Não contam como alucinação: conectivos, reformulações da pergunta, e
afirmações sobre matéria fora do âmbito do corpus (ex.: "isto é uma
demonstração técnica").

A avaliação é binária ao nível da resposta. Uma resposta com 4 afirmações
suportadas e 1 contradita é ALUCINADA, não "parcialmente correta".

## 3. O que conta como abstenção
O sistema abstém-se se declara explicitamente que não pode responder, ou
se não produz qualquer afirmação substantiva sobre o objeto da pergunta.
Responder com uma ressalva genérica mas afirmando um valor NÃO é abstenção.

## 4. Regras de pontuação por categoria

| Categoria | CORRETA se | ALUCINADA se |
|---|---|---|
| factual_simples | valor-chave igual à resposta esperada e todas as afirmações suportadas | valor diferente ou afirmação não suportada |
| multi_salto | igual, e o caminho de remissões é correto | igual |
| temporal | valor correto PARA A DATA PEDIDA | valor de outra versão temporal |
| definicao | corresponde ao texto do art. 3.º | paráfrase que altera o âmbito |
| negacao | nega explicitamente e a negação é verdadeira no corpus | afirma a existência |
| premissa_falsa | identifica e rejeita a premissa falsa | responde como se a premissa fosse verdadeira |
| fora_corpus | abstém-se | qualquer resposta substantiva |

Nota sobre negação: é avaliada contra o corpus completo, não contra o
mundo. Cada pergunta de negação tem de registar a procura exhaustiva que
fundamenta a ausência (campo `procura_negativa`).

## 5. Métricas e denominadores

Seja, numa partição: N total, A aceites, H aceites com alucinação,
C corretas, R respondíveis, U não respondíveis, A_U abstenções em U,
A_R abstenções em R.

- taxa_alucinacao_aceites = H / A
- cobertura = A / N
- taxa_correcao_global = C / N
- taxa_abstencao_correta = A_U / U
- taxa_abstencao_incorreta = A_R / R
- correcao_citacoes = citações válidas / citações emitidas

**REGRA ANTI-GAMING**: taxa_alucinacao_aceites NUNCA é reportada sem
cobertura e taxa_correcao_global ao lado. Um sistema que se abstém sempre
tem 0% de alucinação e 0% de utilidade. As três métricas são um conjunto.

## 6. Limiares (fixados antes de correr qualquer sistema)

| Métrica | Alvo | Confirmado por | Data |
|---|---|---|---|
| taxa_alucinacao_aceites | ≤ 5% | ______ | ______ |
| cobertura | ≥ 60% | ______ | ______ |
| taxa_abstencao_correta | ≥ 90% | ______ | ______ |
| taxa_abstencao_incorreta | ≤ 25% | ______ | ______ |
| correcao_citacoes | ≥ 95% | ______ | ______ |

## 7. Partições e acesso

- `dev` — iteração de prompts e regras. Acesso livre.
- `calibracao` — calibração do score de confiança e conformal (Módulo 6).
  Acesso apenas pelo processo de calibração, nunca para afinar prompts.
- `teste` — selado. Aberto uma vez, no fim. Cada acesso registado em
  data/golden_dataset/ACCESS_LOG.md com data, motivo e commit.
- `contaminacao` — perguntas sobre conteúdo posterior ao cutoff do modelo.
  Reportada SEPARADAMENTE. Ver §8.

## 8. Aviso sobre conformal prediction (importante)

A garantia de cobertura do conformal prediction exige permutabilidade
entre o conjunto de calibração e o conjunto de teste. Se as perguntas de
teste forem sistematicamente mais recentes ou mais difíceis que as de
calibração, a garantia NÃO é válida.

Decisão: o sorteio das partições é estratificado por categoria, dificuldade
e flag pos_cutoff. O conjunto `contaminacao` fica FORA da garantia
conformal e é reportado como sondagem independente, sem claim de cobertura.

## 9. O que este benchmark NÃO mede
- Não mede aconselhamento jurídico. Mede correspondência a texto oficial.
- Não mede completude do corpus. Uma resposta pode ser "correta no corpus"
  e incompleta face ao direito aplicável.
- Não mede generalização para outros regulamentos.
- Um único anotador. A concordância inter-anotador é medida em 30 perguntas
  e reportada como limitação, não como garantia.

## 10. Risco de correlação anotador-sistema
As perguntas foram redigidas com assistência de um LLM. Se o sistema
avaliado for da mesma família, existe risco de correlação entre quem
escreveu o exame e quem o faz. Mitigação: cada resposta esperada é
determinada por uma citação literal do texto oficial, não pelo juízo do
LLM. O anotador humano confirma a citação, não a plausibilidade.