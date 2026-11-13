# ADR-001: Open-World Assumption no Verificador Simbólico

## Status
Aceite

## Contexto
Num sistema de QA sobre grafos, é tentador assumir que "se não está no grafo, é falso" (Closed-World Assumption). Isto leva a falsos positivos graves: se um LLM se abstém ("Não sei"), o verificador pode classificar erroneamente como `CONTRADITA`.

## Decisão
O Verificador Simbólico do LexGraph opera sob a **Open-World Assumption**. 
- Se o LLM faz uma afirmação positiva e o grafo a contradiz -> `CONTRADITA`.
- Se o LLM se abstém -> `NAO_VERIFICAVEL` (Nunca `CONTRADITA`).

## Consequências
- **Positivas:** O sistema não penaliza LLMs cautelosos. A métrica de "Abstenção Correta" torna-se fiável.
- **Negativas:** Exige que o grafo seja muito completo para poder afirmar `SUPORTADA` com confiança.
