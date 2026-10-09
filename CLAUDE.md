# Liver disease knowledge graph

A knowledge graph linking gene expression from eight human liver GEO studies
to curated biological knowledge, built to answer the stated aim: **predict the
stage of liver disease progression.**

Read `git log` oldest-to-newest for the decision trail. Every script's
docstring explains why it exists and what it guards against; those are the
real documentation and they are kept current.

## The data

Eight GEO studies, 1,085 samples from 1,027 patients (some re-biopsied):

| Study | Samples | | Study | Samples |
|---|---|---|---|---|
| GSE126848 | 57 | | GSE167523 | 98 |
| GSE130970 | 78 | | GSE193066 | 164 |
| GSE135251 | 216 | | GSE240729 | 67 |
| GSE162694 | 143 | | GSE269412 | 262 |

Raw downloads live under `data/raw/` and are gitignored. `.gitignore` carries
the provenance (Dataverse DOI, MSigDB URL) and a rebuild command for every
excluded bulk folder — read it before assuming data is missing.

## Pipeline, in order

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_full
python map_gene_ids.py
python build_crosswalk.py
python normalize_clinical.py
python build_graph_all.py --interim data/interim_full --out data/graph_full
python build_optimuskg_layer.py
python find_progression_genes.py --graph data/graph_full --out data/progression_full
python export_for_mentor.py
python build_progression_edges.py
python paper1_task1_groups.py       --out Paper1_Results/Task1
python paper1_task2_trajectories.py --out Paper1_Results/Task2
python paper1_task3_transitions.py  --out Paper1_Results/Task3 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python paper1_task4_enrichment.py   --out Paper1_Results/Task4 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python scripts/make_fig1.py
```

Then the prioritisation, in `scripts/`. **The scoring script runs twice** —
the final tables need the leave-one-study-out columns the third step writes:

```bash
python scripts/00_all_4692_progression_genes.py --out Paper1_HighConfidence
python scripts/powermatched_transitions.py      --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py         --out Paper1_HighConfidence --results Paper1_Results
python scripts/loso_validation.py               --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py         --out Paper1_HighConfidence --results Paper1_Results
python scripts/kg_subgraph.py                   --out Paper1_HighConfidence --results Paper1_Results
python build_paper1_package.py
```

**Always pass `--out`, `--results` and `--clusters` explicitly.** The defaults
are convenient, not safe: when more than one version of the results exists, a
default can pair new inputs with old intermediates and the run reports
success. That failure has happened here more than once.

Loading into Neo4j is Cypher: `create_kg_constraints.cypher`, then
`reload_expression.cypher`.

## The graph

Neo4j Enterprise 2026.07.0 via Neo4j Desktop 2, store format
`block-block-1.1` (Enterprise-only — a dump will not load into Community
Edition).

Nodes: Gene 53,993 · Disease 36,044 · BioProcess 12,203 · Drug 12,025 ·
Phenotype 8,666 · Pathway 2,220 · Sample 1,085 · Dataset 8

Edges, as the CSVs contain them: EXPRESSES 32,471,042 ·
ASSOCIATED_WITH 1,832,441 · INTERACTS_WITH 324,116 · HAS_PHENOTYPE 157,144 ·
INVOLVED_IN 157,081 · TREATS 57,601 · IN_PATHWAY 46,751 · PARENT_OF 44,215 ·
ACTS_ON 20,674 · CONTRAINDICATED_IN 11,718 · **TRACKS_FIBROSIS 3,681** ·
**TRACKS_INFLAMMATION 4,018** · IN_DATASET 1,085 · OFF_LABEL_FOR 1,061

`EXPRESSES` is 92% of the graph and is *measurement*, not knowledge. The
`TRACKS_*` edges (7,699, patient-derived) are what those measurements mean,
and they are the project's own contribution to the graph.

**No analysis reads the database.** Every result comes from CSVs, including
the mechanism subgraph. `verify_graph_counts.py` reconciles a loaded graph
against the CSVs per relationship type — the live graph is currently short by
40,247 links across five Disease-touching types, and there is no committed
loader for the knowledge layer. Neither affects any result.

The server is configured with a 1 GB heap against a 2.5 GB store. Counting
all relationships by type in one query times out — count per type, which hits
the count store and returns instantly.

## Decisions already settled — do not re-litigate

- **Measured zeros are kept.** A gene reading zero is a measurement, not a
  missing value, and dropping zeros removes the switching-on that *is* the
  progression signal: IL6 is detected in 10% of stage-1 and 64% of stage-4
  patients. Hence `data/interim_full`.
- **OptimusKG is the knowledge layer.** Genes are identified by Ensembl ID,
  the namespace this pipeline standardises on, so 94% join directly; its
  drug–gene edges carry a mode of action; and it records 74/95/71 drugs
  treating NASH/NAFLD/cirrhosis.
- **Two ladders, not one.** Fibrosis (0→4, scarring, largely permanent) and
  disease (control→NAFL→NASH, inflammation, reversible) are scored separately
  by pathologists and are analysed separately here.
- **Per-study correlation, then combine** — never pool patients across
  studies. Cross-study agreement is the validation rule throughout.
- **`value_z`** is expression standardised per gene *within* each study. It is
  what makes eight cohorts comparable; use it, not raw values.
- **`n_datasets`** (1–8) on every Gene node records how many studies measured
  it. 39,199 genes are missing from at least one study. Never average across
  genes without checking it.
- **One row per patient.** For the 58 twice-biopsied GSE193066 patients the
  first biopsy is used, so expression is paired with the stage recorded at
  that same biopsy.
- **Raw clinical fields are never modified.** `normalize_clinical.py` *adds*
  `fibrosis_stage`, `disease_group`, `patient_id`, `biopsy_number` beside the
  `*_raw` originals so every translation stays auditable.
- **A label is assigned only where the evidence supports it.** GSE162694 and
  GSE135251 carry no diagnosis field in GEO, so their patients are labelled
  NAFLD — true, and silent on the NAFL/NASH subtype. GSE130970's diagnosis is
  derived from its own Kleiner panel and flagged `derived_from_histology`.
  Three studies are left blank.
- **Enrichment background is the 14,794 genes** eligible for cross-study
  analysis, not all ~20,000 human genes. Using the wrong background
  invalidates Task 4.

## Current numbers

| | |
|---|---|
| Progression genes | **5,884** — fibrosis-only 1,866 · inflammation-only 2,203 · shared 1,815 |
| **Fibrosis-associated** | **3,681** (fibrosis-only + shared) — the set Tasks 2, 3 and 5 use |
| Trajectory clusters | **5**, from 948 / 1,528 / 209 / 313 / 683 genes |
| Largest transition | **F3→F4**, power-matched median 287 genes against 0, 0, 2 |
| Tier 1 genes | **525** · prioritised shortlist **25** |

## Known limits — state these, never paper over them

- **The disease ladder rests on 3 studies and 221 patients.** GSE135251 and
  GSE162694 label patients NAFLD without a subtype, so neither sits on the
  control→NAFL→NASH ordering. Inflammation-only counts are not comparable
  with fibrosis-only counts: three agreeing studies against five.
- **C1 and C3 cluster membership is not usable at gene level** — 3 and 1
  confidently assigned genes. Report their shapes; name genes only in C2, C4
  and C5.
- **k = 5 is a reported choice, not the rule's output.** The frozen rule
  returned k = 6 by a margin of 0.0006 against a standard deviation of 0.026;
  k = 5 is better on silhouette and both stability measures. State the rule,
  its result and the departure in the Methods.
- **Two validation measures cannot fail.** All 525 Tier 1 genes keep
  direction under leave-one-study-out by arithmetic, and the power-matched
  design cannot carry significance. Quote the measures that can fail: 521
  stay significant, 263 keep their effect size.
- **Leave-one-study-out is 5 runs, not 8** — three studies carry no F0–F4
  labels.
- **F4 is underpowered**: 35 samples against 127–186 elsewhere.
- **Age and sex cover 385 staged samples**, not 1,085.
- **F0 is not a control group**: of 152 samples, 46 are healthy controls, 73
  have fatty liver without scarring, 5 have NASH without scarring.
- **Significant-gene counts are inflated by selection**; the comparisons
  between transitions and clusters remain fair.
- **No predictive model was built or validated.** No classifier, no AUC, no
  held-out set.
- **Link prediction is unresolved** and belongs to Paper 2.

The package's `04_LIMITATIONS.md` carries these with the measurements behind
them.

## Mentor's constraints on deliverables

From the 2026-09-07 meeting, reflected in `export_for_mentor.py`: stage-wise
gene CSVs, age and sex only (no other phenotypes), **no pathway
information**, and not all 53,993 genes — the progression genes.

## Where things stand

Both briefs are complete. `Paper1_Results/` holds Tasks 1–4,
`Paper1_HighConfidence/` the prioritisation and mechanism network, and
`Paper1_Package/` is the self-contained folder a collaborator writes the
manuscript from — 260 files, every one checksummed.

`scripts/` holds the analysis code. It does not live inside the results
folders, deliberately: when it did, scripts resolved each other by position
and several silently read the wrong version's outputs.

`Paper1_Manuscript/` still carries numbers from an earlier run and covers
Tasks 1–4 only. Treat it as draft prose, not as a current document.

## Session history

`handover/` holds earlier Claude Code sessions converted to Markdown. They are
dated snapshots: where they disagree with this file, this file wins; where
this file disagrees with the code, the code wins.
