"""Paper 2 Task 5 (revised): MetaPaths on the heterogeneous knowledge graph.

Revision of Task 5 after review (16 Oct 2026):
  * the Drug -> Gene -> Biological Process MetaPath is removed (GO BP terms too);
  * every MetaPath reports paths, unique drugs / genes / pathways / end nodes, start-end
    pairs, and UNIQUE COMBINATIONS = start-end pairs joined by exactly one route;
  * repurposing pairs: drug - liver disease pairs reached through genes (and pathways)
    that are NOT already known drug uses;
  * the main analysis uses ALL Drug-[:ACTS_ON]->Gene links; a pharmacological-only version
    (ENZYME / TRANSPORTER / CARRIER links removed) is reported beside it.

MetaPaths (T = any gene a drug acts on, P = Paper 1 progression gene, P != T):
  MP1  Drug -> T(progression) -> LiverDisease
  MP2  Drug -> T(progression) -> Pathway
  MP3  Drug -> T -> Pathway <- P
  MP4  as MP3, P in one F0-F4 trajectory cluster (C1..C5)
  MP5  as MP3, P significant at one stage transition (q < 0.05)
  MP6  Drug -> T -> Paper 1 fibrosis-enriched pathway (Reactome via graph node; KEGG and
       Hallmark via Paper 1 gene lists)
  MP7  Drug -> T -> Pathway <- P -> LiverDisease   (full repurposing route)

Read-only Neo4j (live liver_kg). Password from NEO4J_PASSWORD.

    python Paper2_Results/code/task5_revised_metapaths.py
"""
import base64
import getpass
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"
OUT = RES / "Task5_revised"
OUT.mkdir(exist_ok=True)
PK = ["ENZYME", "TRANSPORTER", "CARRIER"]
FIB_SPECTRUM = r"fatty liver|steatohepatitis|cirrhosis|fibrosis|portal hypertension|liver failure"
PW = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")
LOG = []


def cy(name, stmt, params=None):
    LOG.append((name, stmt.strip()))
    h = {"Authorization": "Basic " + base64.b64encode(f"neo4j:{PW}".encode()).decode(),
         "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": stmt, "parameters": params or {}, "accessMode": "Read"}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:7474/db/neo4j/query/v2", data=body, headers=h, method="POST"), timeout=900))
    if r.get("errors"):
        raise RuntimeError(r["errors"])
    return pd.DataFrame(r["data"]["values"], columns=r["data"]["fields"])


# ------------------------------------------------------------------ inputs
genes = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
prog = genes.ensembl_id.tolist()
prog_set = set(prog)
sym = dict(zip(genes.ensembl_id, genes.Gene))
cluster = dict(zip(genes.ensembl_id, genes.trajectory_cluster))
liver = pd.read_csv(RES / "Task4/liver_disease_set.csv")
liver = liver[~liver.excluded_non_hepatic]
liver_ids = liver.disease_id.tolist()
fib_ids = set(liver.loc[liver.disease_name.str.contains(FIB_SPECTRUM, case=False), "disease_id"])
trans = pd.read_csv(ROOT / "Paper1_Results/Task3/task3_all_genes_all_transitions.csv", encoding="utf-8-sig")
trans = trans[trans.q_value < 0.05]
drugs = sorted(pd.read_csv(RES / "Task2/drug_gene_edges.csv").Drug_ID.unique())

cy("TEST MP7 (LIMIT 5)", """
MATCH (d:Drug)-[:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)<-[:IN_PATHWAY]-(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog AND x.node_id IN $liver AND t <> g
RETURN d.name, t.symbol, p.name, g.symbol, x.name LIMIT 5""", {"drugs": drugs[:50], "prog": prog, "liver": liver_ids})
dt = cy("drug -> all targets", """
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE d.node_id IN $drugs
RETURN d.node_id AS drug, d.name AS drug_name, g.ensembl_id AS gene, g.symbol AS symbol, r.action AS action""", {"drugs": drugs})
gp = cy("gene -> pathway", "MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway) RETURN g.ensembl_id AS gene, p.node_id AS pathway, p.name AS pathway_name")
gdis = cy("progression gene -> liver disease", """
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(x:Disease) WHERE g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN g.ensembl_id AS gene, x.node_id AS disease, x.name AS disease_name, r.score AS score""", {"prog": prog, "liver": liver_ids})
known = cy("known drug -> liver disease uses", """
MATCH (d:Drug)-[r:TREATS|OFF_LABEL_FOR|CONTRAINDICATED_IN]->(x:Disease) WHERE d.node_id IN $drugs AND x.node_id IN $liver
RETURN d.node_id AS drug, x.node_id AS disease, type(r) AS relation""", {"drugs": drugs, "liver": liver_ids})
dname = dict(zip(dt.drug, dt.drug_name))
disname = dict(zip(gdis.disease, gdis.disease_name.fillna(gdis.disease)))
pwname = dict(zip(gp.pathway, gp.pathway_name))
known_uses = known[known.relation.isin(["TREATS", "OFF_LABEL_FOR"])].groupby(["drug", "disease"]).relation.agg(lambda s: ";".join(sorted(set(s))))
contra = set(map(tuple, known.loc[known.relation == "CONTRAINDICATED_IN", ["drug", "disease"]].values))

# Paper 1 fibrosis pathways (MP6): Reactome via graph node; KEGG / Hallmark via Paper 1 gene lists. GO BP omitted.
p1 = pd.read_csv(ROOT / "Paper1_Results/Task4/task4_all_significant.csv", encoding="utf-8-sig")
p1 = p1[~p1.group.str.startswith("inflammation_only") & p1.database.isin(["Reactome", "KEGG", "Hallmark"])]
tmap = pd.read_csv(RES / "Task5/prep/paper1_term_to_graph_map.csv").set_index("term")
tl = pd.read_csv(RES / "Task5/prep/paper1_term_genes_long.csv")
mem = []
for term, db in p1[["term", "database"]].drop_duplicates().values:
    node = tmap.graph_node_id.get(term)
    mt = tmap.match_type.get(term, "none")
    if db == "Reactome" and isinstance(node, str) and mt == "name":
        g_ = set(gp.loc[gp.pathway == node, "gene"]); src = "graph node (all members)"
    else:
        g_ = set(tl.loc[(tl.term == term) & ~tl.group.str.startswith("inflammation_only"), "ensembl_id"].dropna()); src = "Paper 1 gene list (progression genes)"
    mem += [(term, db, src, x) for x in g_]
mem = pd.DataFrame(mem, columns=["term", "database", "membership", "gene"])


def run(links, tag):
    """All MetaPaths for one Drug->Gene link set. Returns count rows and pair tables."""
    rows, pairs = [], {}
    d_idx = {d: i for i, d in enumerate(sorted(links.drug.unique()))}
    drugs_ = list(d_idx)
    dp = links[links.gene.isin(prog_set)]

    def summarise(name, path_df, start, mid, end, extra_unique=None):
        cnt = path_df.groupby([start, end]).size()
        r = {"MetaPath": name, "links used": tag, "paths": int(len(path_df)), "unique drugs": path_df[start].nunique(),
             "unique genes": path_df[mid].nunique(), "unique end nodes": path_df[end].nunique(),
             "drug–end pairs": int(len(cnt)), "unique combinations (pairs with exactly one route)": int((cnt == 1).sum())}
        r.update(extra_unique or {})
        rows.append(r)
        return cnt

    # MP1
    p = dp.merge(gdis[["gene", "disease"]], on="gene")
    cnt = summarise("MP1 Drug→Gene→LiverDisease", p, "drug", "gene", "disease")
    pairs["MP1"] = (p, cnt)
    pf = p[p.disease.isin(fib_ids)]
    summarise("MP1f Drug→Gene→FibrosisSpectrumDisease", pf, "drug", "gene", "disease")
    # MP2
    p2 = dp.merge(gp[["gene", "pathway"]], on="gene")
    summarise("MP2 Drug→Gene→Pathway", p2, "drug", "gene", "pathway", {"unique pathways": p2.pathway.nunique()})

    # MP3-MP5, MP7 via sparse matrices, excluding T == P
    pw_ids = sorted(gp.pathway.unique()); w_idx = {w: i for i, w in enumerate(pw_ids)}
    p_idx = {g: i for i, g in enumerate(prog)}
    lt = links.merge(gp[["gene", "pathway"]], on="gene")
    K = sparse.csr_matrix((np.ones(len(lt)), (lt.drug.map(d_idx), lt.pathway.map(w_idx))), shape=(len(drugs_), len(pw_ids)))
    gpp = gp[gp.gene.isin(prog_set)]
    M = sparse.csr_matrix((np.ones(len(gpp)), (gpp.pathway.map(w_idx), gpp.gene.map(p_idx))), shape=(len(pw_ids), len(prog)))
    P = (K @ M).toarray()
    npw = np.asarray(M.sum(axis=0)).ravel()
    for d, g in zip(dp.drug, dp.gene):
        P[d_idx[d], p_idx[g]] -= npw[p_idx[g]]
    assert P.min() >= 0
    # pathways that carry at least one valid route (target and a different progression gene)
    tgt_in = lt.groupby("pathway").gene.agg(set)
    prog_in = gpp.groupby("pathway").gene.agg(set)
    valid_pw = {w for w in tgt_in.index.intersection(prog_in.index)
                if any(t != q for t in tgt_in[w] for q in prog_in[w])}
    mid_genes = set(lt.loc[lt.pathway.isin(valid_pw), "gene"])

    def mat_row(name, cols, pw_subset=None):
        sub = P[:, cols]
        has = sub > 0
        pws = valid_pw if pw_subset is None else pw_subset
        mids = set(lt.loc[lt.pathway.isin(pws), "gene"])
        rows.append({"MetaPath": name, "links used": tag, "paths": int(sub.sum()), "unique drugs": int(has.any(axis=1).sum()),
                     "unique genes": len(mids), "unique end nodes": int(has.any(axis=0).sum()),
                     "drug–end pairs": int(has.sum()), "unique combinations (pairs with exactly one route)": int((sub == 1).sum()),
                     "unique pathways": len(pw_subset) if pw_subset is not None else len(valid_pw)})
        return sub

    allcols = list(range(len(prog)))
    mat_row("MP3 Drug→Gene→Pathway←ProgressionGene", allcols)
    for c in ["C1", "C2", "C3", "C4", "C5"]:
        cols = [p_idx[g] for g in prog if cluster.get(g) == c]
        pw_c = {w for w in valid_pw if prog_in[w] & {prog[i] for i in cols}}
        mat_row(f"MP4 Drug→Gene→Pathway←{c} gene", cols, pw_c)
    for t, s in trans.groupby("transition"):
        tg = set(s.ensembl_id)
        cols = [p_idx[g] for g in prog if g in tg]
        pw_t = {w for w in valid_pw if prog_in[w] & tg}
        mat_row(f"MP5 Drug→Gene→Pathway←{t} transition gene", cols, pw_t)

    # MP6 Paper 1 fibrosis pathways
    for db in ["Reactome", "KEGG", "Hallmark"]:
        m6 = links.merge(mem[mem.database == db], on="gene")
        summarise(f"MP6 Drug→Gene→Paper1 fibrosis pathway [{db}]", m6, "drug", "gene", "term",
                  {"unique pathways": m6.term.nunique()})

    # MP7 full route to liver disease
    dis_ids = sorted(gdis.disease.unique()); x_idx = {x: i for i, x in enumerate(dis_ids)}
    A = sparse.csr_matrix((np.ones(len(gdis)), (gdis.gene.map(p_idx), gdis.disease.map(x_idx))), shape=(len(prog), len(dis_ids)))
    D = (sparse.csr_matrix(P) @ A).toarray()
    has = D > 0
    prog_with_dis = set(gdis.gene)
    pw7 = {w for w in valid_pw if prog_in[w] & prog_with_dis}
    rows.append({"MetaPath": "MP7 Drug→Gene→Pathway←ProgressionGene→LiverDisease", "links used": tag, "paths": int(D.sum()),
                 "unique drugs": int(has.any(axis=1).sum()), "unique genes": len(set(lt.loc[lt.pathway.isin(pw7), "gene"])),
                 "unique end nodes": int(has.any(axis=0).sum()), "drug–end pairs": int(has.sum()),
                 "unique combinations (pairs with exactly one route)": int((D == 1).sum()),
                 "unique pathways": len(pw7)})
    ii, jj = np.nonzero(has)
    pairs["MP7"] = pd.DataFrame({"drug": [drugs_[i] for i in ii], "disease": [dis_ids[j] for j in jj], "paths": D[ii, jj].astype(int)})
    return pd.DataFrame(rows), pairs


all_links = dt[["drug", "gene", "action"]].drop_duplicates(["drug", "gene"])
pharm_links = all_links[~all_links.action.isin(PK)]
counts_all, pairs_all = run(all_links, "all links")
counts_ph, _ = run(pharm_links, "pharmacological only")
counts = pd.concat([counts_all, counts_ph], ignore_index=True)

# ------------------------------------------------------------------ Neo4j cross-checks
xc = []
for name, stmt, params, key in [
    ("COUNT MP1", """MATCH (d:Drug)-[:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog AND x.node_id IN $liver RETURN count(*) AS paths""",
     {"drugs": drugs, "prog": prog, "liver": liver_ids}, "MP1 Drug→Gene→LiverDisease"),
    ("COUNT MP2", """MATCH (d:Drug)-[:ACTS_ON]->(g:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs AND g.ensembl_id IN $prog RETURN count(*) AS paths""",
     {"drugs": drugs, "prog": prog}, "MP2 Drug→Gene→Pathway"),
    ("COUNT MP3 (aggregated per pathway, minus T = P)", """MATCH (d:Drug)-[:ACTS_ON]->(t:Gene)-[:IN_PATHWAY]->(p:Pathway)
WHERE d.node_id IN $drugs
WITH p, count(*) AS dt_pairs, sum(CASE WHEN t.ensembl_id IN $prog THEN 1 ELSE 0 END) AS self_pairs
MATCH (p)<-[:IN_PATHWAY]-(g:Gene) WHERE g.ensembl_id IN $prog
WITH p, dt_pairs, self_pairs, count(g) AS n_prog
RETURN sum(dt_pairs * n_prog - self_pairs) AS paths""", {"drugs": drugs, "prog": prog}, "MP3 Drug→Gene→Pathway←ProgressionGene"),
]:
    n = int(cy(name, stmt, params).paths.iloc[0])
    mine = int(counts_all.set_index("MetaPath").loc[key, "paths"])
    xc.append({"MetaPath": key, "python": mine, "neo4j": n, "match": n == mine})
xc = pd.DataFrame(xc)
xc.to_csv(OUT / "crosscheck_python_vs_neo4j.csv", index=False)
assert xc.match.all(), xc

# ------------------------------------------------------------------ repurposing pairs (drug - liver disease)
p1df, cnt1 = pairs_all["MP1"]
mp1 = cnt1.rename("MP1_paths").reset_index()
mp1["MP1_genes"] = p1df.groupby(["drug", "disease"]).gene.agg(lambda s: ";".join(sorted({sym.get(g, g) for g in s}))).values
mp7 = pairs_all["MP7"].rename(columns={"paths": "MP7_paths"})
rp = mp7.merge(mp1, on=["drug", "disease"], how="outer").fillna({"MP1_paths": 0, "MP7_paths": 0})
rp[["MP1_paths", "MP7_paths"]] = rp[["MP1_paths", "MP7_paths"]].astype(int)
rp["drug_name"] = rp.drug.map(dname)
rp["disease_name"] = rp.disease.map(disname)
rp["fibrosis_spectrum"] = rp.disease.isin(fib_ids)
rp["known_use"] = [known_uses.get((d, x), "") for d, x in zip(rp.drug, rp.disease)]
rp["contraindicated"] = [(d, x) in contra for d, x in zip(rp.drug, rp.disease)]
rp["status"] = np.where(rp.known_use != "", "known use", "NEW pair (repurposing hypothesis)")
drugs_with_liver_use = set(known_uses.reset_index().drug)
rp["drug_has_any_liver_use"] = rp.drug.isin(drugs_with_liver_use)
cand = set(pd.read_csv(RES / "Task4/repurposing_candidates.csv").Drug_ID)
mech = set(pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv").Drug_ID)
rp["repurposing_candidate_drug"] = rp.drug.isin(cand)
rp["main_list_drug"] = rp.drug.isin(mech)
rp = rp[["drug", "drug_name", "disease", "disease_name", "fibrosis_spectrum", "MP1_paths", "MP1_genes", "MP7_paths",
         "status", "known_use", "drug_has_any_liver_use", "contraindicated", "repurposing_candidate_drug", "main_list_drug"]]
rp = rp.sort_values(["status", "fibrosis_spectrum", "MP1_paths", "MP7_paths"], ascending=[True, False, False, False])
rp.to_csv(OUT / "drug_liver_disease_pairs.csv", index=False)
new = rp[rp.status.str.startswith("NEW")]

defs = pd.DataFrame([
    ("MP1", "Drug -[ACTS_ON]-> Gene (progression) -[ASSOCIATED_WITH]-> Disease", "161 liver diseases (MP1f: fibrosis-spectrum subset)"),
    ("MP2", "Drug -[ACTS_ON]-> Gene (progression) -[IN_PATHWAY]-> Pathway", "Reactome pathways"),
    ("MP3", "Drug -[ACTS_ON]-> Gene -[IN_PATHWAY]-> Pathway <-[IN_PATHWAY]- Progression gene (different gene)", "progression genes"),
    ("MP4", "MP3 with the end gene in one F0–F4 trajectory cluster", "Paper 1 clusters C1–C5"),
    ("MP5", "MP3 with the end gene significant at one stage transition (q < 0.05)", "Paper 1 Task 3 transitions"),
    ("MP6", "Drug -[ACTS_ON]-> Gene ∈ Paper 1 fibrosis-enriched pathway", "Reactome (graph node), KEGG and Hallmark (Paper 1 gene lists); GO BP omitted"),
    ("MP7", "Drug -[ACTS_ON]-> Gene -[IN_PATHWAY]-> Pathway <-[IN_PATHWAY]- Progression gene -[ASSOCIATED_WITH]-> Liver disease", "161 liver diseases"),
], columns=["MetaPath", "Pattern", "End nodes"])
defs["Unique combination"] = "a drug–end pair joined by exactly one route (one gene, or one gene–pathway–gene chain)"
defs.to_csv(OUT / "metapath_definitions.csv", index=False)
counts.to_csv(OUT / "metapath_counts.csv", index=False)
with open(OUT / "metapath_queries.cypher", "w", encoding="utf-8") as f:
    f.write("// Paper 2 Task 5 (revised) — read-only Cypher used. $drugs = 3,027 drugs linked to progression genes;\n"
            "// $prog = 6,222 progression genes; $liver = 161 liver diseases. MP3–MP5 and MP7 path counts are\n"
            "// computed from the pulled edges by sparse matrix products; MP1–MP3 are re-counted in Neo4j.\n\n")
    for n, s in LOG:
        f.write(f"// ---- {n}\n{s};\n\n")


# ------------------------------------------------------------------ summary
def md(df):
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * df.shape[1]]
    for row in df.values:
        lines.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else (f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)) for v in row) + " |")
    return "\n".join(lines)


show = counts_all.drop(columns=["links used"]).copy()
for c in show.columns[1:]:
    show[c] = show[c].map(lambda v: "" if pd.isna(v) else int(v))
cmp_ = counts.pivot_table(index="MetaPath", columns="links used", values="paths", aggfunc="first").reindex(counts_all.MetaPath)
cmp_ = cmp_.reset_index().rename(columns={"all links": "paths (all links)", "pharmacological only": "paths (pharmacological only)"})
for c in cmp_.columns[1:]:
    cmp_[c] = cmp_[c].astype(int)
true_new = new[~new.drug_has_any_liver_use]
top_new = (true_new[true_new.fibrosis_spectrum & true_new.main_list_drug]
           .sort_values(["MP1_paths", "MP7_paths"], ascending=False).head(15).copy())
top_new["contraindicated"] = top_new.contraindicated.map({True: "yes", False: ""})
top_new = top_new[["drug_name", "disease_name", "MP1_paths", "MP1_genes", "MP7_paths", "contraindicated"]]
summary = f"""# Paper 2 — Task 5 (revised): MetaPaths on the knowledge graph

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph only (live Neo4j, read-only). Repurposing hypotheses, not treatments.
**Changes from the first Task 5:** the Drug → Gene → Biological Process MetaPath is removed (GO BP terms too); unique counts and unique combinations are added; the full repurposing route MP7 is added; ALL drug–gene links are used (pharmacological-only counts beside them). Script: `code/task5_revised_metapaths.py`.

![Task 5 revised](Task5_revised_diagram.png)

![Graph schema](../Graph_files/graph_schema.png)

## Definitions
{md(defs)}

## Counts (all drug–gene links)
{md(show)}

**Unique combination** = a drug–end pair connected by exactly one route.

## All links vs pharmacological links only
{md(cmp_)}

## Repurposing pairs: drug → liver disease through genes
Drug–liver-disease pairs reached by MP1 (through a gene the drug acts on) or MP7 (through a pathway shared with a progression gene associated with the disease): **{len(rp):,} pairs**. Of these, **{(rp.status == 'known use').sum():,}** are already known uses in the graph (TREATS / OFF_LABEL_FOR) and **{len(new):,} are NEW pairs**. Of the new pairs, **{len(true_new):,}** come from drugs with **no liver-disease use at all** in the graph (true repurposing), {int(true_new.fibrosis_spectrum.sum()):,} of them for fibrosis-spectrum diseases (fatty liver, NASH, cirrhosis, liver failure …). {int(true_new.main_list_drug.sum()):,} of these true-repurposing pairs involve main-list (mechanism-annotated) candidate drugs, {int((true_new.fibrosis_spectrum & true_new.main_list_drug).sum()):,} of them for fibrosis-spectrum diseases. {int(new.contraindicated.sum()):,} new pairs are flagged as contraindicated.

| Pair set | Pairs |
|---|---|
| All drug–liver-disease pairs reached (MP1 or MP7) | {len(rp):,} |
| Known uses (TREATS / OFF_LABEL_FOR) | {(rp.status == 'known use').sum():,} |
| New pairs | {len(new):,} |
| New pairs, drug has no liver use at all | {len(true_new):,} |
| … and disease is fibrosis-spectrum | {int(true_new.fibrosis_spectrum.sum()):,} |
| … and drug is on the main list | {int((true_new.fibrosis_spectrum & true_new.main_list_drug).sum()):,} |
| New pairs reached by exactly one MP1 route (unique combination) | {int((new.MP1_paths == 1).sum()):,} |

### New fibrosis-spectrum pairs from main-list drugs with no liver use (most direct MP1 routes)
{md(top_new)}

Full list: `drug_liver_disease_pairs.csv`.

## Verification
MP1, MP2 and MP3 path counts were re-counted inside Neo4j: {', '.join(f"{r.MetaPath.split()[0]} {r.python:,} = {r.neo4j:,}" for r in xc.itertuples())} ({'all match' if xc.match.all() else 'MISMATCH'}). LIMIT 5 test query for MP7 run first. All queries: `metapath_queries.cypher`.

## Caveats
- More routes mean more graph connectivity, not efficacy. Well-studied drugs and genes have more routes.
- Gene–disease links are Open Targets associations (score ≥ 0.1), many from cancer studies.
- KEGG and Hallmark pathways reach drugs only through their Paper 1 progression genes (no graph node).
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
