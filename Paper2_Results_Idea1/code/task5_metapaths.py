"""Paper 2 Task 5: MetaPaths connecting drugs to fibrosis-progression biology.

Knowledge graph only (read-only Neo4j) + Paper 1 results. Drug -> Gene steps use
pharmacological-target links only (ACTS_ON actions other than ENZYME / TRANSPORTER /
CARRIER, as decided in Task 3). Drugs = the drugs from Task 2 with >=1 such link to a
progression gene.

MetaPaths (P = progression gene, T = any pharmacological target):
  M1   Drug -> P -> Disease (liver disease set from Task 4)
  M1f  Drug -> P -> Disease (fibrosis-spectrum subset: fatty liver, steatohepatitis,
       cirrhosis, fibrosis, portal hypertension, liver failure)
  M2   Drug -> P -> Pathway (Reactome)
  M3   Drug -> P -> BioProcess (GO BP)
  M4   Drug -> T -> Pathway <- P          (T != P)
  M5   Drug -> T -> Pathway <- P(cluster Ck), k = 1..5
  M6   Drug -> P where P is a significant stage-transition gene (Paper 1 Task 3, q < 0.05)
  M7   Drug -> P in Paper 1 fibrosis-enriched term (GO_BP / Reactome / KEGG / Hallmark);
       term membership from its graph node when linked (exact name or gene-overlap
       proxy), otherwise from Paper 1 gene lists (Task 5 prep)

Degree-normalised support for a drug d and end node e:
    DNS(d, e) = paths(d, e) / sqrt(deg(d) * deg(e))
deg(d) = pharmacological targets of d in the whole graph; deg(e) = genes attached to e
(disease, pathway, process, term) or, for gene end nodes, the gene's number of pathways
(M4/M5) or pharmacological drugs (M6). Totals are sums over (d, e) pairs.

Every Cypher statement used is written to Task5/metapath_queries.cypher.
Run from the repository root:

    python Paper2_Results_Idea1/code/task5_metapaths.py
"""
import base64
import getpass
import json
import os
import re
import time
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results_Idea1" / "Task5"
EX = OUT / "examples"
EX.mkdir(parents=True, exist_ok=True)

GENES = ROOT / "Paper2_Results_Idea1/Task1/Paper2_progression_genes.csv"
EDGES = ROOT / "Paper2_Results_Idea1/Task2/drug_gene_edges.csv"
CAND = ROOT / "Paper2_Results_Idea1/Task4/repurposing_candidates.csv"
MECH = ROOT / "Paper2_Results_Idea1/Task4/repurposing_candidates_mechanism_annotated.csv"
LIVER = ROOT / "Paper2_Results_Idea1/Task4/liver_disease_set.csv"
TRANS = ROOT / "Paper1_Results/Task3/task3_all_genes_all_transitions.csv"
TERM_MAP = ROOT / "Paper2_Results_Idea1/Task5/prep/paper1_term_to_graph_map.csv"
TERM_GENES = ROOT / "Paper2_Results_Idea1/Task5/prep/paper1_term_genes_long.csv"
P1_TERMS = ROOT / "Paper1_Results/Task4/task4_all_significant.csv"

PK = ["ENZYME", "TRANSPORTER", "CARRIER"]
FIB_SPECTRUM = r"fatty liver|steatohepatitis|cirrhosis|fibrosis|portal hypertension|liver failure"
Q_TRANSITION = 0.05

NEO4J_URL = os.environ.get("NEO4J_HTTP", "http://127.0.0.1:7474")
NEO4J_DB = os.environ.get("NEO4J_DATABASE", "neo4j")
NEO4J_USER = os.environ.get("NEO4J_USERNAME", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")

CYPHER_LOG = []


def cy(name, statement, params=None, log=True):
    """Run a read-only Cypher statement and record it."""
    if log:
        CYPHER_LOG.append((name, statement.strip()))
    headers = {"Authorization": "Basic " + base64.b64encode(f"{NEO4J_USER}:{PASSWORD}".encode()).decode(),
               "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": statement, "parameters": params or {}, "accessMode": "Read"}).encode()
    req = urllib.request.Request(f"{NEO4J_URL}/db/{NEO4J_DB}/query/v2", data=body, headers=headers, method="POST")
    t0 = time.time()
    res = json.load(urllib.request.urlopen(req, timeout=900))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    df = pd.DataFrame(res["data"]["values"], columns=res["data"]["fields"])
    print(f"  [{name}] {len(df):,} rows in {time.time() - t0:.1f}s")
    return df


# ------------------------------------------------------------------ inputs
genes = pd.read_csv(GENES)
prog = set(genes.ensembl_id)
t2 = pd.read_csv(EDGES)
drugs = sorted(t2.loc[~t2.Action_raw.isin(PK), "Drug_ID"].unique())
cand_ids = set(pd.read_csv(CAND).Drug_ID)
mech_ids = set(pd.read_csv(MECH).Drug_ID)
liver = pd.read_csv(LIVER)
liver = liver[~liver.excluded_non_hepatic]
liver_ids = liver.disease_id.tolist()
fib_ids = liver.loc[liver.disease_name.str.contains(FIB_SPECTRUM, case=False), "disease_id"].tolist()
print(f"drugs {len(drugs):,}; liver diseases {len(liver_ids)}; fibrosis-spectrum {len(fib_ids)}")

# ------------------------------------------------------------------ test small first
print("LIMIT tests")
cy("TEST M1", """
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN d.name, g.symbol, x.name LIMIT 5""", {"drugs": drugs[:50], "pk": PK, "prog": list(prog), "liver": liver_ids})
cy("TEST M4", """
MATCH (d:Drug)-[r:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)<-[:IN_PATHWAY]-(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND t <> g
RETURN d.name, t.symbol, p.name, g.symbol LIMIT 5""", {"drugs": drugs[:50], "pk": PK, "prog": list(prog)})

# ------------------------------------------------------------------ pull the graph pieces once
print("Pulling graph edges")
dt = cy("drug -> pharmacological targets (all genes)", """
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk
RETURN d.node_id AS drug, g.ensembl_id AS gene, r.action AS action""", {"drugs": drugs, "pk": PK})
gp = cy("gene -> Reactome pathway", "MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway) RETURN g.ensembl_id AS gene, p.node_id AS node, p.name AS name")
gb = cy("gene -> GO biological process", "MATCH (g:Gene)-[:INVOLVED_IN]->(b:BioProcess) RETURN g.ensembl_id AS gene, b.node_id AS node, b.name AS name")
gd = cy("gene -> liver disease", """
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(x:Disease) WHERE x.node_id IN $liver
RETURN g.ensembl_id AS gene, x.node_id AS node, x.name AS name, r.score AS score""", {"liver": liver_ids})
gene_drug_deg = cy("gene pharmacological drug degree", """
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE g.ensembl_id IN $prog AND NOT r.action IN $pk
RETURN g.ensembl_id AS gene, count(DISTINCT d) AS deg""", {"prog": list(prog), "pk": PK}).set_index("gene").deg

drug_deg = dt.groupby("drug").gene.nunique()
assert set(drug_deg.index) == set(drugs)
dp = dt[dt.gene.isin(prog)]                     # drug -> progression gene (pharmacological)
assert len(dp) == (~t2.Action_raw.isin(PK)).sum(), "drug->progression links must match Task 2"
sym = dict(zip(genes.ensembl_id, genes.Gene))
dname = dict(zip(t2.Drug_ID, t2.Drug))


def summarise(name, pairs, mid_col, end_col, end_deg, extra=None):
    """pairs: one row per path with columns drug, mid_col, end_col (or 'paths' weights)."""
    w = pairs["paths"] if "paths" in pairs else pd.Series(1, index=pairs.index)
    agg = pairs.assign(paths=w).groupby(["drug", end_col], as_index=False).paths.sum()
    agg["dns"] = agg.paths / np.sqrt(agg.drug.map(drug_deg).values * agg[end_col].map(end_deg).values)
    row = {"MetaPath": name, "paths": int(agg.paths.sum()), "unique drugs": agg.drug.nunique(),
           "unique genes": pairs[mid_col].nunique() if mid_col else np.nan,
           "unique end nodes": agg[end_col].nunique(), "drug–end pairs": len(agg),
           "degree-normalised support (sum)": round(agg.dns.sum(), 2),
           "mean DNS per pair": round(agg.dns.mean(), 4) if len(agg) else np.nan,
           "candidate drugs": len(set(agg.drug) & cand_ids), "main-list drugs": len(set(agg.drug) & mech_ids)}
    if extra:
        row.update(extra)
    per_drug = agg.groupby("drug").agg(paths=("paths", "sum"), dns=("dns", "sum")).rename(
        columns={"paths": f"{name}_paths", "dns": f"{name}_dns"})
    return row, per_drug, agg


rows, per_drug = [], []

# ------------------------------------------------------------------ M1 / M1f / M2 / M3
end_deg_disease = cy("liver disease gene degree", """
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(x:Disease) WHERE x.node_id IN $liver RETURN x.node_id AS node, count(g) AS deg""",
                     {"liver": liver_ids}).set_index("node").deg
pw_size = gp.groupby("node").gene.nunique()
bp_size = gb.groupby("node").gene.nunique()
for name, rel, deg in [("M1 Drug→Gene→LiverDisease", gd, end_deg_disease),
                       ("M1f Drug→Gene→FibrosisSpectrumDisease", gd[gd.node.isin(fib_ids)], end_deg_disease),
                       ("M2 Drug→Gene→Pathway", gp, pw_size),
                       ("M3 Drug→Gene→BioProcess", gb, bp_size)]:
    paths = dp.merge(rel[["gene", "node"]], on="gene")
    r, pd_, agg = summarise(name, paths, "gene", "node", deg)
    rows.append(r)
    per_drug.append(pd_)
    if name.startswith("M1"):
        agg.assign(drug_name=agg.drug.map(dname)).merge(
            rel[["node", "name"]].drop_duplicates(), on="node").to_csv(OUT / f"{name.split()[0]}_drug_disease_pairs.csv", index=False)

# ------------------------------------------------------------------ M4 / M5 (matrix form, T != P)
dr_idx = {d: i for i, d in enumerate(drugs)}
pw_ids = sorted(gp.node.unique())
pw_idx = {p: i for i, p in enumerate(pw_ids)}
prog_list = sorted(prog)
pg_idx = {g: i for i, g in enumerate(prog_list)}
gp_t = gp[gp.gene.isin(set(dt.gene))]
K = (dt.merge(gp_t[["gene", "node"]], on="gene").groupby(["drug", "node"]).size().reset_index(name="k"))
Km = sparse.csr_matrix((K.k.astype(np.float32), (K.drug.map(dr_idx), K.node.map(pw_idx))), shape=(len(drugs), len(pw_ids)))
gpp = gp[gp.gene.isin(prog)]
Mm = sparse.csr_matrix((np.ones(len(gpp), np.float32), (gpp.node.map(pw_idx), gpp.gene.map(pg_idx))),
                       shape=(len(pw_ids), len(prog_list)))
P = (Km @ Mm).toarray()
# remove T == P paths: drug d targets progression gene g, counted once per pathway containing g
n_pw_of_gene = np.asarray(Mm.sum(axis=0)).ravel()
for d, g in zip(dp.drug, dp.gene):
    P[dr_idx[d], pg_idx[g]] -= n_pw_of_gene[pg_idx[g]]
assert P.min() >= 0
deg_d = drug_deg.reindex(drugs).values.astype(float)
with np.errstate(divide="ignore", invalid="ignore"):
    DNS = P / np.sqrt(np.outer(deg_d, np.where(n_pw_of_gene > 0, n_pw_of_gene, np.nan)))
DNS = np.nan_to_num(DNS)
mid_genes_m4 = set(dt.gene) & set(gp.gene)


def m4_row(name, cols, extra=None):
    sub, subd = P[:, cols], DNS[:, cols]
    has = sub > 0
    rows.append({"MetaPath": name, "paths": int(sub.sum()), "unique drugs": int(has.any(axis=1).sum()),
                 "unique genes": np.nan, "unique end nodes": int(has.any(axis=0).sum()), "drug–end pairs": int(has.sum()),
                 "degree-normalised support (sum)": round(float(subd.sum()), 2),
                 "mean DNS per pair": round(float(subd[has].mean()), 4) if has.any() else np.nan,
                 "candidate drugs": int(sum(has[dr_idx[d]].any() for d in cand_ids if d in dr_idx)),
                 "main-list drugs": int(sum(has[dr_idx[d]].any() for d in mech_ids if d in dr_idx)), **(extra or {})})
    per_drug.append(pd.DataFrame({f"{name}_paths": sub.sum(axis=1), f"{name}_dns": subd.sum(axis=1)}, index=drugs))


m4_row("M4 Drug→Gene→Pathway←ProgressionGene", list(range(len(prog_list))),
       {"notes": f"middle genes (any pharmacological target in a pathway): {len(mid_genes_m4):,}"})
cl = genes.set_index("ensembl_id").trajectory_cluster
for c in ["C1", "C2", "C3", "C4", "C5"]:
    cols = [pg_idx[g] for g in prog_list if cl.get(g) == c]
    m4_row(f"M5 Drug→Gene→Pathway←{c} gene", cols, {"notes": f"{len(cols)} cluster genes"})

# ------------------------------------------------------------------ M6 stage-transition genes
tr = pd.read_csv(TRANS, encoding="utf-8-sig")
tr = tr[tr.q_value < Q_TRANSITION]
for t, s in tr.groupby("transition"):
    paths = dp[dp.gene.isin(set(s.ensembl_id))].rename(columns={"gene": "end"}).assign(mid=lambda x: x.end)
    up_ids = set(s.loc[s.beta_adjusted > 0, "ensembl_id"])
    r, pd_, agg = summarise(f"M6 Drug→{t} transition gene", paths, "mid", "end", gene_drug_deg,
                            {"notes": f"{len(s)} significant genes; {len(set(paths.end)):,} with a drug "
                                      f"({len(set(paths.end) & up_ids)} rising / {len(set(paths.end) - up_ids)} falling at this step)"})
    rows.append(r)
    per_drug.append(pd_)

# ------------------------------------------------------------------ M7 Paper 1 fibrosis-enriched terms
tmap = pd.read_csv(TERM_MAP)
tgl = pd.read_csv(TERM_GENES)
p1 = pd.read_csv(P1_TERMS, encoding="utf-8-sig")
fib_groups = [g for g in p1.group.unique() if not g.startswith("inflammation_only")]
fib_terms = set(p1.loc[p1.group.isin(fib_groups), "term"])
tmap = tmap[tmap.term.isin(fib_terms)]
graph_members = pd.concat([gp[["gene", "node"]], gb[["gene", "node"]]])
mem_rows = []
for r in tmap.itertuples():
    if r.match_type in ("name", "gene_overlap_proxy"):
        g = set(graph_members.loc[graph_members.node == r.graph_node_id, "gene"]) & prog
        size = int(((graph_members.node == r.graph_node_id)).sum())
    else:
        g = set(tgl.loc[(tgl.term == r.term) & tgl.group.isin(fib_groups), "ensembl_id"].dropna())
        size = int(p1.loc[p1.term == r.term, "set_size"].max())
    mem_rows += [(r.term, r.database, r.match_type, x, size) for x in g]
mem = pd.DataFrame(mem_rows, columns=["term", "database", "match_type", "gene", "size"])
term_size = mem.drop_duplicates("term").set_index("term")["size"]
m7_all = dp.merge(mem, on="gene")
for db in ["GO_BP", "Reactome", "KEGG", "Hallmark"]:
    for mt_label, mts in [("graph node", ["name"]), ("graph proxy (approx.)", ["gene_overlap_proxy"]),
                          ("Paper 1 gene list", ["none"])]:
        sub = m7_all[(m7_all.database == db) & m7_all.match_type.isin(mts)]
        nterms = int(((tmap.database == db) & tmap.match_type.isin(mts)).sum())
        if nterms == 0:
            continue
        r, pd_, agg = summarise(f"M7 {db} [{mt_label}]", sub, "gene", "term", term_size,
                                {"notes": f"{nterms} fibrosis-enriched terms of this kind"})
        rows.append(r)
        per_drug.append(pd_)
m7_pairs = m7_all.groupby(["drug", "term", "database", "match_type"]).gene.agg(
    n_genes="nunique", genes=lambda s: ";".join(sorted(sym.get(x, x) for x in set(s)))).reset_index()
m7_pairs["drug_name"] = m7_pairs.drug.map(dname)
m7_pairs.to_csv(OUT / "M7_drug_term_pairs.csv", index=False)

# ------------------------------------------------------------------ Neo4j cross-checks (counts computed in the graph)
print("Cross-checking counts inside Neo4j")
xc = []
for name, stmt, params, key in [
    ("COUNT M1", """MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT x) AS ends""",
     {"drugs": drugs, "pk": PK, "prog": list(prog), "liver": liver_ids}, "M1 Drug→Gene→LiverDisease"),
    ("COUNT M2", """MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT p) AS ends""",
     {"drugs": drugs, "pk": PK, "prog": list(prog)}, "M2 Drug→Gene→Pathway"),
    ("COUNT M3", """MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:INVOLVED_IN]->(b:BioProcess)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $prog
RETURN count(*) AS paths, count(DISTINCT d) AS drugs, count(DISTINCT g) AS genes, count(DISTINCT b) AS ends""",
     {"drugs": drugs, "pk": PK, "prog": list(prog)}, "M3 Drug→Gene→BioProcess"),
    ("COUNT M4 (aggregated: per pathway, target pairs x progression members, minus T = P)", """
MATCH (d:Drug)-[r:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk
WITH p, count(*) AS dt_pairs, sum(CASE WHEN t.ensembl_id IN $prog THEN 1 ELSE 0 END) AS self_pairs
MATCH (p)<-[:IN_PATHWAY]-(g:Gene) WHERE g.ensembl_id IN $prog
WITH p, dt_pairs, self_pairs, count(g) AS n_prog
RETURN sum(dt_pairs * n_prog - self_pairs) AS paths""",
     {"drugs": drugs, "pk": PK, "prog": list(prog)}, "M4 Drug→Gene→Pathway←ProgressionGene"),
]:
    res = cy(name, stmt, params).iloc[0]
    mine = next(r for r in rows if r["MetaPath"] == key)
    ok = int(res.paths) == mine["paths"] and all(
        int(res[c]) == mine[k] for c, k in [("drugs", "unique drugs"), ("genes", "unique genes"), ("ends", "unique end nodes")]
        if c in res)
    xc.append({"MetaPath": key, "paths_python": mine["paths"], "paths_neo4j": int(res.paths), "match": ok})
for t, s in tr.groupby("transition"):
    res = cy(f"COUNT M6 {t}", """MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE d.node_id IN $drugs AND NOT r.action IN $pk AND g.ensembl_id IN $genes RETURN count(*) AS paths""",
             {"drugs": drugs, "pk": PK, "genes": s.ensembl_id.tolist()}).iloc[0]
    mine = next(r for r in rows if r["MetaPath"] == f"M6 Drug→{t} transition gene")
    xc.append({"MetaPath": mine["MetaPath"], "paths_python": mine["paths"], "paths_neo4j": int(res.paths),
               "match": int(res.paths) == mine["paths"]})
xc = pd.DataFrame(xc)
xc.to_csv(OUT / "crosscheck_python_vs_neo4j.csv", index=False)
assert xc.match.all(), xc

# ------------------------------------------------------------------ outputs
counts = pd.DataFrame(rows)
counts.to_csv(OUT / "metapath_counts.csv", index=False)
defs = pd.DataFrame([
    ("M1", "Drug -[ACTS_ON, pharmacological]-> ProgressionGene -[ASSOCIATED_WITH]-> Disease", "Liver disease set (Task 4, 161 diseases)", "genes associated with the disease"),
    ("M1f", "as M1", f"Fibrosis-spectrum liver diseases ({len(fib_ids)}; name matches /{FIB_SPECTRUM}/)", "genes associated with the disease"),
    ("M2", "Drug -[ACTS_ON]-> ProgressionGene -[IN_PATHWAY]-> Pathway", "Reactome pathways in the graph", "pathway size"),
    ("M3", "Drug -[ACTS_ON]-> ProgressionGene -[INVOLVED_IN]-> BioProcess", "GO biological processes in the graph", "process size"),
    ("M4", "Drug -[ACTS_ON]-> Gene -[IN_PATHWAY]-> Pathway <-[IN_PATHWAY]- ProgressionGene (Gene ≠ ProgressionGene)", "any progression gene", "number of pathways of the end gene"),
    ("M5", "as M4, end gene restricted to one F0–F4 trajectory cluster", "Paper 1 clusters C1–C5", "number of pathways of the end gene"),
    ("M6", "Drug -[ACTS_ON]-> ProgressionGene, gene significant at a stage transition", "Paper 1 Task 3, q < 0.05, per transition", "number of pharmacological drugs of the gene"),
    ("M7", "Drug -[ACTS_ON]-> ProgressionGene ∈ Paper 1 fibrosis-enriched term", "terms enriched in fibrosis_only / shared / C1–C5 groups; membership via graph node or Paper 1 gene list", "term size"),
], columns=["MetaPath", "Pattern", "End-node set", "End-node degree used in DNS"])
defs["Drug -> Gene rule"] = "ACTS_ON with action not in ENZYME/TRANSPORTER/CARRIER; drugs from Task 2"
defs["DNS formula"] = "paths(d,e) / sqrt(deg(d) × deg(e)), deg(d) = pharmacological targets of d"
defs.to_csv(OUT / "metapath_definitions.csv", index=False)

drug_scores = pd.concat(per_drug, axis=1).fillna(0)
drug_scores.index.name = "Drug_ID"
drug_scores.insert(0, "Drug", drug_scores.index.map(dname))
drug_scores.insert(1, "repurposing_candidate", drug_scores.index.isin(cand_ids))
drug_scores.insert(2, "main_list", drug_scores.index.isin(mech_ids))
drug_scores.insert(3, "pharm_targets_graph", drug_scores.index.map(drug_deg))
drug_scores.round(4).sort_values("M1f Drug→Gene→FibrosisSpectrumDisease_dns", ascending=False).to_csv(OUT / "metapath_drug_scores.csv")

with open(OUT / "metapath_queries.cypher", "w", encoding="utf-8") as f:
    f.write("// Paper 2 Task 5 — every read-only Cypher statement used (run order).\n"
            "// Parameters: $drugs = Task 2 drugs with a pharmacological link to a progression gene;\n"
            "// $pk = ['ENZYME','TRANSPORTER','CARRIER']; $prog = 6,222 progression genes (Ensembl);\n"
            "// $liver = Task 4 liver disease set (161 ids); $genes = significant transition genes.\n"
            "// M4/M5 path counts are computed from the pulled edges by sparse matrix product and\n"
            "// verified with the aggregated COUNT M4 statement below.\n\n")
    for name, s in CYPHER_LOG:
        f.write(f"// ---- {name}\n{s};\n\n")

# ------------------------------------------------------------------ 3 example subgraphs for quality checking
ga = genes.set_index("ensembl_id")
dir_of = ga.fibrosis_direction.fillna(ga.inflammation_direction)
cls_of = ga.progression_class
act = dict(zip(zip(t2.Drug_ID, t2.Gene_ID), t2.Action_direction))
phase = dict(zip(t2.Drug_ID, t2.max_phase))
COLG = {"fibrosis_only": "#c0392b", "shared": "#7d3c98", "inflammation_only": "#2471a3"}
COLE = {"down": "#2471a3", "up": "#c0392b", "mixed": "#d4ac0d", "unknown": "#aab4be"}


def gene_label(g):
    return f"{sym[g]} {'⬆' if dir_of.get(g) == 'positive' else '⬇'}"


def draw(edges, gene_ids, title, caption, fname):
    """edges: source, target, relation, source_type, target_type, action_direction (+ extras)."""
    edges.to_csv(EX / f"{fname}.csv", index=False)
    gclass = {gene_label(g): cls_of[g] for g in gene_ids}
    G = nx.DiGraph()
    for r in edges.itertuples():
        G.add_node(r.source, layer={"drug": 0, "gene": 1}.get(r.source_type, 2))
        G.add_node(r.target, layer={"drug": 0, "gene": 1}.get(r.target_type, 2))
        G.add_edge(r.source, r.target, d=r.action_direction)
    pos = nx.multipartite_layout(G, subset_key="layer", align="vertical", scale=2)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    for d, c in COLE.items():
        es = [(u, v) for u, v, a in G.edges(data=True) if a["d"] == d]
        nx.draw_networkx_edges(G, pos, edgelist=es, edge_color=c, width=2.4 if d in ("up", "down") else 1.2,
                               arrows=True, arrowsize=14, ax=ax, node_size=1700)
    for layer, shape, size, colour in [(0, "s", 1800, None), (1, "o", 1600, None), (2, "h", 2400, "#d5f5e3")]:
        ns = [n for n, a in G.nodes(data=True) if a["layer"] == layer]
        col = ["#f4d03f"] * len(ns) if layer == 0 else ([COLG[gclass[n]] for n in ns] if layer == 1 else [colour] * len(ns))
        nx.draw_networkx_nodes(G, pos, nodelist=ns, node_shape=shape, node_size=size, node_color=col,
                               edgecolors="#1f2933", alpha=0.9, ax=ax)
    lab = {n: n if len(n) <= 18 else n[:17] + "…" for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=lab, font_size=8, ax=ax)
    ax.set_title(title, fontsize=12.5, fontweight="bold", loc="left")
    ax.text(0, -0.04, caption, transform=ax.transAxes, fontsize=9.5, va="top", wrap=True)
    handles = [plt.Line2D([], [], color=COLE["down"], lw=2.4, label="drug pushes gene ⬇"),
               plt.Line2D([], [], color=COLE["up"], lw=2.4, label="drug pushes gene ⬆"),
               plt.Line2D([], [], color=COLE["unknown"], lw=1.2, label="direction unknown / link"),
               plt.Line2D([], [], marker="o", ls="", color=COLG["fibrosis_only"], ms=9, label="fibrosis-only gene"),
               plt.Line2D([], [], marker="o", ls="", color=COLG["shared"], ms=9, label="shared gene"),
               plt.Line2D([], [], marker="o", ls="", color=COLG["inflammation_only"], ms=9, label="inflammation-only gene"),
               plt.Line2D([], [], ls="", label="⬆ / ⬇ after gene = rises / falls with fibrosis")]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=False, bbox_to_anchor=(1.0, 1))
    ax.axis("off")
    fig.savefig(EX / f"{fname}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


examples = []
# E1: main-list drug with the highest M1f support -> its genes -> fibrosis-spectrum diseases
ds = drug_scores[drug_scores.main_list].sort_values("M1f Drug→Gene→FibrosisSpectrumDisease_dns", ascending=False)
e1 = ds.index[0]
x = dp[dp.drug == e1].merge(gd[gd.node.isin(fib_ids)], on="gene")
e1_edges = pd.concat([
    pd.DataFrame({"source": dname[e1], "target": x.gene.map(gene_label), "relation": "ACTS_ON",
                  "source_type": "drug", "target_type": "gene",
                  "action_direction": [act.get((e1, g), "unknown") for g in x.gene]}).drop_duplicates(),
    pd.DataFrame({"source": x.gene.map(gene_label), "target": x.name, "relation": "ASSOCIATED_WITH",
                  "source_type": "gene", "target_type": "disease", "action_direction": "unknown", "score": x.score.round(3)})])
draw(e1_edges, x.gene.unique(), f"Example 1 (M1f): {dname[e1]} → progression genes → fibrosis-spectrum liver diseases",
     f"{dname[e1]} (max phase {phase[e1]:g}; {int(drug_deg[e1])} pharmacological targets in the graph) acts on "
     f"{x.gene.nunique()} progression genes that the graph links to {x.node.nunique()} fibrosis-spectrum liver diseases. "
     "It has the highest degree-normalised M1f support among main-list drugs.", "example1_M1f")
examples.append(("Example 1 (M1f)", dname[e1], ";".join(x.gene.map(sym).unique()), "; ".join(sorted(x.name.unique()))))

# E2: Hallmark EMT (fibrosis program, no graph node): main-list drugs with most EMT genes
emt = mem[mem.term == "HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION"]
y = dp[dp.gene.isin(set(emt.gene)) & dp.drug.isin(mech_ids)]
e2_drugs = y.groupby("drug").gene.nunique().sort_values(ascending=False).index[:3].tolist()
y = y[y.drug.isin(e2_drugs)]
e2_edges = pd.concat([
    pd.DataFrame({"source": y.drug.map(dname), "target": y.gene.map(gene_label), "relation": "ACTS_ON",
                  "source_type": "drug", "target_type": "gene",
                  "action_direction": [act.get((d, g), "unknown") for d, g in zip(y.drug, y.gene)]}),
    pd.DataFrame({"source": y.gene.map(gene_label).unique(), "target": "Hallmark EMT\n(Paper 1 list)",
                  "relation": "IN_TERM (Paper 1 gene list)", "source_type": "gene", "target_type": "term",
                  "action_direction": "unknown"})])
draw(e2_edges, y.gene.unique(), "Example 2 (M7): main-list drugs → genes of the Hallmark EMT fibrosis program",
     "Hallmark epithelial–mesenchymal transition is enriched among Paper 1 fibrosis genes but has no graph node, so its "
     f"membership comes from the Paper 1 gene list. Shown: the 3 main-list drugs touching the most EMT genes "
     f"({', '.join(dname[d] for d in e2_drugs)}).", "example2_M7_EMT")
examples.append(("Example 2 (M7)", ", ".join(dname[d] for d in e2_drugs), ";".join(y.gene.map(sym).unique()), "Hallmark EMT"))

# E3: shortlist stage-transition gene PDGFRA and the repurposing candidates acting on it
g3 = genes.loc[genes.Gene == "PDGFRA", "ensembl_id"].iloc[0]
z = dp[(dp.gene == g3) & dp.drug.isin(cand_ids)]
trz = tr[tr.ensembl_id == g3].sort_values("q_value")
tlab = f"{trz.transition.iloc[0]} (q={trz.q_value.iloc[0]:.1e})" if len(trz) else "no significant step"
e3_edges = pd.concat([
    pd.DataFrame({"source": z.drug.map(dname), "target": gene_label(g3), "relation": "ACTS_ON", "source_type": "drug",
                  "target_type": "gene", "action_direction": [act.get((d, g3), "unknown") for d in z.drug],
                  "main_list": z.drug.isin(mech_ids)}),
    pd.DataFrame({"source": [gene_label(g3)], "target": [f"stage step\n{tlab}"], "relation": "STAGE_TRANSITION (Paper 1)",
                  "source_type": "gene", "target_type": "transition", "action_direction": "unknown"})])
draw(e3_edges, [g3], "Example 3 (M6): repurposing candidates acting on PDGFRA (Paper 1 shortlist, stage-transition gene)",
     f"PDGFRA rises with fibrosis and is significant at the {tlab} step. {z.drug.nunique()} repurposing candidates act on it; "
     "blue arrows are inhibitors, i.e. they push a rising gene down (direction-consistency is assessed formally in Task 7).",
     "example3_M6_PDGFRA")
examples.append(("Example 3 (M6)", ", ".join(sorted(z.drug.map(dname))), "PDGFRA", tlab))
pd.DataFrame(examples, columns=["Example", "Drugs", "Genes", "End nodes"]).to_csv(EX / "examples_index.csv", index=False)

# ------------------------------------------------------------------ summary.md
def md(df, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(r[c]) else (f"{r[c]:,}" if isinstance(r[c], (int, np.integer)) else
                                                                   (f"{r[c]:,.0f}" if isinstance(r[c], float) and r[c] == int(r[c]) else str(r[c])))
                                     for c in cols) + " |")
    return "\n".join(out)


top_m1f = drug_scores[drug_scores.main_list].sort_values("M1f Drug→Gene→FibrosisSpectrumDisease_dns", ascending=False).head(10)
top_m1f = top_m1f.assign(**{"M1f paths": top_m1f["M1f Drug→Gene→FibrosisSpectrumDisease_paths"].astype(int),
                            "M1f DNS": top_m1f["M1f Drug→Gene→FibrosisSpectrumDisease_dns"].round(3),
                            "targets": top_m1f.pharm_targets_graph.astype(int)})
m6n = counts[counts.MetaPath.str.startswith("M6")][["MetaPath", "notes"]]
summary = f"""# Paper 2 — Task 5: MetaPaths from drugs to fibrosis-progression biology

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **{len(genes):,} genes**.
**Scope:** knowledge graph (read-only Neo4j) + Paper 1 results only. Drug → Gene steps use **pharmacological-target links** (no ENZYME/TRANSPORTER/CARRIER; Task 3). Drugs = the **{len(drugs):,}** Task 2 drugs with such a link to a progression gene ({len(cand_ids):,} repurposing candidates, {len(mech_ids)} on the main list; Task 4).
Script: `Paper2_Results_Idea1/code/task5_metapaths.py`. Every Cypher statement: `metapath_queries.cypher`.

**MetaPaths show biological connectivity in the graph, not proof that a drug works.**

![Task 5 diagram](Task5_diagram.png)

## Definitions
See `metapath_definitions.csv`. Degree-normalised support for drug *d* and end node *e*: **DNS = paths(d,e) / √(deg(d) × deg(e))**, where deg(d) = pharmacological targets of *d* in the whole graph and deg(e) = genes on the end node (disease, pathway, process, term) or, for gene end nodes, pathways of the gene (M4/M5) or drugs of the gene (M6). DNS down-weights promiscuous drugs and huge pathways. DNS values are comparable **within** a MetaPath, not across MetaPaths (different end-node degrees).

## Results

{md(counts, ["MetaPath", "paths", "unique drugs", "unique genes", "unique end nodes", "degree-normalised support (sum)", "mean DNS per pair", "candidate drugs", "main-list drugs"])}

"unique genes" = middle gene (for M4/M5 it is any pharmacological target, so it is not shown per row; {len(mid_genes_m4):,} target genes sit in at least one pathway). M7 rows are split by database and by how the term reaches the graph: graph node (exact name), graph proxy (gene overlap, **approximate**), or Paper 1 gene list (no graph node).

### Stage-transition genes with drugs (M6)
{md(m6n, ["MetaPath", "notes"])}

### Main-list drugs with the strongest fibrosis-spectrum disease support (M1f, DNS)
{md(top_m1f.reset_index(), ["Drug", "targets", "M1f paths", "M1f DNS"])}

The top of this list is dominated by **PPAR agonists** (glitazars, fenofibric acid, GW501516). The graph reaches them through PPARA/PPARG/PPARD → fatty liver disease / NASH / cirrhosis. This is a plausible pattern, but **support is not efficacy**, and PPARA falls while PPARG/PPARD rise with fibrosis (see Example 1 and Task 7).

## Verification
Path counts computed in Python were re-computed **inside Neo4j** with aggregated Cypher (`crosscheck_python_vs_neo4j.csv`). All {len(xc)} checks match (M1, M2, M3, M4 and the four M6 transitions). LIMIT 5 test queries were run first for M1 and M4.

## Example subgraphs (quality checks, `examples/`)
1. **Example 1 (M1f), `example1_M1f.png`**: **{dname[e1]}** → PPARA ⬇ / PPARG ⬆ / PPARD ⬆ → 7 fibrosis-spectrum diseases. All three arrows are "agonist" (pushes ⬆). For PPARA, which falls with fibrosis, that is direction-consistent. For PPARG and PPARD, which rise, it is not. A good reminder that one drug can be consistent on one target and inconsistent on another.
2. **Example 2 (M7), `example2_M7_EMT.png`**: main-list drugs reaching the **Hallmark EMT** fibrosis program (no graph node, so Paper 1 gene list). Marimastat inhibits MMP2 (rising) and also links to MMP14; adapalene and pseudoephedrine reach JUN via "target" links of unknown direction. This shows that M7 works for KEGG/Hallmark terms, and that weak "unknown" links must not be over-read.
3. **Example 3 (M6), `example3_M6_PDGFRA.png`**: **PDGFRA**, a Paper 1 shortlist gene that rises and is significant at the **{tlab}** step. 4 repurposing candidates act on it; ripretinib and amuvatinib are inhibitors (push a rising gene down), while fostamatinib and ponatinib links have unknown direction.

## Files
`metapath_definitions.csv`, `metapath_counts.csv`, `metapath_drug_scores.csv` (per-drug paths and DNS for every MetaPath, with candidate/main-list flags: input for the Task 6 K component), `M1_drug_disease_pairs.csv`, `M1f_drug_disease_pairs.csv`, `M7_drug_term_pairs.csv`, `crosscheck_python_vs_neo4j.csv`, `metapath_queries.cypher`, `examples/`.

## Caveats
- Raw path counts favour well-connected drugs and genes. Use DNS, and treat it as a supporting feature, not a ranking.
- M4/M5 count paths through *any* pharmacological target sharing a pathway with a progression gene, so they are broad by design.
- Gene–disease links include cancer-heavy liver terms. M1f restricts to the fibrosis spectrum ({len(fib_ids)} diseases).
- KEGG/Hallmark terms reach the graph mostly through Paper 1 gene lists. Graph proxies are approximate.
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(counts.to_string())
print(xc.to_string())
