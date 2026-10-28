"""Paper 2 Task 7 — EXTERNAL LAYER (separate from the graph-only results).

Adds the drug-action directions found in external resources (External_action_check/:
Guide to Pharmacology, DGIdb, ChEMBL) for links the knowledge graph labels only TARGET /
ENZYME / TRANSPORTER / CARRIER. Only links where the external sources agree are used (297).

The graph-only Task 7 (Paper2_Results/Task7/) and Task 7 revised (Task7_revised/) are NOT
changed. Every row here carries a `direction_source` column:
  "knowledge graph"                       the 1,001 links with a graph action label
  "external: <sources>"                   the 297 links filled from external resources
Classification rules are identical to Task 7 (gene direction from Paper 1; cluster conflict
or discordant shared gene -> ambiguous).

    python Paper2_Results/code/task7_external_layer.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"
OUT = RES / "Task7_external_layer"
OUT.mkdir(exist_ok=True)
ORDER = ["direction-consistent", "direction-inconsistent", "ambiguous"]
CLUSTER_DIR = {"C1": "positive", "C2": "positive", "C3": "positive", "C4": "negative", "C5": "negative"}

graph = pd.read_csv(RES / "Task7/drug_action_evidence.csv")
ext = pd.read_csv(RES / "External_action_check/unknown_links_external_lookup.csv")
genes = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv").set_index("ensembl_id")
cand = set(pd.read_csv(RES / "Task4/repurposing_candidates.csv").Drug_ID)
mech = set(pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv").Drug_ID)

# ------------------------------------------------------------------ graph layer (unchanged, known directions only)
g = graph[graph["Action class"].isin(["down", "up", "mixed"])].copy()
g_layer = pd.DataFrame({"Drug_ID": g.Drug_ID, "Drug": g.Drug, "Gene_ID": g.Gene_ID, "Gene": g.Gene,
                        "action_label": g["Drug action"], "push": g["Action class"],
                        "direction_source": "knowledge graph", "Consistency": g.Consistency})

# ------------------------------------------------------------------ external layer
x = ext[ext.external_direction.isin(["down", "up"])].copy()
gi = genes.reindex(x.Gene_ID)
gdir = np.where(gi.progression_class.values == "inflammation_only", gi.inflammation_direction.values, gi.fibrosis_direction.values)
cdir = gi.trajectory_cluster.map(CLUSTER_DIR).values
discordant = gi.paper1_group.str.startswith("shared_discordant").values
conflict = pd.notna(cdir) & (cdir != gdir)
push = x.external_direction.values
consistency = np.select([discordant | conflict,
                         ((gdir == "positive") & (push == "down")) | ((gdir == "negative") & (push == "up"))],
                        ["ambiguous", "direction-consistent"], "direction-inconsistent")
srcs = [";".join(s for s, d in (("GtoPdb", a), ("DGIdb", b), ("ChEMBL", c)) if d == p)
        for a, b, c, p in zip(x.gtopdb_dir, x.dgidb_dir, x.chembl_dir, push)]
labels = [" | ".join(str(v) for v in (a, b, c) if isinstance(v, str)) for a, b, c in zip(x.gtopdb_action, x.dgidb_action, x.chembl_action)]
e_layer = pd.DataFrame({"Drug_ID": x.Drug_ID, "Drug": x.Drug, "Gene_ID": x.Gene_ID, "Gene": x.Gene,
                        "action_label": labels, "push": push,
                        "direction_source": ["external: " + s for s in srcs], "Consistency": consistency,
                        "graph_label": x.Action_raw.values})
assert len(e_layer) == 297, len(e_layer)
assert not set(map(tuple, e_layer[["Drug_ID", "Gene_ID"]].values)) & set(map(tuple, g_layer[["Drug_ID", "Gene_ID"]].values))

both = pd.concat([g_layer, e_layer], ignore_index=True)
ann = genes[["paper1_group", "trajectory_cluster", "progression_class"]]
both = both.join(ann, on="Gene_ID")
both["layer"] = np.where(both.direction_source == "knowledge graph", "graph", "external")
both["repurposing_candidate"] = both.Drug_ID.isin(cand)
both["main_list"] = both.Drug_ID.isin(mech)
both.to_csv(OUT / "drug_action_evidence_graph_plus_external.csv", index=False)
e_layer.join(ann, on="Gene_ID").to_csv(OUT / "external_layer_links.csv", index=False)


# ------------------------------------------------------------------ comparisons
def tab(df, by):
    t = pd.crosstab(df[by], df.Consistency).reindex(columns=ORDER, fill_value=0)
    dec = t["direction-consistent"] + t["direction-inconsistent"]
    t["% consistent"] = (100 * t["direction-consistent"] / dec.replace(0, np.nan)).round(1)
    return t


GROUPS = ["fibrosis_only_positive", "fibrosis_only_negative", "shared_positive", "shared_negative",
          "shared_discordant_fib_negative", "inflammation_only_positive", "inflammation_only_negative"]
gonly, plus = tab(both[both.layer == "graph"], "paper1_group").reindex(GROUPS), tab(both, "paper1_group").reindex(GROUPS)
cmp_group = pd.DataFrame({"graph only: decided": (gonly[ORDER[0]] + gonly[ORDER[1]]).fillna(0).astype(int),
                          "graph only: % consistent": gonly["% consistent"],
                          "+ external: decided": (plus[ORDER[0]] + plus[ORDER[1]]).fillna(0).astype(int),
                          "+ external: % consistent": plus["% consistent"]})
cmp_group.to_csv(OUT / "consistency_by_group_graph_vs_plus_external.csv")
cg, cp = tab(both[both.layer == "graph"], "trajectory_cluster"), tab(both, "trajectory_cluster")
cmp_cluster = pd.DataFrame({"graph only: decided": cg[ORDER[0]] + cg[ORDER[1]], "graph only: % consistent": cg["% consistent"],
                            "+ external: decided": cp[ORDER[0]] + cp[ORDER[1]], "+ external: % consistent": cp["% consistent"]})
cmp_cluster.to_csv(OUT / "consistency_by_cluster_graph_vs_plus_external.csv")


def drugs_with(df, cand_only=True):
    d = df[df.repurposing_candidate] if cand_only else df
    c = set(d[d.Consistency == "direction-consistent"].Drug_ID)
    i = set(d[d.Consistency == "direction-inconsistent"].Drug_ID)
    return c, i


gc, gi_ = drugs_with(both[both.layer == "graph"])
pc, pi_ = drugs_with(both)
cand_tab = pd.DataFrame({
    "Measure": ["Candidates with ≥1 direction-consistent link", "… only consistent links", "… only inconsistent links"],
    "graph only": [len(gc), len(gc - gi_), len(gi_ - gc)],
    "graph + external": [len(pc), len(pc - pi_), len(pi_ - pc)],
})
cand_tab.to_csv(OUT / "candidates_graph_vs_plus_external.csv", index=False)
new_cons = e_layer[(e_layer.Consistency == "direction-consistent") & e_layer.Drug_ID.isin(cand - gc)]
new_cons_tab = (new_cons.groupby(["Drug"]).agg(genes=("Gene", lambda s: ";".join(sorted(set(s)))),
                                               sources=("direction_source", lambda s: ";".join(sorted({t for x in s for t in x.replace("external: ", "").split(";")}))))
                .reset_index().sort_values("Drug"))
new_cons_tab.to_csv(OUT / "new_consistent_candidates_from_external.csv", index=False)


# ------------------------------------------------------------------ summary
def md(df, idx=True):
    t = df.reset_index() if idx else df
    lines = ["| " + " | ".join(map(str, t.columns)) + " |", "|" + "---|" * t.shape[1]]
    for row in t.values:
        lines.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else (f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)) for v in row) + " |")
    return "\n".join(lines)


ec = e_layer.Consistency.value_counts().reindex(ORDER, fill_value=0)
src_counts = e_layer.direction_source.str.replace("external: ", "").value_counts()
summary = f"""# Paper 2 — Task 7 external layer (separate from graph-only results)

**What this is:** the Task 7 direction check with an **extra, clearly labelled layer** of drug-action directions taken from external resources (Guide to Pharmacology, DGIdb, ChEMBL), for links the knowledge graph labels only TARGET / ENZYME / TRANSPORTER / CARRIER. Only links where the external sources agree are used.
**The graph-only results are unchanged** (`Task7/`, `Task7_revised/`). Every row here has a `direction_source` column ("knowledge graph" or "external: …").
**Scope note:** this layer uses data outside the knowledge graph; it should be reported as a sensitivity / supplementary analysis unless the supervisor approves it for the main results. Gene set: corrected Paper 1 union of 6,222 genes (earlier plans cite 4,692, the pre-correction count). Results are repurposing hypotheses, not proof.

![Task 7 external layer](Task7_external_layer_diagram.png)

## The two layers
| Layer | Links with an action label | direction-consistent | direction-inconsistent | ambiguous |
|---|---|---|---|---|
| Knowledge graph (unchanged) | {len(g_layer):,} | {int((g_layer.Consistency == 'direction-consistent').sum()):,} | {int((g_layer.Consistency == 'direction-inconsistent').sum()):,} | {int((g_layer.Consistency == 'ambiguous').sum()):,} |
| External (new) | {len(e_layer):,} | {int(ec['direction-consistent']):,} | {int(ec['direction-inconsistent']):,} | {int(ec['ambiguous']):,} |
| **Graph + external** | **{len(both):,}** | **{int((both.Consistency == 'direction-consistent').sum()):,}** | **{int((both.Consistency == 'direction-inconsistent').sum()):,}** | **{int((both.Consistency == 'ambiguous').sum()):,}** |

Links with a clear push direction (down / up) rise from {int(g_layer.push.isin(["down", "up"]).sum()):,} ({100 * g_layer.push.isin(["down", "up"]).mean() * len(g_layer) / 8948:.1f}%) to {int(both.push.isin(["down", "up"]).sum()):,} ({100 * both.push.isin(["down", "up"]).sum() / 8948:.1f}%) of all 8,948 drug–gene links (the graph layer also has 28 "mixed" labels, counted as ambiguous). External sources behind the 297 links: {", ".join(f"{k} {v}" for k, v in src_counts.items())}. Of the external links, {int((e_layer.graph_label == 'TARGET').sum())} were TARGET and {int((e_layer.graph_label != 'TARGET').sum())} ENZYME / TRANSPORTER / CARRIER in the graph.

## Consistency by Paper 1 group
{md(cmp_group)}

## Consistency by F0–F4 trajectory cluster
{md(cmp_cluster)}

## Repurposing candidates (1,109)
{md(cand_tab, idx=False)}

**{len(new_cons_tab)} candidates gain their first direction-consistent link from the external layer:**

{md(new_cons_tab, idx=False)}

## Files
`drug_action_evidence_graph_plus_external.csv` (both layers, labelled), `external_layer_links.csv` (the 297 external links), `consistency_by_group_graph_vs_plus_external.csv`, `consistency_by_cluster_graph_vs_plus_external.csv`, `candidates_graph_vs_plus_external.csv`, `new_consistent_candidates_from_external.csv`. Script: `code/task7_external_layer.py`; lookup and positive control: `External_action_check/`.
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
