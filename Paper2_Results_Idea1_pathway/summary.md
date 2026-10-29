# Option 1 + pathway direction: can we rank more candidates? (28 Oct 2026)

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph only. Same method as `Paper2_Results_Idea1/Final_ranking` (equal weights, 1,000 Dirichlet α = 10 draws, stable = top 25 in ≥ 80% of draws). The original results are untouched.
Script: `code/final_ranking_pathway.py`.

## Why
Option 1 has **1,269 repurposing candidates**, but only **666** (the main list) have a drug action recorded on a progression gene. 603 candidates, 337 of them approved, have no direction at gene level.

## What changed (one thing)
If a drug has no gene-level direction call, its direction score (D2) now comes from the **Reactome pathways** of its targets (Task 7 revised, the supervisor's pathway idea): consistent pathways vs inconsistent pathways. Drugs with no call at either level keep the neutral D2 = 0.5, as before. Targets, D1, D3, D4 and the weights are unchanged (target rankings are identical).

## Results
| | Option 1 | Option 1 + pathway direction |
|---|---|---|
| Repurposing candidates | 1,269 | 1,269 |
| Candidates with a direction call | 641 | **742** (+101 through pathways) |
| Drugs ranked as the main list | 666 | **767** (main list + 101 pathway-judged candidates) |
| Stable drugs, main list | 21 | **18** |
| Stable drugs, all 1,269 candidates | 19 | **19** (same drugs) |

- Of the 101 pathway-judged drugs, 65 lean direction-consistent. The highest ranked are cannabidiol (#19), thalidomide (#22), epinastine (#26) and binimetinib (#46). **None becomes stable.**
- **No new stable drug.** Three option 1 stable drugs drop just below the 80% line because the new drugs crowd the top 25: aspirin (80.3% → 79.9%), ciprofibrate and clofibrate (84.1% → 70.7%). They still rank #15 and #23.
- The 18 stable drugs are the option 1 list minus those three. All 18 keep their gene-level, direction-consistent links.

## Interpretation
Adding pathway direction lets **101 more candidates be judged and ranked** (666 → 767) without outside data. It does not produce new top candidates: the stable core is robust, and the borderline drugs (aspirin, fibrates) sit right at the stability cut-off.

## Files
- `final_drugs_main_list_plus_pathway.csv`: 767 drugs, with `direction_source` (gene level / pathway level / unknown) and pathway counts
- `final_drugs_all_candidates_pathway.csv`: all 1,269 candidates
- `ablation_drugs_*.csv`: ablation (drop one component) for each list
