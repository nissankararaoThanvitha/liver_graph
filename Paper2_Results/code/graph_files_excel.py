"""Four edge tables of the heterogeneous knowledge graph for the 6,222 Paper 1 progression genes.

Writes Paper2_Results/Graph_files/:
  1_gene_drug.xlsx      every Drug-[:ACTS_ON]->Gene link (all actions, with an action-type column)
  2_gene_disease.xlsx   every Gene-[:ASSOCIATED_WITH]->Disease link (all diseases; liver flag)
  3_drug_disease.xlsx   every known Drug->Disease use (INDICATION / OFF_LABEL / CONTRAINDICATION)
                        for the drugs in file 1 (liver flag)
  4_gene_pathway.xlsx   every Gene-[:IN_PATHWAY]->Pathway link (Reactome, from the graph), plus a
                        sheet of Paper 1 fibrosis-enriched GO / KEGG / Reactome / Hallmark terms
Each workbook starts with a README sheet (what the rows are, column meanings, counts).

Source: the knowledge-layer export loaded into Neo4j (Paper1_Package/04_DATA/knowledge_layer),
identical to the live graph (checked in Task 2 and the audit). Nothing is filtered.

    python Paper2_Results/code/graph_files_excel.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"
OUT = RES / "Graph_files"
OUT.mkdir(exist_ok=True)
KL = ROOT / "Paper1_Package/04_DATA/knowledge_layer"
PK = {"ENZYME", "TRANSPORTER", "CARRIER"}

genes = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
ann = genes[["ensembl_id", "Gene", "progression_class", "paper1_group", "fibrosis_direction",
             "inflammation_direction", "trajectory_cluster", "in_shortlist"]].rename(
    columns={"ensembl_id": "gene_id", "Gene": "gene", "trajectory_cluster": "F0_F4_cluster",
             "in_shortlist": "paper1_shortlist"})
ids = set(ann.gene_id)
liver = pd.read_csv(RES / "Task4/liver_disease_set.csv")
liver_ids = set(liver.loc[~liver.excluded_non_hepatic, "disease_id"])
dis_names = pd.read_csv(KL / "nodes_disease.csv").set_index("node_id").name
pw_names = pd.read_csv(KL / "nodes_pathway.csv").set_index("node_id").name


def write(path, sheets, readme):
    with pd.ExcelWriter(path, engine="xlsxwriter") as xw:
        pd.DataFrame({"README": readme}).to_excel(xw, sheet_name="README", index=False)
        xw.sheets["README"].set_column(0, 0, 120)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(df), df.shape[1] - 1)
            for i, c in enumerate(df.columns):
                ws.set_column(i, i, min(45, max(10, len(str(c)) + 2)))
    print(f"{path.name}: " + ", ".join(f"{k} {len(v):,} rows" for k, v in sheets.items()))


# ------------------------------------------------------------------ 1. gene - drug
e = pd.read_csv(RES / "Task2/drug_gene_edges.csv")
gd = pd.DataFrame({
    "gene_id": e.Gene_ID, "gene": e.Gene, "drug_id": e.Drug_ID, "drug": e.Drug,
    "action": e.Action_raw,
    "action_type": e.Action_raw.map(lambda a: "drug metabolism/transport (enzyme, transporter, carrier)" if a in PK
                                    else ("binding target, direction not stated" if a == "TARGET" else "pharmacological action")),
    "push_direction": e.Action_direction, "evidence_level": e.evidence_level, "n_sources": e.n_sources,
    "sources": e.Evidence_source.str.replace("OptimusKG/", "", regex=False),
    "mechanism_of_action": e.mechanism_of_action, "drug_max_phase": e.max_phase, "drug_approved": e.is_approved,
    "drug_withdrawn": e.withdrawn,
}).merge(ann.drop(columns="gene"), on="gene_id", how="left").sort_values(["gene", "drug"])
gene_sum = (gd.groupby(["gene_id", "gene"]).agg(n_drugs=("drug_id", "nunique"),
                                                 n_pharmacological=("action_type", lambda s: (s == "pharmacological action").sum()))
            .reset_index())
gene_sum = ann.merge(gene_sum.drop(columns="gene"), on="gene_id", how="left").fillna({"n_drugs": 0, "n_pharmacological": 0})
gene_sum[["n_drugs", "n_pharmacological"]] = gene_sum[["n_drugs", "n_pharmacological"]].astype(int)
write(OUT / "1_gene_drug.xlsx", {"gene_drug_links": gd, "all_6222_genes": gene_sum.sort_values("n_drugs", ascending=False)}, [
    "Gene – Drug links (Drug-[:ACTS_ON]->Gene) for the 6,222 Paper 1 progression genes. Nothing filtered.",
    f"Links: {len(gd):,}. Genes with at least one drug: {gd.gene_id.nunique():,} of 6,222. Drugs: {gd.drug_id.nunique():,}.",
    "Sheet all_6222_genes lists every progression gene, including the {:,} with no drug in the graph.".format(int((gene_sum.n_drugs == 0).sum())),
    "action = label exactly as in the graph (DrugBank / Open Targets).",
    "action_type: 'pharmacological action' = inhibitor, agonist, antagonist, blocker, modulator …; "
    "'binding target, direction not stated' = TARGET; 'drug metabolism/transport' = ENZYME, TRANSPORTER, CARRIER "
    "(the gene processes or moves the drug).",
    "push_direction: down / up / mixed / unknown, derived from action.",
    "progression_class, fibrosis_direction, F0_F4_cluster, paper1_shortlist: from Paper 1 (final, 10 Oct 2026).",
])

# ------------------------------------------------------------------ 2. gene - disease
dg = pd.read_csv(KL / "edges_disease_gene.csv")
dg = dg[dg.from_id.isin(ids)].rename(columns={"from_id": "gene_id", "to_id": "disease_id", "score": "association_score"})
dg["disease"] = dg.disease_id.map(dis_names).fillna(dg.disease_id)
dg["liver_disease"] = dg.disease_id.isin(liver_ids)
dg = dg.merge(ann[["gene_id", "gene", "progression_class", "fibrosis_direction"]], on="gene_id", how="left")
dg = dg[["gene_id", "gene", "disease_id", "disease", "association_score", "liver_disease", "progression_class", "fibrosis_direction"]]
dg = dg.sort_values(["gene", "association_score"], ascending=[True, False])
write(OUT / "2_gene_disease.xlsx", {"gene_disease_links": dg, "liver_diseases_only": dg[dg.liver_disease]}, [
    "Gene – Disease links (Gene-[:ASSOCIATED_WITH]->Disease, Open Targets association score ≥ 0.1) for the 6,222 progression genes.",
    f"Links: {len(dg):,}. Genes: {dg.gene_id.nunique():,}. Diseases: {dg.disease_id.nunique():,}.",
    f"liver_disease = disease is in the cleaned liver-disease set (EFO liver disease + descendants, minus non-hepatic entries; "
    f"{len(liver_ids)} diseases). Sheet liver_diseases_only: {int(dg.liver_disease.sum()):,} links.",
])

# ------------------------------------------------------------------ 3. drug - disease
dd = pd.read_csv(KL / "edges_drug_disease.csv")
dd = dd[dd.from_id.isin(set(gd.drug_id))].rename(columns={"from_id": "drug_id", "to_id": "disease_id", "rel_type": "relation"})
dd["relation"] = dd.relation.map({"INDICATION": "TREATS (indication)", "OFF_LABEL_USE": "OFF_LABEL_FOR",
                                  "CONTRAINDICATION": "CONTRAINDICATED_IN"})
dd["drug"] = dd.drug_id.map(gd.drop_duplicates("drug_id").set_index("drug_id").drug)
dd["disease"] = dd.disease_id.map(dis_names).fillna(dd.disease_id)
dd["liver_disease"] = dd.disease_id.isin(liver_ids)
dd = dd[["drug_id", "drug", "relation", "disease_id", "disease", "liver_disease"]].sort_values(["drug", "relation", "disease"])
write(OUT / "3_drug_disease.xlsx", {"drug_disease_links": dd, "liver_diseases_only": dd[dd.liver_disease]}, [
    "Drug – Disease links already known in the graph (TREATS / OFF_LABEL_FOR / CONTRAINDICATED_IN) for the "
    f"{gd.drug_id.nunique():,} drugs in 1_gene_drug.xlsx.",
    f"Links: {len(dd):,} ({', '.join(f'{k} {v:,}' for k, v in dd.relation.value_counts().items())}).",
    "These are the KNOWN drug–disease pairs. Drug repurposing looks for NEW drug–disease pairs reached through genes "
    "(Drug → Gene → Disease), so a pair listed here as TREATS is not a repurposing result.",
    f"Sheet liver_diseases_only: {int(dd.liver_disease.sum()):,} links.",
])

# ------------------------------------------------------------------ 4. gene - pathway
gp = pd.read_csv(KL / "edges_pathway_gene.csv")
gp = gp[gp.from_id.isin(ids)].rename(columns={"from_id": "gene_id", "to_id": "pathway_id"})
gp["pathway"] = gp.pathway_id.map(pw_names)
gp = gp.merge(ann[["gene_id", "gene", "progression_class", "fibrosis_direction", "F0_F4_cluster"]], on="gene_id", how="left")
gp = gp[["gene_id", "gene", "pathway_id", "pathway", "progression_class", "fibrosis_direction", "F0_F4_cluster"]].sort_values(["pathway", "gene"])
p1 = pd.read_csv(RES / "Task5/prep/paper1_term_genes_long.csv")
p1 = p1[~p1.group.str.startswith("inflammation_only")].drop_duplicates(["database", "term", "ensembl_id"])
mp = pd.read_csv(RES / "Task5/prep/paper1_term_to_graph_map.csv").set_index("term")
p1 = pd.DataFrame({"database": p1.database, "term": p1.term, "term_label": p1.term_label, "gene": p1.gene,
                   "gene_id": p1.ensembl_id,
                   "graph_node_id": p1.term.map(mp.graph_node_id), "graph_match": p1.term.map(mp.match_type)})
write(OUT / "4_gene_pathway.xlsx", {"gene_pathway_links": gp, "paper1_fibrosis_terms": p1}, [
    "Gene – Pathway links (Gene-[:IN_PATHWAY]->Pathway, Reactome, from the graph) for the 6,222 progression genes.",
    f"Links: {len(gp):,}. Genes: {gp.gene_id.nunique():,}. Pathways: {gp.pathway_id.nunique():,}.",
    "Sheet paper1_fibrosis_terms: progression genes in the GO BP / KEGG / Reactome / Hallmark terms that Paper 1 found "
    "enriched in fibrosis groups (fibrosis-only, shared, clusters C1–C5), with term labels and the matching graph node "
    "where one exists (match: name = exact name; gene_overlap_proxy = approximate; none = Paper 1 gene list only).",
    f"Rows: {len(p1):,}; terms: {p1.term.nunique():,}.",
])
summary = pd.DataFrame([
    ("Gene – Drug", len(gd), gd.gene_id.nunique(), gd.drug_id.nunique(), "1_gene_drug.xlsx"),
    ("Gene – Disease", len(dg), dg.gene_id.nunique(), dg.disease_id.nunique(), "2_gene_disease.xlsx"),
    ("Drug – Disease (known uses)", len(dd), dd.drug_id.nunique(), dd.disease_id.nunique(), "3_drug_disease.xlsx"),
    ("Gene – Pathway", len(gp), gp.gene_id.nunique(), gp.pathway_id.nunique(), "4_gene_pathway.xlsx"),
], columns=["edge type", "links", "first-node count", "second-node count", "file"])
summary.to_csv(OUT / "edge_counts.csv", index=False)
print(summary.to_string(index=False))
