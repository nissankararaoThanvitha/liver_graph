"""Build Pathway -> NAFLD links supported by two independent sources.

The metapath Drug -> Gene -> Gene -> Pathway -> Disease needs a Pathway ->
Disease step, which neither OptimusKG nor the graph has. A pathway is linked
to NAFLD (EFO_0003095) only when BOTH of these agree:

  1. Main link -- Paper 1 Task 4 enrichment. The pathway is significantly
     enriched (BH-FDR < 0.05, hypergeometric, 14,794-gene background) in at
     least one fibrosis gene group (fibrosis_only/shared up/down, C1-C5).
     Inflammation-only groups are excluded.
  2. Independent check -- CTD (CTD_diseases_pathways.csv.gz). CTD links the
     pathway to Non-alcoholic Fatty Liver Disease (MESH:D065626) through at
     least MIN_CTD_GENES curated NAFLD genes.

Matching: Reactome by name to the graph's REACT: ids (CTD uses the same ids);
KEGG by name (graph KEGG nodes come from MSigDB KEGG legacy). Hallmark is not
in CTD, so no Hallmark pathway can pass the check.

Writes   data/graph_pathway_disease/edges_pathway_nafld.csv   (the links)
         data/graph_pathway_disease/pathway_nafld_all_candidates.csv
                 (every main-link pathway, with why it passed or failed)
Load     python scripts/build_pathway_nafld_links.py --load
         creates (:Pathway)-[:IMPLICATED_IN {source:'task4_enrichment+CTD', ...}]->(:Disease)
Undo     MATCH ()-[r:IMPLICATED_IN {source:'task4_enrichment+CTD'}]->() DELETE r

CTD terms of use require citing CTD in any publication using these links.
Run from the project root.
"""
import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TASK4 = ROOT / "Paper1_Results/Task4/task4_all_significant.csv"
OKG_PATHWAYS = ROOT / "data/optimuskg/pathway.parquet"
GRAPH_PATHWAYS = ROOT / "data/graph_okg/nodes_pathway.csv"
MSIGDB_NODES = ROOT / "data/graph_msigdb/nodes_pathway_msigdb.csv"
CTD = ROOT / "data/ctd/CTD_diseases_pathways.csv.gz"
OUT = ROOT / "data/graph_pathway_disease"

DISEASE_ID = "EFO_0003095"        # non-alcoholic fatty liver disease
CTD_DISEASE = "MESH:D065626"      # Non-alcoholic Fatty Liver Disease
FDR = 0.05
MIN_CTD_GENES = 2
SOURCE = "task4_enrichment+CTD"
CLUSTER_PATTERN = {
    "C1": "early increase", "C2": "late increase", "C3": "early rise then plateau",
    "C4": "mid decrease", "C5": "late decrease",
}


def norm(s):
    return re.sub(r"[^A-Z0-9]+", "_", str(s).upper()).strip("_")


def main_link():
    e = pd.read_csv(TASK4)
    e = e[(~e.group.str.startswith("inflammation"))
          & e.database.isin(["Reactome", "KEGG", "Hallmark"]) & (e.q_value < FDR)]

    okg = pd.read_parquet(OKG_PATHWAYS)
    in_graph = set(pd.read_csv(GRAPH_PATHWAYS).node_id)
    react = {}
    for pid, props in zip(okg.id, okg.properties):
        if pid in in_graph:
            react.setdefault(norm(props.get("name")), []).append(pid)
    msig = set(pd.read_csv(MSIGDB_NODES).node_id)

    rows = []
    for (db, term), g in e.groupby(["database", "term"]):
        best = g.sort_values("q_value").iloc[0]
        if db == "Reactome":
            hits = react.get(norm(term[len("REACTOME_"):]), [])
            node = hits[0] if len(hits) == 1 else None
        else:
            node = f"{'KEGG' if db == 'KEGG' else 'HALLMARK'}:{term}"
            node = node if node in msig else None
        clusters = sorted({x.split("_")[0] for x in g.group if x[:2] in CLUSTER_PATTERN})
        rows.append(dict(
            pathway_id=node, database=db, term=term, term_label=best.term_label,
            best_q=best.q_value, best_fold=round(best.fold_enrichment, 3),
            best_group=best.group, groups=";".join(sorted(g.group.unique())),
            clusters=";".join(clusters),
            cluster_patterns=";".join(CLUSTER_PATTERN[c] for c in clusters),
            our_genes=";".join(sorted({x.strip() for s in g.genes.dropna() for x in s.split(",")}))))
    return pd.DataFrame(rows)


def ctd_support():
    c = pd.read_csv(CTD, comment="#", header=None,
                    names=["DiseaseName", "DiseaseID", "PathwayName", "PathwayID", "Genes"])
    c = c[c.DiseaseID == CTD_DISEASE]
    agg = c.groupby(["PathwayID", "PathwayName"]).Genes.agg(
        lambda x: sorted({g for s in x.dropna() for g in re.split(r"[|;]", s)} - {""})).reset_index()
    agg["ctd_n_genes"] = agg.Genes.str.len()
    agg["ctd_genes"] = agg.Genes.str.join(";")
    return agg.drop(columns="Genes")


def build():
    m = main_link()
    c = ctd_support()
    by_react = c[c.PathwayID.str.startswith("REACT:")].set_index("PathwayID")
    by_kegg = c[c.PathwayID.str.startswith("KEGG:")].assign(k=lambda d: d.PathwayName.map(norm)).set_index("k")

    def lookup(r):
        if r.database == "Reactome" and r.pathway_id in by_react.index:
            x = by_react.loc[r.pathway_id]
            return r.pathway_id, x.ctd_n_genes, x.ctd_genes
        if r.database == "KEGG" and norm(r.term[len("KEGG_"):]) in by_kegg.index:
            x = by_kegg.loc[norm(r.term[len("KEGG_"):])]
            return x.PathwayID, x.ctd_n_genes, x.ctd_genes
        return None, 0, ""

    m[["ctd_pathway_id", "ctd_n_genes", "ctd_genes"]] = m.apply(lookup, axis=1, result_type="expand")
    m["ctd_n_genes"] = m.ctd_n_genes.astype(int)
    m["status"] = "pass"
    m.loc[m.ctd_n_genes < MIN_CTD_GENES, "status"] = f"fail: CTD support < {MIN_CTD_GENES} genes"
    m.loc[m.ctd_n_genes == 0, "status"] = "fail: not linked to NAFLD in CTD"
    m.loc[m.database == "Hallmark", "status"] = "fail: Hallmark not in CTD"
    m.loc[m.pathway_id.isna(), "status"] = "fail: no gene-linked graph node"
    m["disease_id"] = DISEASE_ID
    return m.sort_values(["status", "best_q"])


def password():
    if os.environ.get("NEO4J_PASSWORD"):
        return os.environ["NEO4J_PASSWORD"]
    return json.load(open(ROOT / ".mcp.json"))["mcpServers"]["neo4j-liver-kg"]["env"]["NEO4J_PASSWORD"]


def load(links):
    from neo4j import GraphDatabase
    rows = links[["pathway_id", "disease_id", "database", "best_q", "best_fold", "best_group",
                  "groups", "clusters", "cluster_patterns", "ctd_pathway_id", "ctd_n_genes"]].to_dict("records")
    drv = GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                               auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password()))
    with drv.session(database="neo4j") as s:
        s.run("""UNWIND $rows AS row
                 MATCH (p:Pathway {node_id: row.pathway_id})
                 MATCH (d:Disease {node_id: row.disease_id})
                 MERGE (p)-[r:IMPLICATED_IN {source: $src}]->(d)
                 SET r.database = row.database, r.task4_best_q = row.best_q,
                     r.task4_best_fold = row.best_fold, r.task4_best_group = row.best_group,
                     r.task4_groups = row.groups, r.clusters = row.clusters,
                     r.cluster_patterns = row.cluster_patterns,
                     r.ctd_pathway_id = row.ctd_pathway_id, r.ctd_n_genes = row.ctd_n_genes""",
              rows=rows, src=SOURCE).consume()
        n = s.run("MATCH ()-[r:IMPLICATED_IN {source:$src}]->() RETURN count(r) AS n", src=SOURCE).single()["n"]
    drv.close()
    print(f"loaded: {n} IMPLICATED_IN links in the graph")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", action="store_true", help="write the links into Neo4j")
    args = ap.parse_args()

    m = build()
    OUT.mkdir(parents=True, exist_ok=True)
    m.to_csv(OUT / "pathway_nafld_all_candidates.csv", index=False)
    links = m[m.status == "pass"]
    links.to_csv(OUT / "edges_pathway_nafld.csv", index=False)

    print(f"main-link pathways: {len(m)}")
    print(m.status.value_counts().to_string())
    print(f"\nlinks kept (Task 4 FDR<{FDR} AND CTD >= {MIN_CTD_GENES} genes): {len(links)}  "
          f"{links.database.value_counts().to_dict()}")
    if args.load:
        load(links)
    else:
        print("not loaded (run with --load to write to Neo4j)")


if __name__ == "__main__":
    main()
