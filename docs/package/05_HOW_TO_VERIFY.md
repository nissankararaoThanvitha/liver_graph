# 5. How to check anything here

Every number in the paper traces to a file in this package, and most can be
re-derived in seconds without re-running anything.

---

## First: confirm nothing was corrupted in transit

`00_START_HERE/06_FILE_MANIFEST.csv` lists every file with its size and
SHA-256.

```bash
python -c "import csv,hashlib,os; bad=0
for r in csv.DictReader(open('00_START_HERE/06_FILE_MANIFEST.csv')):
    h=hashlib.sha256(open(r['path'],'rb').read()).hexdigest()
    if h!=r['sha256']: print('MISMATCH',r['path']); bad+=1
print('checked, mismatches:',bad)"
```

---

## Tracing a claim to its source

| If the claim is about… | Look in |
|---|---|
| the cohort, sample or patient counts | `02_TABLES/main/Table1_cohort.csv` |
| how many genes track progression, and each gene's statistics | `04_DATA/progression_genes/progression_fibrosis.csv` — all 14,794 genes, significant or not |
| the fibrosis-only / inflammation-only / shared split | `03_RESULTS/Task1_gene_groups/` and its `README.txt` |
| a trajectory shape, or one gene's cluster | `02_TABLES/supplementary/TableS2_gene_cluster_assignments.csv` |
| whether a gene changes at a given transition | `02_TABLES/supplementary/TableS6_all_genes_all_transitions.csv` |
| whether a pathway is enriched in a group | `03_RESULTS/Task4_enrichment/enrichment_tables/<group>__<database>.csv` — every tested term with a `significant` flag |
| one of the prioritised genes | `02_TABLES/main/Table6_prioritised_genes.csv` |
| any gene's evidence score and tier | `02_TABLES/supplementary/TableS11_evidence_scores_all_genes.csv` |
| a knowledge-graph connection | `02_TABLES/supplementary/TableS19_knowledge_graph_connections.xlsx` |
| a method, threshold or n | `00_START_HERE/03_STATISTICS.md` |
| whether a claim is safe to make | `00_START_HERE/04_LIMITATIONS.md` |

**The `README.txt` inside each `03_RESULTS/` folder is authoritative** for
what that analysis did and what it does not support.

---

## Checks you can run in seconds

All need only pandas.

**Is this gene a progression gene, and how strong?**

```bash
python -c "import pandas as pd; d=pd.read_csv('04_DATA/progression_genes/progression_fibrosis.csv'); print(d[d.symbol=='TREM2'].T)"
```

`min_rho` and `max_rho` are the per-study range — the fastest way to see
whether one cohort is carrying the signal.

**Confirm the group counts.**

```bash
python -c "import pandas as pd; print(pd.read_csv('03_RESULTS/Task1_gene_groups/task1_summary.csv',encoding='utf-8-sig').to_string())"
```

**Confirm the cohort totals.**

```bash
python -c "import pandas as pd; d=pd.read_csv('04_DATA/progression_genes/sample_demographics.csv'); print(len(d),'samples |',d.patient_id.nunique(),'patients |',int(d.fibrosis_stage.notna().sum()),'staged'); print(d.fibrosis_stage.value_counts().sort_index())"
```

**Confirm the enrichment background is 14,794.**

```bash
python -c "import pandas as pd; print(len(pd.read_csv('04_DATA/progression_genes/progression_fibrosis.csv')))"
```

That file holds exactly the tested universe, which is the background used in
enrichment. If this number ever disagrees with a figure or table, the figure
or table is wrong.

**Confirm which clusters support gene-level claims.**

```bash
python -c "import pandas as pd; print(pd.read_csv('03_RESULTS/Task2_trajectories/task2_bootstrap_shape_stability.csv',encoding='utf-8-sig').to_string(index=False))"
```

---

## Re-running an analysis

```bash
pip install -r 05_CODE/requirements.txt
```

Versions are pinned to the ones that produced these results. Skip `pykeen`
and `torch` — they are not used by anything in this package.

| To rebuild | Run | Needs |
|---|---|---|
| Task 1 | `05_CODE/analysis/task1_groups.py` | shipped CSVs |
| Task 2 | `05_CODE/analysis/task2_trajectories.py` | **`data/graph_full`** — rebuild first |
| Task 3 | `05_CODE/analysis/task3_transitions.py` | `data/graph_full` |
| Task 4 | `05_CODE/analysis/task4_enrichment.py` | MSigDB gene sets — see `06_PROVENANCE/DATA_SOURCES.md` |
| Figure 1 | `05_CODE/analysis/make_figure1.py` | shipped CSVs |
| Task 5 | `hc0` → `hc1` → `hc2` → `hc3` → `hc2` again → `hc4` | `data/graph_full` for hc1/hc3 |
| This package | `05_CODE/build_paper1_package.py` | the full project tree |

**Task 5 runs `hc2` twice.** The second run picks up the leave-one-study-out
columns that `hc3` produces; running it once leaves the final tables without
them.

**Every script takes `--out` and, where relevant, `--results` and
`--clusters`.** Pass them explicitly — these flags exist so a re-run cannot
silently mix outputs from one version with inputs from another.

**`hc4` (the mechanism network) needs no database.** It filters the
knowledge-layer CSVs shipped in `04_DATA/knowledge_layer/`.

---

## Validation tools

`05_CODE/validation/` holds the checks, not just the analyses:

| Script | What it checks |
|---|---|
| `check_gene_mapping.py` | two raw identifiers collapsing onto one Ensembl ID, and what kinds of identifier failed to map |
| `inspect_parsed_files.py` | sample keys, identifier formats and units in the parsed files |
| `diagnose_membership_confidence.py` | whether cluster-membership confidence is measuring gene stability or its own label-matching |
| `verify_graph_counts.py` | the edge CSVs against the relationship counts a loaded graph reports |
| `verify_subgraph_against_neo4j.py` | the mechanism network against a running database, at four levels including membership itself |
| `compare_result_versions.py` | two result folders, reporting membership rather than counts |

The last one matters if you ever re-run the pipeline: a count can be
unchanged while the membership behind it has moved.

---

## If you want the graph itself

You do not need it for anything here. `05_CODE/cypher/` holds the constraint
and expression-load scripts, and `06_PROVENANCE/REBUILD.md` has the commands
that generate the CSVs they load.

**The curated knowledge layer ships in full** as `04_DATA/knowledge_layer/`,
and `verify_graph_counts.py` reconciles those files against whatever a loaded
graph reports.

Two practical notes: the store format is Enterprise-only, so a dump will not
load into Community Edition — rebuild from CSVs instead. And counting all
relationships by type in one query times out on a small heap; count per type,
which hits the count store and returns instantly.
