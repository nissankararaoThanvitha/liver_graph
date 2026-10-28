"""Paper 2 Task 5 preparation: map Paper 1 enriched terms onto knowledge-graph nodes.

Paper 1 enrichment used MSigDB GO_BP, Reactome, KEGG and Hallmark. The knowledge
graph contains GO biological processes (BioProcess) and Reactome pathways (Pathway)
only. This script links every significant Paper 1 term to a graph node using only
the graph and Paper 1 data (no external resources):

  1. name   : exact match of normalised term name (GO_BP -> BioProcess, Reactome -> Pathway)
  2. genes  : graph node whose progression-gene members best overlap the Paper 1 term
              genes (Jaccard >= 0.5 and >= 5 shared genes). Used for KEGG/Hallmark and
              for GO/Reactome terms without a name match. Marked as a proxy.

Fuzzy (character-similarity) name matching was tested and rejected: it paired
biologically different terms (catabolic/metabolic, type II/type III, amide/amine).

Paper 1 per-term gene lists (progression genes in the term) are also written in long
form so MetaPaths can use them directly when no graph node matches.

Read-only Neo4j access; password from NEO4J_PASSWORD (prompted if unset).
Run from the repository root:

    python Paper2_Results_Idea1/code/task5_prep_pathway_map.py
"""
import base64
import getpass
import json
import os
import re
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results_Idea1" / "Task5" / "prep"
OUT.mkdir(parents=True, exist_ok=True)

TERMS = ROOT / "Paper1_Results/Task4/task4_all_significant.csv"
GENES = ROOT / "Paper2_Results_Idea1/Task1/Paper2_progression_genes.csv"
KL = ROOT / "Paper1_Package/04_DATA/knowledge_layer"

JACCARD_MIN = 0.5
SHARED_MIN = 5

NEO4J_URL = os.environ.get("NEO4J_HTTP", "http://127.0.0.1:7474")
NEO4J_DB = os.environ.get("NEO4J_DATABASE", "neo4j")
NEO4J_USER = os.environ.get("NEO4J_USERNAME", "neo4j")


def neo4j_query(statement, password):
    headers = {"Authorization": "Basic " + base64.b64encode(f"{NEO4J_USER}:{password}".encode()).decode(),
               "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": statement, "accessMode": "Read"}).encode()
    req = urllib.request.Request(f"{NEO4J_URL}/db/{NEO4J_DB}/query/v2", data=body, headers=headers, method="POST")
    res = json.load(urllib.request.urlopen(req, timeout=600))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return pd.DataFrame(res["data"]["values"], columns=res["data"]["fields"])


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


# ------------------------------------------------------------------ graph members
MEMBERS = """
MATCH (g:Gene)-[:IN_PATHWAY]->(n:Pathway)
RETURN 'Pathway' AS node_type, n.node_id AS node_id, n.name AS node_name, g.ensembl_id AS ensembl_id
UNION ALL
MATCH (g:Gene)-[:INVOLVED_IN]->(n:BioProcess)
RETURN 'BioProcess' AS node_type, n.node_id AS node_id, n.name AS node_name, g.ensembl_id AS ensembl_id
"""
source = "Neo4j (live liver_kg, read-only)"
try:
    pw = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")
    mem = neo4j_query(MEMBERS, pw)
except Exception as exc:
    print(f"Neo4j unavailable ({exc}); using knowledge-layer CSVs")
    source = "CSV fallback (knowledge_layer) — Neo4j unavailable"
    pwy = pd.read_csv(KL / "edges_pathway_gene.csv").merge(
        pd.read_csv(KL / "nodes_pathway.csv"), left_on="to_id", right_on="node_id")
    bp = pd.read_csv(KL / "edges_biological_process_gene.csv").merge(
        pd.read_csv(KL / "nodes_bioprocess.csv"), left_on="to_id", right_on="node_id")
    mem = pd.concat([
        pd.DataFrame({"node_type": "Pathway", "node_id": pwy.node_id, "node_name": pwy.name, "ensembl_id": pwy.from_id}),
        pd.DataFrame({"node_type": "BioProcess", "node_id": bp.node_id, "node_name": bp.name, "ensembl_id": bp.from_id}),
    ])

genes = pd.read_csv(GENES)
sym2ens = dict(zip(genes.Gene, genes.ensembl_id))
prog = set(genes.ensembl_id)

nodes = mem.groupby(["node_type", "node_id", "node_name"]).ensembl_id.agg(set).reset_index()
nodes["n_members"] = nodes.ensembl_id.map(len)
nodes["prog_members"] = nodes.ensembl_id.map(lambda s: s & prog)
nodes["n_prog_members"] = nodes.prog_members.map(len)
nodes["key"] = nodes.node_name.map(norm)

# ------------------------------------------------------------------ Paper 1 terms
t = pd.read_csv(TERMS, encoding="utf-8-sig")
long = (t.assign(gene=t.genes.str.split(r",\s*")).explode("gene")
         [["database", "term", "term_label", "group", "gene"]])
long["ensembl_id"] = long.gene.map(sym2ens)
long.to_csv(OUT / "paper1_term_genes_long.csv", index=False)

terms = (long.groupby(["database", "term", "term_label"])
         .agg(groups=("group", lambda s: ";".join(sorted(set(s)))),
              term_genes=("ensembl_id", lambda s: set(s.dropna())))
         .reset_index())
best_q = t.groupby("term").q_value.min()
terms["best_q"] = terms.term.map(best_q)
terms["n_term_genes"] = terms.term_genes.map(len)

TYPE_FOR = {"GO_BP": "BioProcess", "Reactome": "Pathway"}
by_type = {k: v.set_index("key") for k, v in nodes.groupby("node_type")}
names_by_type = {k: list(v.index) for k, v in by_type.items()}


def match(row):
    want = TYPE_FOR.get(row.database)
    key = norm(row.term_label)
    if want:
        tbl = by_type[want]
        if key in tbl.index:
            n = tbl.loc[[key]].iloc[0]
            return want, n.node_id, n.node_name, "name", 1.0, None
    # gene-overlap proxy across both node types
    tg = row.term_genes
    if len(tg) < SHARED_MIN:
        return None, None, None, "none", None, None
    cand = nodes[nodes.n_prog_members >= SHARED_MIN]
    shared = cand.prog_members.map(lambda s: len(s & tg))
    jac = shared / cand.prog_members.map(lambda s: len(s | tg))
    jac = jac[shared >= SHARED_MIN]
    if want:  # GO/Reactome: stay within the same node type
        jac = jac[cand.loc[jac.index, "node_type"] == want]
    if jac.empty or jac.max() < JACCARD_MIN:
        return None, None, None, "none", round(float(jac.max()), 3) if not jac.empty else None, None
    i = jac.idxmax()
    n = nodes.loc[i]
    return n.node_type, n.node_id, n.node_name, "gene_overlap_proxy", round(float(jac[i]), 3), int(shared[i])


res = terms.apply(lambda r: pd.Series(match(r), index=[
    "graph_node_type", "graph_node_id", "graph_node_name", "match_type", "match_score", "shared_genes"]), axis=1)
mapped = pd.concat([terms.drop(columns=["term_genes"]), res], axis=1)


def nearest(tg):
    """Closest graph node by Jaccard, for transparency on unlinked terms."""
    cand = nodes[nodes.n_prog_members > 0]
    jac = cand.prog_members.map(lambda s: len(s & tg) / len(s | tg) if tg else 0.0)
    i = jac.idxmax()
    return pd.Series([cand.loc[i, "node_id"], cand.loc[i, "node_name"], round(float(jac[i]), 3)])


unl = mapped.match_type == "none"
mapped[["nearest_node_id", "nearest_node_name", "nearest_jaccard"]] = None
mapped.loc[unl, ["nearest_node_id", "nearest_node_name", "nearest_jaccard"]] = (
    terms.loc[unl, "term_genes"].apply(nearest).values)
mapped["use_in_metapaths"] = mapped.match_type.map(
    {"name": "graph node", "gene_overlap_proxy": "graph node (proxy)",
     "none": "Paper 1 gene list only"})
mapped.sort_values(["database", "best_q"]).to_csv(OUT / "paper1_term_to_graph_map.csv", index=False)

nodes_out = nodes[["node_type", "node_id", "node_name", "n_members", "n_prog_members"]]
nodes_out.to_csv(OUT / "graph_pathway_process_nodes.csv", index=False)

# ------------------------------------------------------------------ summary
tab = pd.crosstab(mapped.database, mapped.match_type).reindex(
    columns=["name", "gene_overlap_proxy", "none"], fill_value=0).astype(int)
tab["total"] = tab.sum(axis=1)
tab["linked_to_graph"] = tab.total - tab["none"]
tab["pct_linked"] = (100 * tab.linked_to_graph / tab.total).round(1)
tab.to_csv(OUT / "mapping_coverage.csv")

edge_counts = mem.groupby("node_type").size()
lines = ["| Database | Exact name | Gene-overlap proxy | Not linked (Paper 1 genes only) | Total | Linked to graph |",
         "|---|---|---|---|---|---|"]
for db, r in tab.iterrows():
    lines.append(f"| {db} | {int(r['name'])} | {int(r.gene_overlap_proxy)} | {int(r['none'])} | {int(r.total)} | "
                 f"{int(r.linked_to_graph)} ({r.pct_linked}%) |")
proxy_ex = mapped[mapped.match_type == "gene_overlap_proxy"].sort_values("match_score", ascending=False)
ex_lines = ["| Paper 1 term | Graph node | Jaccard | Shared genes |", "|---|---|---|---|"]
for _, r in proxy_ex[proxy_ex.database.isin(["KEGG", "Hallmark"])].head(10).iterrows():
    ex_lines.append(f"| {r.term} | {r.graph_node_name} ({r.graph_node_id}) | {r.match_score} | {int(r.shared_genes)} |")
n_terms = len(mapped)
n_graph = int((mapped.match_type != "none").sum())
genes_per_term = long.dropna(subset=["ensembl_id"]).groupby("term").ensembl_id.nunique()
n_usable = int(mapped.term.isin(genes_per_term.index).sum())

summary = f"""# Task 5 preparation: linking Paper 1 pathways to the knowledge graph

**Gene set note:** uses the corrected 6,222-gene union (the plan's 4,692 was the pre-correction count).
**Scope:** knowledge graph + Paper 1 only (project scope decision); no external pathway resources.
**Graph source:** {source}. Graph members: {edge_counts.get('Pathway', 0):,} Gene→Pathway (Reactome) and {edge_counts.get('BioProcess', 0):,} Gene→BioProcess (GO BP) lines.

## The problem
Paper 1 enrichment used four collections (GO BP, Reactome, KEGG, Hallmark). The graph holds only GO BP (`BioProcess`) and Reactome (`Pathway`). KEGG and Hallmark terms have no graph node of their own.

## The fix (two matching steps, best first)
1. **name**: identical normalised name, same collection (GO→BioProcess, Reactome→Pathway).
2. **gene_overlap_proxy**: the graph node whose progression-gene members best overlap the term's Paper 1 genes (Jaccard ≥ {JACCARD_MIN}, ≥ {SHARED_MIN} shared genes). This is how KEGG/Hallmark terms reach the graph. Proxies are labelled and must be reported as approximate.

Fuzzy (character-similarity) name matching was tried and **rejected**: it paired different biology (e.g. "catabolic" with "metabolic", "type II" with "type III" interferon, "amide" with "amine").

Terms that stay unlinked are still usable: `paper1_term_genes_long.csv` holds their Paper 1 gene lists, so MetaPath M7 can test Drug → Gene ∈ term directly.

## Coverage of the {len(mapped):,} significant Paper 1 terms

{chr(10).join(lines)}

**Result:** {n_graph:,} / {n_terms:,} terms ({100 * n_graph / n_terms:.1f}%) are linked to a graph node. **{n_usable:,} / {n_terms:,} terms are usable in MetaPaths**, because unlinked terms fall back to their Paper 1 gene lists (Drug →ACTS_ON→ Gene ∈ term).
KEGG and Hallmark sets rarely match one Reactome/GO node closely, because they are broad, mixed collections. That is expected, not an error. Their nearest graph node and Jaccard are still recorded (`nearest_*` columns) for transparency.

## Best KEGG/Hallmark proxies (top 10)

{chr(10).join(ex_lines)}

## Files
- `paper1_term_to_graph_map.csv`: one row per Paper 1 term → graph node, match type, score, and `use_in_metapaths`.
- `paper1_term_genes_long.csv`: Paper 1 term → progression gene (symbol + Ensembl), per group.
- `graph_pathway_process_nodes.csv`: all graph Pathway/BioProcess nodes with total and progression-gene member counts.
- `mapping_coverage.csv`: the coverage table above.

Note: Paper 1 gene lists contain only the progression genes in each term (the enrichment overlap), not the full pathway membership. Full membership is available only for graph-linked terms.
"""
(OUT / "README.md").write_text(summary, encoding="utf-8")
print(summary)
