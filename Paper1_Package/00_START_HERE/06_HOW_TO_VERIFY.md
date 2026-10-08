# 6. How to check anything in this package

Every number in the paper can be traced to a file here, and most can be
re-derived in a few seconds without re-running the pipeline. This document
says where to look for each kind of claim, and what to run if you want to
rebuild rather than just check.

---

## First: check nothing was corrupted in transit

`00_START_HERE/07_FILE_MANIFEST.csv` lists every file with its size and
SHA-256.

```bash
python -c "import csv,hashlib,os,sys; bad=0
for r in csv.DictReader(open('00_START_HERE/07_FILE_MANIFEST.csv')):
    h=hashlib.sha256(open(r['path'],'rb').read()).hexdigest()
    if h!=r['sha256']: print('MISMATCH',r['path']); bad+=1
print('checked, mismatches:',bad)"
```

---

## Tracing a claim to its source

| If the claim is about… | Look in |
|---|---|
| the cohort, sample or patient counts | `02_TABLES/main/Table1_cohort.csv` and `04_DATA/gene_tables/sample_demographics.csv` |
| how many genes track progression, and each gene's statistics | `04_DATA/progression_statistics/progression_fibrosis.csv` (all 14,794 genes, significant or not) |
| the fibrosis-only / inflammation-only / shared split | `03_RESULTS/Task1_gene_groups/` + its `README.txt` |
| a trajectory shape, or one gene's cluster | `02_TABLES/supplementary/TableS2_gene_cluster_assignments.csv` |
| whether a gene changes at a given transition | `02_TABLES/supplementary/TableS6_all_genes_all_transitions.csv` |
| whether a pathway is enriched in a group | `03_RESULTS/Task4_enrichment/enrichment_tables/<group>__<database>.csv` — every tested term, with a `significant` flag |
| one of the 25 prioritised genes | `02_TABLES/main/Table6_prioritised_25_genes.csv` |
| any gene's evidence score and tier | `02_TABLES/supplementary/TableS11_evidence_scores_all_genes.csv` (all 3,645, every intermediate) |
| a knowledge-graph connection or mechanism | `02_TABLES/supplementary/TableS17_knowledge_graph_connections.xlsx` |
| a statistical method, threshold or n | `00_START_HERE/03_STATISTICS.md` |
| why a choice was made | `00_START_HERE/04_DECISIONS.md` |
| whether a claim is safe to make | `00_START_HERE/05_LIMITATIONS.md` |

**The five `README.txt` files inside `03_RESULTS/` are authoritative** for
what each analysis did and what it does not support. They were written
alongside the analyses, not afterwards.

---

## Worked checks you can run in seconds

All of these run from the package root with pandas installed. Nothing else is
needed.

**Is this gene a progression gene, and how strong?**

```bash
python -c "import pandas as pd; d=pd.read_csv('04_DATA/progression_statistics/progression_fibrosis.csv'); print(d[d.symbol=='TREM2'].T)"
```

`median_rho` is the cross-study correlation, `n_agree` how many studies agree
on direction, `min_rho`/`max_rho` the per-study range — the fastest way to
see whether one cohort is carrying the signal.

**Confirm the 4,692 / 1,953 / 1,047 / 1,692 split.**

```bash
python -c "import pandas as pd; print(pd.read_csv('03_RESULTS/Task1_gene_groups/task1_summary.csv').to_string())"
```

**Confirm the cohort totals (1,085 samples, 1,027 patients, 668 staged).**

```bash
python -c "import pandas as pd; d=pd.read_csv('04_DATA/gene_tables/sample_demographics.csv'); print(len(d), d.patient_id.nunique(), d.fibrosis_stage.notna().sum()); print(d.fibrosis_stage.value_counts().sort_index())"
```

**Confirm the 40 NASH-at-F0 patients.**

```bash
python -c "import pandas as pd; d=pd.read_csv('04_DATA/gene_tables/sample_demographics.csv'); print(((d.disease_group=='NASH')&(d.fibrosis_stage==0)).sum())"
```

**Confirm the tier counts (507 / 1,483 / 1,655).**

```bash
python -c "import pandas as pd; print(pd.read_csv('02_TABLES/supplementary/TableS11_evidence_scores_all_genes.csv').tier.value_counts())"
```

**Confirm the enrichment background is 14,794.**

```bash
python -c "import pandas as pd; print(len(pd.read_csv('04_DATA/progression_statistics/progression_fibrosis.csv')))"
```

That file holds exactly the tested universe, which is the background used in
stages 13 and 14. If this number ever disagrees with a figure or table, the
figure or table is wrong.

---

## Re-running an analysis

Stages 10–14 read committed CSVs and are quick. Stages 2–9 read the bulk data
that is **not shipped** in this package — see `06_PROVENANCE/REBUILD.md` for
how to regenerate it from GEO first.

```bash
pip install -r 05_CODE/requirements.txt
```

Versions are pinned to the ones that produced these results. Skip `pykeen`
and `torch` (a ~2 GB install) unless you are running the unresolved
link-prediction code, which you should not need to.

| To rebuild | Run | Needs |
|---|---|---|
| Stage 10 (groups) | `05_CODE/analysis/task1_groups.py` | shipped CSVs |
| Stage 11 (trajectories) | `05_CODE/analysis/task2_trajectories.py` | shipped CSVs |
| Stage 12 (transitions) | `05_CODE/analysis/task3_transitions.py` | **`data/graph_full`** — rebuild first |
| Stage 13 (enrichment) | `05_CODE/analysis/task4_enrichment.py` | MSigDB gene sets — download first, see `06_PROVENANCE/DATA_SOURCES.md` |
| Stage 14 (prioritisation) | `hc1` → `hc2` → `hc3` → `hc2` again → `hc4` | `data/graph_full` for hc1/hc3; the shipped `04_DATA/knowledge_layer_primekg_superseded/` for hc4 |
| Figure 1 | `05_CODE/analysis/make_figure1.py` | nothing — numbers are inline |
| This package | `05_CODE/build_paper1_package.py` | the full project tree |

**Stage 14 runs its second script twice.** `hc2` must run again after `hc3`
so that step 11 picks up the leave-one-study-out columns. The order is in
`03_RESULTS/Task5_high_confidence_genes/README.txt`.

**`hc4` (the mechanism subgraph) needs no database.** It filters
knowledge-layer CSVs shipped in this package. Note that it reads
`knowledge_layer_primekg_superseded/`, **not** the OptimusKG layer that the
graph holds -- see `05_LIMITATIONS.md` section 14.

---

## If you want the graph itself

You do not need it for anything in this package. If you want it anyway:
`05_CODE/cypher/` holds the constraint and load scripts in order, and
`06_PROVENANCE/REBUILD.md` has the commands that generate the CSVs they load.

Two practical notes carried from the original setup. The store format is
`block-block-1.1`, which is **Neo4j Enterprise only** — a dump of this graph
will not load into Community Edition. And counting all relationships by type
in one query times out on a 1 GB heap against a 2.5 GB store; **count per
type instead**, which hits the count store and returns instantly.
