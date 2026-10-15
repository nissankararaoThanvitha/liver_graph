# Paper 2 — Task 7: drug action vs. progression direction

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **6,222 genes**.
**Scope:** knowledge-graph action labels only (project scope decision: repurposing, not reversal; no external data). Input: all 8,948 Task 2 drug–gene links.
Script: `Paper2_Results/code/task7_direction_consistency.py`.

> **Direction-consistency is a repurposing hypothesis, not proof.** A drug that lowers a gene which rises with fibrosis is *mechanistically interesting*. That alone does not show the drug is anti-fibrotic: the gene may be a consequence rather than a driver, the effect may be tissue- or dose-dependent, and the graph label says nothing about liver exposure.

![Task 7 diagram](Task7_diagram.png)

## Rules
| Gene direction (Paper 1) | Drug pushes ⬇ | Drug pushes ⬆ |
|---|---|---|
| rises with fibrosis (positive) | **direction-consistent** | direction-inconsistent |
| falls with fibrosis (negative) | direction-inconsistent | **direction-consistent** |

**Ambiguous** = mixed action (modulator, binding agent …), or a shared gene whose fibrosis and inflammation directions disagree, or a gene whose direction disagrees with its F0–F4 cluster. **Unknown** = action TARGET / ENZYME / TRANSPORTER / CARRIER.
Gene direction = fibrosis direction for fibrosis-associated genes, inflammation direction for inflammation-only genes. Cluster directions (F4 vs F0 mean): C1 positive, C2 positive, C3 positive, C4 negative, C5 negative.

## 1. Known vs. unknown action
| Links | total | known direction (down/up) | mixed | unknown | % unknown |
|---|---|---|---|---|---|
| all drug–gene links | 8,948 | 1,001 | 28 | 7,919 | 88.5 |
| pharmacological links only | 4,987 | 1,001 | 28 | 3,958 | 79.4 |

**Limitation: 88.5% of drug–gene links in the graph have unknown direction.** Consistency can only be judged for the remaining links; the rest stay "unknown", not "inconsistent".

Overall: direction-consistent 530, direction-inconsistent 471, ambiguous 28, unknown 7,919.

## 2. Consistency by Paper 1 group
| paper1_group | direction-consistent | direction-inconsistent | ambiguous | unknown | total | % consistent among decided |
|---|---|---|---|---|---|---|
| fibrosis_only_positive | 140 | 17 | 4 | 721 | 882 | 89.2 |
| fibrosis_only_negative | 56 | 133 | 11 | 2,645 | 2,845 | 29.6 |
| shared_positive | 201 | 155 | 10 | 1,192 | 1,558 | 56.5 |
| shared_negative | 20 | 78 | 0 | 1,674 | 1,772 | 20.4 |
| shared_discordant_fib_negative | 0 | 0 | 0 | 14 | 14 |  |
| inflammation_only_positive | 102 | 63 | 3 | 1,387 | 1,555 | 61.8 |
| inflammation_only_negative | 11 | 25 | 0 | 286 | 322 | 30.6 |

## 3. Consistency by F0–F4 trajectory cluster
| cluster | cluster direction | direction-consistent | direction-inconsistent | ambiguous | unknown | total | % consistent among decided |
|---|---|---|---|---|---|---|---|
| C1 | positive | 104 | 50 | 0 | 737 | 891 | 67.5 |
| C2 | positive | 171 | 116 | 6 | 940 | 1,233 | 59.6 |
| C3 | positive | 66 | 6 | 8 | 236 | 316 | 91.7 |
| C4 | negative | 3 | 48 | 0 | 702 | 753 | 5.9 |
| C5 | negative | 73 | 163 | 11 | 3,631 | 3,878 | 30.9 |

## 4. Repurposing candidates with ≥1 direction-consistent link
| Set | ≥1 direction-consistent link | only consistent | mixed | only inconsistent | no decided link |
|---|---|---|---|---|---|
| Repurposing candidates (Task 4, n=1,109) | 315 | 269 | 46 | 222 | 572 |
| Main list (mechanism-annotated, n=559) | 315 | 269 | 46 | 222 | 22 |

**315 of 1,109 repurposing candidates** have at least one direction-consistent link (315 of 559 on the main list). Per-drug detail: `drug_direction_summary.csv`.

### Main-list drugs with the most direction-consistent fibrosis-gene links (NOT a ranking)
| Drug | max_phase | n_consistent_fibrosis_genes | n_consistent | n_inconsistent | direction_pattern | consistent_genes | inconsistent_genes |
|---|---|---|---|---|---|---|---|
| DALFAMPRIDINE | 4.0 | 3 | 4 | 2 | mixed (consistent + inconsistent) | KCNA2;KCNA3;KCNB1;KCND1 | KCNC2;KCND3 |
| OXTRIPHYLLINE | 4.0 | 3 | 3 | 0 | only consistent | ADORA1;PDE3A;PDE4A |  |
| THEOPHYLLINE | 4.0 | 3 | 3 | 0 | only consistent | ADORA1;PDE3A;PDE4A |  |
| IBUDILAST | 4.0 | 3 | 3 | 0 | only consistent | PDE3A;PDE4A;PDE4D |  |
| MARIMASTAT | 3.0 | 3 | 3 | 0 | only consistent | MMP2;MMP7;MMP9 |  |
| MECLOFENAMIC ACID | 4.0 | 3 | 3 | 0 | only consistent | ALOX5;PTGS1;PTGS2 |  |
| BALSALAZIDE | 4.0 | 3 | 3 | 1 | mixed (consistent + inconsistent) | ALOX5;PTGS1;PTGS2 | PPARG |
| MESALAMINE | 4.0 | 3 | 3 | 1 | mixed (consistent + inconsistent) | ALOX5;PTGS1;PTGS2 | PPARG |
| TOLMETIN | 4.0 | 2 | 2 | 0 | only consistent | PTGS1;PTGS2 |  |
| NEPAFENAC | 4.0 | 2 | 2 | 0 | only consistent | PTGS1;PTGS2 |  |
| OXAPROZIN | 4.0 | 2 | 2 | 0 | only consistent | PTGS1;PTGS2 |  |
| SGS-742 | 2.0 | 2 | 2 | 0 | only consistent | GABBR1;GABBR2 |  |
| FENOPROFEN | 4.0 | 2 | 2 | 0 | only consistent | PTGS1;PTGS2 |  |
| AMINOPHYLLINE | 4.0 | 2 | 2 | 0 | only consistent | ADORA1;PDE3A |  |
| DICLOFENAC | 4.0 | 2 | 2 | 0 | only consistent | PTGS1;PTGS2 |  |

### Checks on earlier examples
- **PPAR agonists (Task 5, Example 1):**

| Drug | n_consistent | n_inconsistent | consistent_genes | inconsistent_genes |
|---|---|---|---|---|
| FENOFIBRIC ACID | 1 | 0 | PPARA |  |
| MURAGLITAZAR | 1 | 1 | PPARA | PPARG |
| TESAGLITAZAR | 1 | 1 | PPARA | PPARG |
| ALEGLITAZAR | 1 | 1 | PPARA | PPARG |
| INDEGLITAZAR | 1 | 2 | PPARA | PPARD;PPARG |
| GW501516 | 0 | 1 |  | PPARD |

  PPARA falls with fibrosis and is activated (consistent). PPARG/PPARD rise and are also activated (inconsistent). These drugs are **mixed**, as flagged in Task 5.
- **PDGFRA (Task 5, Example 3):** AMUVATINIB: INHIBITOR → direction-consistent; FOSTAMATINIB: TARGET → unknown; PONATINIB: TARGET → unknown; RIPRETINIB: INHIBITOR → direction-consistent.

## 5. Is the pairing different from chance? (descriptive)
Among decided links (known direction, unambiguous gene): 1,001 links, 530 direction-consistent vs. 564 expected if drug action were independent of gene direction (Fisher OR 0.69, p = 0.017).
So known drug actions are slightly **less** often direction-consistent than chance. The main reason is visible in section 2: genes that **fall** with fibrosis mostly have *inhibitors* in the graph (fibrosis-only ⬇ 30% consistent, shared ⬇⬇ 20%, cluster C4 6%), while rising fibrosis-only genes are mostly inhibited, which is consistent (89%). This matches the Task 3 warning: falling genes would need activators, and few exist. The graph contains no fibrosis information, so this pattern says which drugs exist, not whether they would work.

## Files
`drug_action_evidence.csv` (one row per link, all requested columns), `summary_known_vs_unknown.csv`, `consistency_by_paper1_group.csv`, `consistency_by_cluster.csv`, `candidates_direction_summary.csv`, `drug_direction_summary.csv` (per drug, for the later DrugScore).
