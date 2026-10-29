"""Add the KEGG (legacy) and Hallmark pathways to the graph.

Paper 1 chose its genes using four enrichment libraries (GO BP, KEGG, Reactome,
Hallmark; MSigDB 2024.1). The graph only carried Reactome as Pathway nodes and
GO as BioProcess nodes. This adds the other two from the same MSigDB files
Paper 1 used (data/genesets), so the pathway step of Paper 2 rests on the same
libraries as the gene selection.

What it writes
    (:Pathway {node_id, name, msigdb_id, source, msigdb_version, n_genes})
    (:Gene)-[:IN_PATHWAY {source}]->(:Pathway)

    node_id   "KEGG:KEGG_..."  or  "HALLMARK:HALLMARK_..."
    source    "KEGG_legacy" or "Hallmark", on both nodes and links

The existing Reactome nodes ("REACT:" ids) and links are not touched. Anything
that should stay Reactome-only filters on the "REACT:" prefix or on
`r.source IS NULL`. To undo this whole step:

    MATCH (p:Pathway) WHERE p.source IN ['KEGG_legacy','Hallmark'] DETACH DELETE p

Genes are matched by HGNC symbol, which is unique in the graph. MSigDB symbols
with no Gene node are listed in the unmatched file, not loaded.

Run from the project root:
    python scripts/add_msigdb_pathways.py            # write CSVs and load
    python scripts/add_msigdb_pathways.py --dry-run  # write CSVs only

Password: NEO4J_PASSWORD, or else the neo4j-liver-kg entry in .mcp.json.
"""
import argparse
import json
import os
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
GMT_DIR = ROOT / "data/genesets"
OUT = ROOT / "data/graph_msigdb"
VERSION = "2024.1"
LIBRARIES = [  # file, source tag, node_id prefix, MSigDB name prefix
    ("c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt", "KEGG_legacy", "KEGG", "KEGG_"),
    ("h.all.v2024.1.Hs.symbols.gmt", "Hallmark", "HALLMARK", "HALLMARK_"),
]
BATCH = 5000
ACRONYMS = {"ABC", "TGF", "ECM", "DNA", "RNA", "MAPK", "JAK", "STAT", "NOD", "RIG",
            "PPAR", "MTOR", "ERBB", "VEGF", "GNRH", "WNT", "NK", "T", "B", "II",
            "UV", "KRAS", "TNFA", "NFKB", "MYC", "E2F", "G2M", "UPR", "EMT",
            "SNARE", "GPI", "TCA", "FC", "HIF", "HCM", "ARVC", "SHH"}


def readable(term, prefix):
    """KEGG_TGF_BETA_SIGNALING_PATHWAY -> 'TGF beta signaling pathway'."""
    words = term[len(prefix):].split("_")
    # keep acronyms and gene-like words (with a digit) upper case
    out = [w if w in ACRONYMS or any(c.isdigit() for c in w) else w.lower()
           for w in words]
    s = " ".join(out)
    return s[0].upper() + s[1:]


def build(graph_symbols):
    nodes, edges, unmatched = [], [], []
    for fname, source, id_prefix, name_prefix in LIBRARIES:
        for line in open(GMT_DIR / fname, encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            term, genes = parts[0], sorted(set(parts[2:]))
            node_id = f"{id_prefix}:{term}"
            nodes.append(dict(node_id=node_id, name=readable(term, name_prefix),
                              msigdb_id=term, source=source,
                              msigdb_version=VERSION, n_genes=len(genes)))
            for g in genes:
                if g in graph_symbols:
                    edges.append(dict(symbol=g, node_id=node_id, source=source))
                else:
                    unmatched.append(dict(symbol=g, node_id=node_id, source=source))
    return pd.DataFrame(nodes), pd.DataFrame(edges), pd.DataFrame(unmatched)


def password():
    if os.environ.get("NEO4J_PASSWORD"):
        return os.environ["NEO4J_PASSWORD"]
    cfg = json.load(open(ROOT / ".mcp.json"))
    return cfg["mcpServers"]["neo4j-liver-kg"]["env"]["NEO4J_PASSWORD"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    ap.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    args = ap.parse_args()

    driver = GraphDatabase.driver(args.uri, auth=(args.user, password()))
    with driver.session(database="neo4j") as s:
        syms = {r["s"] for r in s.run(
            "MATCH (g:Gene) WHERE g.symbol IS NOT NULL RETURN g.symbol AS s")}
        nodes, edges, unmatched = build(syms)

        OUT.mkdir(parents=True, exist_ok=True)
        nodes.to_csv(OUT / "nodes_pathway_msigdb.csv", index=False)
        edges.to_csv(OUT / "edges_pathway_gene_msigdb.csv", index=False)
        unmatched.to_csv(OUT / "unmatched_symbols_msigdb.csv", index=False)
        for src in ("KEGG_legacy", "Hallmark"):
            print(f"{src:12s} pathways {int((nodes.source == src).sum()):4d}  "
                  f"links {int((edges.source == src).sum()):6,d}  "
                  f"unmatched {int((unmatched.source == src).sum()):4d}")
        if args.dry_run:
            print("dry run: CSVs written to", OUT.relative_to(ROOT), "- nothing loaded")
            return

        s.run("""UNWIND $rows AS row
                 MERGE (p:Pathway {node_id: row.node_id})
                 SET p.name = row.name, p.msigdb_id = row.msigdb_id,
                     p.source = row.source, p.msigdb_version = row.msigdb_version,
                     p.n_genes = row.n_genes""",
              rows=nodes.to_dict("records")).consume()
        rows = edges.to_dict("records")
        for i in range(0, len(rows), BATCH):
            s.run("""UNWIND $rows AS row
                     MATCH (g:Gene {symbol: row.symbol})
                     MATCH (p:Pathway {node_id: row.node_id})
                     MERGE (g)-[r:IN_PATHWAY]->(p)
                     SET r.source = row.source""",
                  rows=rows[i:i + BATCH]).consume()

        res = s.run("""MATCH (g:Gene)-[r:IN_PATHWAY]->(p:Pathway)
                       RETURN coalesce(p.source, 'Reactome') AS src,
                              count(DISTINCT p) AS pathways, count(r) AS links
                       ORDER BY src""").data()
        print("graph now:")
        for r in res:
            print(f"  {r['src']:12s} pathways {r['pathways']:5,d}  links {r['links']:6,d}")
    driver.close()


if __name__ == "__main__":
    main()
