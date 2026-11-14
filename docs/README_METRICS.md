# 📊 Comparative Results and Performance Analysis

## 1. Baselines and Graph Gain (Ablation)
The system was evaluated by comparing a local LLM (Llama 3.2 8B via Ollama) in *Zero-Shot* mode (no context) against the **LexGraph** pipeline (with Symbolic Verification).

| Metrics | LLM Zero-Shot (Llama 3.2) | LexGraph (Symbolic GraphRAG) | Gain / Impact |
| :--- | :--- | :--- | :--- |
| **Hallucination Rate (Accepted)** | 66.7% (2/3 accepted answers were wrong) | **0.0%** (Verifier caught all) | 🛡️ **Total elimination of accepted hallucinations** |
| **False Premise Detection** | 0% (Accepted that the AI ​​Act was repealed) | **100%** (Contradicted with graph evidence) | 🎯 **Immunity to accidental jailbreaks** |
| **Evidence Coverage** | N/A (Does not use a true source) | **90.0%** (18/20 target entities in the graph) | 🧠 **Robust coverage of the normative backbone** |
| **Faithfulness** | Low (Fallen GDPR dates for the AI ​​Act) | **High** (By construction via SHACL + SPARQL) | 🔒 **Responses anchored in real law** |

*Note: The "Hallucination Rate (Accepted)" measures only responses where the model dared to respond. LexGraph forces a disclaimer or correction when the evidence does not support the claim.*

2. Cost and Latency (Operation)
Metrics extracted from actual benchmark execution (20 questions) on a MacBook Air M1.

| Configuration | Average Latency (p50) | P95 Latency | Cost per 1k Questions | Privacy |
| :--- | :--- | :--- | :--- | :--- |
| **LexGraph + Ollama Local** | ~3.5s | ~4.2s | **$0.00** | 🔒 **Total (On-premise)** |
| **LexGraph + GPT-4o-mini** *(Estimated)* | ~1.2s | ~2.5s | ~$0.15 | ☁️ Cloud (Sensitive data exposed) |

*The Symbolic Verifier (SPARQL) overhead is <50ms per query, making it negligible compared to LLM generation.*

## 3. Failure Analysis (Where and Why We Failed)
Full transparency regarding the 10% failure in *Evidence Coverage* (2/20 questions):
- **Root Cause:** Questions `q_014` and `q_015` cite *"Considering (46)"* from the preamble of the regulation.

- **Current Limitation:** The MVP parser extracts only the normative part (Articles and Paragraphs), ignoring the Considerings (Recitals).

- **Mitigation (v1.1):** Expand the parser to create `lg:Considering` nodes and link them to the articles they support.

4. Architecture Decision Records (ADRs)
To understand the *why* of the code, consult the [Architecture Decision Records](docs/decisions/).

- **ADR-001:** Adoption of the Open World Assumption in the Verifier (Abstention ! = Contradiction).
- **ADR-002:** Structural Integrity (SHACL) over Temporal Fragmentation in the Parser.
