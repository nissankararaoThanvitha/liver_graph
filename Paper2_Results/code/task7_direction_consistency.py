"""Paper 2 Task 7: drug action vs. gene progression direction (knowledge-graph labels only).

For every drug-gene link from Task 2, compare the knowledge-graph action label with the
Paper 1 direction of the gene:

    gene rises with fibrosis (positive)  + drug pushes down  -> direction-consistent
    gene rises                           + drug pushes up    -> direction-inconsistent
    gene falls (negative)                + drug pushes up    -> direction-consistent
    gene falls                           + drug pushes down  -> direction-inconsistent
    mixed action, or shared gene whose fibrosis and inflammation
    directions disagree, or gene direction disagrees with its
    F0-F4 trajectory cluster                                 -> ambiguous
    unknown action (TARGET / ENZYME / TRANSPORTER / CARRIER)  -> unknown

Gene direction = fibrosis direction for fibrosis-associated genes, inflammation direction
for inflammation-only genes. Direction-consistency is a repurposing hypothesis, not proof
that a drug would help.

    python Paper2_Results/code/task7_direction_consistency.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results" / "Task7"
OUT.mkdir(parents=True, exist_ok=True)

EDGES = ROOT / "Paper2_Results/Task2/drug_gene_edges.csv"
GENES = ROOT / "Paper2_Results/Task1/Paper2_progression_genes.csv"
CAND = ROOT / "Paper2_Results/Task4/repurposing_candidates.csv"
MECH = ROOT / "Paper2_Results/Task4/repurposing_candidates_mechanism_annotated.csv"
CLUSTER_MEANS = ROOT / "Paper1_Results/Task2/task2_cluster_sizes.csv"

PK = ["ENZYME", "TRANSPORTER", "CARRIER"]
ORDER = ["direction-consistent", "direction-inconsistent", "ambiguous", "unknown"]

e = pd.read_csv(EDGES)
genes = pd.read_csv(GENES).set_index("ensembl_id")
cand = set(pd.read_csv(CAND).Drug_ID)
mech = set(pd.read_csv(MECH).Drug_ID)

# cluster direction from Paper 1 cluster means (F4 vs F0)
cm = pd.read_csv(CLUSTER_MEANS, encoding="utf-8-sig")
cluster_dir = {f"C{r.cluster}": ("positive" if r.mean_F4 > r.mean_F0 else "negative") for r in cm.itertuples()}

g = genes.reindex(e.Gene_ID)
e["gene_direction"] = np.where(g.progression_class.values == "inflammation_only",
                               g.inflammation_direction.values, g.fibrosis_direction.values)
e["discordant_shared"] = (g.paper1_group.str.startswith("shared_discordant")).values
e["cluster_direction"] = e.cluster.map(cluster_dir)
e["cluster_conflict"] = e.cluster_direction.notna() & (e.cluster_direction != e.gene_direction)


def classify(r):
    if r.Action_direction == "unknown":
        return "unknown"
    if r.Action_direction == "mixed" or r.discordant_shared or r.cluster_conflict:
        return "ambiguous"
    rising = r.gene_direction == "positive"
    if (rising and r.Action_direction == "down") or (not rising and r.Action_direction == "up"):
        return "direction-consistent"
    return "direction-inconsistent"


e["Consistency"] = e.apply(classify, axis=1)
e["pharmacological_link"] = ~e.Action_raw.isin(PK)
e["repurposing_candidate"] = e.Drug_ID.isin(cand)
e["main_list"] = e.Drug_ID.isin(mech)

out = pd.DataFrame({
    "Drug": e.Drug, "Drug_ID": e.Drug_ID, "Gene": e.Gene, "Gene_ID": e.Gene_ID,
    "Gene progression direction": e.gene_direction.map({"positive": "rises (positive)", "negative": "falls (negative)"}),
    "Paper 1 group": e.paper1_group, "cluster": e.cluster, "cluster direction": e.cluster_direction,
    "Drug action": e.Action_raw, "Action class": e.Action_direction,
    "Evidence source": e.Evidence_source, "Evidence level": e.evidence_level,
    "mechanism_of_action": e.mechanism_of_action, "Consistency": e.Consistency,
    "is_approved": e.is_approved, "max_phase": e.max_phase,
    "repurposing candidate (Task 4)": e.repurposing_candidate, "main list (Task 4)": e.main_list,
    "pharmacological_link": e.pharmacological_link, "in_shortlist": e.in_shortlist,
})
out.sort_values(["Consistency", "Drug", "Gene"]).to_csv(OUT / "drug_action_evidence.csv", index=False)

# ------------------------------------------------------------------ summaries
n = len(e)
known = e.Action_direction.isin(["up", "down"])
known_tab = pd.DataFrame({
    "Links": ["all drug–gene links", "pharmacological links only"],
    "total": [n, int(e.pharmacological_link.sum())],
    "known direction (down/up)": [int(known.sum()), int((known & e.pharmacological_link).sum())],
    "mixed": [int((e.Action_direction == "mixed").sum()), int(((e.Action_direction == "mixed") & e.pharmacological_link).sum())],
    "unknown": [int((e.Action_direction == "unknown").sum()), int(((e.Action_direction == "unknown") & e.pharmacological_link).sum())],
})
known_tab["% unknown"] = (100 * known_tab.unknown / known_tab.total).round(1)
known_tab.to_csv(OUT / "summary_known_vs_unknown.csv", index=False)
pct_unknown_all = float(known_tab.loc[0, "% unknown"])


def ctab(by):
    t = pd.crosstab(e[by], e.Consistency).reindex(columns=ORDER, fill_value=0)
    t["total"] = t.sum(axis=1)
    decided = t["direction-consistent"] + t["direction-inconsistent"]
    t["% consistent among decided"] = np.where(decided > 0, (100 * t["direction-consistent"] / decided.replace(0, np.nan)).round(1), np.nan)
    return t


GROUP_ORDER = ["fibrosis_only_positive", "fibrosis_only_negative", "shared_positive", "shared_negative",
               "shared_discordant_fib_negative", "inflammation_only_positive", "inflammation_only_negative"]
by_group = ctab("paper1_group").reindex(GROUP_ORDER)
by_group.to_csv(OUT / "consistency_by_paper1_group.csv")
by_cluster = ctab("cluster").reindex(["C1", "C2", "C3", "C4", "C5"])
by_cluster.insert(0, "cluster direction", by_cluster.index.map(cluster_dir))
by_cluster.to_csv(OUT / "consistency_by_cluster.csv")

# per-drug summary
d = e.groupby("Drug_ID").agg(
    Drug=("Drug", "first"), max_phase=("max_phase", "first"), is_approved=("is_approved", "first"),
    repurposing_candidate=("repurposing_candidate", "first"), main_list=("main_list", "first"),
    n_links=("Gene_ID", "size"),
    n_consistent=("Consistency", lambda s: (s == "direction-consistent").sum()),
    n_inconsistent=("Consistency", lambda s: (s == "direction-inconsistent").sum()),
    n_ambiguous=("Consistency", lambda s: (s == "ambiguous").sum()),
    n_unknown=("Consistency", lambda s: (s == "unknown").sum()))
fibmask = e.paper1_group.str.startswith(("fibrosis_only", "shared"))
d["n_consistent_fibrosis_genes"] = e[fibmask & (e.Consistency == "direction-consistent")].groupby("Drug_ID").Gene_ID.nunique()
d["consistent_genes"] = e[e.Consistency == "direction-consistent"].groupby("Drug_ID").Gene.agg(lambda s: ";".join(sorted(set(s))))
d["inconsistent_genes"] = e[e.Consistency == "direction-inconsistent"].groupby("Drug_ID").Gene.agg(lambda s: ";".join(sorted(set(s))))
d["n_consistent_fibrosis_genes"] = d.n_consistent_fibrosis_genes.fillna(0).astype(int)


def pattern(r):
    if r.n_consistent and not r.n_inconsistent:
        return "only consistent"
    if r.n_consistent and r.n_inconsistent:
        return "mixed (consistent + inconsistent)"
    if r.n_inconsistent:
        return "only inconsistent"
    return "no decided link"


d["direction_pattern"] = d.apply(pattern, axis=1)
d = d.sort_values(["n_consistent_fibrosis_genes", "n_consistent", "n_inconsistent"], ascending=[False, False, True])
d.to_csv(OUT / "drug_direction_summary.csv")

cand_d = d[d.repurposing_candidate]
mech_d = d[d.main_list]
cand_tab = pd.DataFrame({
    "Set": [f"Repurposing candidates (Task 4, n={len(cand):,})", f"Main list (mechanism-annotated, n={len(mech)})"],
    "≥1 direction-consistent link": [int((cand_d.n_consistent > 0).sum()), int((mech_d.n_consistent > 0).sum())],
    "only consistent": [int((cand_d.direction_pattern == "only consistent").sum()), int((mech_d.direction_pattern == "only consistent").sum())],
    "mixed": [int((cand_d.direction_pattern == "mixed (consistent + inconsistent)").sum()),
              int((mech_d.direction_pattern == "mixed (consistent + inconsistent)").sum())],
    "only inconsistent": [int((cand_d.direction_pattern == "only inconsistent").sum()), int((mech_d.direction_pattern == "only inconsistent").sum())],
    "no decided link": [int((cand_d.direction_pattern == "no decided link").sum()), int((mech_d.direction_pattern == "no decided link").sum())],
})
cand_tab.to_csv(OUT / "candidates_direction_summary.csv", index=False)

# is the action–direction pairing different from chance? (descriptive; graph does not "know" fibrosis)
dec = e[known & ~e.discordant_shared & ~e.cluster_conflict]
tab = pd.crosstab(dec.gene_direction, dec.Action_direction).reindex(index=["positive", "negative"], columns=["down", "up"])
orr, pval = fisher_exact(tab.values)
exp_cons = (tab.loc["positive", "down"] + tab.loc["negative", "up"])
p_rise = tab.loc["positive"].sum() / tab.values.sum()
p_down = tab["down"].sum() / tab.values.sum()
expected = (p_rise * p_down + (1 - p_rise) * (1 - p_down)) * tab.values.sum()


# ------------------------------------------------------------------ summary.md
def md(df, idx=True):
    x = df.reset_index() if idx else df
    lines = ["| " + " | ".join(map(str, x.columns)) + " |", "|" + "---|" * x.shape[1]]
    lines += ["| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else
                                (f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)) for v in row) + " |" for row in x.values]
    return "\n".join(lines)


tot = e.Consistency.value_counts().reindex(ORDER).fillna(0).astype(int)
show = d[d.main_list & (d.n_consistent_fibrosis_genes > 0)].head(15)[
    ["Drug", "max_phase", "n_consistent_fibrosis_genes", "n_consistent", "n_inconsistent", "direction_pattern", "consistent_genes", "inconsistent_genes"]]
ppar = d[d.Drug.isin(["INDEGLITAZAR", "TESAGLITAZAR", "MURAGLITAZAR", "GW501516", "FENOFIBRIC ACID", "ALEGLITAZAR"])][
    ["Drug", "n_consistent", "n_inconsistent", "consistent_genes", "inconsistent_genes"]]
pdg = out[(out.Gene == "PDGFRA") & out["repurposing candidate (Task 4)"]][["Drug", "Drug action", "Consistency"]]

summary = f"""# Paper 2 — Task 7: drug action vs. progression direction

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **{len(genes):,} genes**.
**Scope:** knowledge-graph action labels only (project scope decision: repurposing, not reversal; no external data). Input: all {n:,} Task 2 drug–gene links.
Script: `Paper2_Results/code/task7_direction_consistency.py`.

> **Direction-consistency is a repurposing hypothesis, not proof.** A drug that lowers a gene which rises with fibrosis is *mechanistically interesting*. That alone does not show the drug is anti-fibrotic: the gene may be a consequence rather than a driver, the effect may be tissue- or dose-dependent, and the graph label says nothing about liver exposure.

![Task 7 diagram](Task7_diagram.png)

## Rules
| Gene direction (Paper 1) | Drug pushes ⬇ | Drug pushes ⬆ |
|---|---|---|
| rises with fibrosis (positive) | **direction-consistent** | direction-inconsistent |
| falls with fibrosis (negative) | direction-inconsistent | **direction-consistent** |

**Ambiguous** = mixed action (modulator, binding agent …), or a shared gene whose fibrosis and inflammation directions disagree, or a gene whose direction disagrees with its F0–F4 cluster. **Unknown** = action TARGET / ENZYME / TRANSPORTER / CARRIER.
Gene direction = fibrosis direction for fibrosis-associated genes, inflammation direction for inflammation-only genes. Cluster directions (F4 vs F0 mean): {", ".join(f"{k} {v}" for k, v in cluster_dir.items())}.

## 1. Known vs. unknown action
{md(known_tab, idx=False)}

**Limitation: {pct_unknown_all}% of drug–gene links in the graph have unknown direction.** Consistency can only be judged for the remaining links; the rest stay "unknown", not "inconsistent".

Overall: {", ".join(f"{k} {v:,}" for k, v in tot.items())}.

## 2. Consistency by Paper 1 group
{md(by_group)}

## 3. Consistency by F0–F4 trajectory cluster
{md(by_cluster)}

## 4. Repurposing candidates with ≥1 direction-consistent link
{md(cand_tab, idx=False)}

**{int((cand_d.n_consistent > 0).sum()):,} of {len(cand):,} repurposing candidates** have at least one direction-consistent link ({int((mech_d.n_consistent > 0).sum())} of {len(mech)} on the main list). Per-drug detail: `drug_direction_summary.csv`.

### Main-list drugs with the most direction-consistent fibrosis-gene links (NOT a ranking)
{md(show.reset_index(drop=True), idx=False)}

### Checks on earlier examples
- **PPAR agonists (Task 5, Example 1):**

{md(ppar.reset_index(drop=True), idx=False)}

  PPARA falls with fibrosis and is activated (consistent). PPARG/PPARD rise and are also activated (inconsistent). These drugs are **mixed**, as flagged in Task 5.
- **PDGFRA (Task 5, Example 3):** {"; ".join(f"{r.Drug}: {r['Drug action']} → {r.Consistency}" for _, r in pdg.iterrows())}.

## 5. Is the pairing different from chance? (descriptive)
Among decided links (known direction, unambiguous gene): {int(tab.values.sum()):,} links, {int(exp_cons):,} direction-consistent vs. {expected:.0f} expected if drug action were independent of gene direction (Fisher OR {orr:.2f}, p = {pval:.2g}).
So known drug actions are slightly **less** often direction-consistent than chance. The main reason is visible in section 2: genes that **fall** with fibrosis mostly have *inhibitors* in the graph (fibrosis-only ⬇ {by_group.loc['fibrosis_only_negative', '% consistent among decided']:.0f}% consistent, shared ⬇⬇ {by_group.loc['shared_negative', '% consistent among decided']:.0f}%, cluster C4 {by_cluster.loc['C4', '% consistent among decided']:.0f}%), while rising fibrosis-only genes are mostly inhibited, which is consistent ({by_group.loc['fibrosis_only_positive', '% consistent among decided']:.0f}%). This matches the Task 3 warning: falling genes would need activators, and few exist. The graph contains no fibrosis information, so this pattern says which drugs exist, not whether they would work.

## Files
`drug_action_evidence.csv` (one row per link, all requested columns), `summary_known_vs_unknown.csv`, `consistency_by_paper1_group.csv`, `consistency_by_cluster.csv`, `candidates_direction_summary.csv`, `drug_direction_summary.csv` (per drug, for the later DrugScore).
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
