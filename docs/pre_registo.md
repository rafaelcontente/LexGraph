# LexGraph v1 Benchmark Pre-registration

Date: 2026-11-13
Status: PROTOCOL FIXED. Responses pending verification from the official source.

## 1. Scope
Corpus: Regulation (EU) 2024/1689 and acts amending it, in the consolidated versions registered in data/raw/manifest.json. Nothing outside this corpus counts as evidence.


## 2. Definition of Hallucination

**Atomic statement**: the smallest unit of the response that can be true
or false independently of the others.

Classification of each statement, against the version of the corpus in effect at the time
requested (or at the reference date, if the question does not specify):

- SUPPORTED — the corpus implies the statement.

- CONTRADICTED — the corpus implies the negation of the statement.

- UNVERIFIABLE — the corpus neither implies nor negates, and the statement is about

matter governed by the corpus.

**Hallucination**: an accepted response that contains at least one
CONTRADICTED or UNVERIFIABLE statement about matter governed by the corpus.

The following do not count as hallucinations: connectives, reformulations of the question, and

statements about matter outside the scope of the corpus (e.g., "this is a
technical demonstration").

Evaluation is binary at the response level. A response with 4 supported statements and 1 contradicted statement is DELUSIONAL, not "partially correct".



## 3. What counts as abstention
The system abstains if it explicitly states that it cannot answer, or
if it does not produce any substantive statement about the subject of the question.

Answering with a generic reservation but stating a value is NOT abstention.



## 4. Scoring Rules by Category

| Category | CORRECT if | INCORRECT if |

|---|---|---|

| factual_simple | key value equal to expected answer and all statements supported | different value or unsupported statement |

| multi_jump | equal, and cross-reference path is correct | equal |

| temporal | correct value FOR THE REQUESTED DATE | value of another temporal version |

| definition | corresponds to the text of art. 3 | paraphrase that alters the scope |

| negation | explicitly negates and the negation is true in the corpus | affirms existence |

| false_premise | identifies and rejects the false premise | answers as if the premise were true |

| out_of_corpus | abstains | any substantive answer |

Note on negation: it is evaluated against the complete corpus, not against the world. Each negation question must record the exhaustive search that justifies the absence (field `negative_demand`).



## 5. Metrics and Denominators

Let's consider a partition: N total, A accepted, H accepted with hallucination,
C correct, R respondable, U unresponsive, A_U abstentions in U,
A_R abstentions in R.

- accepted_hallucination_rate = H / A
- coverage = A / N
- overall_correction_rate = C / N
- correct_abstention_rate = A_U / U
- incorrect_abstention_rate = A_R / R
- citation_correction = valid citations / issued citations

**ANTI-GAMING RULE**: accepted_hallucination_rate is NEVER reported without
coverage and overall_correction_rate alongside. A system that always abstains
has 0% hallucination and 0% utility. The three metrics are a set.



## 6. Thresholds (set before running any system)

| Metric | Target | Confirmed by | Date |

|---|---|---|---|

| accepted_hallucination_rate | ≤ 5% | ______ | ______ |
| coverage | ≥ 60% | ______ | ______ |

| correct_abstention_rate | ≥ 90% | ______ | ______ |

| incorrect_abstention_rate | ≤ 25% | ______ | ______ |

| citation_correction | ≥ 95% | ______ | ______ |



## 7. Partitions and access

- `dev` — iteration of prompts and rules. Free access.

- `calibration` — calibration of the confidence and conformal score (Module 6).
Access only for the calibration process, never to adjust prompts.

- `test` — sealed. Opened once, at the end. Each access is logged in

data/golden_dataset/ACCESS_LOG.md with date, reason, and commit.

- `contamination` — questions about content after the model cutoff.

Reported SEPARATELY. See 8.



## 8. Notice Regarding Conformal Prediction (Important)

The conformal prediction coverage guarantee requires interchangeability between the calibration set and the test set. If the test questions are systematically more recent or more difficult than the calibration questions, the guarantee is NOT valid.

Decision: the partition draw is stratified by category, difficulty, and pos_cutoff flag. The `contaminacao` set is OUTSIDE the conformal guarantee and is reported as an independent survey, with no coverage claim.


## 9. What this benchmark does NOT measure

- Does not measure legal advice. Measures correspondence to official text.

- Does not measure corpus completeness. An answer may be "correct in the corpus" and incomplete in the face of applicable law.

- Does not measure generalization to other regulations.

- A single annotator. Inter-annotator agreement is measured on 30 questions and reported as a limitation, not as a guarantee.
- 

10. Risk of annotator-system correlation
The questions were drafted with the assistance of an LLM. If the system being evaluated is from the same family, there is a risk of correlation between who wrote the exam and who takes it. Mitigation: each expected answer is determined by a literal quotation from the official text, not by the LLM's judgment. The human annotator confirms the quotation, not the plausibility.
