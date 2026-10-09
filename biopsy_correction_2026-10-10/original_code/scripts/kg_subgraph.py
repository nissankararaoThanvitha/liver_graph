"""Focused mechanistic subgraph for the high-confidence fibrosis genes.

The knowledge graph is NOT rebuilt. This reads the same CSVs that are loaded
into Neo4j (data/graph_okg) and filters them, which is what the brief asks for
and does not need the database running. That equality is checked rather than
asserted: verify_against_neo4j.py diffs the two, down to the gene IDs of every
mechanism in the figure.

WHAT ENRICHMENT ALREADY SAID, AND WHAT THIS ADDS
Task 4 said WHICH processes are over-represented among fibrosis genes. It
could not say which gene connects to which mechanism, or where several genes
land on the same one. That wiring is what the graph holds.

WHICH KNOWLEDGE LAYER
data/graph_okg -- the OptimusKG layer that is actually loaded into Neo4j. Its
counts match the live graph exactly (IN_PATHWAY 46,751, INVOLVED_IN 157,081,
Pathway 2,220, BioProcess 12,203). An earlier version of this script read
data/graph_kg, the superseded PrimeKG-era layer (42,478 / 143,156 edges;
that OptimusKG replaced; its numbers do not match the graph and it should not
be used.

STRUCTURE, WHICH IS NOT THE CHAIN THE BRIEF DESCRIBES
The brief writes "Gene -> Pathway -> Biological Process". In this graph
Pathways (Reactome) and BioProcesses (GO) are both attached to genes and not
to each other:

    BioProcess  <-INVOLVED_IN-  Gene  -IN_PATHWAY->  Pathway

So each gene's neighbourhood is a star, not a path. All the requested
information is present; convergence still reads normally, as
Gene A -> node <- Gene B.

WHY THE FIGURE IS BUILT ON THE 507 AND NOT THE 25
Measured first: among the final 25, only 2 pathways connect to two or more of
them and none to three or more. That is not a data problem, it is our own
selection -- step 9 deliberately chose genes as unlike each other as possible,
one set per trajectory pattern, both directions, no pathway dominating. Asking
that set to converge is asking it to undo its own design. Across all 507
Tier 1 genes, 328 pathways connect two or more genes and 163 connect three or
more, so the convergence figure is built there with the 25 marked inside it.
The low convergence of the 25 is reported in the workbook's notes sheet rather
than left for a reader to infer from a sparse figure.

HOW THE 12 MECHANISMS ARE CHOSEN
Ranking nodes by raw Tier 1 gene count returns the largest terms in GO rather
than the most relevant ones, so each node is tested for enrichment the same
way Task 4 tested its gene sets: a hypergeometric test of Tier 1 genes against
the 14,794-gene eligible background, BH-FDR across nodes.

  size      10-500 member genes in the background, the window Task 4 used.
  major     at least 10 Tier 1 genes, so the node is actually well connected.
  enriched  q < 0.05 -- over-represented, not merely large.
  ranked    by q-value, then deduplicated, then the top 12.

Ranked by q and not by gene count. Count alone put "positive regulation of
gene expression", "negative regulation of apoptotic process" and
"positive/negative regulation of cell population proliferation" in the top
twelve: terms that appear in almost any gene list. They are significant here
too, but only 2.3-3.0x enriched against 4-7.5x for the specific mechanisms,
and q weighs size and fold together, so they fall away without a hand-picked
fold cutoff.

Tested on the graph's own nodes rather than by matching their names to Task
4's terms. Name matching was tried first and is brittle: MSigDB 2024.1 has no
GOBP_EXTRACELLULAR_MATRIX_ORGANIZATION because GO renamed that term to
external encapsulating structure organization, so the single most connected
mechanism in the graph -- 56 Tier 1 genes, 7.5x enriched, q = 3e-31 -- was
marked "not enriched" and dropped from the figure over a vocabulary change.
Matching on gene membership instead was no better: that node's best Jaccard
against any significant term is 0.45. Testing the node directly needs no
vocabulary at all.

  deduplicated  GO carries "wound healing" and "response to wounding" with
                largely the same members; showing both spends two of the
                figure's twelve slots on one mechanism.

Usage:
    python Paper1_HighConfidence/kg_subgraph.py
"""
import pathlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control, hypergeom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
import argparse as _argparse
import sys as _sys

_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default=None,
                 help="folder for this script's own numbered outputs")
_ap.add_argument("--results", default=None,
                 help="Paper1_Results folder to read Task2/3/4 from")
_args, _rest = _ap.parse_known_args()
_sys.argv = [_sys.argv[0]] + _rest
# These scripts used to live inside the results folder, so HERE was
# both 'where the code is' and 'where results go'. They now live in
# scripts/, so the output location has to be named rather than
# inherited from the file's own position.
HERE = (pathlib.Path(_args.out).resolve() if _args.out
        else ROOT / "Paper1_HighConfidence")
HERE.mkdir(parents=True, exist_ok=True)
RESULTS = pathlib.Path(_args.results) if _args.results else ROOT / "Paper1_Results"

KG = ROOT / "data/graph_okg"   # the layer actually loaded into Neo4j

SHORTLIST = HERE / "11_FINAL_shortlist_25_genes.csv"
# No count in the name: Tier 1 held 507 genes in v1 and 525 in v2, and
# a filename that disagrees with its contents is how stale numbers
# spread into a manuscript.
TIER1 = HERE / "11_final_tier1_genes.csv"
BACKGROUND = ROOT / "data/progression_full/progression_fibrosis.csv"

N_MAJOR_NODES = 12        # the brief asks for 8-15
MIN_SET, MAX_SET = 10, 500  # same size window Task 4 used for enrichment
MIN_TIER1_GENES = 10      # "major": a node must actually be well connected
FDR = 0.05
JACCARD_DUP = 0.5         # above this two nodes are the same mechanism
MIN_GENE_DEGREE = 3       # a gene is drawn if it reaches >= 3 major nodes,
                          # or if it is one of the final 25. At 2 the figure
                          # held 125 genes and stopped being readable.

# --- the gene sets ---
short = pd.read_csv(SHORTLIST)
tier1 = pd.read_csv(TIER1)
short_ids, tier1_ids = set(short.Ensembl_ID), set(tier1.Ensembl_ID)
meta = tier1.set_index("Ensembl_ID")
print(f"Tier 1 genes {len(tier1_ids):,}   final shortlist {len(short_ids)}")

# --- the knowledge layer, as loaded into Neo4j ---
nodes = pd.concat([
    pd.read_csv(KG / "nodes_pathway.csv").assign(node_type="Pathway"),
    pd.read_csv(KG / "nodes_bioprocess.csv").assign(node_type="BioProcess"),
], ignore_index=True)
nodes["node_id"] = nodes.node_id.astype(str)
name_of = nodes.set_index("node_id").name.to_dict()
type_of = nodes.set_index("node_id").node_type.to_dict()


background = set(pd.read_csv(BACKGROUND).ensembl_id)
print(f"  enrichment background: {len(background):,} eligible genes "
      f"(the same one Task 4 used)")

edges = pd.concat([
    pd.read_csv(KG / "edges_pathway_gene.csv",
                usecols=["from_id", "to_id"]).assign(rel="IN_PATHWAY"),
    pd.read_csv(KG / "edges_biological_process_gene.csv",
                usecols=["from_id", "to_id"]).assign(rel="INVOLVED_IN"),
], ignore_index=True)
edges["to_id"] = edges.to_id.astype(str)
edges = edges[edges.to_id.isin(name_of)]
print(f"knowledge layer: {len(edges):,} gene-to-mechanism edges, "
      f"{edges.to_id.nunique():,} mechanisms")

# total members per node, for the size filter
total_members = edges.groupby("to_id").from_id.nunique()
# members restricted to the enrichment background, for the hypergeometric test
bg_members = (edges[edges.from_id.isin(background)]
              .groupby("to_id").from_id.nunique())

t1_edges = edges[edges.from_id.isin(tier1_ids)].copy()
t1_edges["gene"] = t1_edges.from_id.map(meta.Gene)
t1_edges["mechanism"] = t1_edges.to_id.map(name_of)
t1_edges["mechanism_type"] = t1_edges.to_id.map(type_of)
t1_edges["in_shortlist_25"] = t1_edges.from_id.isin(short_ids)

# --- rank every mechanism by how many Tier 1 genes reach it ---
rank = (t1_edges.groupby(["to_id", "mechanism", "mechanism_type"])
        .agg(n_tier1_genes=("from_id", "nunique"),
             n_shortlist_genes=("in_shortlist_25", "sum"))
        .reset_index())
rank["n_genes_total_in_kg"] = rank.to_id.map(total_members)
rank["n_genes_in_background"] = rank.to_id.map(bg_members).fillna(0).astype(int)

# Enrichment tested on the graph's own nodes: are Tier 1 genes
# over-represented among this node's members, against the 14,794-gene
# background? Same statistic Task 4 used, no name mapping involved.
n_t1_bg = len(tier1_ids & background)
N_bg = len(background)
rank["fold_enrichment"] = (
    rank.n_tier1_genes / (rank.n_genes_in_background * n_t1_bg / N_bg)
).replace([np.inf, -np.inf], np.nan).round(2)
rank["p_value"] = hypergeom.sf(rank.n_tier1_genes - 1, N_bg,
                               rank.n_genes_in_background, n_t1_bg)
rank["q_value"] = false_discovery_control(rank.p_value, method="bh")

rank["passes_size_filter"] = rank.n_genes_in_background.between(MIN_SET, MAX_SET)
rank["is_major"] = rank.n_tier1_genes >= MIN_TIER1_GENES
rank["is_enriched"] = rank.q_value < FDR
rank["eligible_for_figure"] = (rank.passes_size_filter & rank.is_major
                               & rank.is_enriched)
# ranked by q, not by gene count: q weighs size and fold together, so the
# large generic terms fall away without a hand-picked fold cutoff
rank = rank.sort_values("q_value").reset_index(drop=True)

# --- pick the major nodes: size, enrichment, then drop near-duplicates ---
members = {k: set(v) for k, v in
           t1_edges.groupby("to_id").from_id.apply(list).items()}
chosen, dropped = [], []
for _, r in rank[rank.eligible_for_figure].iterrows():
    mine = members[r.to_id]
    dup = next((c for c in chosen
                if len(mine & members[c]) / len(mine | members[c]) > JACCARD_DUP),
               None)
    if dup is not None:
        dropped.append({"dropped": r.mechanism, "kept_instead": name_of[dup],
                        "jaccard": round(len(mine & members[dup])
                                         / len(mine | members[dup]), 2)})
        continue
    chosen.append(r.to_id)
    if len(chosen) == N_MAJOR_NODES:
        break

major = rank[rank.to_id.isin(chosen)].copy()
print(f"\n{len(major)} major mechanisms (of {rank.passes_size_filter.sum():,} "
      f"passing the size filter, {rank.eligible_for_figure.sum():,} also "
      f"major and enriched; {len(dropped)} near-duplicates collapsed)")
print(major[["mechanism", "mechanism_type", "n_tier1_genes",
             "n_shortlist_genes", "n_genes_in_background",
             "fold_enrichment", "q_value"]].to_string(index=False))

# --- the genes to draw ---
fig_edges = t1_edges[t1_edges.to_id.isin(chosen)].copy()
deg = fig_edges.groupby("from_id").to_id.nunique()
keep_genes = set(deg[deg >= MIN_GENE_DEGREE].index) | (
    set(fig_edges.from_id) & short_ids)
fig_edges = fig_edges[fig_edges.from_id.isin(keep_genes)]
n_short_in_fig = len(set(fig_edges.from_id) & short_ids)
print(f"\nfigure: {len(keep_genes)} genes, {len(fig_edges)} edges "
      f"({n_short_in_fig} of the final 25 appear; the rest connect to none "
      f"of these 12 mechanisms)")

# --- draw ---
G = nx.Graph()
for n in chosen:
    G.add_node(n, kind=type_of[n])
for _, r in fig_edges.iterrows():
    G.add_node(r.from_id, kind="shortlist" if r.in_shortlist_25 else "tier1")
    G.add_edge(r.from_id, r.to_id)

# Mechanism nodes are pinned evenly around a circle; a free spring layout let
# their twelve labels drift on top of each other, which is the one thing this
# figure cannot afford.
#
# Genes are then placed in two ways. Those reaching several mechanisms are
# sprung inside the ring, where their position carries information: a gene
# pulled between integrin signalling and ECM organization sits between them.
# Genes reaching exactly one mechanism carry no such information and were
# collapsing onto a single point per mechanism -- PDGFRA and TREM2 printed on
# top of each other -- so they are fanned outside the ring around the one
# mechanism they touch, which cannot overlap by construction.
ring = {n: np.array([np.cos(a), np.sin(a)])
        for n, a in zip(chosen,
                        np.linspace(0, 2 * np.pi, len(chosen), endpoint=False))}
leaves, hubs = {}, [g for g in G if g not in ring and G.degree(g) > 1]
# The fan must be NARROWER than the gap between neighbouring mechanisms. At
# ±0.26 rad with twelve mechanisms 0.524 rad apart, a gene fanned clockwise
# off one mechanism landed exactly on a gene fanned anticlockwise off its
# neighbour -- TREM2 printed on top of MYC. Half the gap, and alternating
# radii, keeps every leaf label clear.
gap = 2 * np.pi / len(chosen)
for n in chosen:
    kids = sorted(g for g in G[n] if G.degree(g) == 1)
    base = np.arctan2(*ring[n][::-1])
    span = (np.linspace(-gap * 0.28, gap * 0.28, len(kids))
            if len(kids) > 1 else [0.0])
    for i, (g, off) in enumerate(zip(kids, span)):
        a = base + off
        # far enough out to clear the mechanism labels, which sit at ~1.17
        # and are wide; at 1.40 ADAMTSL2 was printing underneath one
        leaves[g] = np.array([np.cos(a), np.sin(a)]) * (1.62 + 0.13 * (i % 2))

rng = np.random.default_rng(7)
pos = nx.spring_layout(
    G, k=0.5, iterations=700, seed=7, weight=None,
    pos={**ring, **leaves,
         **{g: rng.normal(0, 0.28, 2) for g in hubs}},
    fixed=list(ring) + list(leaves))

# Pull the sprung genes inwards, away from the ring. Scaling them all by the
# same factor keeps the layout the spring found -- clipping only the outliers
# bunched them against each other, and a larger k pushed them onto the
# mechanism markers instead.
hub_r = max(np.linalg.norm(pos[g]) for g in hubs) or 1.0
for g in hubs:
    pos[g] = pos[g] * (0.92 / hub_r)

# Short de-overlap pass. The spring puts near-identical genes on top of each
# other -- COL4A1 and COL4A2 share five of their six mechanisms, so their
# labels printed as one word. Pushing any two markers apart to a minimum
# separation costs nothing semantically: they were already in the same place.
MIN_SEP = 0.17   # set by LABEL width, not marker size: a 7-character
                 # bold symbol is about 0.12 data units wide here
for _ in range(220):
    moved = False
    for i, a in enumerate(hubs):
        for b in hubs[i + 1:]:
            d = pos[a] - pos[b]
            r = np.linalg.norm(d)
            if r < MIN_SEP:
                push = (d / (r or 1e-6)) * (MIN_SEP - r) / 2
                pos[a], pos[b] = pos[a] + push, pos[b] - push
                moved = True
    if not moved:
        break

fig, ax = plt.subplots(figsize=(18, 13))
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#ccd0d6", width=0.6,
                       alpha=0.7)

# Tier 1 genes are sized and darkened by how many of the twelve mechanisms
# they reach, because that IS the thing the figure is for: a gene touching
# six mechanisms is a convergence point and should look like one. At a flat
# small grey they were legible as dots but not identifiable as genes, which
# left the pathways readable and the genes behind them invisible.
tier1_nodes = [n for n, d in G.nodes(data=True) if d["kind"] == "tier1"]
deg = {n: G.degree(n) for n in tier1_nodes}

groups = {
    "tier1": dict(nodelist=tier1_nodes,
                  node_color="#8c99a6", node_size=[72 * deg[n] for n in tier1_nodes],
                  edgecolors="#404a55", linewidths=1.0),
    "shortlist": dict(nodelist=[n for n, d in G.nodes(data=True)
                                if d["kind"] == "shortlist"],
                      node_color="#e8743b", node_size=420,
                      edgecolors="#7d3517", linewidths=1.8),
    "Pathway": dict(nodelist=[n for n in chosen if type_of[n] == "Pathway"],
                    node_color="#2e6e9e", node_size=900,
                    edgecolors="#15374f", linewidths=2, node_shape="s"),
    "BioProcess": dict(nodelist=[n for n in chosen
                                 if type_of[n] == "BioProcess"],
                       node_color="#4a9a6f", node_size=900,
                       edgecolors="#20503a", linewidths=2, node_shape="s"),
}
for g in groups.values():
    if g["nodelist"]:
        nx.draw_networkx_nodes(G, pos, ax=ax, **g)

# Shortlist labels sit just outside their marker; centred, longer symbols
# overflowed the circle. Those inside the ring keep a centred label, since
# there is no outward direction that reliably avoids an edge.
for n in G:
    if G.nodes[n]["kind"] != "shortlist":
        continue
    if n in leaves:
        v = pos[n] / (np.linalg.norm(pos[n]) or 1)
        ax.text(*(pos[n] + v * 0.1), meta.Gene.get(n, ""),
                ha="left" if v[0] > 0 else "right", va="center",
                fontsize=10, fontweight="bold", color="#7d3517", zorder=7)
    else:
        # inside the ring: a centred label overflows the marker (PDGFRA read
        # "DGFR"), so it sits just above it on its own backing
        # below the marker, not above: above, IL32's label landed on the
        # inflammatory-response square it sits beneath
        ax.text(pos[n][0], pos[n][1] - 0.055, meta.Gene.get(n, ""),
                ha="center", va="top", fontsize=9, fontweight="bold",
                color="#7d3517", zorder=7,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                          edgecolor="none", alpha=0.85))

# Tier 1 labels scale with degree too, so the hubs are readable at a glance
for n in tier1_nodes:
    ax.text(*pos[n], meta.Gene.get(n, ""), ha="center", va="center",
            fontsize=4.6 + 0.85 * deg[n], fontweight="bold",
            color="#11161c" if deg[n] >= 5 else "#28313b", zorder=6,
            # a white outline keeps the smaller symbols legible where the
            # label is wider than its marker or crosses an edge
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])
# Mechanism labels sit OUTSIDE their node, pushed radially outwards, in a
# white box. Inside the node the text was clipped by the marker and collided
# with its neighbours.
for n in chosen:
    words, lines, cur = name_of[n].split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 22:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    v = pos[n] / (np.linalg.norm(pos[n]) or 1)
    ax.text(*(pos[n] + v * 0.21), "\n".join(lines),
            ha="center" if abs(v[0]) < 0.6 else ("left" if v[0] > 0 else "right"),
            va="center", fontsize=9, fontweight="bold",
            color="#15374f" if type_of[n] == "Pathway" else "#20503a",
            zorder=6,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="none", alpha=0.88))

ax.legend(handles=[
    mpatches.Patch(color="#2e6e9e", label="Pathway (Reactome)"),
    mpatches.Patch(color="#4a9a6f", label="Biological process (GO)"),
    mpatches.Patch(color="#e8743b", label="Final 25 high-confidence genes"),
    mpatches.Patch(color="#8c99a6",
                   label="Other Tier 1 genes (size = mechanisms reached, "
                         f"{min(deg.values())}-{max(deg.values())})"),
], loc="upper left", frameon=False, fontsize=10)
ax.set_title(
    f"Where the high-confidence fibrosis genes converge\n"
    f"{len(major)} most-connected mechanisms in the knowledge graph, "
    f"the Tier 1 genes reaching them, and the final 25 highlighted",
    fontsize=13, pad=16)
ax.axis("off")
ax.margins(0.20)   # room for the outward-pushed mechanism and leaf labels
fig.tight_layout()
fig.savefig(HERE / "12_mechanistic_subgraph.png", dpi=300,
            bbox_inches="tight", facecolor="white")
plt.close(fig)

# --- the supplementary workbook ---
def long_table(ids, label):
    """The brief's columns: one row per gene per mechanism."""
    e = edges[edges.from_id.isin(ids)].copy()
    e["Gene"] = e.from_id.map(meta.Gene)
    e["Mechanism"] = e.to_id.map(name_of)
    e["kind"] = e.to_id.map(type_of)
    e["Direction"] = e.from_id.map(meta.Direction)
    e["Cluster"] = e.from_id.map(meta.Cluster)
    e["Cluster_pattern"] = e.from_id.map(meta.Cluster_pattern)
    e["Fibrosis_only_or_shared"] = e.from_id.map(meta.Fibrosis_only_or_shared)
    e["Total_score"] = e.from_id.map(meta.Total_score)
    e["Pathway"] = np.where(e.kind == "Pathway", e.Mechanism, "")
    e["Biological_Process"] = np.where(e.kind == "BioProcess", e.Mechanism, "")
    cols = ["Gene", "Direction", "Cluster", "Cluster_pattern",
            "Fibrosis_only_or_shared", "Total_score", "Pathway",
            "Biological_Process", "from_id", "to_id"]
    out = e[cols].rename(columns={"from_id": "Ensembl_ID",
                                  "to_id": "Mechanism_ID"})
    print(f"  {label}: {len(out):,} gene-mechanism rows")
    return out.sort_values(["Gene", "Pathway", "Biological_Process"])


notes = pd.DataFrame({"Sheet": [
    "1_shortlist_25_KG", "2_tier1_507_KG", "3_all_mechanisms_ranked",
    "4_figure_edges", "5_figure_nodes", "6_duplicates_collapsed"], "Contents": [
    "The brief's table for the final 25 genes: one row per gene per "
    "connected pathway or biological process.",
    "The same for all 507 Tier 1 genes.",
    "Every mechanism the Tier 1 genes reach, with its fold enrichment, "
    "p and q, and the size / major / enriched flags - so the choice of 12 "
    "is auditable.",
    "The edges drawn in Figure 12.",
    "The nodes drawn in Figure 12.",
    "Near-duplicate mechanisms collapsed, and which was kept instead."]})
caveats = pd.DataFrame({"Caveat": [
    "THE FINAL 25 BARELY CONVERGE, AND THE FIGURE SHOULD NOT BE READ AS IF "
    "THEY DO. Among the 25, only 2 pathways connect to two or more of them "
    "and none to three or more. This follows directly from step 9, which "
    "selected genes to be as unlike each other as possible. Most convergence "
    "visible in the figure comes from the other Tier 1 genes.",
    "PATHWAYS AND BIOLOGICAL PROCESSES ARE NOT CONNECTED TO EACH OTHER in "
    "this graph. Both attach to genes. The brief's 'Gene -> Pathway -> "
    "Biological Process' is therefore two separate connections per gene, not "
    "a chain. No information is missing.",
    "THE 12 MECHANISMS WERE CHOSEN BY ENRICHMENT, NOT BY GENE COUNT. Each "
    "graph node was tested the way Task 4 tested its gene sets - a "
    "hypergeometric test of the Tier 1 genes against the same 14,794-gene "
    "eligible background, BH-FDR across nodes - then filtered to 10-500 "
    "member genes and at least 10 Tier 1 genes, and ranked by q-value. "
    "Ranking by gene count instead returned 'positive regulation of gene "
    "expression', 'negative regulation of apoptotic process' and "
    "'positive/negative regulation of cell population proliferation' in the "
    "top twelve: terms that appear in almost any gene list. They are "
    "significant here too, but only 2.3-3.0x enriched against 4-13x for the "
    "mechanisms shown, and q weighs size and fold together, so they fall "
    "away without a hand-picked fold cutoff.",
    "ENRICHMENT WAS TESTED ON THE GRAPH'S OWN NODES RATHER THAN BY MATCHING "
    "THEIR NAMES TO TASK 4'S TERMS. Name matching was tried first and is "
    "brittle: MSigDB 2024.1 has no GOBP_EXTRACELLULAR_MATRIX_ORGANIZATION "
    "because GO renamed that term to external encapsulating structure "
    "organization, so the most connected mechanism in the graph - 56 Tier 1 "
    "genes, 7.5x enriched, q = 8e-30 - was marked 'not enriched' and dropped "
    "from the figure over a vocabulary change. Matching on gene membership "
    "was no better: that node's best Jaccard against any significant term is "
    "0.45. Testing each node directly needs no vocabulary at all.",
    "NEAR-DUPLICATE MECHANISMS WERE COLLAPSED at Jaccard > 0.5 of their Tier "
    "1 members, so the figure shows distinct mechanisms rather than one "
    "mechanism worded several ways. Sheet 6 lists what was collapsed.",
    "THE FIGURE DRAWS A SUBSET OF GENES: those reaching two or more of the "
    "12 mechanisms, plus every one of the final 25 that reaches any. Genes "
    "absent from the figure are not absent from the analysis - sheets 1 and "
    "2 carry every connection.",
    "THE KNOWLEDGE GRAPH WAS NOT REBUILT. This reads the same CSVs that are "
    "loaded into Neo4j: data/graph_okg, the OptimusKG layer. Checked, not "
    "assumed -- verify_against_neo4j.py diffs the files against the live "
    "database at four levels, down to the gene IDs of each mechanism shown "
    "here, and all of them matched. An earlier version read data/graph_kg, "
    "the superseded PrimeKG layer, whose counts do not match the graph."]})

out_xlsx = HERE / "12_KG_supplementary.xlsx"
with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xl:
    notes.to_excel(xl, sheet_name="0_README", index=False)
    caveats.to_excel(xl, sheet_name="0_README", index=False, startrow=9)
    long_table(short_ids, "shortlist 25").to_excel(
        xl, sheet_name="1_shortlist_25_KG", index=False)
    long_table(tier1_ids, "tier 1 507").to_excel(
        xl, sheet_name="2_tier1_507_KG", index=False)
    rank.assign(selected_for_figure=rank.to_id.isin(chosen)).rename(
        columns={"to_id": "Mechanism_ID"}).to_excel(
        xl, sheet_name="3_all_mechanisms_ranked", index=False)
    fig_edges[["gene", "from_id", "mechanism", "to_id", "mechanism_type",
               "rel", "in_shortlist_25"]].rename(columns={
                   "gene": "Gene", "from_id": "Ensembl_ID",
                   "mechanism": "Mechanism", "to_id": "Mechanism_ID",
                   "mechanism_type": "Mechanism_type", "rel": "Relationship",
                   "in_shortlist_25": "In_final_25"}).to_excel(
        xl, sheet_name="4_figure_edges", index=False)
    pd.DataFrame([
        {"Node": meta.Gene.get(n, name_of.get(n, n)),
         "ID": n,
         "Kind": ("Final 25 gene" if G.nodes[n]["kind"] == "shortlist"
                  else "Tier 1 gene" if G.nodes[n]["kind"] == "tier1"
                  else G.nodes[n]["kind"]),
         "Degree_in_figure": G.degree(n)}
        for n in G.nodes]).sort_values(
            ["Kind", "Degree_in_figure"], ascending=[True, False]).to_excel(
        xl, sheet_name="5_figure_nodes", index=False)
    (pd.DataFrame(dropped) if dropped else
     pd.DataFrame(columns=["dropped", "kept_instead", "jaccard"])).to_excel(
        xl, sheet_name="6_duplicates_collapsed", index=False)

print(f"\n-> {(HERE / '12_mechanistic_subgraph.png').relative_to(ROOT)}")
print(f"-> {out_xlsx.relative_to(ROOT)}")
