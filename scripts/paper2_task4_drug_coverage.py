"""
paper2_task4_drug_coverage.py
-----------------------------
Paper 2, Task 4: which drugs reach many progression genes, and do they reach a
coherent programme or just a lot of unrelated genes?

WHAT THE PLAN ASKS FOR
"For each drug calculate the number of progression-associated genes to which it
is connected... In addition to raw coverage, calculate coverage separately for
Paper 1 fibrosis-only positive, fibrosis-only negative, shared positive, shared
negative, and important F0-F4 trajectory clusters. This will reveal whether a
drug covers a coherent progression program or merely many unrelated genes."

And, twice over: "This is candidate generation only. Do not describe a
high-degree drug as the best therapeutic candidate."

THE SPECIFICITY MEASURE IS A TRAP IF USED NAIVELY
The plan asks for progression-target fraction = progression targets / all known
targets, "as a supporting feature and not as a standalone therapeutic score".
That caveat is doing a lot of work. In this graph 1,872 of 4,212 drugs with any
target have exactly ONE, so every single-target drug whose one target happens to
be a progression gene scores a perfect 1.0 and outranks a well-characterised
inhibitor with ten targets of which six are progression genes.

So the fraction is reported for every drug, and a Wilson lower bound is reported
beside it. The lower bound penalises small denominators the way the raw fraction
does not: 1/1 gives 0.21, while 6/10 gives 0.31. Ranking uses the bound; the raw
fraction is kept because the plan asks for it.

COHERENCE, NOT JUST COUNT
A drug hitting eight genes that all rise late in fibrosis is a different object
from a drug hitting eight unrelated genes. Two measures are computed per drug:

  dominant_class_fraction      largest share of its progression targets falling
                               in one class x direction group
  dominant_cluster_fraction    same for the F0-F4 trajectory clusters

Neither is a therapeutic score. They separate "covers a programme" from "covers
a lot".

THE DRUG VOCABULARY IS NOT ALL MEDICINES
Top raw coverage is led by promiscuous kinase inhibitors, mineral salts and
nutrients -- in Task 3 the most drug-connected entities included zinc chloride,
calcium citrate, glutamic acid, ATP and ALCOHOL. Team 1's handover says to
filter on molecule type and clinical phase before any coverage ranking.

THE GRAPH CANNOT DO THAT. Drug nodes carry exactly two properties, node_id and
name: there is no molecule type, no clinical phase, no modality. So the filter
is a name-based heuristic over salts, elements, vitamins and simple metabolites,
it is certainly incomplete, and it FLAGS rather than deletes -- every drug stays
in the table with a `likely_non_therapeutic` column so the judgement is visible
and reversible. Doing this properly needs ChEMBL molecule metadata, which is
not in this project.

Usage:
    uv run --with neo4j --with pandas --with numpy --with scipy --with openpyxl python scripts/paper2_task4_drug_coverage.py
"""

import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables
from paper2_drug_filters import is_inorganic, flag_entities

EDGES = "Paper2_Results/Task2/task2_drug_gene_edges.csv"
# Paper 1's COMPLETE significant enrichment results. Its
# task4_top_pathways_per_group.csv keeps only the leading terms per group
# (456 rows of 3,945), so a gene enriched only under a lower-ranked term
# would read as having no significant enrichment at all.
PATHWAYS = "Paper1_Results/Task4/task4_all_significant.csv"
# Recovered molecule types that are never a small-molecule therapeutic.
# Reported, not relied on: see the comment at the flag block.
NON_THERAPEUTIC_TYPES = {"Unknown"}
OUT_DIR = "Paper2_Results/Task4"
TOP_N = 50
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


def wilson_lower(k, n, z=1.96):
    """Lower bound of the Wilson interval for k/n.

    The point estimate k/n cannot tell 1/1 from 60/100. The lower bound can:
    it is what the fraction is worth once the size of the denominator is taken
    into account, which is the whole reason the plan calls specificity a
    supporting feature rather than a score.
    """
    k, n = np.asarray(k, float), np.asarray(n, float)
    out = np.zeros_like(n)
    m = n > 0
    p = np.divide(k, n, out=np.zeros_like(n), where=m)
    denom = 1 + z**2 / n[m]
    centre = p[m] + z**2 / (2 * n[m])
    margin = z * np.sqrt(p[m] * (1 - p[m]) / n[m] + z**2 / (4 * n[m]**2))
    out[m] = np.clip((centre - margin) / denom, 0, 1)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task4")

    e = pd.read_csv(EDGES)
    e = e[~e.Action_Mechanism.isin(PHARMACOKINETIC)].copy()   # therapeutic only
    print(f"therapeutic drug-gene edges on progression genes: {len(e):,}")

    # Group label, matching Task 3. Task 2 already resolved the per-gene
    # direction and left it blank for the genes whose two ladders disagree, so
    # that column is reused rather than re-deriving it from the two ladders.
    def grp(r):
        cls = "shared" if r.progression_class == "both" else r.progression_class
        if pd.isna(r.gene_direction):
            return f"{cls} / discordant"
        return (f"{cls} / "
                f"{'positive' if r.gene_direction == 'increasing' else 'negative'}")
    e["group"] = e.apply(grp, axis=1)

    # ---- denominator: every target the drug has, progression or not --------
    drv, db = driver()
    with drv.session(database=db) as s:
        allt = pd.DataFrame(s.run("""
            MATCH (dr:Drug)-[a:ACTS_ON]->(g:Gene)
            WHERE NOT a.action IN $pk
            RETURN dr.node_id AS Drug_ID, count(a) AS all_targets
        """, pk=sorted(PHARMACOKINETIC)).data())
        # The recovered chemistry, read off the Drug node. These properties were
        # written back from OptimusKG and ChEMBL, so reading them here rather
        # than stitching them on afterwards is what lets a re-run of this script
        # stand on its own. A graph without them yields empty columns and the
        # name heuristic carries on alone.
        chem = pd.DataFrame(s.run("""
            MATCH (dr:Drug)
            RETURN dr.node_id            AS Drug_ID,
                   dr.recovered_name     AS drug_name,
                   dr.recovered_name_source AS drug_name_source,
                   dr.molecule_type      AS molecule_type,
                   dr.molecule_type_source AS molecule_type_source,
                   dr.max_phase          AS max_phase,
                   dr.max_phase_source   AS max_phase_source,
                   dr.smiles             AS smiles,
                   dr.smiles_source      AS smiles_source,
                   dr.is_approved        AS is_approved,
                   dr.has_been_withdrawn AS has_been_withdrawn,
                   dr.inchi_key          AS inchi_key,
                   dr.cd_formula         AS cd_formula,
                   dr.cd_mol_weight      AS cd_mol_weight
        """).data())
    drv.close()
    print(f"recovered chemistry: formula for "
          f"{int(chem.cd_formula.notna().sum()):,} of {len(chem):,} drugs, "
          f"molecule type for {int(chem.molecule_type.notna().sum()):,}")

    # ---- coverage per drug -------------------------------------------------
    piv = (e.pivot_table(index="Drug_ID", columns="group", values="Gene_ID",
                         aggfunc="nunique", fill_value=0)
             .rename(columns=lambda c: "n_" + c.replace(" / ", "_")
                                               .replace("-", "_")))
    base = (e.groupby(["Drug_ID", "Drug"])
              .agg(n_progression_genes=("Gene_ID", "nunique"),
                   target_genes=("Gene", lambda s: ";".join(sorted(set(s)))))
              .reset_index())

    cls = (e.pivot_table(index="Drug_ID", columns="progression_class",
                         values="Gene_ID", aggfunc="nunique", fill_value=0)
             .rename(columns={"fibrosis-only": "fibrosis_only_targets",
                              "inflammation-only": "inflammation_only_targets",
                              "both": "shared_targets"}))

    d = (base.merge(cls, on="Drug_ID", how="left")
             .merge(piv, on="Drug_ID", how="left")
             .merge(allt, on="Drug_ID", how="left").fillna(0))

    # ---- specificity, raw and size-aware ----------------------------------
    d["all_known_targets"] = d.all_targets.astype(int)
    d["progression_target_fraction"] = (
        d.n_progression_genes / d.all_known_targets.replace(0, np.nan)).round(3)
    d["progression_fraction_lower95"] = wilson_lower(
        d.n_progression_genes, d.all_known_targets).round(3)

    # ---- coherence ---------------------------------------------------------
    gcols = [c for c in d.columns if c.startswith("n_") and
             c != "n_progression_genes"]
    d["dominant_class_fraction"] = (d[gcols].max(axis=1)
                                    / d.n_progression_genes).round(3)
    clus = (e.dropna(subset=["Cluster"])
              .pivot_table(index="Drug_ID", columns="Cluster", values="Gene_ID",
                           aggfunc="nunique", fill_value=0))
    if len(clus):
        # Per-cluster counts, not only the dominant share. The plan asks for
        # coverage calculated "separately for ... important F0-F4 trajectory
        # clusters", which a single dominant-fraction column does not give.
        d = d.merge(clus.rename(columns=lambda c: f"n_cluster_{c}"),
                    on="Drug_ID", how="left")
        dom = (clus.max(axis=1) / clus.sum(axis=1)).round(3)
        d = d.merge(dom.rename("dominant_cluster_fraction"),
                    on="Drug_ID", how="left")
        d = d.merge(clus.sum(axis=1).rename("genes_with_a_cluster"),
                    on="Drug_ID", how="left")

    # The rule lives in paper2_drug_filters.py and is shared with Tasks 3, 6
    # and 7. It used to be defined here, which is how the tasks drifted to
    # different answers for the same question.
    _flags = flag_entities(dict(zip(d.Drug_ID, d.Drug)),
                           e.groupby("Drug_ID").Gene_ID.apply(set).to_dict())
    d["flag_name"] = d.Drug_ID.map(lambda i: _flags[i]["flag_name"])
    # An entry whose name is only its ChEMBL id cannot be judged by name at all.
    d["flag_unnamed"] = d.Drug_ID.map(lambda i: _flags[i]["flag_unnamed"])

    # Near-duplicate entities, now restricted to UNNAMED accessions only.
    # CHEMBL1201279 shares all 126 of its targets with ZINC ACETATE and no name
    # rule can catch it. Applying the same test to named medicines flagged
    # omeprazole, erythromycin and warfarin for sharing a CYP panel, so it no
    # longer runs on them.
    d["flag_duplicate"] = d.Drug_ID.map(lambda i: _flags[i]["flag_duplicate"])

    # Chemistry, joined from the graph. The carbon test is certain where it
    # fires -- a formula with no carbon is not an organic therapeutic -- and it
    # reaches entities no name rule can: ZnCl2, MgSO4, Na2SO4, AlCl3, CaCl2, NO.
    # It cannot reach the organic nutrients, because ATP, FAD and glutamic acid
    # all contain carbon, so the name heuristic stays beside it as the broader,
    # cruder net. Both are reported and neither replaces the other.
    #
    # Molecule type and clinical phase were recovered as Team 1 asked and do NOT
    # work for this: the name-flagged entries are all `Small molecule`, and ZINC
    # ACETATE carries max_phase 4.0 with is_approved True, because it genuinely
    # is an approved small molecule. They are reported as data, not used as a
    # filter.
    d = d.merge(chem, on="Drug_ID", how="left")
    d["flag_molecule_type"] = d.molecule_type.isin(NON_THERAPEUTIC_TYPES)
    d["flag_inorganic"] = d.cd_formula.map(is_inorganic)
    d["likely_non_therapeutic"] = (d.flag_name | d.flag_unnamed
                                   | d.flag_duplicate | d.flag_inorganic)
    d = d.sort_values("n_progression_genes", ascending=False).reset_index(drop=True)

    ccols = sorted(c for c in d.columns if c.startswith("n_cluster_C"))
    keep = (["Drug", "Drug_ID", "n_progression_genes", "fibrosis_only_targets",
             "shared_targets", "inflammation_only_targets"]
            + sorted(gcols) + ccols
            + ["all_known_targets", "progression_target_fraction",
               "progression_fraction_lower95", "dominant_class_fraction",
               "dominant_cluster_fraction", "genes_with_a_cluster",
               "flag_name", "flag_unnamed", "flag_duplicate",
               "flag_molecule_type", "flag_inorganic",
               "likely_non_therapeutic",
               # the recovered chemistry, each field beside the source it came
               # from so OptimusKG and ChEMBL stay separable in the delivered
               # table and not only upstream
               "drug_name", "drug_name_source",
               "molecule_type", "molecule_type_source",
               "max_phase", "max_phase_source",
               "smiles", "smiles_source",
               "is_approved", "has_been_withdrawn",
               "inchi_key", "cd_formula", "cd_mol_weight",
               "target_genes"])
    d = d[[c for c in keep if c in d.columns]]
    d.to_csv(f"{OUT_DIR}/task4_drug_coverage.csv", index=False)

    # ---- top N, raw and filtered ------------------------------------------
    top_raw = d.head(TOP_N)
    top_raw.to_csv(f"{OUT_DIR}/task4_top_drugs_raw_coverage.csv", index=False)

    # The plan asks for the top 20-50 by RAW coverage, which is the list above.
    # It also says not to call a high-degree drug the best candidate. Both are
    # satisfied by shipping the raw list and, beside it, the same list with the
    # non-therapeutic entities removed -- which is the one a reader should use.
    # Ranked by coherence instead of by count. Coverage and coherence correlate
    # NEGATIVELY (computed below, not asserted), so this is a genuinely
    # different list and it is the one
    # worth reading first: it is where TRAPIDIL, MARIMASTAT and GLYCYRRHIZIN
    # sit, none of which the coverage ranking surfaces. A floor of five genes
    # keeps out drugs that score 1.0 coherence on two targets.
    coherent = (d[(~d.likely_non_therapeutic) & (d.n_progression_genes >= 5)]
                .sort_values(["dominant_class_fraction", "n_progression_genes"],
                             ascending=[False, False])
                .head(TOP_N))
    coherent.to_csv(f"{OUT_DIR}/task4_top_drugs_by_coherence.csv", index=False)

    # ---- coverage vs coherence, MEASURED ----------------------------------
    # This number is quoted in five documents. It used to be carried by hand as
    # -0.124 and drifted when the coherence definition and the gene set changed,
    # because nothing recomputed it. It is computed here and written to disk so
    # a stale value cannot survive a rerun again.
    corr_rows = []
    for coh_col in ["dominant_class_fraction", "dominant_cluster_fraction"]:
        for label, mask in [
                ("not non-therapeutic", ~d.likely_non_therapeutic),
                ("named only", ~d.flag_unnamed)]:
            sub = d[mask & (d.n_progression_genes >= 5)].dropna(
                subset=["n_progression_genes", coh_col])
            if len(sub) < 10:
                continue
            rho, pval = spearmanr(sub.n_progression_genes, sub[coh_col])
            corr_rows.append({"coherence_measure": coh_col,
                              "drug_set": label,
                              "min_progression_genes": 5,
                              "n_drugs": len(sub),
                              "spearman_rho": round(float(rho), 3),
                              "p_value": float(pval)})
    corr = pd.DataFrame(corr_rows)
    corr.to_csv(f"{OUT_DIR}/task4_coverage_vs_coherence_correlation.csv",
                index=False)
    headline = corr[(corr.coherence_measure == "dominant_class_fraction")
                    & (corr.drug_set == "not non-therapeutic")]
    rho_headline = float(headline.spearman_rho.iloc[0])
    print("\ncoverage vs coherence (Spearman), measured:")
    print(corr.to_string(index=False))
    print(f"   headline (class coherence, non-therapeutic removed, n>=5): "
          f"rho = {rho_headline:+.3f}")
    assert rho_headline < 0, (
        "coverage and coherence are no longer negatively correlated -- the "
        "Task 4 / 6 / 8 argument rests on this sign, so stop and re-read")

    # ---- bipartite network, annotated with Paper 1 evidence ----------------
    net_drugs = set(d[(d.n_progression_genes >= 3)
                      & (~d.likely_non_therapeutic)].Drug_ID)
    ne = e[e.Drug_ID.isin(net_drugs)].copy()
    edges_out = ne[["Drug", "Drug_ID", "Gene", "Gene_ID", "Action_Mechanism",
                    "action_class", "mechanism_consistency"]]
    edges_out.to_csv(f"{OUT_DIR}/task4_network_edges.csv", index=False)

    gnodes = (ne.groupby(["Gene", "Gene_ID"])
                .agg(progression_class=("progression_class", "first"),
                     group=("group", "first"),
                     fibrosis_rho=("fibrosis_rho", "first"),
                     inflammation_rho=("inflammation_rho", "first"),
                     cluster=("Cluster", "first"),
                     cluster_pattern=("Cluster_pattern", "first"),
                     largest_transition=("Largest_transition", "first"),
                     tier=("Tier", "first"),
                     n_drugs=("Drug_ID", "nunique")).reset_index())
    # "major fibrosis-associated pathway/process", as the plan requires on the
    # network. Paper 1's gene table carries only booleans per database, so the
    # name comes from Paper 1's own enrichment.
    #
    # HOW THE REPRESENTATIVE TERM IS CHOSEN. A gene can sit under dozens of
    # significant terms. The one reported is the most significant: lowest
    # q_value, ties broken by higher fold_enrichment and then by term label, so
    # the choice is deterministic and does not depend on row order.
    #
    # A blank here means "no significant enriched term lists this gene" and
    # nothing more -- `pathway_annotation` says which of the two it is, because
    # absence of annotation and absence of enrichment are different facts.
    pw = pd.read_csv(PATHWAYS)
    pw = pw[pw.significant.astype(str).str.lower() == "true"]
    pw = pw.sort_values(["q_value", "fold_enrichment", "term_label"],
                        ascending=[True, False, True])
    best = {}
    for r in pw.itertuples(index=False):
        for sym in str(r.genes).split(","):
            sym = sym.strip()
            if sym and sym not in best:
                best[sym] = (r.term_label, r.database, r.q_value)
    print(f"pathway lookup: {len(pw):,} significant terms covering "
          f"{len(best):,} gene symbols")
    gnodes["major_pathway"] = gnodes.Gene.map(lambda g: best.get(g, (None,))[0])
    gnodes["major_pathway_db"] = gnodes.Gene.map(
        lambda g: best[g][1] if g in best else None)
    gnodes["major_pathway_q"] = gnodes.Gene.map(
        lambda g: best[g][2] if g in best else None)
    gnodes["pathway_annotation"] = np.where(
        gnodes.Gene.isin(best), "significant term",
        "no significant term in Paper 1 enrichment")
    n_blank = int((~gnodes.Gene.isin(best)).sum())
    print(f"   {len(gnodes) - n_blank:,} network genes carry a term, "
          f"{n_blank:,} have none")

    gnodes.insert(0, "node_type", "gene")
    gnodes = gnodes.rename(columns={"Gene": "label", "Gene_ID": "node_id"})
    dnodes = d[d.Drug_ID.isin(net_drugs)][
        ["Drug", "Drug_ID", "n_progression_genes", "all_known_targets",
         "progression_fraction_lower95", "dominant_class_fraction"]].copy()
    dnodes.insert(0, "node_type", "drug")
    dnodes = dnodes.rename(columns={"Drug": "label", "Drug_ID": "node_id"})
    nodes_out = pd.concat([dnodes, gnodes], ignore_index=True)
    nodes_out.to_csv(f"{OUT_DIR}/task4_network_nodes.csv", index=False)

    # ---- supporting --------------------------------------------------------
    sup.add("coverage_by_group", d[["Drug", "n_progression_genes"] + sorted(gcols)]
            .head(100))
    sup.add("flagged_non_therapeutic",
            d[d.likely_non_therapeutic][
                ["Drug", "n_progression_genes", "all_known_targets",
                 "progression_target_fraction"]])
    sup.add("specificity_trap",
            d[d.all_known_targets <= 2].nlargest(
                30, "progression_target_fraction")[
                ["Drug", "n_progression_genes", "all_known_targets",
                 "progression_target_fraction", "progression_fraction_lower95"]])
    sup.write()

    # ---- report ------------------------------------------------------------
    print(f"\ndrugs reaching >=1 progression gene (therapeutic): {len(d):,}")
    print(f"  reaching >=3: {(d.n_progression_genes >= 3).sum():,}")
    print(f"  flagged likely non-therapeutic: {int(d.likely_non_therapeutic.sum()):,}")
    print(f"\nnetwork: {len(net_drugs):,} drugs x {gnodes.node_id.nunique():,} "
          f"genes, {len(edges_out):,} edges")
    print(f"\nTop 15 by raw coverage:")
    print(d.head(15)[["Drug", "n_progression_genes", "all_known_targets",
                      "progression_target_fraction", "dominant_class_fraction",
                      "likely_non_therapeutic"]].to_string(index=False))
    print(f"\nwrote {OUT_DIR}/task4_drug_coverage.csv")
    print(f"wrote {OUT_DIR}/task4_top_drugs_raw_coverage.csv")
    print(f"wrote {OUT_DIR}/task4_top_drugs_by_coherence.csv")
    print(f"wrote {OUT_DIR}/task4_network_edges.csv")
    print(f"wrote {OUT_DIR}/task4_network_nodes.csv")


if __name__ == "__main__":
    main()
