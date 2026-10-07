# Liver Disease Knowledge Graph

A knowledge graph that links gene expression from eight human liver studies to
curated biological knowledge, built to answer one question:

> **Can we tell what stage of liver disease a patient is at, and what is pushing
> them to the next one?**

Liver disease progresses quietly. By the time scarring is advanced the options
narrow sharply, and the staging that decides treatment still depends on a biopsy
read by a pathologist. This project asks whether the molecular signal in the
tissue carries that stage information on its own — and, if it does, which genes
carry it and when they switch.

**Paper 1 is complete.** Its four analyses, their results and their caveats are
in [`Paper1_Results/`](Paper1_Results) and are summarised below.

---

## Contents

- [What is in here](#what-is-in-here)
- [The data](#the-data)
- [Getting started](#getting-started)
- [The pipeline](#the-pipeline)
- [The graph](#the-graph)
- [Paper 1](#paper-1)
  - [Task 1 — Splitting the progression genes into groups](#task-1--splitting-the-progression-genes-into-groups)
  - [Task 2 — How fibrosis genes change from F0 to F4](#task-2--how-fibrosis-genes-change-from-f0-to-f4)
  - [Task 3 — Where the biggest change happens](#task-3--where-the-biggest-change-happens)
  - [Task 4 — What biology each group represents](#task-4--what-biology-each-group-represents)
  - [How to read Paper 1's results](#how-to-read-paper-1s-results)
- [Decisions that shape every number](#decisions-that-shape-every-number)
- [Known limits](#known-limits)
- [Repository map](#repository-map)
- [Further reading](#further-reading)

---

## What is in here

Three things, layered:

1. **A measurement layer** — 1,085 liver biopsies from eight public GEO studies,
   parsed, mapped to canonical gene IDs, and harmonised so the eight cohorts can
   be compared at all.
2. **A knowledge layer** — genes, diseases, drugs, pathways, phenotypes and
   biological processes from OptimusKG, attached to the same gene nodes.
3. **The project's own contribution** — `TRACKS_FIBROSIS` and
   `TRACKS_INFLAMMATION` edges, derived from these patients, that say which genes
   actually move with disease stage in this cohort rather than in the literature.

Paper 1 is the analysis of that third layer: which genes track progression, what
shape their trajectories take, where the molecular change concentrates, and what
biology each group represents.

---

## The data

Eight GEO studies, **1,085 samples from 1,027 patients** (some patients were
biopsied twice):

| Study | Samples | | Study | Samples |
|---|---:|---|---|---:|
| GSE126848 | 57 | | GSE167523 | 98 |
| GSE130970 | 78 | | GSE193066 | 164 |
| GSE135251 | 216 | | GSE240729 | 67 |
| GSE162694 | 143 | | GSE269412 | 262 |

Raw downloads live under `data/raw/` and are gitignored because of their size.
**`.gitignore` carries the provenance for every excluded folder** — Dataverse
DOIs, the MSigDB URL, and a rebuild command — so read it before assuming data is
missing.

Patients are scored on two separate ladders, because pathologists score them
separately and they are not the same thing:

| Ladder | Range | What it measures |
|---|---|---|
| **Fibrosis** | F0 → F4 | Scarring. Largely permanent. |
| **Disease** | control → NAFL → NASH | Inflammation. Reversible. |

668 of the 1,085 samples carry a fibrosis stage. The two ladders are analysed
separately throughout — see [Decisions](#decisions-that-shape-every-number).

---

## Getting started

```bash
git clone https://github.com/nissankararaoThanvitha/liver_graph.git
cd liver_graph
pip install -r requirements.txt
```

Built and run on **Python 3.13.7**. Versions in `requirements.txt` are pinned to
the ones that produced the committed results, so Paper 1's numbers are
reproducible rather than approximately reproducible.

`pykeen` and `torch` are only needed for `train_link_prediction.py` and pull in a
~2 GB install — skip both if you are not running it.

To get Neo4j, the code and the data running from scratch, see
[`handover/SETUP.md`](handover/SETUP.md).

**If you only want the results,** you do not need to run anything.
[`Paper1_Results/`](Paper1_Results) holds every table and figure, and each task
folder has a `README.txt` stating its method and its caveats.

---

## The pipeline

Run in this order:

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_full   # GEO files -> long format
python map_gene_ids.py                                                      # -> canonical Ensembl IDs via HGNC
python build_crosswalk.py                                                   # sample_key -> GSM accession
python normalize_clinical.py                                                # harmonise fibrosis/disease labels
python build_graph_all.py --interim data/interim_full --out data/graph_full  # Neo4j-ready CSVs
python build_optimuskg_layer.py                                             # knowledge layer CSVs
python find_progression_genes.py                                            # -> data/progression_full/
python export_for_mentor.py                                                 # -> data/for_mentor/
```

Then the four Paper 1 analyses, in order — Task 4 depends on Task 2's clusters:

```bash
python paper1_task1_groups.py
python paper1_task2_trajectories.py
python paper1_task3_transitions.py
python paper1_task4_enrichment.py        # -> Paper1_Results/
```

Loading into Neo4j is Cypher, not Python: run `create_kg_constraints.cypher`
first, then `load_edges.cypher` / `reload_expression.cypher`.

Every script's docstring explains why it exists and what trap it avoids. Those
docstrings are the real documentation and they are kept current.

---

## The graph

Neo4j Enterprise 2026.07.0 via Neo4j Desktop 2.
**126,244 nodes / 35,091,066 relationships**, store format `block-block-1.1`
(Enterprise-only — a dump of this will not load into Community Edition).

**Nodes**

| | | | |
|---|---:|---|---:|
| Gene | 53,993 | Phenotype | 8,666 |
| Disease | 36,044 | Pathway | 2,220 |
| BioProcess | 12,203 | Sample | 1,085 |
| Drug | 12,025 | Dataset | 8 |

**Relationships**

| | | | |
|---|---:|---|---:|
| EXPRESSES | 32,471,042 | PARENT_OF | 28,919 |
| ASSOCIATED_WITH | 1,832,441 | ACTS_ON | 20,674 |
| INTERACTS_WITH | 324,116 | CONTRAINDICATED_IN | 8,255 |
| INVOLVED_IN | 157,081 | TRACKS_FIBROSIS | 3,645 |
| HAS_PHENOTYPE | 149,960 | TRACKS_INFLAMMATION | 2,739 |
| IN_PATHWAY | 46,751 | IN_DATASET | 1,085 |
| TREATS | 43,636 | OFF_LABEL_FOR | 722 |

`EXPRESSES` is 93% of the graph and is **measurement**, not knowledge. The 6,384
`TRACKS_*` edges are patient-derived and say what those measurements *mean* —
they are this project's own contribution to the graph, and they are what Paper 1
analyses.

> **Performance note.** The server runs a 1 GB heap and 512 MB page cache against
> a 2.5 GB store. Counting all relationships by type in a single query times out.
> Count per type instead — that hits the count store and returns instantly.

---

## Paper 1

Paper 1 starts from **4,692 progression genes**: genes whose expression tracks
disease stage consistently across the eight studies.

How they were found (`find_progression_genes.py`): within each study separately,
each gene's `value_z` is correlated against ladder position by Spearman — ordered
stages, with no meaningful spacing between them, so rank correlation is the
honest test. Per-study correlations are then combined by their median and
per-study p-values by Fisher's method, with Benjamini–Hochberg correction. A gene
is kept only where the studies agree on direction. Only genes measured in all
eight studies are tested, and the 58 twice-biopsied GSE193066 patients are
collapsed to one row per patient first, so they do not carry double weight.

The four analyses below take that gene list and ask four questions of it.

---

### Task 1 — Splitting the progression genes into groups

**Question:** do fibrosis and inflammation recruit the same genes?

Each of the 4,692 genes carries a fibrosis ρ, an inflammation ρ, or both.
Task 1 counts the groups, splits each into genes that rise and genes that fall
with worsening disease, and tests whether the two scores agree.

| Group | Genes | % | Up | Down |
|---|---:|---:|---:|---:|
| Fibrosis-only | 1,953 | 41.6% | 1,301 | 652 |
| Inflammation-only | 1,047 | 22.3% | 597 | 450 |
| Shared | 1,692 | 36.1% | 1,335 | 356 |

**Result.** The two ladders overlap substantially but are far from identical:
roughly a third of the genes respond to both, and nearly two thirds to only one.
Across the 1,692 shared genes, fibrosis ρ and inflammation ρ correlate at
ρ = 0.725 (p = 2.9e-276) — but that figure is partly driven by two separate
up and down clouds. Within direction the honest estimates are ρ = 0.453 for the
up genes (n = 1,335) and ρ = 0.354 for the down genes (n = 356).

Exactly **one** gene out of 1,692 is discordant — GPD1, up with fibrosis and down
with inflammation. It is excluded from Task 4's groups.

📁 [`Paper1_Results/Task1/`](Paper1_Results/Task1) — summary table, Venn diagram,
ρ-vs-ρ scatter, top 20 rising and falling fibrosis genes.

---

### Task 2 — How fibrosis genes change from F0 to F4

**Question:** do all fibrosis genes change at the same point, or are there
distinct timings?

The 3,645 fibrosis-associated genes (fibrosis-only + shared) each have five stage
means, from 668 staged samples (F0 152, F1 168, F2 186, F3 127, F4 35). Each
gene's five values are z-scored *across stages*, so genes group by the **shape**
of their curve rather than its size, then clustered by k-means with 50 random
starts.

**k was chosen by stability, not by eye.** k = 3–8 were each scored on silhouette,
on 50 random 80% gene subsamples, and on 50 patient bootstraps resampled within
study. The rule — largest k whose gene-subsample ARI stays ≥ 0.95 — gives **k = 5**.
Clusters were named *after* clustering, from their average curves. No gene was
assigned to a pattern by hand.

| Cluster | Shape | Genes | High-confidence |
|---|---|---:|---:|
| **C1** | Early increase (F0→F1), then continued | 927 | 47 |
| **C2** | Late increase, largest at F3→F4 | 1,514 | 841 |
| **C3** | Early rise, then plateau | 197 | 36 |
| **C4** | Mid decrease, largest at F1→F2 | 309 | 78 |
| **C5** | Late decrease, largest at F3→F4 | 698 | 423 |

**What is solid, and what is not.** The five *shapes* are reproducible — in 100
patient bootstraps each was recovered at median correlation 0.97–0.997 — and they
are not an artefact of which studies contributed: profiles re-estimated as
`value_z ~ stage + study` correlate 0.998 with the plain stage means.

Individual gene *membership* is less certain. Genes move between neighbouring
clusters under bootstrap, mostly among the three increasing clusters, which
differ only in timing. C2 and C5 have large stable cores; C1, C3 and C4 are
dominated by borderline genes. **Every gene carries a `membership_confidence`
column — use the high-confidence genes for any claim about a specific gene.**

C3 was originally named "Rise to F3, then reverse" from its stage means. Task 3's
patient-level test found no significant F3→F4 drop in any of its 197 genes, so it
was renamed. Its core is cell-cycle genes — ANLN, ASPM, KIF20A, RRM2, TTK, TOP2A.

📁 [`Paper1_Results/Task2/`](Paper1_Results/Task2) — per-gene cluster assignments
with confidence, cluster trajectories, heatmap, the k-selection curves, and both
robustness checks.

---

### Task 3 — Where the biggest change happens

**Question:** which transition — F0→F1, F1→F2, F2→F3 or F3→F4 — carries the
largest molecular change?

Stage means alone would not settle this, so Task 3 works at patient level. For
each gene and each transition it fits `value_z ~ stage + study` on the patients of
those two stages only. Including `study` means stages are compared **within** each
study, so a difference in which studies contributed to which stage cannot
manufacture a change. Repeat biopsies at the same stage are averaged (28
patients); a patient biopsied on both sides of a transition keeps one sample,
chosen at random with a fixed seed (24 patients). "Substantially changing" means
q < 0.05 **and** |β| ≥ 0.2 SD.

| | F0→F1 | F1→F2 | F2→F3 | F3→F4 |
|---|---:|---:|---:|---:|
| Patients (a / b) | 152/166 | 160/165 | 165/109 | 118/34 |
| Substantial genes | 1,165 | 1,175 | 1,117 | **936** |
| — up | 1,135 | 647 | 906 | 865 |
| — down | 30 | 528 | 211 | 71 |
| Median &#124;β&#124; | 0.188 | 0.189 | 0.221 | **0.378** |
| **Power-matched, median** | 0 | 0 | 2 | **311** |

**Result — the largest change is at F3 → F4.** On raw counts the four transitions
look comparable, but that comparison is unfair: F4 has only 34 patients. Because
F4 is underpowered, every transition was refitted 50 times on the **same**
study-balanced design — 30 patients per stage — so all four have equal
statistical power. Once power is equalised, F3→F4 dominates outright (median 311
genes against 0–2), with a typical effect size about twice that of any earlier
transition.

The picture that gives: **earlier transitions are many small consistent changes
that need large samples to detect; the transition into cirrhosis is fewer,
larger ones.** Direction matters too — F0→F1 is almost entirely increases
(1,135 up against 30 down), and genes only begin switching *off* at F1→F2.

> **Stated honestly:** these genes were selected because they correlate with
> fibrosis stage in this same data, so the absolute counts of significant genes
> are inflated by circularity. The *comparison between transitions* — which is the
> question asked — remains fair, because all four use the same genes. F3→F4 still
> rests on 34 patients and is the least precisely estimated.

📁 [`Paper1_Results/Task3/`](Paper1_Results/Task3) — every gene × transition with
β, SE, p, q and cluster; top genes per transition; the four-panel comparison
figure.

---

### Task 4 — What biology each group represents

**Question:** what processes do these gene groups actually correspond to?

Enrichment is run **separately on each group** — never on all 4,692 genes at once,
which would blur opposing programmes into mush. Eleven groups are tested: the six
direction-split groups from Task 1, and the five Task 2 clusters. Four databases:
GO Biological Process, KEGG, Reactome and MSigDB Hallmark (v2024.1), one-sided
hypergeometric with BH-FDR within each group × database.

> **The background is the methodological point.** Enrichment is tested against the
> **14,794 genes eligible for the cross-study analysis** — those measured in every
> study — not all ~20,000 human genes. Using the full genome would make these
> results look more significant than they are. Every gene set was first restricted
> to those 14,794 genes and kept only if 10–500 of them remained.

| Group | Biology |
|---|---|
| **Fibrosis-only, up** | Immune cell activation (myeloid, T cell), IL6–JAK–STAT3, inflammatory response |
| **Fibrosis-only, down** | Xenobiotic, fatty acid and bile acid metabolism, peroxisome — loss of normal liver function |
| **Inflammation-only** | Weak: interferon-α response and G2/M up; **nothing significant** for the down genes |
| **Shared, up** | ECM / collagen formation, EMT, TNFα–NFκB, apoptosis, p53, angiogenesis — the core fibrogenic programme |
| **Shared, down** | Amino-acid catabolism, xenobiotic and bile acid metabolism, coagulation |
| **C1** early increase | Adaptive immunity, T cell activation, interferon-γ — **immune activation starts early** |
| **C2** late increase | EMT, matrix organisation, cell migration, hypoxia, TGF-β — **scarring accelerates late** |
| **C3** early rise, plateau | Cell cycle: E2F targets, G2/M checkpoint, chromosome segregation |
| **C4** mid decrease | Few terms — no clear theme |
| **C5** late decrease | Bile acid, fatty acid and xenobiotic metabolism, peroxisome — **metabolic failure as cirrhosis develops** |

Read across the clusters and a sequence appears: immune activation first,
proliferation alongside it, then matrix deposition and metabolic failure together
at the late stages — matching Task 3's finding that F3→F4 carries the largest
change.

**Does the biology survive the uncertainty in cluster membership?** Each cluster
was re-run using only its high-confidence genes. C2, C3 and C5 hold (10/10 top GO
BP terms retained for C2 and C5). C1 holds only at the level of "immune
activation" — 8/10 GO BP terms survive, but its 47 core genes cannot support the
Hallmark/KEGG/Reactome terms. C4 is too weak to judge either way.

📁 [`Paper1_Results/Task4/`](Paper1_Results/Task4) — significance counts, top
pathways per group, all FDR < 0.05 terms, the core-gene check, four combined
heatmaps, and per-group dot plots.

---

### How to read Paper 1's results

Each task folder carries its own `README.txt` stating exactly how that analysis
was run and what it does not support. **Those files are authoritative** — read the
one for a task before quoting its numbers.

Three habits that keep conclusions honest here:

- **Report shapes with confidence; report specific genes with caution.** Task 2's
  five trajectory shapes are stable. Which cluster a borderline gene landed in is
  not. Filter on `membership_confidence >= 0.8`.
- **Mind the circularity in Task 3.** Counts of significant genes are inflated;
  comparisons between transitions are not.
- **Never quote an enrichment term without its background.** The 14,794-gene
  background is what makes Task 4's numbers mean anything.

---

## Decisions that shape every number

These were argued out and settled. They are recorded here because each one
silently changes results if reversed.

**Measured zeros are kept.** Dropping zero values removes the *switching-on* that
is the progression signal — IL6 is detected in 10% of stage-1 patients and 64% of
stage-4 patients. Keeping them added 9.1M measurements and 514 progression genes,
and is how TREM2 was found. Hence `data/interim_full`, not `data/interim`.

**Two ladders, not one.** Fibrosis and disease activity are scored separately by
pathologists and analysed separately here. 40 NASH patients sit at fibrosis stage
0 — inflamed but not yet scarred, the most treatable moment in the disease, and
invisible if you only look at the fibrosis ladder.

**Per-study correlation, then combine — never pool patients across studies.** A
gene that climbs in one cohort and does nothing in the other four is a quirk of
that cohort. Cross-study agreement is the validation rule throughout.

**`value_z`, not raw expression.** Expression standardised per gene *within* each
study is what makes eight cohorts comparable at all.

**`n_datasets` (1–8) is on every Gene node.** 39,199 genes are missing from at
least one study and 10,621 appear in exactly one. Never average across genes
without checking it.

**Raw clinical fields are never modified.** `normalize_clinical.py` *adds*
`fibrosis_stage`, `disease_group`, `patient_id` and `biopsy_number` beside the
`*_raw` originals, so every translation stays auditable.

**OptimusKG replaced PrimeKG.** PrimeKG records 0 drugs treating NASH, NAFLD or
cirrhosis; OptimusKG records 74 / 95 / 71. It also identifies genes by Ensembl ID
— the same identifier this pipeline standardises on — so 94% of genes join
directly, against 49% for PrimeKG, and its drug–gene edges carry mode of action
(INHIBITOR, AGONIST, BLOCKER and 20 more) rather than a single untyped link.

---

## Known limits

State these; do not paper over them.

**Age and sex cover only part of the cohort.** Five of eight studies record them,
and only three of those also stage fibrosis. The stage × age × sex comparison
rests on **385 samples** from GSE130970, GSE162694 and GSE193066 — not 1,085. The
per-stage gene table itself uses all 668 staged samples. Every output file carries
its own n so the limit stays visible.

**Label rulers differ per study.** The eight studies write fibrosis as `"0".."4"`,
`"F0".."F4"`, or `"normal liver histology"`, and sex six different ways. Querying
`fibrosis_stage_raw = '4'` returns 29 of 35 real cirrhosis samples **and reports
no error**. Always use the harmonised fields.

**F4 is underpowered** relative to the other stages. Task 3 refits every
transition on equal-size random subsamples as a power-matched check precisely
because of this.

**Link prediction is unresolved.** The pipeline exists (`export_triples.py`,
`train_link_prediction.py`) but the first model failed its own validation. Treat
any drug-repurposing output as **unverified**.

---

## Repository map

```
.
├── Paper1_Results/          Paper 1 output — Task1..4, each with its own README.txt
│   ├── Task1/               progression gene groups
│   ├── Task2/               F0->F4 trajectory clusters
│   ├── Task3/               transition analysis
│   └── Task4/               pathway enrichment
├── data/                    inputs and derived tables (bulk folders gitignored)
│   ├── for_mentor/          stage-wise gene CSVs + their README.txt
│   └── progression_full/    the progression gene lists
├── handover/                how the project's decisions were reached
│   ├── README.md            reading order for the sessions
│   ├── SETUP.md             Neo4j + code + data from scratch
│   └── sessions/            four annotated working sessions
├── CLAUDE.md                project context, settled decisions, known limits
├── requirements.txt         pinned to the versions that produced these results
│
├── parse_expression.py        GEO files -> long format
├── map_gene_ids.py            -> canonical Ensembl IDs via HGNC
├── build_crosswalk.py         sample_key -> GSM accession
├── normalize_clinical.py      harmonise fibrosis / disease labels
├── build_graph_all.py         Neo4j-ready CSVs
├── build_optimuskg_layer.py   knowledge layer
├── find_progression_genes.py  the 4,692 progression genes
├── export_for_mentor.py       stage-wise CSVs
├── paper1_task1_groups.py        Task 1
├── paper1_task2_trajectories.py  Task 2
├── paper1_task3_transitions.py   Task 3
├── paper1_task4_enrichment.py    Task 4
├── export_triples.py          link prediction input   (unresolved)
├── train_link_prediction.py   ComplEx model           (unresolved)
└── *.cypher                   constraints and loaders
```

---

## Further reading

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | The distillation — conclusions, pipeline order, settled decisions, known limits. **Read this first**; it takes five minutes and it is what you need to *work* on the project. |
| [`handover/README.md`](handover/README.md) | Reading order for the four working sessions. |
| [`handover/SETUP.md`](handover/SETUP.md) | Getting Neo4j, the code and the data running from scratch. |
| `Paper1_Results/Task*/README.txt` | Per-task method and caveats. Authoritative for that task's numbers. |
| Script docstrings | Why each script exists and what trap it avoids. Kept current. |

The handover sessions are **dated snapshots**, not current truth. Where they
disagree with `CLAUDE.md`, `CLAUDE.md` wins; where `CLAUDE.md` disagrees with the
code, the code wins.
