"""Paper 2 Task 2: extract every drug-gene (ACTS_ON) edge for the progression genes.

Primary source: the live Neo4j liver_kg graph, read-only (HTTP query API).
Cross-check: Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv.
If Neo4j cannot be reached, the CSV is used and the summary says so.

Password is read from the NEO4J_PASSWORD environment variable (prompted if unset).
Run from the repository root:

    python Paper2_Results/code/task2_drug_gene_edges.py
"""
import base64
import getpass
import json
import os
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Paper2_Results" / "Task2"
OUT.mkdir(parents=True, exist_ok=True)

GENES = ROOT / "Paper2_Results/Task1/Paper2_progression_genes.csv"
CSV_EDGES = ROOT / "Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv"
CSV_DRUGS = ROOT / "Paper1_Package/04_DATA/knowledge_layer/nodes_drug.csv"

NEO4J_URL = os.environ.get("NEO4J_HTTP", "http://127.0.0.1:7474")
NEO4J_DB = os.environ.get("NEO4J_DATABASE", "neo4j")
NEO4J_USER = os.environ.get("NEO4J_USERNAME", "neo4j")

# Drug action -> effect on the gene product ("switch down" / "switch up").
DOWN = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE_MODULATOR", "NEGATIVE_ALLOSTERIC_MODULATOR",
        "ALLOSTERIC_ANTAGONIST", "INVERSE_AGONIST", "DEGRADER"}
UP = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR", "POSITIVE_MODULATOR", "POSITIVE_ALLOSTERIC_MODULATOR",
      "OPENER", "STABILISER"}
MIXED = {"MODULATOR", "BINDING_AGENT", "SUBSTRATE", "RELEASING_AGENT"}
UNKNOWN = {"TARGET", "ENZYME", "TRANSPORTER", "CARRIER"}


def action_direction(action):
    a = str(action).upper()
    if a in DOWN:
        return "down"
    if a in UP:
        return "up"
    if a in MIXED:
        return "mixed"
    return "unknown"


def edge_direction(action, assertions):
    """Direction of the edge's consolidated action, demoted to 'mixed' when the
    individual source assertions point both down and up."""
    d = action_direction(action)
    if isinstance(assertions, str) and assertions:
        dirs = {action_direction(a.split(":", 1)[-1]) for a in assertions.split(";")}
        if {"down", "up"} <= dirs:
            return "mixed"
    return d


# ------------------------------------------------------------------ inputs
genes = pd.read_csv(GENES)
ids = genes.ensembl_id.tolist()

csv_edges = pd.read_csv(CSV_EDGES).rename(columns={"from_id": "Drug_ID", "to_id": "Gene_ID", "rel_type": "Action_raw"})
csv_sub = csv_edges[csv_edges.Gene_ID.isin(ids)]


# ------------------------------------------------------------------ Neo4j
def neo4j_query(statement, params, password):
    headers = {"Authorization": "Basic " + base64.b64encode(f"{NEO4J_USER}:{password}".encode()).decode(),
               "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": statement, "parameters": params, "accessMode": "Read"}).encode()
    req = urllib.request.Request(f"{NEO4J_URL}/db/{NEO4J_DB}/query/v2", data=body, headers=headers, method="POST")
    res = json.load(urllib.request.urlopen(req, timeout=300))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return pd.DataFrame(res["data"]["values"], columns=res["data"]["fields"])


QUERY = """
MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)
WHERE g.ensembl_id IN $ids
RETURN d.node_id AS Drug_ID, d.name AS Drug, d.molecule_type AS molecule_type,
       d.max_phase AS max_phase, d.is_approved AS is_approved, d.has_been_withdrawn AS withdrawn,
       g.ensembl_id AS Gene_ID, g.symbol AS graph_symbol,
       type(r) AS Relationship, r.action AS Action_raw,
       r.relation_assertions AS relation_assertions, r.relation_conflict AS relation_conflict,
       r.sources_direct AS sources_direct, r.sources_indirect AS sources_indirect,
       r.n_sources AS n_sources, r.evidence_level AS evidence_level,
       r.mechanisms_of_action AS mechanism_of_action, r.source_urls AS source_urls
"""
source_used = "Neo4j (live liver_kg, read-only)"
try:
    password = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")
    edges = neo4j_query(QUERY, {"ids": ids}, password)
    drug_degree = neo4j_query("MATCH (d:Drug)-[r:ACTS_ON]->(:Gene) RETURN d.node_id AS Drug_ID, count(r) AS drug_total_targets", {}, password)
except Exception as exc:  # fall back to the identical CSV export
    print(f"Neo4j unavailable ({exc}); using CSV")
    source_used = "CSV fallback (edges_drug_gene.csv) — Neo4j unavailable"
    drugs = pd.read_csv(CSV_DRUGS).rename(columns={"node_id": "Drug_ID", "name": "Drug"})
    edges = csv_sub.merge(drugs, on="Drug_ID", how="left")
    edges["Relationship"] = "ACTS_ON"
    drug_degree = csv_edges.groupby("Drug_ID").size().rename("drug_total_targets").reset_index()

# ------------------------------------------------------------------ cross-check
key = ["Drug_ID", "Gene_ID", "Action_raw"]
neo_keys = set(map(tuple, edges[key].values))
csv_keys = set(map(tuple, csv_sub[key].values))
xcheck = {
    "source_used": source_used,
    "edges_source": len(edges),
    "edges_csv": len(csv_sub),
    "counts_match": len(edges) == len(csv_sub),
    "identical_drug_gene_action_triples": neo_keys == csv_keys,
    "only_in_source": len(neo_keys - csv_keys),
    "only_in_csv": len(csv_keys - neo_keys),
    "duplicate_drug_gene_pairs": int(edges.duplicated(["Drug_ID", "Gene_ID"]).sum()),
}
(OUT / "crosscheck_neo4j_vs_csv.json").write_text(json.dumps(xcheck, indent=2))

# ------------------------------------------------------------------ build table
ann = genes[["ensembl_id", "Gene", "progression_class", "paper1_group", "fibrosis_direction",
             "inflammation_direction", "trajectory_cluster", "Tier", "in_shortlist"]]
ann = ann.rename(columns={"ensembl_id": "Gene_ID", "trajectory_cluster": "cluster"})
df = edges.merge(ann, on="Gene_ID", how="left").merge(drug_degree, on="Drug_ID", how="left")

df["Action_direction"] = [edge_direction(a, s) for a, s in zip(df.Action_raw, df.get("relation_assertions", pd.Series([None] * len(df))))]
df["Evidence_source"] = ("OptimusKG/" + df["sources_direct"].fillna("").str.replace(";", "+")) if "sources_direct" in df else "OptimusKG"
df["Database_ID"] = df.Drug_ID + "|" + df.Gene_ID

# Gene direction used for comparison: fibrosis direction where available, otherwise inflammation.
df["gene_direction"] = df.fibrosis_direction.fillna(df.inflammation_direction)
df["gene_direction_axis"] = df.fibrosis_direction.notna().map({True: "fibrosis", False: "inflammation"})
df["direction_comparable"] = df.Action_direction.isin(["up", "down"]) & df.gene_direction.notna()
df["cluster_comparable"] = df.Action_direction.isin(["up", "down"]) & df.cluster.notna()

cols = ["Drug", "Drug_ID", "Gene", "Gene_ID", "Relationship", "Action_raw", "Action_direction",
        "Evidence_source", "Database_ID", "evidence_level", "n_sources", "relation_assertions",
        "relation_conflict", "mechanism_of_action", "sources_indirect", "source_urls",
        "molecule_type", "max_phase", "is_approved", "withdrawn", "drug_total_targets",
        "progression_class", "paper1_group", "fibrosis_direction", "inflammation_direction",
        "gene_direction", "gene_direction_axis", "cluster", "Tier", "in_shortlist",
        "direction_comparable", "cluster_comparable"]
df = df[[c for c in cols if c in df.columns]].sort_values(["Gene", "Drug"])
df.to_csv(OUT / "drug_gene_edges.csv", index=False)

# ------------------------------------------------------------------ summary numbers
n = len(df)
g_conn = df.Gene_ID.nunique()
known = df.Action_direction.isin(["up", "down"]).sum()
dir_counts = df.Action_direction.value_counts().reindex(["down", "up", "mixed", "unknown"]).fillna(0).astype(int)
raw_counts = df.Action_raw.value_counts()
cls_tot = genes.progression_class.value_counts()
cls_conn = df.groupby("progression_class").Gene_ID.nunique()
cls_drugs = df.groupby("progression_class").Drug_ID.nunique()
cls_edges = df.groupby("progression_class").size()
evid = df.evidence_level.value_counts() if "evidence_level" in df else pd.Series(dtype=int)
conflicts = int(df.relation_conflict.fillna(False).astype(bool).sum()) if "relation_conflict" in df else 0
approved = df.loc[df.is_approved == True, "Drug_ID"].nunique() if "is_approved" in df else None
shortlist_conn = df.loc[df.in_shortlist == True, "Gene_ID"].nunique()
comp_dir = int(df.direction_comparable.sum())
comp_clu = int(df.cluster_comparable.sum())

summary_rows = {
    "progression_genes": len(genes), "genes_with_drug": g_conn, "unique_drugs": df.Drug_ID.nunique(),
    "edges": n, "edges_known_direction": int(known), "edges_direction_comparable": comp_dir,
    "edges_cluster_comparable": comp_clu, "relation_conflict_edges": conflicts,
    "shortlist_genes_with_drug": shortlist_conn,
}
pd.Series(summary_rows).to_csv(OUT / "summary_numbers.csv", header=["value"])


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "–"


def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


summary = f"""# Paper 2 — Task 2: drug–gene relationships

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **{len(genes):,} genes** from Task 1.

**Source used:** {source_used}. Query: `MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE g.ensembl_id IN $ids` (read-only).
Script: `Paper2_Results/code/task2_drug_gene_edges.py`. Output: `drug_gene_edges.csv` ({n:,} rows).

![Task 2 diagram](Task2_diagram.png)

## Cross-check: Neo4j vs. CSV export

{md(["Check", "Result"], [
    ("Edges from source", f"{xcheck['edges_source']:,}"),
    ("Edges in edges_drug_gene.csv (same genes)", f"{xcheck['edges_csv']:,}"),
    ("Counts match", "YES" if xcheck['counts_match'] else "NO"),
    ("Identical drug–gene–action triples", "YES" if xcheck['identical_drug_gene_action_triples'] else "NO"),
    ("Duplicate drug–gene pairs", xcheck['duplicate_drug_gene_pairs']),
])}

## Headline numbers

{md(["Measure", "Value"], [
    ("Progression genes with ≥1 drug", f"{g_conn:,} / {len(genes):,} ({pct(g_conn, len(genes))})"),
    ("Unique drugs", f"{df.Drug_ID.nunique():,}" + (f" ({approved:,} approved)" if approved is not None else "")),
    ("Total drug–gene relationships", f"{n:,}"),
    ("Relationships with known direction (down/up)", f"{known:,} ({pct(known, n)})"),
    ("…comparable with Paper 1 gene direction", f"{comp_dir:,} ({pct(comp_dir, n)})"),
    ("…comparable with an F0–F4 trajectory cluster", f"{comp_clu:,} ({pct(comp_clu, n)})"),
    ("23-gene shortlist genes with ≥1 drug", f"{shortlist_conn} / 23"),
])}

"Comparable" means the drug pushes the gene down or up **and** Paper 1 gives the gene a direction (fibrosis direction; inflammation direction for inflammation-only genes) or a trajectory cluster. Whether each comparison is direction-consistent is Task 7. A comparable relationship is a check of mechanism consistency, not proof that a drug would help (repurposing hypothesis only).

## Drug action direction

{md(["Direction", "Edges", "%", "Raw actions included"], [
    ("down", f"{dir_counts['down']:,}", pct(dir_counts['down'], n), ", ".join(sorted(DOWN))),
    ("up", f"{dir_counts['up']:,}", pct(dir_counts['up'], n), ", ".join(sorted(UP))),
    ("mixed", f"{dir_counts['mixed']:,}", pct(dir_counts['mixed'], n), ", ".join(sorted(MIXED)) + "; or sources disagree (down vs up)"),
    ("unknown", f"{dir_counts['unknown']:,}", pct(dir_counts['unknown'], n), ", ".join(sorted(UNKNOWN))),
])}

Raw action counts: {", ".join(f"{k} {v:,}" for k, v in raw_counts.items())}.
Edges flagged `relation_conflict` by OptimusKG: {conflicts:,}.

## By progression class

{md(["Class", "Genes", "Genes with drug", "%", "Unique drugs", "Edges"], [
    (c, f"{cls_tot.get(c, 0):,}", f"{cls_conn.get(c, 0):,}", pct(cls_conn.get(c, 0), cls_tot.get(c, 0)),
     f"{cls_drugs.get(c, 0):,}", f"{cls_edges.get(c, 0):,}") for c in ["fibrosis_only", "shared", "inflammation_only"]
])}

(Statistics comparing these groups are Task 3.)

## Evidence level

{md(["Evidence level", "Edges"], [(k, f"{v:,}") for k, v in evid.items()]) if len(evid) else "Not available from the CSV fallback."}

## What the source does and does not contain (honest notes)

- **Present on every Neo4j edge:** consolidated action, per-source assertions (`relation_assertions`), contributing sources (`sources_direct`: DrugBank, Open Targets, etc.), number of sources, evidence level (single-/multi-source), conflict flag.
- **Present only on some edges:** mechanism-of-action text, literature URLs (PubMed/Europe PMC), indirect sources.
- **Not available:** a per-source record or accession ID for each assertion. `Database_ID` is therefore the stable pair `ChEMBL drug ID | Ensembl gene ID`. There is also no quantitative affinity/potency, and no dose or tissue context.
- The CSV export (`edges_drug_gene.csv`) keeps only drug, gene and action; its `score` column is empty for drug–gene edges. The extra evidence fields come from Neo4j only.
- Action labels such as TARGET, ENZYME, TRANSPORTER and CARRIER describe what the gene product is for the drug, not whether the drug switches it down or up. They are counted as **unknown direction**.
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
print(json.dumps(xcheck, indent=2))
