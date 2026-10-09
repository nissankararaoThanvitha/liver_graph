"""Paper 1, Task 4 -- pathway enrichment per biologically meaningful gene group.

Groups: fibrosis-only / inflammation-only / shared, each split up/down (Task 1),
and the five F0->F4 trajectory clusters (Task 2) -- all genes, plus a check on
high-confidence genes only (membership_confidence >= 0.8).

Databases (MSigDB 2024.1, symbols): GO Biological Process, KEGG (legacy),
Reactome, Hallmark.

Background: the 14,794 genes eligible for the cross-study progression analysis
(data/progression_full). Every gene set is first restricted to that background,
then kept if it has 10-500 background genes; enrichment is a one-sided
hypergeometric test (gseapy.enrich), BH-FDR within each group x database.
Outputs go to Paper1_Results/Task4/.
"""
import sys
import argparse
from pathlib import Path
import re

import gseapy as gp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

STAGE_FILE = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
CLUSTERS = None  # set below from --clusters; see the argparse block
BACKGROUND = Path("data/progression_full/progression_fibrosis.csv")
GMT_DIR = Path("data/genesets")
# Below this a group cannot support an enrichment test. The
# corrected membership-confidence metric leaves C1_core and
# C3_core at 3 and 1 genes, which is a finding in itself rather
# than something to test.
MIN_GROUP_GENES = 5
DATABASES = {"GO_BP": "c5.go.bp", "KEGG": "c2.cp.kegg_legacy",
             "Reactome": "c2.cp.reactome", "Hallmark": "h.all"}
# Output folder. Defaults to the committed location; --out redirects
# it so a re-run can be compared against the previous version instead
# of overwriting it.
# One parse for both options. Parsing twice strips --out from
# sys.argv on the first call, so the second call silently falls
# back to the default and the run writes to the wrong folder.
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default="Paper1_Results/Task4")
_ap.add_argument("--clusters",
                 default="Paper1_Results/Task2/task2_gene_clusters.csv")
_args, _rest = _ap.parse_known_args()
sys.argv = [sys.argv[0]] + _rest
# Task 2's clusters were read from a hardcoded v1 path, so a v2
# re-run silently mixed v2 gene groups with v1 cluster
# assignments. --clusters makes the pairing explicit.
CLUSTERS = Path(_args.clusters)
OUT = Path(_args.out)
PER_RUN = OUT / "enrichment_tables"
DOTS = OUT / "dot_plots"
for d in (OUT, PER_RUN, DOTS):
    d.mkdir(parents=True, exist_ok=True)
FDR, MIN_SIZE, MAX_SIZE, CORE_CONF = 0.05, 10, 500, 0.8

# --- background and groups ---
background = set(pd.read_csv(BACKGROUND).symbol.dropna())
print(f"background: {len(background):,} eligible genes")

g = pd.read_csv(STAGE_FILE)
f, i = g.fibrosis_rho, g.inflammation_rho
groups = {
    "fibrosis_only_up": g[(g.ladder == "fibrosis_only") & (f > 0)],
    "fibrosis_only_down": g[(g.ladder == "fibrosis_only") & (f < 0)],
    "inflammation_only_up": g[(g.ladder == "inflammation_only") & (i > 0)],
    "inflammation_only_down": g[(g.ladder == "inflammation_only") & (i < 0)],
    "shared_up": g[(g.ladder == "both") & (f > 0) & (i > 0)],
    "shared_down": g[(g.ladder == "both") & (f < 0) & (i < 0)],
}
groups = {k: set(v.symbol) for k, v in groups.items()}
cl = pd.read_csv(CLUSTERS)
cluster_names = cl.drop_duplicates("cluster").set_index("cluster").cluster_name.to_dict()
core_groups = {}
for c, name in sorted(cluster_names.items()):
    groups[f"C{c}_all"] = set(cl.Gene[cl.cluster == c])
    core_groups[f"C{c}_core"] = set(cl.Gene[(cl.cluster == c) & (cl.membership_confidence >= CORE_CONF)])
all_groups = {**groups, **core_groups}
MAIN = list(groups)
for k, v in all_groups.items():
    print(f"  {k:24s} {len(v):5d} genes ({len(v & background)} in background)")

# --- gene sets restricted to the background ---
def read_gmt(path):
    sets = {}
    for line in open(path, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        genes = set(parts[2:]) & background
        if MIN_SIZE <= len(genes) <= MAX_SIZE:
            sets[parts[0]] = sorted(genes)
    return sets

genesets = {}
for db, stem in DATABASES.items():
    genesets[db] = read_gmt(GMT_DIR / f"{stem}.v2024.1.Hs.symbols.gmt")
    print(f"{db}: {len(genesets[db]):,} gene sets with {MIN_SIZE}-{MAX_SIZE} background genes")


def pretty(term):
    t = re.sub(r"^(GOBP|KEGG|REACTOME|HALLMARK)_", "", term).replace("_", " ").lower()
    return t[:1].upper() + t[1:]


# --- run enrichment ---
N = len(background)
rows = []
for grp, genes in all_groups.items():
    glist = sorted(genes & background)
    for db, sets in genesets.items():
        if len(glist) < MIN_GROUP_GENES:
            print(f"  {grp:22s} {db:9s} skipped: only {len(glist)} "
                  f"gene(s) in the background")
            continue
        res = gp.enrich(gene_list=glist, gene_sets=sets, background=sorted(background),
                        outdir=None, cutoff=1.0, no_plot=True, verbose=False).results
        if not isinstance(res, pd.DataFrame) or res.empty:
            # gseapy returns a plain list, not an empty frame, when a
            # gene list is too small to overlap any set.
            print(f"  {grp:22s} {db:9s} no testable overlap")
            continue
        res = res.rename(columns={"P-value": "p_value", "Adjusted P-value": "q_value",
                                  "Genes": "genes", "Term": "term"})
        k = res.Overlap.str.split("/").str[0].astype(int)
        K = res.Overlap.str.split("/").str[1].astype(int)
        res = res.assign(group=grp, database=db, n_group_genes=len(glist), overlap=k,
                         set_size=K, gene_ratio=(k / len(glist)).round(4),
                         bg_ratio=(K / N).round(4),
                         fold_enrichment=((k / len(glist)) / (K / N)).round(3),
                         term_label=res.term.map(pretty))
        res["genes"] = res.genes.str.replace(";", ", ")
        res = res[["group", "database", "term", "term_label", "overlap", "set_size",
                   "n_group_genes", "gene_ratio", "bg_ratio", "fold_enrichment",
                   "p_value", "q_value", "genes"]].sort_values("p_value")
        res["significant"] = res.q_value < FDR
        res.to_csv(PER_RUN / f"{grp}__{db}.csv", index=False, encoding="utf-8-sig")
        rows.append(res)
allres = pd.concat(rows, ignore_index=True)

# sanity check: recompute one p-value directly with the hypergeometric distribution
r0 = allres.iloc[0]
p_check = hypergeom.sf(r0.overlap - 1, N, r0.set_size, r0.n_group_genes)
print(f"\nhypergeometric check ({r0.group}, {r0.term}): gseapy p={r0.p_value:.3e}, scipy p={p_check:.3e}")

sig = allres[allres.significant]
sig.to_csv(OUT / "task4_all_significant.csv", index=False, encoding="utf-8-sig")
# fillna(0): a group skipped for being too small has no rows at all, and
# reindexing it back in yields NaN. Zero is the honest count -- it was not
# tested, and task4_cluster_core_check.csv records which groups those were.
summary = (allres.groupby(["group", "database"]).significant.sum().unstack()
           .reindex(list(all_groups))[list(DATABASES)]
           .fillna(0).astype(int))
summary.insert(0, "n_genes", [len(all_groups[k] & background) for k in summary.index])
summary.to_csv(OUT / "task4_significant_counts.csv", encoding="utf-8-sig")
print("\nSignificant terms (FDR < 0.05):\n" + summary.to_string())

top = (sig.sort_values("p_value").groupby(["group", "database"], sort=False).head(10)
       .sort_values(["group", "database", "p_value"]))
top = top.assign(group=pd.Categorical(top.group, list(all_groups), ordered=True)).sort_values(
    ["group", "database", "p_value"])
top.to_csv(OUT / "task4_top_pathways_per_group.csv", index=False, encoding="utf-8-sig")


# --- dot plots: top 5 per database for each group ---
DB_COLOR = {"GO_BP": "#2471a3", "KEGG": "#c0392b", "Reactome": "#7d3c98", "Hallmark": "#1e8449"}

def dot_plot(grp, path):
    d = sig[sig.group == grp].sort_values("p_value").groupby("database").head(5)
    if d.empty:
        n = len(all_groups[grp] & background)
        fig, ax = plt.subplots(figsize=(7, 2.2))
        ax.axis("off")
        message = (f"Enrichment not tested: {n} gene(s); minimum {MIN_GROUP_GENES} required."
                   if n < MIN_GROUP_GENES else f"Tested: no enriched terms at FDR < {FDR}.")
        ax.text(0.5, 0.65, grp, ha="center", va="center", fontsize=13, fontweight="bold")
        ax.text(0.5, 0.35, message, ha="center", va="center", fontsize=11)
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return True
    d = d.assign(db=pd.Categorical(d.database, list(DATABASES), ordered=True)).sort_values(
        ["db", "gene_ratio"], ascending=[False, True])
    labels = [f"{t[:60]}{'…' if len(t) > 60 else ''}  [{db}]" for t, db in zip(d.term_label, d.database)]
    fig, ax = plt.subplots(figsize=(9, 0.38 * len(d) + 1.6))
    y = np.arange(len(d))
    sc = ax.scatter(d.gene_ratio, y, s=d.overlap * 6 + 10, c=-np.log10(d.q_value), cmap="viridis",
                    edgecolor="black", linewidth=0.4)
    ax.set_yticks(y, labels, fontsize=8)
    for tick, db in zip(ax.get_yticklabels(), d.database):
        tick.set_color(DB_COLOR[db])
    ax.set_xlabel("Gene ratio (genes in pathway / genes in group)")
    ax.set_title(f"{grp}  (n={len(all_groups[grp] & background):,} genes)  top 5 per database, FDR<{FDR}")
    fig.colorbar(sc, ax=ax, label="-log10 FDR", fraction=0.04, pad=0.02)
    for n in (5, 20, 50):
        ax.scatter([], [], s=n * 6 + 10, color="grey", label=f"{n} genes")
    ax.legend(loc="lower right", fontsize=7, title="overlap", title_fontsize=7)
    ax.margins(x=0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return True

for grp in all_groups:
    if not dot_plot(grp, DOTS / f"dot_{grp}.png"):
        print(f"  no significant terms for {grp}: no dot plot")


# --- combined heatmaps across the main groups ---
def heatmap(db, per_group, path, title):
    d = sig[(sig.database == db) & sig.group.isin(MAIN)]
    terms = (d.sort_values("p_value").groupby("group").head(per_group).term.unique()
             if per_group else d.term.unique())
    if len(terms) == 0:
        return
    m = (d[d.term.isin(terms)].pivot_table(index="term", columns="group", values="q_value")
         .reindex(columns=MAIN))
    m = -np.log10(m).fillna(0)
    m = m.loc[m.idxmax(axis=1).map(MAIN.index).sort_values(kind="stable").index]
    fig, ax = plt.subplots(figsize=(0.55 * len(MAIN) + 6, 0.28 * len(m) + 2))
    im = ax.imshow(m.clip(upper=10), aspect="auto", cmap="Reds", vmin=0, vmax=10)
    ax.set_xticks(range(len(MAIN)), [c if not c.startswith("C") else
                                     f"{c.replace('_all', '')}: {cluster_names[int(c[1])]}"
                                     for c in MAIN], rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(m)), [pretty(t)[:70] for t in m.index], fontsize=7)
    ax.axvline(5.5, color="black", lw=1.5)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="-log10 FDR (0 = not significant, capped at 10)",
                 fraction=0.03, pad=0.02)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)

heatmap("Hallmark", None, OUT / "task4_heatmap_hallmark.png",
        "MSigDB Hallmark processes across gene groups (FDR < 0.05)")
heatmap("GO_BP", 5, OUT / "task4_heatmap_go_bp.png",
        "GO Biological Process: top 5 per group, shown across all groups")
heatmap("Reactome", 5, OUT / "task4_heatmap_reactome.png",
        "Reactome: top 5 per group, shown across all groups")
heatmap("KEGG", 5, OUT / "task4_heatmap_kegg.png",
        "KEGG: top 5 per group, shown across all groups")


# --- cluster check: do high-confidence genes give the same biology? ---
check = []
for c in sorted(cluster_names):
    for db in DATABASES:
        a = set(sig[(sig.group == f"C{c}_all") & (sig.database == db)].term)
        b = set(sig[(sig.group == f"C{c}_core") & (sig.database == db)].term)
        top_all = list(sig[(sig.group == f"C{c}_all") & (sig.database == db)].sort_values("p_value").term[:10])
        check.append({"cluster": f"C{c}", "cluster_name": cluster_names[c], "database": db,
                      "n_sig_all": len(a), "n_sig_core": len(b), "n_shared": len(a & b),
                      "pct_core_terms_also_in_all": round(100 * len(a & b) / len(b), 1) if b else np.nan,
                      "top10_all_also_sig_in_core": sum(t in b for t in top_all)})
check = pd.DataFrame(check)
check.to_csv(OUT / "task4_cluster_core_check.csv", index=False, encoding="utf-8-sig")
print("\nCluster check, all genes vs high-confidence genes:\n" + check.to_string(index=False))

print("\nTop Hallmark / GO_BP per main group:")
for grp in MAIN:
    for db in ("Hallmark", "GO_BP"):
        t = sig[(sig.group == grp) & (sig.database == db)].sort_values("p_value").term_label.head(4)
        print(f"  {grp:24s} {db:8s} {' | '.join(t) if len(t) else '-'}")
print(f"\nWrote outputs to {OUT}/")
