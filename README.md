# LexGraph: Neuro-Symbolic AI for European Regulatory Auditing

[![CI](https://github.com/rafaelcontente/LexGraph/actions/workflows/ci.yml/badge.svg)](https://github.com/rafaelcontente/LexGraph/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen)](https://github.com/rafaelcontente/LexGraph/actions)
[![Evidence Coverage](https://img.shields.io/badge/evidence%20coverage-90%25-blue)](docs/RESULTS.md)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/downloads/)

**Neuro-Symbolic AI System that detects and proves LLMs' hallucinations about EU regulation, using knowledge graphs validated by SHACL.**

---

In a Sentence

LexGraph is an "automatic auditor" that doesn't just respond: it verifies whether AI responses are correct, mathematically proving when a model fabricates information.

**Example:** If the AI ​​says *"The AI ​​Act has been repealed"*, LexGraph responds: *"False."* The graph contains no evidence of repeal.*

---

## Comparative Results

| Metric | LLM Zero-Shot | LexGraph (GraphRAG) | Gain |

| :--- | :--- | :--- | :--- |
| **Hallucination (Accepted)** | 66.7% | **0.0%** | Total Elimination |
| **False Premises** | 0% | **100%** | Immunity |
| **Evidence Coverage** | N/A | **90.0%** | Robust |

---

Failure Analysis

The 10% failure rate (q_014, q_015) is due to citations of *"Considering (46)"*, which the MVP analyzer does not yet extract as dedicated nodes. Mitigation scheduled for v1.1.

---

##  Demo Interativa

```bash
python scripts/demo.py
```

---

Graph Quality

- **Triples:** 7,010 | **Items:** 113 | **SHACL Violations:**

- **Entity Recall:** 100% | **Temporal Coverage:** 100%

---

Test Coverage

**59 tests passing** across 3 layers of CI, including critical regression tests for abstraction and overlays.

---

## Quick Start

```bash
make install && make pipeline && make test && make demo
```

---

Architectural Decision Reports (ADRs)

- [ADR-001](docs/decisions/001-open-world-verifier.md): Open-World Assumption (Abstention from Contradiction).
- [ADRÑ002](docs/decisions/002-shacl-over-fragmentation.md): Structural Integrity (SHACL).

---

**Built with:** Python 3.12 · RDFLib · Pydantic · pytest · GitHub Shares · Ollama
