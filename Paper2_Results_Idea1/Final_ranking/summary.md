# Paper 2 — Final target and drug ranking

**Paper 1:** final combined version, 10 Oct 2026 (confirmed final by the Paper 1 team). **Gene set:** corrected Paper 1 union of 6,222 genes (the plan's 4,692 was the pre-correction count).
**Scope:** knowledge graph + Paper 1 only (project scope decision: repurposing, not reversal). **All results are repurposing hypotheses, not treatments.**
Rules were frozen before ranking: `PREREGISTRATION.md`. Script: `Paper2_Results_Idea1/code/final_ranking.py`.

## 1. Final targets
Two lists, as decided in Task 6: **biology** (P, F, T, B; finds new targets with or without drugs) and **actionable** (P, F, T, K, B; targets with drug evidence, for repurposing). Equal weights. A target is **stable** if it stays in the top 50 in ≥ 80% of 1,000 near-equal weight draws (Dirichlet α = 10).

| List | Stable targets (top 50 in ≥ 80% of draws) | Stable at α = 1 (stress test) | Shortlist genes in top 50 |
|---|---|---|---|
| Biology | 27 | 8 | 3 |
| Actionable | 29 | 7 | 4 |

### Actionable list, top 20
| rank | Gene | progression_class | trajectory_cluster | dir | TargetScore | P(top50) | in_shortlist |
|---|---|---|---|---|---|---|---|
| 1 | BCL2 | fibrosis_only | C2 | ⬆ | 0.9008 | 1.0 | False |
| 2 | CACNA1C | fibrosis_only | C2 | ⬆ | 0.8872 | 1.0 | True |
| 3 | SRC | fibrosis_only | C1 | ⬆ | 0.8858 | 1.0 | False |
| 4 | EPHA2 | fibrosis_only | C2 | ⬆ | 0.8763 | 1.0 | False |
| 5 | PDGFRA | fibrosis_only | C2 | ⬆ | 0.8744 | 1.0 | True |
| 6 | PIK3CG | fibrosis_only | C1 | ⬆ | 0.8472 | 1.0 | False |
| 7 | PDGFRB | shared | C1 | ⬆ | 0.8358 | 1.0 | False |
| 8 | ALDH2 | fibrosis_only | C5 | ⬇ | 0.8327 | 1.0 | False |
| 9 | CXCR4 | shared | C2 | ⬆ | 0.8326 | 1.0 | False |
| 10 | DPYD | fibrosis_only | C5 | ⬇ | 0.8289 | 1.0 | False |
| 11 | MYC | fibrosis_only | C2 | ⬆ | 0.8179 | 0.97 | False |
| 12 | ADRA2A | shared | C2 | ⬆ | 0.8165 | 0.98 | False |
| 13 | MMP2 | shared | C2 | ⬆ | 0.8111 | 0.99 | False |
| 14 | AKR1D1 | fibrosis_only | C5 | ⬇ | 0.811 | 1.0 | False |
| 15 | PTGS2 | shared | C2 | ⬆ | 0.8073 | 0.97 | False |
| 16 | GSTP1 | shared | C2 | ⬆ | 0.807 | 0.98 | False |
| 17 | SYK | fibrosis_only | C1 | ⬆ | 0.7996 | 0.97 | False |
| 18 | MMP7 | shared | C2 | ⬆ | 0.7959 | 0.96 | False |
| 19 | MAOB | fibrosis_only | C5 | ⬇ | 0.7854 | 0.91 | False |
| 20 | TUBA1A | shared | C2 | ⬆ | 0.7843 | 0.9 | False |

### Biology list, top 20
| rank | Gene | progression_class | trajectory_cluster | dir | TargetScore | P(top50) | in_shortlist |
|---|---|---|---|---|---|---|---|
| 1 | MYC | fibrosis_only | C2 | ⬆ | 0.9777 | 1.0 | False |
| 2 | ITGA2 | fibrosis_only | C2 | ⬆ | 0.973 | 1.0 | False |
| 3 | TGFB3 | fibrosis_only | C2 | ⬆ | 0.9539 | 1.0 | False |
| 4 | FLNA | fibrosis_only | C2 | ⬆ | 0.9457 | 1.0 | False |
| 5 | EPHA2 | fibrosis_only | C2 | ⬆ | 0.9429 | 1.0 | False |
| 6 | ZC3H12A | fibrosis_only | C2 | ⬆ | 0.9414 | 1.0 | False |
| 7 | TNFRSF21 | fibrosis_only | C2 | ⬆ | 0.9348 | 1.0 | False |
| 8 | SRC | fibrosis_only | C1 | ⬆ | 0.9307 | 1.0 | False |
| 9 | VWF | fibrosis_only | C2 | ⬆ | 0.9295 | 1.0 | False |
| 10 | BCL2 | fibrosis_only | C2 | ⬆ | 0.9286 | 1.0 | False |
| 11 | FOXC1 | fibrosis_only | C2 | ⬆ | 0.9137 | 1.0 | False |
| 12 | PDGFRA | fibrosis_only | C2 | ⬆ | 0.9133 | 1.0 | True |
| 13 | STC1 | fibrosis_only | C2 | ⬆ | 0.912 | 0.97 | False |
| 14 | AKR1D1 | fibrosis_only | C5 | ⬇ | 0.9108 | 1.0 | False |
| 15 | CACNA1C | fibrosis_only | C2 | ⬆ | 0.909 | 0.99 | True |
| 16 | LIF | shared | C2 | ⬆ | 0.9052 | 0.94 | False |
| 17 | ITGB8 | fibrosis_only | C2 | ⬆ | 0.9046 | 0.98 | False |
| 18 | CCL2 | shared | C2 | ⬆ | 0.9029 | 0.92 | False |
| 19 | THBS1 | shared | C2 | ⬆ | 0.9024 | 0.92 | False |
| 20 | ALDH2 | fibrosis_only | C5 | ⬇ | 0.9009 | 0.96 | False |

### Stage-informed view: top 5 biology targets per F0–F4 trajectory cluster
| trajectory_cluster | Gene | progression_class | TargetScore | rank |
|---|---|---|---|---|
| C1 | SRC | fibrosis_only | 0.9307 | 8 |
| C1 | PIK3CG | fibrosis_only | 0.8936 | 23 |
| C1 | ITGAM | fibrosis_only | 0.8827 | 28 |
| C1 | COL1A1 | shared | 0.8812 | 29 |
| C1 | ITGB2 | fibrosis_only | 0.8752 | 33 |
| C2 | MYC | fibrosis_only | 0.9777 | 1 |
| C2 | ITGA2 | fibrosis_only | 0.973 | 2 |
| C2 | TGFB3 | fibrosis_only | 0.9539 | 3 |
| C2 | FLNA | fibrosis_only | 0.9457 | 4 |
| C2 | EPHA2 | fibrosis_only | 0.9429 | 5 |
| C3 | CDC45 | shared | 0.8104 | 187 |
| C3 | ITGA4 | fibrosis_only | 0.8011 | 226 |
| C3 | TREM2 | shared | 0.7966 | 249 |
| C3 | ZWINT | shared | 0.7627 | 400 |
| C3 | CCNA2 | shared | 0.7506 | 456 |
| C4 | SHMT2 | fibrosis_only | 0.7952 | 258 |
| C4 | ADH5 | fibrosis_only | 0.7814 | 314 |
| C4 | OAT | shared | 0.7647 | 392 |
| C4 | F2 | fibrosis_only | 0.7591 | 423 |
| C4 | CYP4A11 | shared | 0.748 | 474 |
| C5 | AKR1D1 | fibrosis_only | 0.9108 | 14 |
| C5 | ALDH2 | fibrosis_only | 0.9009 | 20 |
| C5 | CYP2C8 | fibrosis_only | 0.8853 | 26 |
| C5 | CAT | fibrosis_only | 0.8844 | 27 |
| C5 | ACSL5 | fibrosis_only | 0.8771 | 32 |

### Target ablation (actionable; drop one component)
| dropped | spearman | kendall | top50_overlap |
|---|---|---|---|
| P | 0.9594 | 0.8384 | 40 |
| F | 0.9881 | 0.9324 | 34 |
| T | 0.9852 | 0.9167 | 34 |
| K | 0.9875 | 0.9469 | 24 |
| B | 0.9552 | 0.8589 | 29 |

## 2. Final drugs (repurposing candidates)
DrugScore = mean of D1 target relevance (best biology TargetScore of the drug's targets), D2 direction-consistency (Task 7), D3 specificity (progression-target fraction) and D4 knowledge-graph support (Task 5 MetaPaths). Primary list: the 666 mechanism-annotated candidates (`final_drugs_main_list.csv`); all 1,269 candidates are in `final_drugs_all_candidates.csv`.

**Stable drugs** (top 25 in ≥ 80% of draws, α = 10): **21**. Shortlist-supported drugs in the top 25: **2**; broad-evidence-only: **23**.

### Main list, top 25
| rank | Drug | phase | DrugScore | P(top25) | top-scoring target (any link) | right-way targets | wrong-way targets | liver CI |
|---|---|---|---|---|---|---|---|---|
| 1 | MAVORIXAFOR | 3 | 0.9297 | 1.0 | CXCR4 | CXCR4 |  |  |
| 2 | DROTAVERINE | 3 | 0.9222 | 1.0 | CACNA1C | PDE4A |  |  |
| 3 | APLAVIROC | 3 | 0.8964 | 1.0 | CCR5 | CCR5 |  |  |
| 3 | MARAVIROC | 4 | 0.8964 | 1.0 | CCR5 | CCR5 |  | ⚠️ |
| 3 | INCB-9471 | 2 | 0.8964 | 1.0 | CCR5 | CCR5 |  |  |
| 3 | VICRIVIROC | 3 | 0.8964 | 1.0 | CCR5 | CCR5 |  |  |
| 7 | OBATOCLAX | 3 | 0.8818 | 1.0 | BCL2 | BCL2 |  |  |
| 7 | VENETOCLAX | 4 | 0.8818 | 1.0 | BCL2 | BCL2 |  |  |
| 9 | DEXIBUPROFEN | 4 | 0.8795 | 0.92 | BCL2 | PTGS1;PTGS2 |  |  |
| 10 | FENOPROFEN | 4 | 0.8738 | 1.0 | PTGS2 | PTGS1;PTGS2 |  | ⚠️ |
| 11 | TG100-115 | 2 | 0.8674 | 1.0 | PIK3CG | PIK3CD;PIK3CG |  |  |
| 11 | DUVELISIB | 4 | 0.8674 | 1.0 | PIK3CG | PIK3CD;PIK3CG |  |  |
| 13 | GEMFIBROZIL | 4 | 0.8601 | 0.91 | SLCO1B3 | PPARA |  | ⚠️ |
| 14 | IBUPROFEN | 4 | 0.86 | 0.81 | BCL2 | PTGS1;PTGS2 |  | ⚠️ |
| 15 | ASPIRIN | 4 | 0.8584 | 0.8 | MYC | PTGS1;PTGS2 |  |  |
| 16 | PITAVASTATIN | 4 | 0.8567 | 1.0 | ITGAL | HMGCR |  |  |
| 17 | LOVASTATIN | 4 | 0.8554 | 1.0 | ITGAL | HMGCR |  |  |
| 18 | BARNIDIPINE | 2 | 0.8512 | 0.94 | CACNA1C | CACNA1C |  |  |
| 19 | R-406 | 2 | 0.8494 | 0.98 | SYK | SYK |  |  |
| 20 | SULINDAC | 4 | 0.8347 | 0.66 | PTGS2 | PTGS1;PTGS2 |  |  |
| 21 | CLOFIBRATE | 4 | 0.8288 | 0.84 | PPARA | PPARA |  |  |
| 21 | CIPROFIBRATE | 4 | 0.8288 | 0.84 | PPARA | PPARA |  |  |
| 23 | BALSALAZIDE | 4 | 0.8281 | 0.58 | PTGS2 | ALOX5;PTGS1;PTGS2 | PPARG |  |
| 24 | EZATIOSTAT | 2 | 0.823 | 0.63 | GSTP1 | GSTP1 |  |  |
| 25 | PENTOSTATIN | 4 | 0.8204 | 0.53 | ADA | ADA |  |  |

### Evidence cards: which layers support (✔), contradict (✘) or are missing (–) for the top 25
| rank | Drug | phase | DrugScore | stable | best target | Progression (P) | Fibrosis specificity (F) | Trajectory / transition (T) | Pathway (B) | Drug mechanism direction | Graph support (MetaPaths) | Liver safety flag | Paper 1 shortlist |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MAVORIXAFOR | 3.0 | 0.9297 | yes | CXCR4 (#45) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 2 | DROTAVERINE | 3.0 | 0.9222 | yes | CACNA1C (#15) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | ✔ |
| 3 | APLAVIROC | 3.0 | 0.8964 | yes | CCR5 (#298) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 3 | MARAVIROC | 4.0 | 0.8964 | yes | CCR5 (#298) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✘ contraindicated | – |
| 3 | INCB-9471 | 2.0 | 0.8964 | yes | CCR5 (#298) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 3 | VICRIVIROC | 3.0 | 0.8964 | yes | CCR5 (#298) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 7 | OBATOCLAX | 3.0 | 0.8818 | yes | BCL2 (#10) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 7 | VENETOCLAX | 4.0 | 0.8818 | yes | BCL2 (#10) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 9 | DEXIBUPROFEN | 4.0 | 0.8795 | yes | BCL2 (#10) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 10 | FENOPROFEN | 4.0 | 0.8738 | yes | PTGS2 (#216) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✘ contraindicated | – |
| 11 | TG100-115 | 2.0 | 0.8674 | yes | PIK3CG (#23) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 11 | DUVELISIB | 4.0 | 0.8674 | yes | PIK3CG (#23) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 13 | GEMFIBROZIL | 4.0 | 0.8601 | yes | SLCO1B3 (#522) | – | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | ✔ | ✘ contraindicated | – |
| 14 | IBUPROFEN | 4.0 | 0.86 | yes | BCL2 (#10) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | ✔ | ✘ contraindicated | – |
| 15 | ASPIRIN | 4.0 | 0.8584 | yes | MYC (#1) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 16 | PITAVASTATIN | 4.0 | 0.8567 | yes | ITGAL (#593) | – | ✔ fibrosis-only | – | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 17 | LOVASTATIN | 4.0 | 0.8554 | yes | ITGAL (#593) | – | ✔ fibrosis-only | – | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 18 | BARNIDIPINE | 2.0 | 0.8512 | yes | CACNA1C (#15) | ✔ | ✔ fibrosis-only | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | ✔ |
| 19 | R-406 | 2.0 | 0.8494 | yes | SYK (#95) | ✔ | ✔ fibrosis-only | – | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 20 | SULINDAC | 4.0 | 0.8347 | no | PTGS2 (#216) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 21 | CLOFIBRATE | 4.0 | 0.8288 | yes | PPARA (#819) | – | ✔ shared | – | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 21 | CIPROFIBRATE | 4.0 | 0.8288 | yes | PPARA (#819) | – | ✔ shared | – | ✔ | ✔ consistent | ✔ | ✔ none recorded | – |
| 23 | BALSALAZIDE | 4.0 | 0.8281 | no | PTGS2 (#216) | ✔ | ✔ shared | ✔ | ✔ | ~ mixed | ✔ | ✔ none recorded | – |
| 24 | EZATIOSTAT | 2.0 | 0.823 | no | GSTP1 (#199) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |
| 25 | PENTOSTATIN | 4.0 | 0.8204 | no | ADA (#369) | ✔ | ✔ shared | ✔ | ✔ | ✔ consistent | – | ✔ none recorded | – |

### Drug ablation (drop one component)
| dropped | spearman | kendall | top25_overlap |
|---|---|---|---|
| D1_target_relevance | 0.9333 | 0.8015 | 19 |
| D2_direction | 0.7196 | 0.576 | 13 |
| D3_specificity | 0.8974 | 0.7249 | 15 |
| D4_graph_support | 0.9555 | 0.8192 | 10 |

## 3. How to read this
- A high rank means **several independent knowledge-graph and Paper 1 layers agree**. It does not show that a drug would help patients. Every candidate remains a **repurposing hypothesis**.
- D2 = 0.5 means the graph does not say which way the drug pushes its targets (unknown, not wrong).
- ⚠️ = contraindicated in some liver disease in the graph: high priority for safety review, not automatically excluded.
- Independent validation and transcriptomic reversal are out of scope by the project scope decision.
