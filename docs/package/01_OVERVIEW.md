# 1. Overview

## The aim

The project's stated aim, set at the outset, is to **predict the stage of
liver disease progression**. Everything here serves that: the harmonisation
exists so that eight cohorts can be read on one scale, the graph exists so
that measurement and biology can be queried together, and the analyses exist
to establish which genes carry stage information, what shape that information
takes across stages, where along the ladder the largest change happens, what
biology it corresponds to, and which genes survive every independent check.

## The data

Eight human liver transcriptome studies from the Gene Expression Omnibus:
**1,085 samples from 1,027 patients.**

| Study | Samples | Patients | Fibrosis staged | Disease labelled |
|---|---|---|---|---|
| GSE126848 | 57 | 57 | no | yes |
| GSE130970 | 78 | 78 | yes (F0–F4) | derived from histology |
| GSE135251 | 216 | 216 | yes (F0–F4) | yes |
| GSE162694 | 143 | 143 | yes (F0–F4) | yes (recovered from titles) |
| GSE167523 | 98 | 98 | no | yes |
| GSE193066 | 164 | **106** | yes (F0–F4) | no (left blank deliberately) |
| GSE240729 | 67 | 67 | yes (F0–F4) | no |
| GSE269412 | 262 | 262 | no | no (no join key exists) |

The full version of this table, with the per-stage breakdown and demographic
coverage, is `02_TABLES/main/Table1_cohort.csv`.

Three facts about this cohort govern most of what follows:

- **668 samples carry a fibrosis stage**, from five studies. The stage
  distribution is uneven: F0 152, F1 168, F2 186, F3 127, **F4 only 35.**
- **592 samples carry a disease group**, from five studies.
- **GSE193066's 164 samples are 106 people** — 58 were biopsied twice.
  Treating them as independent is pseudo-replication; samples are collapsed
  to one row per patient before any statistic is computed.
- **Demographic coverage is partial.** Sex is recorded by five of the eight
  studies (540 samples) and age by four (483 samples). Only three studies
  record demographics *and* stage fibrosis, so any analysis crossing stage
  with age or sex rests on **385 samples**, not 1,085.

## The two ladders

Liver disease progresses along two axes that pathologists score separately,
and this project never merges them:

| Ladder | Scale | What it measures |
|---|---|---|
| **Fibrosis** | F0 → F1 → F2 → F3 → F4 | Scarring. Largely permanent. |
| **Disease** | control → NAFL → NASH | Inflammation. Reversible. |

They are not interchangeable. **40 patients in this cohort have NASH at
fibrosis stage 0** — inflamed but not yet scarred, which is the most
treatable moment in the disease and is invisible on the fibrosis ladder
alone. Both ladders are therefore analysed separately throughout, and the
overlap between them is itself a result (Figures 2 and 3).

## The graph

The harmonised measurements and curated biology were loaded into a Neo4j
property graph: **126,244 nodes and 35,091,066 relationships.**

| Nodes | | Edges | |
|---|---|---|---|
| Gene | 53,993 | EXPRESSES | 32,471,042 |
| Disease | 36,044 | ASSOCIATED_WITH | 1,832,441 |
| BioProcess | 12,203 | INTERACTS_WITH | 324,116 |
| Drug | 12,025 | INVOLVED_IN | 157,081 |
| Phenotype | 8,666 | HAS_PHENOTYPE | 149,960 |
| Pathway | 2,220 | IN_PATHWAY | 46,751 |
| Sample | 1,085 | TREATS | 43,636 |
| Dataset | 8 | PARENT_OF | 28,919 |
| | | ACTS_ON | 20,674 |
| | | CONTRAINDICATED_IN | 8,255 |
| | | **TRACKS_FIBROSIS** | **3,645** |
| | | **TRACKS_INFLAMMATION** | **2,739** |
| | | IN_DATASET | 1,085 |
| | | OFF_LABEL_FOR | 722 |

`EXPRESSES` is 93% of the graph and is **measurement**, not knowledge. The
`TRACKS_FIBROSIS` and `TRACKS_INFLAMMATION` edges — 6,384 in total, derived
from these patients — are what those measurements *mean*, and they are the
project's own contribution to the graph rather than something imported.

**You do not need the database to use this package.** Every analysis here
reads CSV files, including the knowledge-graph figure. The graph is how the
data was organised, not a dependency of the results.

## What was produced

| Stage | Output | Where |
|---|---|---|
| 1–8 | Harmonised data, the graph, 4,692 progression genes | `04_DATA/` |
| 9 | Genes split into fibrosis-only / inflammation-only / shared | `03_RESULTS/Task1_gene_groups/` |
| 10 | Five reproducible F0→F4 trajectory shapes | `03_RESULTS/Task2_trajectories/` |
| 11 | The four stage transitions compared at patient level | `03_RESULTS/Task3_transitions/` |
| 12 | Pathway enrichment per group and per cluster | `03_RESULTS/Task4_enrichment/` |
| 13 | 507 high-confidence genes, a prioritised 25, mechanism subgraph | `03_RESULTS/Task5_high_confidence_genes/` |

## The headline results

1. **4,692 genes track progression** across eight independent studies:
   1,953 fibrosis-only, 1,047 inflammation-only, 1,692 both.
2. **Fibrosis genes follow five reproducible shapes**, not one. Immune
   activation starts early; matrix remodelling accelerates late.
3. **The largest transcriptional change is at F3→F4**, the transition into
   cirrhosis — and this only becomes visible once statistical power is
   equalised across transitions.
4. **Each programme carries distinct biology.** Rising fibrosis-only genes
   are immune; falling genes are the loss of normal liver metabolism; genes
   shared by both ladders are the core fibrogenic programme.
5. **507 genes are supported by every independent kind of evidence
   available**, from which 25 were prioritised to span all five trajectory
   shapes and both directions.

Each of these is stated with its own caveats in `05_LIMITATIONS.md`. Result 3
in particular depends on a design choice that is explained rather than
assumed.
