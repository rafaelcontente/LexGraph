# ADR-002: Integridade Estrutural (SHACL) sobre Fragmentação Temporal

## Status
Aceite

## Contexto
O parser inicial tentava extrair datas de vigência específicas de cada parágrafo (ex: "aplicável a partir de 2027"). Isto criava múltiplas versões sobrepostas para o mesmo Artigo, violando as regras SHACL de não-sobreposição temporal e gerando 600+ erros de validação.

## Decisão
Priorizar a **Integridade Estrutural**. O `vigenciaInicio` de uma Unidade Normativa representa a data da versão do documento (ex: 2024-08-01 para o AI Act original). As datas específicas de aplicação permanecem no campo `texto` e são extraídas dinamicamente pelo Verificador via SPARQL/Regex quando necessário.

## Consequências
- **Positivas:** Grafo 100% SHACL-compliant, 0 duplicados,推理 (raciocínio) temporal robusto.
- **Negativas:** Perde-se a ligação explícita `artigo -> temPrazo -> data` (agendado para v1.1 como nós `ai:Prazo`).
