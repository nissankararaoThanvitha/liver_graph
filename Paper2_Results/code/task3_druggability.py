"""Paper 2 Task 3: druggability of Paper 1 progression-gene groups.

For each Paper 1 group (classes and class x direction), compares the fraction of
drug-connected genes against the Paper 1 eligible-gene background (14,794 genes).
Two definitions of "drug-connected" are analysed:
  A. any drug    : >=1 Drug-[:ACTS_ON]->Gene line (any action)
  B. pharmacological target : >=1 line whose action is NOT ENZYME / TRANSPORTER /
     CARRIER (those describe drug metabolism or transport, not a drug target)
Statistics, for each definition:
  * Fisher's exact test (group vs. rest of background), odds ratio + 95% CI, BH-FDR
  * pairwise Fisher tests between the three classes, BH-FDR
  * a degree-aware permutation test: 1,000 random background gene sets matched to
    each group on gene-gene network degree (INTERACTS_WITH) bins, seed 42.

Knowledge graph only (read-only Neo4j); password from NEO4J_PASSWORD (prompted if unset).
Run from the repository root:

    python Paper2_Results/code/task3_druggability.py
"""
import base64
import getpass
import json
import os
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, false_discovery_control
from scipy.stats.contingency import odds_ratio

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results" / "Task3"
OUT.mkdir(parents=True, exist_ok=True)

GENES = ROOT / "Paper2_Results/Task1/Paper2_progression_genes.csv"
EDGES = ROOT / "Paper2_Results/Task2/drug_gene_edges.csv"
BACKGROUND = ROOT / "Paper1_HighConfidence/10_loso_all_eligible_runs.csv"
KL = ROOT / "Paper1_Package/04_DATA/knowledge_layer"

N_PERM = 1000
SEED = 42
N_DEGREE_BINS = 10

NEO4J_URL = os.environ.get("NEO4J_HTTP", "http://127.0.0.1:7474")
NEO4J_DB = os.environ.get("NEO4J_DATABASE", "neo4j")
NEO4J_USER = os.environ.get("NEO4J_USERNAME", "neo4j")


def neo4j_query(statement, params, password):
    headers = {"Authorization": "Basic " + base64.b64encode(f"{NEO4J_USER}:{password}".encode()).decode(),
               "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": statement, "parameters": params, "accessMode": "Read"}).encode()
    req = urllib.request.Request(f"{NEO4J_URL}/db/{NEO4J_DB}/query/v2", data=body, headers=headers, method="POST")
    res = json.load(urllib.request.urlopen(req, timeout=600))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return pd.DataFrame(res["data"]["values"], columns=res["data"]["fields"])


PK_ACTIONS = ["ENZYME", "TRANSPORTER", "CARRIER"]   # pharmacokinetic roles, not drug targets
DEFS = {
    "any": {"col": "drug_connected", "label": "any drug (all ACTS_ON actions)", "suffix": ""},
    "pharm": {"col": "pharm_connected", "label": "pharmacological target (excludes ENZYME/TRANSPORTER/CARRIER)",
              "suffix": "_pharmacological"},
}

# ------------------------------------------------------------------ background
bg_ids = sorted(set(pd.read_csv(BACKGROUND, usecols=["ensembl_id"]).ensembl_id))
genes = pd.read_csv(GENES)
assert genes.ensembl_id.isin(bg_ids).all(), "progression genes must lie inside the background"

QUERY = """
UNWIND $ids AS id
MATCH (g:Gene {ensembl_id: id})
OPTIONAL MATCH (d:Drug)-[r:ACTS_ON]->(g)
WITH g, count(DISTINCT d) AS n_drugs,
     count(DISTINCT CASE WHEN NOT r.action IN $pk THEN d END) AS n_pharm_drugs
OPTIONAL MATCH (g)-[:INTERACTS_WITH]-(h:Gene)
RETURN g.ensembl_id AS ensembl_id, n_drugs, n_pharm_drugs, count(DISTINCT h) AS ppi_degree
"""
source = "Neo4j (live liver_kg, read-only)"
try:
    pw = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")
    bg = neo4j_query(QUERY, {"ids": bg_ids, "pk": PK_ACTIONS}, pw)
except Exception as exc:
    print(f"Neo4j unavailable ({exc}); using knowledge-layer CSVs")
    source = "CSV fallback (knowledge_layer) — Neo4j unavailable"
    dg = pd.read_csv(KL / "edges_drug_gene.csv")
    gg = pd.read_csv(KL / "edges_gene_gene.csv")
    und = pd.concat([gg[["from_id", "to_id"]], gg[["to_id", "from_id"]].set_axis(["from_id", "to_id"], axis=1)])
    und = und[und.from_id != und.to_id].drop_duplicates()
    bg = pd.DataFrame({"ensembl_id": bg_ids})
    bg["n_drugs"] = bg.ensembl_id.map(dg.groupby("to_id").from_id.nunique())
    bg["n_pharm_drugs"] = bg.ensembl_id.map(dg[~dg.rel_type.isin(PK_ACTIONS)].groupby("to_id").from_id.nunique())
    bg["ppi_degree"] = bg.ensembl_id.map(und.groupby("from_id").to_id.nunique())

bg = pd.DataFrame({"ensembl_id": bg_ids}).merge(bg, on="ensembl_id", how="left")
bg[["n_drugs", "n_pharm_drugs", "ppi_degree"]] = bg[["n_drugs", "n_pharm_drugs", "ppi_degree"]].fillna(0).astype(int)
bg["drug_connected"] = bg.n_drugs > 0
bg["pharm_connected"] = bg.n_pharm_drugs > 0

# consistency with Task 2
edges = pd.read_csv(EDGES)
in_prog = bg.ensembl_id.isin(genes.ensembl_id)
assert set(bg.loc[bg.drug_connected & in_prog, "ensembl_id"]) == set(edges.Gene_ID), "drug flags disagree with Task 2"
pharm_edges = edges[~edges.Action_raw.isin(PK_ACTIONS)]
assert set(bg.loc[bg.pharm_connected & in_prog, "ensembl_id"]) == set(pharm_edges.Gene_ID), "pharm flags disagree with Task 2"

# degree bins: degree 0 is its own bin, the rest are deciles
nz = bg.ppi_degree > 0
bg["degree_bin"] = 0
bg.loc[nz, "degree_bin"] = pd.qcut(bg.loc[nz, "ppi_degree"].rank(method="first"), N_DEGREE_BINS, labels=False) + 1
bg.to_csv(OUT / "background_genes_druggability.csv", index=False)

# ------------------------------------------------------------------ groups
GROUPS = [
    ("All progression genes", genes.ensembl_id),
    ("Fibrosis-associated (fibrosis-only + shared)", genes.loc[genes.progression_class != "inflammation_only", "ensembl_id"]),
    ("fibrosis_only", genes.loc[genes.progression_class == "fibrosis_only", "ensembl_id"]),
    ("shared", genes.loc[genes.progression_class == "shared", "ensembl_id"]),
    ("inflammation_only", genes.loc[genes.progression_class == "inflammation_only", "ensembl_id"]),
]
for g in ["fibrosis_only_positive", "fibrosis_only_negative", "shared_positive", "shared_negative",
          "shared_discordant_fib_negative", "inflammation_only_positive", "inflammation_only_negative"]:
    GROUPS.append((g, genes.loc[genes.paper1_group == g, "ensembl_id"]))
LEVEL = {name: ("summary" if i < 2 else "class" if i < 5 else "class x direction") for i, (name, _) in enumerate(GROUPS)}

bgi = bg.set_index("ensembl_id")
bins = bg.degree_bin.values
bin_index = {b: np.flatnonzero(bins == b) for b in np.unique(bins)}


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return c - h, c + h


def analyse(col, edge_table):
    """Fisher + degree-matched permutation for every group, using flag column `col`."""
    rng = np.random.default_rng(SEED)
    conn = bg[col].values
    drugs_per_gene = edge_table.groupby("Gene_ID").Drug_ID.agg(set)
    rows = []
    for name, ids in GROUPS:
        ids = pd.Index(ids)
        sub = bgi.loc[ids]
        k, n = int(sub[col].sum()), len(sub)
        rest = bgi.drop(ids)
        k0, n0 = int(rest[col].sum()), len(rest)
        table = [[k, n - k], [k0, n0 - k0]]
        orr = odds_ratio(table)
        ci = orr.confidence_interval(0.95)
        lo, hi = wilson(k, n)
        drugs = set().union(*[drugs_per_gene.get(g, set()) for g in ids])
        need = sub.degree_bin.value_counts()
        null = np.empty(N_PERM)
        for i in range(N_PERM):
            pick = np.concatenate([rng.choice(bin_index[b], size=c, replace=False) for b, c in need.items()])
            null[i] = conn[pick].mean()
        obs = k / n
        p_enr = (1 + (null >= obs).sum()) / (N_PERM + 1)
        p_dep = (1 + (null <= obs).sum()) / (N_PERM + 1)
        rows.append({
            "Group": name, "Level": LEVEL[name], "Total genes": n, "Drug-connected genes": k,
            "Percentage": round(100 * obs, 2), "Wilson_CI_low_%": round(100 * lo, 2), "Wilson_CI_high_%": round(100 * hi, 2),
            "Unique drugs": len(drugs), "Median PPI degree": float(sub.ppi_degree.median()),
            "Rest-of-background %": round(100 * k0 / n0, 2),
            "Odds ratio": round(orr.statistic, 3), "OR_CI_low": round(ci.low, 3), "OR_CI_high": round(ci.high, 3),
            "Fisher_p": fisher_exact(table).pvalue,
            "Degree-matched expected %": round(100 * null.mean(), 2),
            "Degree-matched null 95% range %": f"{100 * np.quantile(null, 0.025):.1f}–{100 * np.quantile(null, 0.975):.1f}",
            "Fold vs degree-matched": round(obs / null.mean(), 3),
            "Perm_p_enrichment": p_enr, "Perm_p_depletion": p_dep,
            "Perm_p_two_sided": min(1.0, 2 * min(p_enr, p_dep)),
        })
    df = pd.DataFrame(rows)
    df["Fisher_BH_FDR"] = false_discovery_control(df.Fisher_p, method="bh")
    df["Perm_BH_FDR"] = false_discovery_control(df.Perm_p_two_sided, method="bh")

    pairs = []
    cls = {c: bgi.loc[genes.loc[genes.progression_class == c, "ensembl_id"]] for c in ["fibrosis_only", "shared", "inflammation_only"]}
    for a, b in [("fibrosis_only", "inflammation_only"), ("shared", "inflammation_only"), ("fibrosis_only", "shared")]:
        ka, na = int(cls[a][col].sum()), len(cls[a])
        kb, nb = int(cls[b][col].sum()), len(cls[b])
        t = [[ka, na - ka], [kb, nb - kb]]
        r = odds_ratio(t)
        ci = r.confidence_interval(0.95)
        pairs.append({"Comparison": f"{a} vs {b}", "%A": round(100 * ka / na, 1), "%B": round(100 * kb / nb, 1),
                      "Odds ratio": round(r.statistic, 3), "OR_CI_low": round(ci.low, 3), "OR_CI_high": round(ci.high, 3),
                      "Fisher_p": fisher_exact(t).pvalue})
    pairs = pd.DataFrame(pairs)
    pairs["BH_FDR"] = false_discovery_control(pairs.Fisher_p, method="bh")
    return df, pairs


COLORS = {"fibrosis_only": "#c0392b", "shared": "#7d3c98", "inflammation_only": "#2471a3"}
LABEL = {
    "fibrosis_only": "Fibrosis-only\n(all)", "shared": "Shared\n(all)", "inflammation_only": "Inflammation-only\n(all)",
    "fibrosis_only_positive": "Fibrosis-only\n⬆", "fibrosis_only_negative": "Fibrosis-only\n⬇",
    "shared_positive": "Shared\n⬆⬆", "shared_negative": "Shared\n⬇⬇", "shared_discordant_fib_negative": "Shared\nmixed",
    "inflammation_only_positive": "Inflammation-only\n⬆", "inflammation_only_negative": "Inflammation-only\n⬇",
}
ORDER = ["fibrosis_only", "fibrosis_only_positive", "fibrosis_only_negative", "shared", "shared_positive",
         "shared_negative", "shared_discordant_fib_negative", "inflammation_only", "inflammation_only_positive",
         "inflammation_only_negative"]


def barplot(ax, df, col, title):
    plot = df.set_index("Group").loc[ORDER].reset_index()
    plot["color"] = plot.Group.map(lambda g: next(c for k, c in COLORS.items() if g.startswith(k)))
    bg_pct = 100 * bg[col].mean()
    x = np.arange(len(plot))
    for xi, (_, r) in zip(x, plot.iterrows()):
        pct, lo, hi = r["Percentage"], r["Wilson_CI_low_%"], r["Wilson_CI_high_%"]
        a = 1.0 if r["Level"] == "class" else 0.55
        ax.bar(xi, pct, color=r["color"], alpha=a, edgecolor=r["color"])
        ax.errorbar(xi, pct, yerr=[[pct - lo], [hi - pct]], color="#1f2933", capsize=4, lw=1)
        ax.plot([xi - 0.4, xi + 0.4], [r["Degree-matched expected %"]] * 2, color="#1f2933", ls=":", lw=1.4)
        star = "*" if r["Perm_BH_FDR"] < 0.05 else ""
        ax.text(xi, hi + 0.6, f"{pct:.1f}%{star}", ha="center", fontsize=8.5)
    ax.axhline(bg_pct, color="#616e7c", ls="--", lw=1.2)
    ax.text(len(plot) - 0.5, bg_pct + 0.4, f"Background {bg_pct:.1f}%", ha="right", fontsize=9, color="#616e7c")
    ax.set_xticks(x, [LABEL[g] for g in plot.Group], fontsize=8.5)
    ax.set_ylabel("% genes drug-connected")
    ax.set_ylim(0, plot["Wilson_CI_high_%"].max() * 1.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")


results = {}
for key, d in DEFS.items():
    et = edges if key == "any" else pharm_edges
    df, pairs = analyse(d["col"], et)
    df.to_csv(OUT / f"druggability_summary{d['suffix']}.csv", index=False)
    pairs.to_csv(OUT / f"pairwise_class_comparisons{d['suffix']}.csv", index=False)
    results[key] = (df, pairs)

fig, axes = plt.subplots(2, 1, figsize=(13, 10.5))
barplot(axes[0], results["any"][0], "drug_connected", "A. Any drug link (all ACTS_ON actions)")
barplot(axes[1], results["pharm"][0], "pharm_connected",
        "B. Pharmacological target only (ENZYME / TRANSPORTER / CARRIER links removed)")
fig.text(0.07, 0.01, "Bars: observed % (error bars = 95% Wilson CI); light bars = direction sub-groups. Dotted line: expected % "
                     "for random background genes with the same network degree (1,000 permutations). "
                     "* = degree-matched permutation BH-FDR < 0.05.", fontsize=8.5, color="#616e7c")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT / "druggability_barplot.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# degree vs druggability in background (explains the study-bias warning)
deg_tab = bg.groupby("degree_bin").agg(genes=("ensembl_id", "size"), min_degree=("ppi_degree", "min"),
                                       max_degree=("ppi_degree", "max"), pct_any=("drug_connected", "mean"),
                                       pct_pharm=("pharm_connected", "mean"))
deg_tab[["pct_any", "pct_pharm"]] = (100 * deg_tab[["pct_any", "pct_pharm"]]).round(1)
deg_tab.to_csv(OUT / "background_degree_bins.csv")

# action mix per group (why definitions differ)
mix = edges.assign(pk=edges.Action_raw.isin(PK_ACTIONS)).groupby("paper1_group").agg(
    edges=("pk", "size"), pct_enzyme_transporter_carrier=("pk", "mean"))
mix["pct_enzyme_transporter_carrier"] = (100 * mix.pct_enzyme_transporter_carrier).round(1)
top_pk = (edges[edges.Action_raw.isin(PK_ACTIONS)].groupby(["paper1_group", "Gene"]).size()
          .sort_values(ascending=False).groupby(level=0).head(4).reset_index(name="n"))
mix["top enzyme/transporter genes"] = mix.index.map(
    lambda g: ", ".join(top_pk.loc[top_pk.paper1_group == g, "Gene"]))
mix.to_csv(OUT / "action_mix_by_group.csv")


# ------------------------------------------------------------------ summary.md
def fmt_p(p):
    return f"{p:.2e}" if p < 0.001 else f"{p:.3f}"


def md(df, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def pretty(df):
    s = df.copy()
    s["Genes"] = s["Total genes"].map("{:,}".format)
    s["Connected"] = s["Drug-connected genes"].map("{:,}".format)
    s["Drugs"] = s["Unique drugs"].map("{:,}".format)
    s["% (95% CI)"] = s.apply(lambda r: f"{r.Percentage:.1f} ({r['Wilson_CI_low_%']:.1f}–{r['Wilson_CI_high_%']:.1f})", axis=1)
    s["OR (95% CI)"] = s.apply(lambda r: f"{r['Odds ratio']:.2f} ({r.OR_CI_low:.2f}–{r.OR_CI_high:.2f})", axis=1)
    s["Fisher FDR"] = s.Fisher_BH_FDR.map(fmt_p)
    s["Matched exp. %"] = s["Degree-matched expected %"].map("{:.1f}".format)
    s["Fold vs matched"] = s["Fold vs degree-matched"].map("{:.2f}".format)
    s["Perm FDR"] = s.Perm_BH_FDR.map(fmt_p)
    return md(s, ["Group", "Genes", "Connected", "% (95% CI)", "Drugs", "OR (95% CI)", "Fisher FDR",
                  "Matched exp. %", "Fold vs matched", "Perm FDR"])


def pretty_pairs(p):
    p = p.copy()
    p["OR (95% CI)"] = p.apply(lambda r: f"{r['Odds ratio']:.2f} ({r.OR_CI_low:.2f}–{r.OR_CI_high:.2f})", axis=1)
    p["BH-FDR"] = p.BH_FDR.map(fmt_p)
    return md(p, ["Comparison", "%A", "%B", "OR (95% CI)", "BH-FDR"])


dt = deg_tab.reset_index()
dt["degree range"] = dt.apply(lambda r: f"{int(r.min_degree)}–{int(r.max_degree)}", axis=1)
mx = mix.reset_index()
bg_n = len(bg)
any_df, pharm_df = results["any"][0], results["pharm"][0]


def get(df, g, c):
    return df.set_index("Group").loc[g, c]


summary = f"""# Paper 2 — Task 3: druggability across progression-gene groups

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **{len(genes):,} genes**.
**Scope:** knowledge graph only (project scope decision). **Graph source:** {source}.
Script: `Paper2_Results/code/task3_druggability.py`.

![Task 3 diagram](Task3_diagram.png)

## Key findings (definition B, pharmacological targets)
1. **Fibrosis-associated genes are over-represented among drug targets**: {get(pharm_df, 'Fibrosis-associated (fibrosis-only + shared)', 'Percentage'):.1f}% vs {100 * bg.pharm_connected.mean():.1f}% background (fold {get(pharm_df, 'Fibrosis-associated (fibrosis-only + shared)', 'Fold vs degree-matched'):.2f} vs degree-matched; permutation FDR {fmt_p(get(pharm_df, 'Fibrosis-associated (fibrosis-only + shared)', 'Perm_BH_FDR'))}). This holds beyond network connectivity.
2. **Inflammation-only genes are not**: {get(pharm_df, 'inflammation_only', 'Percentage'):.1f}% (fold {get(pharm_df, 'inflammation_only', 'Fold vs degree-matched'):.2f}; FDR {fmt_p(get(pharm_df, 'inflammation_only', 'Perm_BH_FDR'))}). Fibrosis-only and shared genes are each more druggable than inflammation-only genes (pairwise FDR {fmt_p(results['pharm'][1].BH_FDR.iloc[0])} and {fmt_p(results['pharm'][1].BH_FDR.iloc[1])}).
3. **The excess comes mainly from genes that FALL with fibrosis**: shared ⬇⬇ {get(pharm_df, 'shared_negative', 'Percentage'):.1f}% (fold {get(pharm_df, 'shared_negative', 'Fold vs degree-matched'):.2f}) and fibrosis-only ⬇ {get(pharm_df, 'fibrosis_only_negative', 'Percentage'):.1f}% (fold {get(pharm_df, 'fibrosis_only_negative', 'Fold vs degree-matched'):.2f}). Rising fibrosis-only genes are at background ({get(pharm_df, 'fibrosis_only_positive', 'Percentage'):.1f}%), and rising shared genes are modestly enriched ({get(pharm_df, 'shared_positive', 'Percentage'):.1f}%, fold {get(pharm_df, 'shared_positive', 'Fold vs degree-matched'):.2f}).
4. **Removing ENZYME/TRANSPORTER/CARRIER links does not change these conclusions** (compare A and B), although it removes many liver drug-metabolism genes (CYPs, ABC/SLC transporters) from the falling groups.
5. **Repurposing implication**: falling genes would need drugs that *raise* their activity (agonists/activators), which are rarer in the graph than inhibitors. This is examined in Task 7.

## Background used
`data/expression_analysis_core` is **not present** in this checkout, so the background is the **{bg_n:,} eligible genes** (all-eight-study analysis universe) in `Paper1_HighConfidence/10_loso_all_eligible_runs.csv`. All 6,222 progression genes lie inside it. Drug flags for progression genes match Task 2 exactly.

## Two definitions of "drug-connected"
- **A. Any drug**: ≥1 `Drug-[:ACTS_ON]->Gene` line. Background: {int(bg.drug_connected.sum()):,} / {bg_n:,} ({100 * bg.drug_connected.mean():.1f}%).
- **B. Pharmacological target**: ≥1 line whose action is **not** ENZYME, TRANSPORTER or CARRIER. Background: {int(bg.pharm_connected.sum()):,} / {bg_n:,} ({100 * bg.pharm_connected.mean():.1f}%).

Why B is needed: ENZYME/TRANSPORTER/CARRIER lines mostly say the gene **metabolises or moves the drug** (e.g. CYP1A2, CYP2C19, CYP2E1, ABCG2). They do not say the drug acts *on* the gene to change disease biology. Genes that **fall** with fibrosis include many such liver drug-metabolism genes:

{md(mx, ["paper1_group", "edges", "pct_enzyme_transporter_carrier", "top enzyme/transporter genes"])}

**Definition B is the one to use for repurposing.** A is reported for completeness and comparison with the plan.

## A. Any drug link

{pretty(any_df)}

Pairwise class comparisons (Fisher, BH-FDR):

{pretty_pairs(results["any"][1])}

## B. Pharmacological target only (recommended)

{pretty(pharm_df)}

Pairwise class comparisons (Fisher, BH-FDR):

{pretty_pairs(results["pharm"][1])}

![Bar plot](druggability_barplot.png)

**Column guide:** % = observed drug-connected fraction (95% Wilson CI). OR/Fisher = group vs rest of background (2×2 Fisher's exact; conditional MLE odds ratio), BH-FDR across the {len(any_df)} groups. Matched exp. % = mean of {N_PERM:,} random background gene sets with the same INTERACTS_WITH degree profile ({N_DEGREE_BINS} deciles + a degree-0 bin, seed {SEED}). Perm FDR = two-sided empirical p, BH across groups.

## Why degree matters (study bias)
Background genes with more known protein–protein interactions are more likely to have a known drug:

{md(dt, ["degree_bin", "genes", "degree range", "pct_any", "pct_pharm"])}

A raw difference can therefore just mean "better-studied genes". The degree-matched permutation removes this: a group counts as more or less druggable **beyond connectivity** only if its observed % lies outside its degree-matched null.

## Interpretation and caveats
- Percentages describe **representation among known drug targets in the knowledge graph**. They partly reflect which genes scientists have studied and drugged (DrugBank/Open Targets annotation bias), not biology alone.
- Druggability is not therapeutic relevance. A drug-connected gene is a *repurposing hypothesis entry point*, not evidence a drug would help.
- Groups are kept separate as in Paper 1. The 30 shared genes with discordant direction are reported on their own and are small (wide CIs).
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
