# Code map

Every script, what it does, what it reads, what it writes. Filenames are
prefixed with their order, so the pipeline reads top to bottom.

Install first:

```bash
pip install -r requirements.txt
```

Versions are pinned to the ones that produced the committed results (Python
3.13.7). **Skip `pykeen` and `torch`** — a ~2 GB install needed only by the
unresolved link-prediction code.

**Read the docstring at the top of each script.** They are the real
documentation: each explains why the script exists and what trap it avoids,
and they are kept current with the code.

---

## `pipeline/` — raw data to analysable tables

| | Script | Reads | Writes |
|---|---|---|---|
| 01 | `parse_expression.py` | `data/raw/` GEO files | `data/interim_full/` long-format expression |
| 02 | `map_gene_ids.py` | interim + HGNC complete set | `data/processed/gene_id_map.csv`, `unmapped_genes.csv` |
| 03 | `build_crosswalk.py` | interim + series matrices | `data/processed/sample_crosswalk.csv` |
| 04 | `normalize_clinical.py` | series matrices | harmonised clinical fields |
| 05 | `build_graph_all.py` | interim + gene map | `data/graph_full/` node and edge CSVs |
| 06 | `build_optimuskg_layer.py` | `data/optimuskg/` | `data/graph_okg/` knowledge layer |
| 07 | `find_progression_genes.py` | `data/graph_full/` | `data/progression_full/` |
| 08 | `export_for_mentor.py` | progression + clinical | `data/for_mentor/` the stage-wise gene tables |

**Script 01 must not be given `--drop-zeros`.** Measured zeros are kept
deliberately — see `00_START_HERE/04_DECISIONS.md` §1. The analyses read
`data/interim_full`, which is the no-flag output.

---

## `analysis/` — the five analyses of the paper

| Script | Produces | Output folder |
|---|---|---|
| `make_figure1.py` | Figure 1, the pipeline diagram. Numbers are inline from the committed outputs | — |
| `task1_groups.py` | the fibrosis-only / inflammation-only / shared split | `Task1_gene_groups/` |
| `task2_trajectories.py` | the five trajectory clusters, k selection, bootstrap stability | `Task2_trajectories/` |
| `task3_transitions.py` | the four stage transitions, power-matched refits | `Task3_transitions/` |
| `task4_enrichment.py` | enrichment per group and cluster, four databases | `Task4_enrichment/` |
| `hc0_all_progression_genes.py` | the 4,692-gene table used as stage 14's input | `Task5_high_confidence_genes/` |
| `hc1_powermatched_transitions.py` | per-gene power-matched results (**slow**) | → `05_…csv` |
| `hc2_high_confidence_genes.py` | the five scores, tiers, sensitivity, the shortlist | → `01_`, `03_`, `04_`, `08_`, `09_`, `11_` |
| `hc3_loso_validation.py` | leave-one-study-out, 2,535 runs (**slow**) | → `10_…csv` |
| `hc4_kg_subgraph.py` | Figure 9 and the knowledge-graph workbook | → `12_…` |
| `hc5_audit_handover.py` | consistency audit of the stage 14 outputs | — |

**Stage 14 runs `hc2` twice:**

```
hc1 → hc2 → hc3 → hc2 (again) → hc4
```

The second `hc2` is not a mistake — step 11 needs the leave-one-study-out
columns that `hc3` produces. Running it once leaves the final tables without
them.

`hc1` and `hc3` read `data/graph_full` (2.1 GB, not shipped) and are slow.
`hc4` reads only knowledge-layer CSVs that **are** shipped, so Figure 9 can
be regenerated from this package alone — but note which layer it reads
(`05_LIMITATIONS.md` §14).

---

## `cypher/` — loading the graph

| | File | Purpose |
|---|---|---|
| 01 | `create_kg_constraints.cypher` | uniqueness constraints and indexes. **Run first** |
| 02 | `load_edges.cypher` | **only** the eight per-study `EXPRESSES` files. Despite its name it does *not* load the knowledge layer |
| 03 | `reload_expression.cypher` | re-loads only the expression edges, leaving the knowledge layer intact |

**There is no committed script that loads the knowledge layer.** The three
files above cover constraints and expression edges only, yet
`create_kg_constraints.cypher` states the constraints "must exist before the
knowledge-layer edges are loaded". That loader was never committed; the layer
was loaded ad hoc through a session. This is the reproducibility gap that let
the live graph fall 40,247 links short without anyone noticing — see
`00_START_HERE/05_LIMITATIONS.md` §16. **Writing that loader is the fix.**

Loading is Cypher, not Python, and is entirely optional: **no result in this
package requires a running database.**

Two notes from the original setup. The store format is `block-block-1.1`,
which is **Enterprise-only** — a dump will not load into Community Edition.
And counting all relationships by type in one query times out on a 1 GB heap
against a 2.5 GB store; count per type instead, which hits the count store
and returns instantly.

---

## `unresolved/` — link prediction

| Script | Status |
|---|---|
| `export_triples.py` | works: exports the graph as triples for embedding |
| `train_link_prediction.py` | **the first model failed its own validation** |

Shipped as part of the honest record of what was tried. **Do not cite it and
do not put its output in the manuscript.** If this direction is mentioned at
all it belongs in future work. See `05_LIMITATIONS.md` §13.

---

## `build_paper1_package.py`

Rebuilds this entire package from the project tree. The figure and table
numbering lives in this script and nowhere else, so a figure cannot be
renumbered in one place and not another. Re-run it after any analysis
changes; it recreates the folder from scratch rather than patching it.
