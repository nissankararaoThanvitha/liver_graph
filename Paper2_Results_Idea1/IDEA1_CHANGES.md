# Paper 2 rerun with Idea 1 (21 Oct 2026)

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph only (same as the main results). No outside data. No diagrams were drawn in this rerun.
The original results in `Paper2_Results/` are untouched; everything here was regenerated from scratch.

## The one change
**Before:** a drug was removed from the repurposing candidates if it had *any* liver-disease use in the graph (TREATS / OFF_LABEL_FOR), including liver cancer and hepatitis.
**Now (Idea 1):** a drug is removed only if it is already used for a **fibrosis-type** liver disease. Using a liver-cancer or hepatitis drug for fibrosis is still repurposing.

Fibrosis-type = liver diseases whose name matches *fatty liver, steatohepatitis, cirrhosis, fibrosis, portal hypertension, liver failure*. This is the same fibrosis-spectrum definition Task 5 already used: 21 of the 161 liver diseases, flagged in `Task4/liver_disease_set.csv` (column `fibrosis_type`).

## What changed
| | Before | Idea 1 |
|---|---|---|
| Phase ≥ 2 drugs removed for a liver use | 224 | **64** (fibrosis-type only) |
| Drugs brought back | – | **160** (138 approved) |
| Repurposing candidates (Task 4) | 1,109 | **1,269** |
| Main list (mechanism-annotated) | 559 | **666** |
| Candidates with ≥ 1 direction-consistent link (Task 7) | 315 | **382** |
| New drug–liver-disease pairs from "true repurposing" drugs (Task 5 revised) | 90,260 | **100,268** |
| …for fibrosis-spectrum diseases | 15,182 | **16,758** |
| …and main-list drugs | 3,517 | **4,239** |
| Stable drugs, main list (final ranking) | 19 of 559 | **21 of 666** |
| Stable drugs, all candidates | 17 of 1,109 | **19 of 1,269** |

Brought-back drugs were used mostly for hepatocellular carcinoma (70), unspecified "liver disease" (48), liver cancer (30), cholangiocarcinoma (27) and hepatitis C (18). The list is in `Task4/repurposing_candidates.csv` (`brought_back_by_idea1 = True`).

**Unchanged (identical files):** Task 1, Task 2, Task 3, Task 6 target components, the Task 5 revised path counts and Task 7 revised pathway directions. These do not depend on the candidate list. The Task 5 count table differs only in its "candidate drugs" and "main-list drugs" columns.

## Examples from the note
| Drug | Before | Idea 1 | Main-list rank (of 666) |
|---|---|---|---|
| Nintedanib (liver cancer use) | removed | **candidate** | 175 |
| Regorafenib (liver / bile-duct cancer) | removed | **candidate** | 129 |
| Dasatinib (liver / bile-duct cancer) | removed | **candidate** | 135 |
| Aspirin (liver cancer, alcoholic liver disease) | removed | **candidate** | **15, stable** |
| Amlodipine ("liver disease") | removed | **candidate** | 88 |
| Duvelisib | removed | **candidate** | **11, stable** |

Still excluded, because they already have a fibrosis-type use: pirfenidone (cirrhosis), obeticholic acid (NASH, biliary cirrhosis), pioglitazone (NASH), sorafenib (portal hypertension).

**Final ranking, main list:** the top 25 is almost the same as before. Duvelisib (11) and aspirin (15) enter, and pyridostigmine and methyltestosterone drop out. Scores are percentile-based, so ranks shift slightly when the candidate pool grows.

## Points to decide
- **Unspecified "liver disease"** (48 brought-back drugs, e.g. amlodipine) and **alcoholic liver disease / alcoholic hepatitis / sclerosing cholangitis** are *not* counted as fibrosis-type, because their names do not say fibrosis. If the supervisor wants them treated as fibrosis-type, add them to the definition and re-run.
- Nintedanib comes back but ranks 175: in the graph its direction-known links are few and it hits many non-progression targets (low specificity), which the frozen equal-weight ranking penalises.

## How to re-run
```bash
python Paper2_Results_Idea1/code/run_all.py
```
Needs `NEO4J_PASSWORD` (read-only queries). The audit passes **93 / 93** (`AUDIT.md`). Checks that apply only to the outside-data layers and the diagrams are not part of this folder.
Changed scripts: `task4_drug_coverage.py` (liver rule), `task5_revised_metapaths.py` (true-repurposing pairs), `audit_tasks.py` (checks the new rule) and `task8_progress_report.py` (wording). The other scripts are unchanged apart from writing to this folder.
