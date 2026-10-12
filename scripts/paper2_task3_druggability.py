"""
paper2_task3_druggability.py
----------------------------
Paper 2, Task 3: is druggability different across the progression groups?

WHAT THE PLAN ASKS FOR
"Compare fibrosis-only, inflammation-only, and shared genes. Also examine
positive and negative progression associations separately. For each group
calculate: Drug-connected genes / Total genes x 100... Add an
enrichment/significance analysis comparing observed drug-connected genes with
an appropriate Paper 1-derived eligible-gene background. Report effect size and
BH-FDR in addition to percentages. Where feasible, use a degree-aware
permutation/null model to determine whether the observed overlap exceeds that
expected from network connectivity alone."

And, emphatically: "Do not collapse them into a single 'progression' category."

THE BACKGROUND
The 14,794 genes eligible for cross-study analysis -- the same background
Paper 1's enrichment used, and the one CLAUDE.md names for LOSO. All 6,222
progression genes sit inside it, so the comparison set is the 8,572 eligible
genes that are NOT progression genes. Using all ~20,000 human genes instead
would inflate every result, because a gene absent from these cohorts has no
chance of being called progression-associated in the first place.

TWO DRUGGABILITY FIGURES, NOT ONE
Task 2 established that 44% of drug-gene edges are pharmacokinetic: the gene
product metabolises or transports the drug rather than being targeted by it. In
a liver study that is systematic, not noise -- the cytochromes live here and
their expression genuinely moves as the liver fails. A druggability percentage
computed over all edges is partly measuring liver drug metabolism.

So both are reported, and the THERAPEUTIC one is primary.

WHY A PLAIN FISHER TEST IS NOT ENOUGH
Progression genes are, on average, better studied than other genes, and
better-studied genes have more of every kind of edge including drug edges. A
significant Fisher test could therefore reflect attention rather than biology.
The degree-aware null controls for that: each group is compared against
background genes matched on NON-DRUG degree (ASSOCIATED_WITH, INTERACTS_WITH,
INVOLVED_IN, IN_PATHWAY). Drug edges are excluded from the matching so the
null is not conditioned on the outcome being tested.

EXPECTED RESULT
Team 1 measured 18.4 / 18.6 / 16.4 per cent on the pre-correction gene set and
flagged it as a null result in advance. A two-point spread at these n will not
survive a degree-aware test. The plan should not depend on a difference
appearing.

Usage:
    uv run --with neo4j --with pandas --with numpy --with scipy python scripts/paper2_task3_druggability.py
"""

import json
import os

import numpy as np
import sys

import pandas as pd
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables
from scipy import stats

MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
UNIVERSE = "data/progression_full/progression_fibrosis.csv"
OUT_DIR = "Paper2_Results/Task3"
SEED = 42
N_PERM = 2000
PHARMACOKINETIC = {"ENZYME", "TRANSPORTER", "CARRIER", "SUBSTRATE"}


def driver():
    cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
    for scope in cfg.get("projects", {}).values():
        srv = (scope.get("mcpServers") or {}).get("neo4j")
        if srv:
            env = srv["env"]
            return (GraphDatabase.driver(env["NEO4J_URI"],
                                         auth=(env["NEO4J_USERNAME"],
                                               env["NEO4J_PASSWORD"])),
                    env.get("NEO4J_DATABASE", "neo4j"))
    raise SystemExit("no neo4j MCP config found")


def fetch(genes):
    """Drug connectivity and non-drug degree for every eligible gene."""
    drv, db = driver()
    with drv.session(database=db) as s:
        drugs = pd.DataFrame(s.run("""
            MATCH (dr:Drug)-[a:ACTS_ON]->(g:Gene)
            WHERE g.ensembl_id IN $genes
            RETURN g.ensembl_id AS Ensembl_ID, dr.node_id AS drug,
                   a.action AS action
        """, genes=genes).data())
        degree = pd.DataFrame(s.run("""
            MATCH (g:Gene) WHERE g.ensembl_id IN $genes
            OPTIONAL MATCH (g)-[r:ASSOCIATED_WITH|INTERACTS_WITH|INVOLVED_IN|IN_PATHWAY]-()
            RETURN g.ensembl_id AS Ensembl_ID, count(r) AS nondrug_degree
        """, genes=genes).data())
    drv.close()
    return drugs, degree


def group_of(row):
    """Group label. The master table calls the shared class "both"; the plan
    and every table here call it "shared", so it is renamed once, at the single
    point where the label is made, rather than in each consumer."""
    cls = row.progression_class
    if cls == "fibrosis-only":
        d = row.fibrosis_direction
    elif cls == "inflammation-only":
        d = row.inflammation_direction
    else:
        cls = "shared"
        f, i = row.fibrosis_direction, row.inflammation_direction
        if f != i:
            return "shared / discordant"
        d = f
    return f"{cls} / {'positive' if d == 'increasing' else 'negative'}"


def degree_matched_null(group_ids, pool, rng, n_perm=N_PERM):
    """Fraction drug-connected in degree-matched background draws.

    Background genes are binned by non-drug degree; for each group gene a
    replacement is drawn from its own bin, so the draw has the same
    connectivity profile as the group and differs only in not being
    progression-associated.
    """
    bins = pool.groupby("degree_bin").Ensembl_ID.apply(list).to_dict()
    conn = pool.set_index("Ensembl_ID").drug_connected.to_dict()
    wanted = group_ids.degree_bin.value_counts().to_dict()

    out = np.empty(n_perm)
    for i in range(n_perm):
        hits = total = 0
        for b, k in wanted.items():
            avail = bins.get(b)
            if not avail:
                continue
            pick = rng.choice(avail, size=min(k, len(avail)), replace=False)
            hits += sum(conn[g] for g in pick)
            total += len(pick)
        out[i] = hits / total if total else np.nan
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task3")
    rng = np.random.default_rng(SEED)

    master = pd.read_csv(MASTER)
    universe = pd.read_csv(UNIVERSE)[["ensembl_id", "symbol"]].rename(
        columns={"ensembl_id": "Ensembl_ID", "symbol": "Gene"})
    print(f"eligible background: {len(universe):,} genes")
    assert master.Ensembl_ID.isin(universe.Ensembl_ID).all(), \
        "a progression gene is outside the eligible background"

    drugs, degree = fetch(universe.Ensembl_ID.tolist())
    drugs["therapeutic"] = ~drugs.action.isin(PHARMACOKINETIC)

    per_gene = (drugs.groupby("Ensembl_ID")
                     .agg(drugs_all=("drug", "nunique"),
                          drugs_therapeutic=("drug",
                                             lambda s: s[drugs.loc[s.index, "therapeutic"]].nunique()))
                     .reset_index())

    g = (universe.merge(per_gene, on="Ensembl_ID", how="left")
                 .merge(degree, on="Ensembl_ID", how="left")
                 .fillna({"drugs_all": 0, "drugs_therapeutic": 0,
                          "nondrug_degree": 0}))
    g["drug_connected_all"] = g.drugs_all > 0
    g["drug_connected"] = g.drugs_therapeutic > 0      # primary definition

    m = master[["Ensembl_ID", "progression_class", "fibrosis_direction",
                "inflammation_direction"]].copy()
    m["group"] = m.apply(group_of, axis=1)
    g = g.merge(m[["Ensembl_ID", "progression_class", "group"]],
                on="Ensembl_ID", how="left")
    g["progression_class"] = g.progression_class.fillna("NOT progression")
    g["group"] = g.group.fillna("NOT progression (background)")

    # Degree bins, quantile-based so every bin is populated.
    g["degree_bin"] = pd.qcut(g.nondrug_degree.rank(method="first"), 20,
                              labels=False)
    pool = g[g.progression_class == "NOT progression"]
    print(f"comparison set (eligible, not progression): {len(pool):,} genes")
    print(f"background drug-connected (therapeutic): "
          f"{100*pool.drug_connected.mean():.1f}%\n")

    # ---- the summary table the plan asks for ------------------------------
    rows = []
    order = (["fibrosis-only / positive", "fibrosis-only / negative",
              "inflammation-only / positive", "inflammation-only / negative",
              "shared / positive", "shared / negative", "shared / discordant"])
    for grp in order + ["NOT progression (background)"]:
        sub = g[g.group == grp]
        if not len(sub):
            continue
        ids = set(sub.Ensembl_ID)
        rows.append({
            "group": grp,
            "total_genes": len(sub),
            "drug_connected_genes": int(sub.drug_connected.sum()),
            "percent": round(100 * sub.drug_connected.mean(), 1),
            "unique_drugs": drugs[drugs.Ensembl_ID.isin(ids)
                                  & drugs.therapeutic].drug.nunique(),
            "drug_connected_ALL_edges": int(sub.drug_connected_all.sum()),
            "percent_ALL_edges": round(100 * sub.drug_connected_all.mean(), 1),
            "median_nondrug_degree": int(sub.nondrug_degree.median()),
        })
    # the three classes, undivided
    for cls in ["fibrosis-only", "inflammation-only", "both"]:
        sub = g[g.progression_class == cls]
        ids = set(sub.Ensembl_ID)
        rows.append({
            "group": f"[class] {cls}", "total_genes": len(sub),
            "drug_connected_genes": int(sub.drug_connected.sum()),
            "percent": round(100 * sub.drug_connected.mean(), 1),
            "unique_drugs": drugs[drugs.Ensembl_ID.isin(ids)
                                  & drugs.therapeutic].drug.nunique(),
            "drug_connected_ALL_edges": int(sub.drug_connected_all.sum()),
            "percent_ALL_edges": round(100 * sub.drug_connected_all.mean(), 1),
            "median_nondrug_degree": int(sub.nondrug_degree.median()),
        })
    summary = pd.DataFrame(rows)

    # Every progression gene must land in exactly one named group. A label that
    # no consumer asks for would otherwise drop its genes silently -- which is
    # how 1,792 shared genes went missing from an earlier run of this table.
    named = set(order) | {"NOT progression (background)"}
    missing = set(g.group.unique()) - named
    assert not missing, f"group label produced but never reported: {missing}"
    counted = summary[summary.group.isin(order)].total_genes.sum()
    assert counted == len(master), \
        f"groups cover {counted:,} genes, master table has {len(master):,}"

    # ---- Fisher vs the background, then the degree-aware null -------------
    bg_hit = int(pool.drug_connected.sum())
    bg_n = len(pool)
    tests = []
    for grp in order + ["[class] fibrosis-only", "[class] inflammation-only",
                        "[class] both"]:
        sub = (g[g.progression_class == grp.replace("[class] ", "")]
               if grp.startswith("[class]") else g[g.group == grp])
        if not len(sub):
            continue
        hit, n = int(sub.drug_connected.sum()), len(sub)
        table = [[hit, n - hit], [bg_hit, bg_n - bg_hit]]
        odds, p = stats.fisher_exact(table)
        null = degree_matched_null(sub, pool, rng)
        obs = hit / n
        p_perm = (np.abs(null - np.nanmean(null)) >=
                  abs(obs - np.nanmean(null))).mean()
        tests.append({
            "group": grp, "genes": n, "drug_connected": hit,
            "percent": round(100 * obs, 1),
            "background_percent": round(100 * bg_hit / bg_n, 1),
            "odds_ratio": round(float(odds), 3),
            "fisher_p": p,
            "degree_matched_null_percent": round(100 * float(np.nanmean(null)), 1),
            "degree_matched_p": round(float(p_perm), 4),
        })
    t = pd.DataFrame(tests)
    t["fisher_q_BH"] = stats.false_discovery_control(t.fisher_p.values)
    t["fisher_p"] = t.fisher_p.map(lambda v: f"{v:.3e}")
    t["fisher_q_BH"] = t.fisher_q_BH.map(lambda v: f"{v:.3e}")
    t["survives_degree_aware"] = np.where(t.degree_matched_p < 0.05, "yes", "no")

    # ---- confound: is this just the classically druggable protein families? -
    # The degree-aware null controls for how connected a gene is, not for what
    # kind of gene it is. The decreasing groups turn out to be led by ADRA1A,
    # HTR2A, ESR1, AR, DRD1, MAOA/B -- receptors and monoamine enzymes that
    # attract drug annotation for reasons that have nothing to do with liver.
    # If the effect is theirs, removing those families should remove it.
    CLASSIC = (r"^(ADR|HTR|DRD|CHRM|CHRN|GRIN|GRIA|GABR|OPR|HRH|TAAR|P2RX|"
               r"P2RY|SCN|KCN|CACN|TRP|SLC|ABC|CYP|UGT|ALDH|ADH|MAO|CA[0-9]|"
               r"ESR|AR$|NR[0-9]|PPAR|RXR|VDR|THR)")
    g["classic_druggable"] = g.Gene.fillna("").str.match(CLASSIC)
    bg_ex = pool[~pool.Gene.fillna("").str.match(CLASSIC)]
    rows_ex = []
    for grp in order:
        sub = g[(g.group == grp) & (~g.classic_druggable)]
        if not len(sub):
            continue
        hit, n = int(sub.drug_connected.sum()), len(sub)
        odds, p = stats.fisher_exact(
            [[hit, n - hit],
             [int(bg_ex.drug_connected.sum()),
              len(bg_ex) - int(bg_ex.drug_connected.sum())]])
        rows_ex.append({
            "group": grp,
            "percent_all_genes": round(100 * g[g.group == grp].drug_connected.mean(), 1),
            "genes_excluding_classic": n,
            "percent_excluding_classic": round(100 * hit / n, 1),
            "background_excluding_classic":
                round(100 * bg_ex.drug_connected.mean(), 1),
            "odds_ratio": round(float(odds), 3),
            "fisher_p": f"{p:.3e}",
        })
    sup.add("classic_druggable_sensitivity", pd.DataFrame(rows_ex))
    sup.write()

    summary.to_csv(f"{OUT_DIR}/task3_druggability_summary.csv", index=False)
    t.to_csv(f"{OUT_DIR}/task3_enrichment_tests.csv", index=False)

    print(summary.to_string(index=False))
    print()
    print(t[["group", "genes", "percent", "background_percent", "odds_ratio",
             "fisher_q_BH", "degree_matched_null_percent", "degree_matched_p",
             "survives_degree_aware"]].to_string(index=False))
    print(f"\nwrote {OUT_DIR}/task3_druggability_summary.csv")
    print(f"wrote {OUT_DIR}/task3_enrichment_tests.csv")


if __name__ == "__main__":
    main()
