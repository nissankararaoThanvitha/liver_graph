# Rebuilding what this package does not ship

You do not need any of this to read the results, check a number, or write the
paper. Everything the paper states traces to a file inside `04_DATA/`,
`02_TABLES/` or `03_RESULTS/`.

You need this only to **re-run the pipeline from the raw data**, or to re-run
the analyses that read the full expression graph.

---

## What is missing and what it costs

| Folder | Size | How to get it | Needed by |
|---|---|---|---|
| `data/raw/` | 104 MB | download from GEO — see `DATA_SOURCES.md` | parsing |
| `data/interim_full/` | 197 MB | `python parse_expression.py --raw-dir data/raw` | gene mapping, graph build |
| `data/graph_full/` | 2.1 GB | `python build_graph_all.py --interim data/interim_full --out data/graph_full` | progression genes, Tasks 2 and 3, hc1 and hc3 |
| `data/optimuskg/` | 161 MB | Dataverse DOI `10.7910/DVN/IYNGEV` | rebuilding the knowledge layer |
| `data/genesets/` | 5.7 MB | MSigDB — URL in `DATA_SOURCES.md` | enrichment |

The built knowledge layer **is** shipped, as `04_DATA/knowledge_layer/`, so
`data/optimuskg/` is only needed to rebuild it from source.

---

## Full pipeline, from nothing to the results

```bash
pip install -r 05_CODE/requirements.txt
```

Then, in order:

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_full
python map_gene_ids.py
python build_crosswalk.py
python normalize_clinical.py
python build_graph_all.py --interim data/interim_full --out data/graph_full
python build_optimuskg_layer.py
python find_progression_genes.py --graph data/graph_full --out data/progression_full
python export_for_mentor.py
python paper1_task1_groups.py          --out Paper1_Results/Task1
python paper1_task2_trajectories.py    --out Paper1_Results/Task2
python paper1_task3_transitions.py     --out Paper1_Results/Task3 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python paper1_task4_enrichment.py      --out Paper1_Results/Task4 --clusters Paper1_Results/Task2/task2_gene_clusters.csv
python scripts/make_fig1.py
```

Then the prioritisation, noting that the scoring script runs **twice**:

```bash
python scripts/00_all_4692_progression_genes.py --out Paper1_HighConfidence
python scripts/powermatched_transitions.py      --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py         --out Paper1_HighConfidence --results Paper1_Results
python scripts/loso_validation.py               --out Paper1_HighConfidence --results Paper1_Results
python scripts/high_confidence_genes.py         --out Paper1_HighConfidence --results Paper1_Results
python scripts/kg_subgraph.py                   --out Paper1_HighConfidence --results Paper1_Results
```

The repeat is required: the final tables need the leave-one-study-out columns
that `loso_validation.py` writes.

Finally:

```bash
python build_paper1_package.py
```

---

## Three things worth knowing

**Pass `--out`, `--results` and `--clusters` explicitly.** The defaults are
convenient, not safe: if more than one version of the results exists, a
default can pair new inputs with old intermediates and the run will report
success.

**`powermatched_transitions.py` and `loso_validation.py` are slow.** They read
2.1 GB and refit per gene — 50 draws × 4 transitions × 3,681 genes, and 2,625
leave-one-study-out runs. Plan for a long wall time.

**`parse_expression.py` keeps measured zeros by default, and should.** A gene
reading zero is a measurement, and the progression signal includes genes
switching on with stage.

---

## Loading the graph (optional)

Nothing in this package needs it.

```
1. create_kg_constraints.cypher     constraints and indexes, first
2. reload_expression.cypher         the per-study expression edges
```

The CSVs must be reachable from Neo4j's import directory.

**There is no committed loader for the knowledge layer** — it was loaded
interactively. `verify_graph_counts.py` reconciles a loaded graph against the
CSVs per relationship type and reports any shortfall, which is the check that
makes that gap detectable.

**The store format is Enterprise-only.** A dump will not load into Community
Edition; rebuild from the CSVs instead.

**Do not count all relationships by type in one query** — it times out on a
small heap. Count per type, which hits the count store and returns instantly.
