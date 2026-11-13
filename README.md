# LexGraph: IA Neuro-Simbólica para Auditoria de Regulamentação Europeia

[![CI](https://github.com/rafaelcontente/LexGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/rafaelcontente/LexGraph/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen)](https://github.com/rafaelcontente/LexGraph/actions)
[![Evidence Coverage](https://img.shields.io/badge/evidence%20coverage-90%25-blue)](docs/RESULTS.md)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/downloads/)

**Sistema de IA Neuro-Simbólica que deteta e prova alucinaões de LLMs sobre regulamentação da UE, usando grafos de conhecimento validados por SHACL.**

---

## 🎉 Em Uma Frase

O LexGraph ã um "auditor automático" que não se limita a responder: ele verifica se as respostas de IA estão corretas, provando matematicamente quando um modelo inventa informações.

**Exemplo:** Se a IA diz *"O AI Act foi revogado"*, o LexGraph responde: *"Falso. O grafo não contém evidência de revogação."*

---

## 🧊 Resultados Comparativos

| Métrica | LLM Zero-Shot | LexGraph (GraphRAG) | Ganho |
| :--- | :--- | :--- | :--- |
| **Alucinação (Aceites)** | 66.7% | **0.0%** | 𞛀� Eliminação total |
| **Premissas Falsas** | 0% | **100%** | 🎏 Immunidade |
| **Evidence Coverage** | N/A | **90.0%** | 🎀 Robusta |

---

## 🌍 Análise de Falhas

Os 10% de falha (q_014, q_015) devem-se a citações de *"Considerando (46)"*, que o parser MVP ainda não extrai como nës dedicados. Mitigação agendada para v1.1.

---

## 🎪� Demo Interativa

```bash
python scripts/demo.py
```

---

## 🧈 Qualidade do Grafo

- **Triplos:** 7,010 | **Artigos:** 113 | **Violações SHACL: **
- **Recall Entidades:** 100% | **Cobertura Temporal:** 100%

---

## 𞧪 Cobertura de Testes

**59 testes passando** em 3 camadas de CI, incluindo testes de regressão críticos para abstenção e sobreposições.

---

## 🚀 Quick Start

```bash
make install && make pipeline && make test && make demo
```

---

## 🌖  Decisões de Arquitetura (ADRs)

- [ADR-001](docs/decisions/001-open-world-verifier.md): Open-World Assumption (Abstenção ⁍ Contradicão).
- [ADR�002](docs/decisions/002-shacl-over-fragmentation.md): Integridade Estrutural (SHACL).

---

**Construído com:** Python 3.12 » RDFLib · Pydantic · pytest · GitHub Actions · Ollama
