# Liver disease knowledge graph

A knowledge graph linking gene expression from eight human liver GEO studies to
curated biological knowledge, built to answer the mentor's stated aim: **predict
the stage of liver disease progression.**

Read `git log` oldest-to-newest for the decision trail. Every script's docstring
explains why it exists and what trap it avoids; those are the real documentation
and they are kept current.

## The data

Eight GEO studies, 1,085 samples from 1,027 patients (some re-biopsied):

| Study | Samples | | Study | Samples |
|---|---|---|---|---|
| GSE126848 | 57 | | GSE167523 | 98 |
| GSE130970 | 78 | | GSE193066 | 164 |
| GSE135251 | 216 | | GSE240729 | 67 |
| GSE162694 | 143 | | GSE269412 | 262 |

Raw downloads live under `data/raw/` and are gitignored. `.gitignore` carries
the provenance (Dataverse DOIs, MSigDB URL) and a rebuild command for every
excluded bulk folder — read it before assuming data is missing.

## Pipeline, in order

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_full   # GEO files -> long format
python map_gene_ids.py                                                      # -> canonical Ensembl IDs via HGNC
python build_crosswalk.py                                                   # sample_key -> GSM accession
python normalize_clinical.py                                                # harmonise fibrosis/disease labels
python build_graph_all.py --interim data/interim_full --out data/graph_full  # Neo4j-ready CSVs
python build_optimuskg_layer.py                                             # knowledge layer CSVs
python find_progression_genes.py                                            # -> data/progression_full/
python export_for_mentor.py                                                 # -> data/for_mentor/
python paper1_task1_groups.py && python paper1_task2_trajectories.py
python paper1_task3_transitions.py && python paper1_task4_enrichment.py     # -> Paper1_Results/
```

Loading into Neo4j is Cypher, not Python: `create_kg_constraints.cypher`, then
`load_edges.cypher` / `reload_expression.cypher`.

## The graph

Neo4j Enterprise 2026.07.0 via Neo4j Desktop 2. **126,244 nodes / 35,091,066
relationships**, store format `block-block-1.1` (Enterprise-only — a dump of
this will not load into Community Edition).

Nodes: Gene 53,993 · Disease 36,044 · BioProcess 12,203 · Drug 12,025 ·
Phenotype 8,666 · Pathway 2,220 · Sample 1,085 · Dataset 8

Edges: EXPRESSES 32,471,042 · ASSOCIATED_WITH 1,832,441 · INTERACTS_WITH 324,116 ·
INVOLVED_IN 157,081 · HAS_PHENOTYPE 149,960 · IN_PATHWAY 46,751 · TREATS 43,636 ·
PARENT_OF 28,919 · ACTS_ON 20,674 · CONTRAINDICATED_IN 8,255 ·
TRACKS_FIBROSIS 3,645 · TRACKS_INFLAMMATION 2,739 · IN_DATASET 1,085 ·
OFF_LABEL_FOR 722

`EXPRESSES` is 93% of the graph and is *measurement*, not knowledge. The
`TRACKS_*` edges (6,384, patient-derived) are what those measurements mean, and
they are the project's own contribution to the graph.

The server is configured with a 1 GB heap and 512 MB page cache against a 2.5 GB
store. Counting all relationships by type in one query times out — count per type
instead, which hits the count store and returns instantly.

## Decisions already settled — do not re-litigate

- **Measured zeros are kept.** Dropping them removes the switching-on that *is*
  the progression signal: IL6 is detected in 10% of stage-1 and 64% of stage-4
  patients. Keeping them added 9.1M measurements and 514 progression genes, and
  is how TREM2 was found. Hence `data/interim_full` (no `--drop-zeros`), not
  `data/interim`.
- **OptimusKG replaced PrimeKG.** PrimeKG records 0 drugs treating NASH, NAFLD
  or cirrhosis; OptimusKG records 74 / 95 / 71. With zero known drug-disease
  links there was nothing for link prediction to learn from.
- **Two ladders, not one.** Fibrosis (0→4, scarring, largely permanent) and
  disease (control→NAFL→NASH, inflammation, reversible) are scored separately by
  pathologists and are analysed separately here. 40 NASH patients sit at fibrosis
  stage 0 — the most treatable moment, invisible on the fibrosis ladder alone.
- **Per-study correlation, then combine** — never pool patients across studies.
  A gene that climbs in one study and does nothing in the other four is a quirk
  of that cohort. Cross-study agreement is the validation rule throughout.
- **`value_z`** is expression standardised per gene *within* each study. It is
  what makes eight cohorts comparable; use it, not raw values.
- **`n_datasets`** (1–8) on every Gene node records how many studies measured it.
  39,199 genes are missing from at least one study and 10,621 appear in exactly
  one. Never average across genes without checking it.
- **Raw clinical fields are never modified.** `normalize_clinical.py` *adds*
  `fibrosis_stage`, `disease_group`, `patient_id`, `biopsy_number` beside the
  `*_raw` originals so every translation stays auditable.
- **Enrichment background is the 14,794 genes** eligible for cross-study analysis,
  not all ~20,000 human genes. Using the wrong background invalidates Task 4.

## Known limits — state these, never paper over them

- **Age and sex cover only part of the cohort.** Five of eight studies record
  them; three of those also stage fibrosis. The stage × age × sex comparison
  rests on 385 samples from GSE130970, GSE162694 and GSE193066 — not 1,085. The
  per-stage gene table itself uses all 668 staged samples. Every output file
  carries its own n so the limit is visible.
- **Label rulers differ per study** (`"0".."4"` vs `"F0".."F4"` vs
  `"normal liver histology"`). Querying `fibrosis_stage_raw = '4'` returns 29 of
  35 real cirrhosis samples and reports no error. Always use the harmonised field.
- **F4 is underpowered** relative to other stages; Task 3 refits every transition
  on equal-size random subsamples as a power-matched check.
- **Link prediction is unresolved.** The pipeline is built (`export_triples.py`,
  `train_link_prediction.py`) but the first model failed its own validation. Treat
  any drug-repurposing output as unverified.

## Mentor's constraints on deliverables

From the 2026-09-07 meeting, reflected in `export_for_mentor.py`: stage-wise gene
CSVs, age and sex only (no other phenotypes), **no pathway information**, and not
all 53,993 genes — the 4,692 progression genes.

## Where things stand

Paper 1's four analyses are complete and committed (`Paper1_Results/Task1..4`,
each with its own `README.txt` stating method and caveats). Branch:
`harmonize-clinical-metadata`.

## Session history

`handover/` holds the Claude Code sessions in which these decisions were argued
out, converted to readable Markdown — the reasoning behind this file. See
`handover/README.md` for the reading order. They are dated snapshots: where they
disagree with this file, this file wins; where this file disagrees with the code,
the code wins.
