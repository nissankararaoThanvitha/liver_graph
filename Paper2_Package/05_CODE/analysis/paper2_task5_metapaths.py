"""
paper2_task5_metapaths.py
-------------------------
Paper 2, Task 5: implement and test biologically meaningful MetaPaths.

WHAT THE PLAN ASKS FOR
"Implement graph queries that connect drugs to the progression biology. At
minimum test: Drug -> Gene -> Disease; Drug -> Gene -> Pathway; Drug -> Gene ->
Biological Process; Drug -> Gene -> Pathway <- Progression Gene... extend to
Drug -> Gene -> Pathway <- F0-F4 trajectory genes... and test whether candidate
drugs converge on genes involved in the transitions identified as molecularly
important in Paper 1. Record the exact graph schema and query logic so the
analysis is reproducible."

Required outputs: a MetaPath definition table; per MetaPath the number of
paths, unique drugs, unique genes and unique pathways/processes; a
degree-normalised path support "because raw path counts can favor highly
connected nodes"; and example interpretable subgraphs.

WHY RAW PATH COUNTS ARE WORSE THAN USELESS HERE
A metapath through a shared node is a join, so a hub multiplies. Measured on
this graph:

    GO "signal transduction"              616 progression genes x 1,683 drugs
                                          = 1,036,728 pairs from ONE term
    GO "lipid metabolic process"          = 650,164
    top five GO terms together            = 2.46 million

Those pairs are an artefact of annotation breadth. Two countermeasures, both
applied and both reported with and without so the effect is visible:

  1. TERM CAP. Intermediate nodes outside 5-200 genes are dropped, the usual
     enrichment convention. This removes "signal transduction" and keeps
     "Interleukin-4 and 13 signalling".
  2. DWPC. Degree-Weighted Path Count (Himmelstein & Baranzini 2015): each path
     is downweighted by the degree of every node along it, raised to -w. A path
     through a hub contributes almost nothing; a path through a specific term
     contributes nearly 1. w = 0.4 is the published default.

         DWPC(source,target) = sum over paths of  prod_i degree(node_i)^-w

REACTOME OVER GO
Team 1's handover found Reactome's top terms on these genes to be specific and
on-topic (neutrophil degranulation, RAC1/RHOA GTPase cycles, integrin
interactions) while GO's are housekeeping (signal transduction, five
near-duplicate transcription-regulation terms counting the same genes). Both
are run; Reactome is the primary bridge and the difference is quantified
rather than asserted.

THE DISEASE AXIS IS NOT A DISEASE AXIS
Its hubs are generic EFO upper-level terms -- "measurement", "neoplasm",
"cancer or benign tumor" -- reached by thousands of genes. Drug -> Gene ->
Disease is therefore run as the plan requires and reported, but it is not a
route to candidates: Team 1 measured that an unfiltered walk from 500
progression genes reaches 70% of the entire drug vocabulary.

NOTHING HERE IS EVIDENCE OF EFFICACY
Per the plan: MetaPaths are evidence of biological connectivity. A high DWPC
says a drug and a progression gene sit close in the annotation graph, not that
the drug does anything useful.

Usage:
    uv run --with neo4j --with pandas --with numpy --with openpyxl python scripts/paper2_task5_metapaths.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paper2_io import SupportingTables

MASTER = "Paper2_Results/Task1/Paper2_progression_genes.csv"
TRAJECTORY = "Paper1_HighConfidence/11_final_all_3845_genes.csv"
TRANSITIONS = "Paper1_Results/Task3/task3_all_genes_all_transitions.csv"
OUT_DIR = "Paper2_Results/Task5"

PK = {"ENZYME", "TRANSPORTER", "CARRIER", "SUBSTRATE"}
CAP_MIN, CAP_MAX = 5, 200      # usual enrichment convention for term size
W = 0.4                        # DWPC damping exponent, published default
TOP_PAIRS = 200


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


def fetch():
    """The three edge tables the metapaths walk, pulled once.

    Done in pandas rather than Cypher because DWPC needs every node's degree
    along the path, and a Cypher count cannot be re-weighted after the fact
    without re-walking.
    """
    drv, db = driver()
    with drv.session(database=db) as s:
        acts = pd.DataFrame(s.run("""
            MATCH (dr:Drug)-[a:ACTS_ON]->(g:Gene)
            WHERE NOT a.action IN $pk
            RETURN dr.node_id AS drug, dr.name AS drug_name,
                   g.ensembl_id AS gene, g.symbol AS symbol
        """, pk=sorted(PK)).data())
        path = pd.DataFrame(s.run("""
            MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway)
            RETURN g.ensembl_id AS gene, p.node_id AS term, p.name AS term_name
        """).data())
        proc = pd.DataFrame(s.run("""
            MATCH (g:Gene)-[:INVOLVED_IN]->(b:BioProcess)
            RETURN g.ensembl_id AS gene, b.node_id AS term, b.name AS term_name
        """).data())
        # ASSOCIATED_WITH is 1.8M edges. Pulling it to count it would move the
        # whole table across Bolt to produce four numbers, so MP1's uncapped
        # counts are aggregated server-side instead. Only the capped slice --
        # terms of 5-200 genes, which is a small fraction -- is transferred.
        mp1 = s.run("""
            MATCH (dr:Drug)-[a:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
            WHERE NOT a.action IN $pk
            RETURN count(*) AS paths, count(DISTINCT dr) AS unique_drugs,
                   count(DISTINCT g) AS unique_genes,
                   count(DISTINCT d) AS unique_terms
        """, pk=sorted(PK)).single().data()
        dis = pd.DataFrame(s.run("""
            MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
            WITH d, count(DISTINCT g) AS n WHERE n >= $lo AND n <= $hi
            MATCH (g2:Gene)-[:ASSOCIATED_WITH]->(d)
            RETURN g2.ensembl_id AS gene, d.node_id AS term, d.name AS term_name
        """, lo=CAP_MIN, hi=CAP_MAX).data())
        dis_sizes = pd.DataFrame(s.run("""
            MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
            RETURN d.node_id AS term, d.name AS term_name,
                   count(DISTINCT g) AS genes
            ORDER BY genes DESC LIMIT 5
        """).data())
    drv.close()
    return acts, path, proc, dis, mp1, dis_sizes


def cap(edges, lo=CAP_MIN, hi=CAP_MAX):
    """Drop intermediate terms outside the size window."""
    size = edges.groupby("term").gene.nunique()
    keep = size[(size >= lo) & (size <= hi)].index
    return edges[edges.term.isin(keep)]


def three_node(acts, bridge, label):
    """Drug -> Gene -> <bridge>. Counts only; no target gene on the far side."""
    j = acts.merge(bridge, on="gene")
    return {"metapath": label, "paths": len(j),
            "unique_drugs": j.drug.nunique(), "unique_genes": j.gene.nunique(),
            "unique_terms": j.term.nunique()}


def four_node_counts_analytic(acts, bridge, targets, label):
    """Counts for Drug -> Gene -> term <- target, without building the table.

    Materialising this is not an option uncapped: one GO term joins 616
    progression genes to 1,683 drugs, and the hub terms together would produce
    hundreds of millions of rows to then count. Per term the arithmetic is
    exact -- L_t drug-gene pairs on the left times R_t targets on the right,
    minus the paths whose source gene IS the target gene, which are a one-hop
    fact rather than a metapath.
    """
    deg_drug = acts.groupby("gene").drug.nunique()
    b = bridge[["gene", "term"]].drop_duplicates()
    b["ndrugs"] = b.gene.map(deg_drug).fillna(0).astype(int)
    left = b.groupby("term").ndrugs.sum()                    # L_t
    right = (b[b.gene.isin(targets)].groupby("term").gene.nunique())  # R_t
    self_paths = (b[b.gene.isin(targets)].groupby("term").ndrugs.sum())

    terms = left.index.intersection(right.index)
    paths = int((left[terms] * right[terms] - self_paths[terms]).clip(lower=0).sum())
    src = set(b[b.term.isin(terms) & (b.ndrugs > 0)].gene)
    tgt = set(b[b.term.isin(terms) & b.gene.isin(targets)].gene)
    drugs = acts[acts.gene.isin(src)].drug.nunique()
    return {"metapath": label, "paths": paths, "unique_drugs": drugs,
            "unique_genes": len(src | tgt), "unique_terms": len(terms)}


def four_node(acts, bridge, targets, label, w=W):
    """Drug -> Gene -> <bridge> <- ProgressionGene, with DWPC.

    Returns the summary row and the per-pair table. Self-pairs (the drug's own
    target being the progression gene) are dropped: they are a one-hop fact
    already in Task 2, not a metapath discovery.
    """
    left = acts[["drug", "drug_name", "gene", "symbol"]].merge(bridge, on="gene")
    right = bridge[bridge.gene.isin(targets)].rename(
        columns={"gene": "target_gene"})
    j = left.merge(right[["term", "target_gene"]], on="term")
    j = j[j.gene != j.target_gene]
    if not len(j):
        return ({"metapath": label, "paths": 0, "unique_drugs": 0,
                 "unique_genes": 0, "unique_terms": 0}, pd.DataFrame())

    # degrees along the path: drug, source gene, term, target gene
    deg_drug = acts.groupby("drug").gene.nunique()
    deg_gene = acts.groupby("gene").drug.nunique()
    deg_term = bridge.groupby("term").gene.nunique()
    deg_tgt = bridge.groupby("gene").term.nunique()

    j["w"] = (j.drug.map(deg_drug).pow(-w)
              * j.gene.map(deg_gene).pow(-w)
              * j.term.map(deg_term).pow(-w)
              * j.target_gene.map(deg_tgt).pow(-w))

    pairs = (j.groupby(["drug", "drug_name", "target_gene"])
               .agg(path_count=("w", "size"), dwpc=("w", "sum"),
                    via_terms=("term", "nunique"))
               .reset_index().sort_values("dwpc", ascending=False))
    summary = {"metapath": label, "paths": len(j),
               "unique_drugs": j.drug.nunique(),
               "unique_genes": pd.concat([j.gene, j.target_gene]).nunique(),
               "unique_terms": j.term.nunique()}
    return summary, pairs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sup = SupportingTables(OUT_DIR, "task5")

    master = pd.read_csv(MASTER)
    prog = set(master.Ensembl_ID)
    acts, path, proc, dis, mp1, dis_sizes = fetch()
    acts = acts[acts.gene.isin(prog) | True]      # drugs may enter via any gene
    print(f"ACTS_ON (therapeutic)   {len(acts):,}")
    print(f"IN_PATHWAY  (Reactome)  {len(path):,}")
    print(f"INVOLVED_IN (GO BP)     {len(proc):,}")
    print(f"ASSOCIATED_WITH         {len(dis):,}\n")

    traj = pd.read_csv(TRAJECTORY)
    cluster_genes = set(traj.Ensembl_ID.dropna())
    tr = pd.read_csv(TRANSITIONS)
    tr = tr[tr.substantial.astype(str).str.lower() == "true"]
    transition_genes = set(tr.ensembl_id.dropna())
    print(f"trajectory-cluster genes {len(cluster_genes):,}")
    print(f"stage-transition genes   {len(transition_genes):,}\n")

    pathc, procc = cap(path), cap(proc)
    disc = dis          # already capped server-side

    # ---- the definition table the plan asks for ---------------------------
    defs = pd.DataFrame([
        ("MP1", "D-G-Di", "Drug -ACTS_ON-> Gene -ASSOCIATED_WITH-> Disease",
         "plan minimum; disease hubs are generic EFO terms, not a candidate route"),
        ("MP2", "D-G-P", "Drug -ACTS_ON-> Gene -IN_PATHWAY-> Pathway",
         "plan minimum; Reactome, the primary bridge"),
        ("MP3", "D-G-B", "Drug -ACTS_ON-> Gene -INVOLVED_IN-> BioProcess",
         "plan minimum; GO BP, hub-dominated"),
        ("MP4", "D-G-P-G", "Drug -> Gene -> Pathway <- Progression gene",
         "plan minimum; the main candidate-generating metapath"),
        ("MP5", "D-G-B-G", "Drug -> Gene -> BioProcess <- Progression gene",
         "same via GO BP, for comparison"),
        ("MP6", "D-G-P-G[traj]",
         "Drug -> Gene -> Pathway <- F0-F4 trajectory gene",
         "plan extension; target restricted to the 3,845 clustered genes"),
        ("MP7", "D-G-P-G[trans]",
         "Drug -> Gene -> Pathway <- stage-transition gene",
         "plan extension; target restricted to genes with a substantial transition"),
    ], columns=["id", "metapath", "schema", "why"])
    defs.to_csv(f"{OUT_DIR}/task5_metapath_definitions.csv", index=False)

    # ---- counts, uncapped and capped --------------------------------------
    rows, pair_tables = [], {}
    mp1_raw = dict(mp1); mp1_raw["metapath"] = "MP1 D-G-Di"
    mp1_raw["terms_filtered"] = "no"
    rows.append(mp1_raw)
    c = three_node(acts, disc, "MP1 D-G-Di")
    c["terms_filtered"] = f"{CAP_MIN}-{CAP_MAX} genes"; rows.append(c)
    for tag, bridge_raw, bridge_cap in [("MP2 D-G-P", path, pathc),
                                        ("MP3 D-G-B", proc, procc)]:
        r = three_node(acts, bridge_raw, tag); r["terms_filtered"] = "no"
        c = three_node(acts, bridge_cap, tag); c["terms_filtered"] = f"{CAP_MIN}-{CAP_MAX} genes"
        rows += [r, c]

    for tag, bridge_raw, bridge_cap, targets in [
            ("MP4 D-G-P-G", path, pathc, prog),
            ("MP5 D-G-B-G", proc, procc, prog),
            ("MP6 D-G-P-G[traj]", path, pathc, cluster_genes),
            ("MP7 D-G-P-G[trans]", path, pathc, transition_genes)]:
        r = four_node_counts_analytic(acts, bridge_raw, targets, tag)
        r["terms_filtered"] = "no"
        c, pairs = four_node(acts, bridge_cap, targets, tag)
        c["terms_filtered"] = f"{CAP_MIN}-{CAP_MAX} genes"
        rows += [r, c]
        pair_tables[tag] = pairs

    counts = pd.DataFrame(rows)[
        ["metapath", "terms_filtered", "paths", "unique_drugs", "unique_genes",
         "unique_terms"]]
    counts.to_csv(f"{OUT_DIR}/task5_metapath_counts.csv", index=False)

    # ---- what the cap removes, and what the hubs were ---------------------
    hub_rows = []
    for name, b in [("Reactome (IN_PATHWAY)", path), ("GO BP (INVOLVED_IN)", proc)]:
        size = b.groupby(["term", "term_name"]).gene.nunique().reset_index(
            name="genes").nlargest(5, "genes")
        drugs_per_term = (acts.merge(b, on="gene").groupby("term").drug.nunique())
        size["drugs_reached"] = size.term.map(drugs_per_term).fillna(0).astype(int)
        size["pairs_manufactured"] = size.genes * size.drugs_reached
        size.insert(0, "axis", name)
        hub_rows.append(size)
    dis_sizes = dis_sizes.copy(); dis_sizes.insert(0, "axis", "Disease (ASSOCIATED_WITH)")
    dis_sizes["drugs_reached"] = ""; dis_sizes["pairs_manufactured"] = ""
    hub_rows.append(dis_sizes)
    hubs = pd.concat(hub_rows, ignore_index=True)
    sup.add("hub_terms", hubs)

    # ---- the main candidate table -----------------------------------------
    main_pairs = pair_tables["MP4 D-G-P-G"]
    sym = master.set_index("Ensembl_ID").Gene.to_dict()
    grp = master.set_index("Ensembl_ID").progression_class.to_dict()
    main_pairs = main_pairs.assign(
        target_symbol=main_pairs.target_gene.map(sym),
        target_class=main_pairs.target_gene.map(grp))
    main_pairs.head(TOP_PAIRS).to_csv(
        f"{OUT_DIR}/task5_top_drug_gene_dwpc.csv", index=False)

    # how differently do raw count and DWPC rank things?
    mp = main_pairs.copy()
    mp["rank_count"] = mp.path_count.rank(ascending=False, method="min")
    mp["rank_dwpc"] = mp.dwpc.rank(ascending=False, method="min")
    spearman = mp.rank_count.corr(mp.rank_dwpc, method="spearman")
    sup.add("count_vs_dwpc_top100", mp.nlargest(100, "dwpc")[
        ["drug_name", "target_symbol", "path_count", "dwpc",
         "rank_count", "rank_dwpc"]])

    # ---- example subgraphs for quality checking ---------------------------
    examples = []
    for _, r in main_pairs.head(3).iterrows():
        via = (acts[acts.drug == r.drug].merge(pathc, on="gene")
               .merge(pathc[pathc.gene == r.target_gene][["term"]], on="term"))
        for _, v in via.head(12).iterrows():
            examples.append({"drug": r.drug_name, "drug_target": v.symbol,
                             "via_term": v.term_name,
                             "progression_gene": r.target_symbol,
                             "dwpc": round(r.dwpc, 6)})
    ex = pd.DataFrame(examples)
    ex.to_csv(f"{OUT_DIR}/task5_example_subgraphs.csv", index=False)
    sup.write()

    # ---- report ------------------------------------------------------------
    print(counts.to_string(index=False))
    print(f"\nrank correlation, raw path count vs DWPC: {spearman:.3f}")
    print(f"\nTop 10 drug / progression-gene pairs by DWPC (MP4, capped):")
    print(main_pairs.head(10)[["drug_name", "target_symbol", "target_class",
                               "path_count", "dwpc"]].to_string(index=False))
    for f in ["task5_metapath_definitions.csv", "task5_metapath_counts.csv",
              "task5_top_drug_gene_dwpc.csv", "task5_example_subgraphs.csv"]:
        print(f"wrote {OUT_DIR}/{f}")


if __name__ == "__main__":
    main()
