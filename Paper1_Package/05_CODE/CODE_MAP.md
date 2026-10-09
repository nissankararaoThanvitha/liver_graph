# Code map

Every script, what it does, what it reads, what it writes. Filenames carry
their order, so each folder reads top to bottom.

```bash
pip install -r requirements.txt
```

Versions are pinned to the ones that produced these results (Python 3.13.7).

**Read the docstring at the top of each script.** They explain why the script
exists and what it guards against, and they are kept current with the code.

---

## `pipeline/` — raw data to analysable tables

| | Script | Reads | Writes |
|---|---|---|---|
| 01 | `parse_expression.py` | `data/raw/` GEO files | `data/interim_full/` long-format expression |
| 02 | `map_gene_ids.py` | interim + HGNC complete set | `data/processed/gene_id_map.csv`, `unmapped_genes.csv` |
| 03 | `build_crosswalk.py` | interim + series matrices | `data/processed/sample_crosswalk.csv` |
| 04 | `normalize_clinical.py` | series matrices | `data/graph/nodes_sample_clinical.csv` |
| 05 | `build_graph_all.py` | interim + gene map | `data/graph_full/` node and edge CSVs |
| 06 | `build_optimuskg_layer.py` | `data/optimuskg/` | `data/graph_okg/` knowledge layer |
| 07 | `find_progression_genes.py` | `data/graph_full/` | `data/progression_full/` |
| 08 | `export_gene_tables.py` | progression + clinical | `data/for_mentor/` stage-wise gene tables |

**Measured zeros are retained**, which is why the analyses read
`data/interim_full`. `parse_expression.py` keeps them by default.

---

## `analysis/` — the four analyses

| Script | Produces | Output folder |
|---|---|---|
| `make_figure1.py` | Figure 1. Counts are read from the committed outputs at draw time, so the figure cannot drift from the tables | — |
| `task1_groups.py` | the fibrosis-only / inflammation-only / shared split | `Task1/` |
| `task2_trajectories.py` | trajectory clusters, k selection, bootstrap stability | `Task2/` |
| `task3_transitions.py` | the four stage transitions, power-matched refits | `Task3/` |
| `task4_enrichment.py` | enrichment per group and cluster, four databases | `Task4/` |

`task2_trajectories.py` takes an optional positional `k` to override the
selection: `python task2_trajectories.py --out <folder> 6`.

---

## `prioritisation/` — the evidence scoring and the shortlist

| | Script | Produces |
|---|---|---|
| hc0 | `hc0_master_gene_table.py` | the master gene table (brief step 1) |
| hc1 | `hc1_powermatched_transitions.py` | per-gene power-matched results (**slow**) |
| hc2 | `hc2_evidence_scores.py` | the five scores, tiers, sensitivity, shortlist (steps 2–9, 11) |
| hc3 | `hc3_leave_one_study_out.py` | leave-one-study-out, 2,625 runs (**slow**) |
| hc4 | `hc4_mechanism_subgraph.py` | Figure 9 and the knowledge-graph workbook |

**Run order — hc2 runs twice:**

```
hc0 → hc1 → hc2 → hc3 → hc2 (again) → hc4
```

The second `hc2` is not a mistake: the final tables need the
leave-one-study-out columns that `hc3` produces.

`hc1` and `hc3` read `data/graph_full` and are slow. `hc4` reads only
knowledge-layer CSVs that ship in this package.

---

## `validation/` — the checks

These are not leftovers. Each validates a stage that has no other check.

| Script | What it catches |
|---|---|
| `check_gene_mapping.py` | two raw identifiers resolving to one Ensembl ID — the condition `build_graph_all.py` sums for — and what kinds of identifier failed to map |
| `inspect_parsed_files.py` | whether expression sample keys match GEO accessions, identifier formats, and units |
| `diagnose_membership_confidence.py` | whether cluster-membership confidence is measuring gene stability or its own label-matching failures |
| `verify_graph_counts.py` | the edge CSVs against the relationship counts a loaded graph reports, per type, with the dedup and dangling-endpoint explanations tested |
| `verify_subgraph_against_neo4j.py` | the mechanism network against a running database at four levels, including gene membership itself |
| `compare_result_versions.py` | two result folders, reporting **membership** rather than counts |

The last one earns its place: a count can be unchanged while the membership
behind it has moved, and comparing counts alone would miss it.

---

## `cypher/` — loading the graph

| | File | Purpose |
|---|---|---|
| 01 | `01_create_constraints.cypher` | uniqueness constraints and indexes. **Run first** |
| 02 | `02_load_expression_edges.cypher` | the per-study expression edges |
| 03 | `03_load_knowledge_layer.cypher` | the curated layer and the project's own `TRACKS_*` edges |

**Every statement in the knowledge-layer loader uses MERGE, not CREATE.**
Running it twice duplicates nothing, so it is safe to re-run after a
partial load. Gene nodes are MATCHed rather than created: a knowledge
edge pointing at a gene this project never measured is dropped, not
invented.

`validation/verify_graph_counts.py` reconciles a loaded graph against the
CSVs per relationship type, and `expected_graph_counts.py` says what each
type should reach once edges with absent endpoints are dropped. Every
type loads complete except PARENT_OF, at 44,073 of 44,215 — 142 rows
point at a disease that is not a node in this layer.

**The CSVs are the authoritative source.** No result in this package requires
a running database.

Two notes: the store format is Enterprise-only, so a dump will not load into
Community Edition — rebuild from CSVs. And counting all relationships by type
in one query times out on a small heap; count per type.

---

## `build_paper1_package.py`

Rebuilds this package from the project tree. Figure and table numbering lives
in this script and nowhere else, so a figure cannot be renumbered in one
place and not another. Re-run it after any analysis change; it recreates the
folder rather than patching it.

---

## A convention worth keeping

**Every analysis script takes `--out`, and where it reads another stage's
output, `--results` or `--clusters`.** Pass them explicitly. These flags
exist so that a re-run cannot pair new inputs with old intermediates — the
defaults are convenient, not safe, when more than one version of the results
exists.
