# 1. Overview

## The aim

**Predict the stage of liver disease progression.** Everything here serves
that: the harmonisation exists so eight cohorts can be read on one scale, the
knowledge graph exists so measurement and biology can be queried together,
and the analyses establish which genes carry stage information, what shape
that information takes across stages, where along the ladder the largest
change happens, what biology it corresponds to, and which genes survive every
independent check.

## The cohort

Eight human liver transcriptome studies from the Gene Expression Omnibus:
**1,085 samples from 1,027 patients.**

| Study | Samples | Patients | Fibrosis staged | Disease labelled |
|---|---|---|---|---|
| GSE126848 | 57 | 57 | — | yes |
| GSE130970 | 78 | 78 | F0–F4 | derived from histology |
| GSE135251 | 216 | 216 | F0–F4 | spectrum only (NAFLD) |
| GSE162694 | 143 | 143 | F0–F4 | spectrum only (NAFLD) |
| GSE167523 | 98 | 98 | — | yes |
| GSE193066 | 164 | **106** | F0–F4 | — |
| GSE240729 | 67 | 67 | F0–F4 | — |
| GSE269412 | 262 | 262 | — | — |

The full version, with per-stage breakdown and demographic coverage, is
`02_TABLES/main/Table1_cohort.csv`.

Four facts about this cohort govern most of what follows:

- **668 samples carry a fibrosis stage**, from five studies. The distribution
  is uneven: F0 152, F1 168, F2 186, F3 127, **F4 only 35.**
- **The disease ladder rests on three studies and 221 patients.** Two further
  studies label patients as NAFLD without stating the NAFL/NASH subtype, so
  they cannot be placed on a control → NAFL → NASH ordering.
- **GSE193066's 164 samples are 106 people** — 58 were biopsied twice. The
  first biopsy is used, so each patient contributes once and the expression
  is paired with the stage recorded at that same biopsy.
- **Demographics cover part of the cohort.** Sex for 540 samples, age for
  483, and only **385 samples have demographics *and* a fibrosis stage.**

## The two ladders

Liver disease progresses along two axes that pathologists score separately,
and they are never merged here:

| Ladder | Scale | What it measures |
|---|---|---|
| **Fibrosis** | F0 → F1 → F2 → F3 → F4 | Scarring. Largely permanent. |
| **Disease** | control → NAFL → NASH | Inflammation. Reversible. |

They are not interchangeable, and the overlap between them is itself a result
(Figures 2 and 3).

## The knowledge graph

Harmonised measurements and curated biology are held together in a Neo4j
property graph: **53,993 genes**, 1,085 samples, and the curated layer —
diseases, drugs, pathways, biological processes and phenotypes — joined on
the same Ensembl identifiers.

The measurement edges are 32.5 million `EXPRESSES` relationships. The
**`TRACKS_FIBROSIS` (3,645) and `TRACKS_INFLAMMATION` (2,739)** edges are
derived from these patients and are the project's own contribution to the
graph rather than something imported.

**You do not need the database to use this package.** Every analysis here
reads CSV files, including the knowledge-graph figure. The graph is how the
data is organised, not a dependency of the results. The curated layer ships
in full as `04_DATA/knowledge_layer/`.

## What was produced

| Stage | Output | Where |
|---|---|---|
| Harmonisation and integration | harmonised data, the graph, 5,884 progression genes | `04_DATA/` |
| Task 1 | genes split into fibrosis-only / inflammation-only / shared | `03_RESULTS/Task1_gene_groups/` |
| Task 2 | five reproducible F0→F4 trajectory shapes | `03_RESULTS/Task2_trajectories/` |
| Task 3 | the four stage transitions compared at patient level | `03_RESULTS/Task3_transitions/` |
| Task 4 | pathway enrichment per group and per cluster | `03_RESULTS/Task4_enrichment/` |
| Task 5 | 525 high-confidence genes, a prioritised 25, mechanism network | `03_RESULTS/Task5_gene_prioritisation/` |

## The headline results

1. **5,884 genes track progression** across eight independent studies:
   1,866 fibrosis-only, 2,203 inflammation-only, 1,815 both. **3,681 track
   fibrosis.**
2. **Fibrosis genes follow five reproducible shapes**, not one. Immune
   activation is established early; matrix remodelling accelerates late.
3. **The largest transcriptional change is at F3→F4**, the transition into
   cirrhosis — and this only becomes visible once statistical power is
   equalised across transitions.
4. **Each programme carries distinct biology.** Rising fibrosis-only genes
   are immune; falling genes are the loss of normal liver metabolism; genes
   shared by both ladders are the core fibrogenic programme.
5. **525 genes are supported by every independent kind of evidence
   available**, from which 25 were prioritised to span all five trajectory
   shapes and both directions.

Each is stated with its own caveats in `04_LIMITATIONS.md`. Result 3 in
particular depends on a design choice that is explained rather than assumed.
