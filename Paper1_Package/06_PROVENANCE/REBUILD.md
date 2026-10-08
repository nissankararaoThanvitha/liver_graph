# Rebuilding what this package does not ship

You do not need any of this to read the results, check a number, or write the
paper. Everything the paper states is traceable to a file inside
`04_DATA/`, `02_TABLES/` or `03_RESULTS/`.

You need this only to **re-run stages 2–9**, or stages 12 and 14, which read
bulk intermediates too large to ship (5.5 GB in total).

---

## What is missing and what it costs to rebuild

| Folder | Size | Rebuild command | Needed by |
|---|---|---|---|
| `data/raw/` | 104 MB | download from GEO — `DATA_SOURCES.md` | stage 2 |
| `data/interim_full/` | 197 MB | `python parse_expression.py --raw-dir data/raw --out-dir data/interim_full` | stages 3, 5, 7 |
| `data/graph_full/` | 2.1 GB | `python build_graph_all.py --interim data/interim_full --out data/graph_full` | stages 9, 12, 14 (`hc1`, `hc3`) |
| `data/optimuskg/` | 161 MB | Dataverse DOI `10.7910/DVN/IYNGEV` | stage 8 |
| `data/primekg/` | 937 MB | Dataverse DOI `10.7910/DVN/IXA7BM` | only to rebuild the superseded layer |
| `data/genesets/` | 5.7 MB | MSigDB URL in `DATA_SOURCES.md` | stage 13 |
| `data/graph_all/` | 1.6 GB | `python build_graph_all.py` | nothing — superseded by `graph_full` |
| `data/kg_triples/` | 138 MB | `python export_triples.py --min-assoc 0.3` | unresolved link prediction only |
| `data/prediction/` | 54 MB | `python train_link_prediction.py` | unresolved link prediction only |

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
python find_progression_genes.py
python export_for_mentor.py
python paper1_task1_groups.py
python paper1_task2_trajectories.py
python paper1_task3_transitions.py
python paper1_task4_enrichment.py
```

Then stage 14, noting that the second script runs **twice**:

```bash
python Paper1_HighConfidence/powermatched_transitions.py
python Paper1_HighConfidence/high_confidence_genes.py
python Paper1_HighConfidence/loso_validation.py
python Paper1_HighConfidence/high_confidence_genes.py
python Paper1_HighConfidence/kg_subgraph.py
```

The repeat is required: step 11 of `high_confidence_genes.py` needs the
leave-one-study-out columns that `loso_validation.py` writes.

Finally, to rebuild this package:

```bash
python build_paper1_package.py
```

---

## Two things that will bite you

**Do not pass `--drop-zeros` to the parser.** Measured zeros are kept
deliberately — dropping them removes the switching-on that *is* the
progression signal (IL6 is detected in 10% of stage-1 and 64% of stage-4
patients), and costs 9.1 M measurements and 514 progression genes. The
analyses read `data/interim_full`, the no-flag output, not `data/interim`.

**`powermatched_transitions.py` and `loso_validation.py` are slow.** They
read `data/graph_full` (2.1 GB) and refit per gene: 50 draws × 4 transitions
× 3,645 genes, and 2,535 leave-one-study-out runs. Expect a long wall time
and plan accordingly.

---

## Loading the graph (optional)

Only if you want the database itself. Nothing in this package needs it.

```
1. create_kg_constraints.cypher      constraints and indexes, first
2. load_edges.cypher                 knowledge layer + expression edges
3. reload_expression.cypher          expression edges only, later re-loads
```

The CSVs must be reachable from Neo4j's import directory — the load scripts
read `file:///liverkg/...`, so copy the generated CSVs there first.

**The store format is `block-block-1.1`, which is Enterprise-only.** A dump
of this graph will not load into Community Edition. Rebuild from the CSVs
instead if you only have Community.

**Do not count all relationships by type in one query.** On a 1 GB heap
against a 2.5 GB store it times out. Count per type instead — that hits the
count store and returns instantly.
