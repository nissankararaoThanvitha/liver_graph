"""Paper 2 Task 7 (revised): drug action direction judged through pathways.

The first Task 7 compared a drug's action with the direction of the gene it acts on. That only
works when the target itself is a progression gene. Following review (16 Oct 2026), direction is
now also decided through the PATHWAYS the target sits in ("how are the genes connected, through
which pathways, and is that pathway going up or down with fibrosis?").

1. Pathway direction (Reactome, from the graph): each pathway's Paper 1 FIBROSIS-associated
   member genes (fibrosis-only + shared) vote by their fibrosis direction.
     rising   : >= 3 member genes and >= 2/3 of them rise with fibrosis
     falling  : >= 3 member genes and >= 2/3 of them fall
     mixed    : >= 3 member genes, no 2/3 majority
     too few  : fewer than 3 fibrosis member genes (no call)
2. Pathway-level consistency for every Drug -[ACTS_ON]-> Gene -[IN_PATHWAY]-> Pathway route
   (all ACTS_ON links; the target need not be a progression gene):
     drug pushes down + pathway rising  -> consistent     drug pushes up + pathway falling -> consistent
     drug pushes down + pathway falling -> inconsistent   drug pushes up + pathway rising  -> inconsistent
     pathway mixed or too few, or mixed action           -> ambiguous
     action TARGET / ENZYME / TRANSPORTER / CARRIER       -> unknown
3. Per drug: gene-level calls (first Task 7) and pathway-level calls side by side, and a
   combined call (gene level where it exists, otherwise the pathway majority).

Read-only Neo4j; password from NEO4J_PASSWORD. Repurposing hypotheses, not proof.

    python Paper2_Results_Idea1/code/task7_revised_pathway_direction.py
"""
import base64
import getpass
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results_Idea1"
OUT = RES / "Task7_revised"
OUT.mkdir(exist_ok=True)
MIN_GENES, MAJORITY = 3, 2 / 3
DOWN = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE_MODULATOR", "NEGATIVE_ALLOSTERIC_MODULATOR",
        "ALLOSTERIC_ANTAGONIST", "INVERSE_AGONIST", "DEGRADER"}
UP = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR", "POSITIVE_MODULATOR", "POSITIVE_ALLOSTERIC_MODULATOR",
      "OPENER", "STABILISER"}
MIXED = {"MODULATOR", "BINDING_AGENT", "SUBSTRATE", "RELEASING_AGENT"}
PW = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password: ")


def cy(stmt, params=None):
    h = {"Authorization": "Basic " + base64.b64encode(f"neo4j:{PW}".encode()).decode(),
         "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": stmt, "parameters": params or {}, "accessMode": "Read"}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:7474/db/neo4j/query/v2", data=body, headers=h, method="POST"), timeout=900))
    if r.get("errors"):
        raise RuntimeError(r["errors"])
    return pd.DataFrame(r["data"]["values"], columns=r["data"]["fields"])


genes = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
fib = genes[genes.progression_class != "inflammation_only"]
fdir = dict(zip(fib.ensembl_id, fib.fibrosis_direction))
drugs = sorted(pd.read_csv(RES / "Task2/drug_gene_edges.csv").Drug_ID.unique())
cand = set(pd.read_csv(RES / "Task4/repurposing_candidates.csv").Drug_ID)
mech = set(pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv").Drug_ID)

gp = cy("MATCH (g:Gene)-[:IN_PATHWAY]->(p:Pathway) RETURN g.ensembl_id AS gene, g.symbol AS symbol, p.node_id AS pathway, p.name AS pathway_name")
links = cy("""MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE d.node_id IN $drugs
RETURN d.node_id AS drug, d.name AS drug_name, g.ensembl_id AS gene, g.symbol AS target, r.action AS action""", {"drugs": drugs})

# ------------------------------------------------------------------ 1. pathway direction
gp["fib_dir"] = gp.gene.map(fdir)
vote = gp.dropna(subset=["fib_dir"]).groupby(["pathway", "pathway_name"]).fib_dir.agg(
    n_rising=lambda s: (s == "positive").sum(), n_falling=lambda s: (s == "negative").sum()).reset_index()
size = gp.groupby("pathway").gene.nunique()
vote["pathway_size"] = vote.pathway.map(size)
vote["n_fibrosis_genes"] = vote.n_rising + vote.n_falling
vote["share_rising"] = (vote.n_rising / vote.n_fibrosis_genes).round(3)


def call(r):
    if r.n_fibrosis_genes < MIN_GENES:
        return "too few genes"
    if r.share_rising >= MAJORITY:
        return "rising"
    if 1 - r.share_rising >= MAJORITY:
        return "falling"
    return "mixed"


vote["pathway_direction"] = vote.apply(call, axis=1)
rising_genes = gp.dropna(subset=["fib_dir"])
vote["example_genes"] = vote.pathway.map(rising_genes.groupby("pathway").symbol.agg(lambda s: ";".join(sorted(s)[:8])))
vote = vote.sort_values(["pathway_direction", "n_fibrosis_genes"], ascending=[True, False])
vote.to_csv(OUT / "pathway_direction.csv", index=False)
pdir = dict(zip(vote.pathway, vote.pathway_direction))

# ------------------------------------------------------------------ 2. drug -> target -> pathway calls
links["push"] = np.select([links.action.isin(DOWN), links.action.isin(UP), links.action.isin(MIXED)], ["down", "up", "mixed"], "unknown")
r = links.merge(gp[["gene", "pathway", "pathway_name"]], on="gene")
r["pathway_direction"] = r.pathway.map(pdir).fillna("too few genes")
r["target_is_progression_gene"] = r.gene.isin(set(genes.ensembl_id))


def consistency(push, d):
    if push == "unknown":
        return "unknown"
    if push == "mixed" or d not in ("rising", "falling"):
        return "ambiguous"
    return "direction-consistent" if (push == "down") == (d == "rising") else "direction-inconsistent"


r["pathway_consistency"] = [consistency(p, d) for p, d in zip(r.push, r.pathway_direction)]
r["repurposing_candidate"] = r.drug.isin(cand)
r["main_list"] = r.drug.isin(mech)
r = r[["drug", "drug_name", "target", "gene", "target_is_progression_gene", "action", "push", "pathway", "pathway_name",
       "pathway_direction", "pathway_consistency", "repurposing_candidate", "main_list"]]
r.to_csv(OUT / "drug_target_pathway_direction.csv", index=False)

# ------------------------------------------------------------------ 3. per drug: gene level vs pathway level
gl = pd.read_csv(RES / "Task7/drug_direction_summary.csv").set_index("Drug_ID")
dec = r[r.pathway_consistency.isin(["direction-consistent", "direction-inconsistent"])]
pw_c = dec[dec.pathway_consistency == "direction-consistent"].groupby("drug").pathway.nunique()
pw_i = dec[dec.pathway_consistency == "direction-inconsistent"].groupby("drug").pathway.nunique()
d = pd.DataFrame(index=sorted(links.drug.unique()))
d.index.name = "drug"
d["drug_name"] = d.index.map(dict(zip(links.drug, links.drug_name)))
d["gene_level_consistent"] = gl.n_consistent.reindex(d.index).fillna(0).astype(int)
d["gene_level_inconsistent"] = gl.n_inconsistent.reindex(d.index).fillna(0).astype(int)
d["pathway_level_consistent"] = pw_c.reindex(d.index).fillna(0).astype(int)
d["pathway_level_inconsistent"] = pw_i.reindex(d.index).fillna(0).astype(int)


def verdict(c, i):
    if c == 0 and i == 0:
        return "no call"
    if c > i:
        return "consistent"
    if i > c:
        return "inconsistent"
    return "tied"


d["gene_level_call"] = [verdict(c, i) for c, i in zip(d.gene_level_consistent, d.gene_level_inconsistent)]
d["pathway_level_call"] = [verdict(c, i) for c, i in zip(d.pathway_level_consistent, d.pathway_level_inconsistent)]
d["combined_call"] = np.where(d.gene_level_call != "no call", d.gene_level_call, d.pathway_level_call)
d["call_source"] = np.where(d.gene_level_call != "no call", "gene level", np.where(d.pathway_level_call != "no call", "pathway level only", "none"))
d["agreement"] = np.where((d.gene_level_call.isin(["consistent", "inconsistent"])) & (d.pathway_level_call.isin(["consistent", "inconsistent"])),
                          np.where(d.gene_level_call == d.pathway_level_call, "agree", "disagree"), "")
d["consistent_pathways"] = dec[dec.pathway_consistency == "direction-consistent"].groupby("drug").pathway_name.agg(
    lambda s: "; ".join(sorted(set(s))[:5])).reindex(d.index)
d["repurposing_candidate"] = d.index.isin(cand)
d["main_list"] = d.index.isin(mech)
d = d.sort_values(["main_list", "pathway_level_consistent"], ascending=False)
d.to_csv(OUT / "drug_direction_gene_vs_pathway.csv")


# ------------------------------------------------------------------ summary
def md(df, idx=False):
    x = df.reset_index() if idx else df
    lines = ["| " + " | ".join(map(str, x.columns)) + " |", "|" + "---|" * x.shape[1]]
    for row in x.values:
        lines.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else (f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)) for v in row) + " |")
    return "\n".join(lines)


pd_tab = vote.pathway_direction.value_counts().reindex(["rising", "falling", "mixed", "too few genes"]).fillna(0).astype(int).rename("pathways").to_frame()
rt = r.pathway_consistency.value_counts().reindex(["direction-consistent", "direction-inconsistent", "ambiguous", "unknown"]).fillna(0).astype(int)
new_info = r[(~r.target_is_progression_gene) & r.pathway_consistency.isin(["direction-consistent", "direction-inconsistent"])]
cs = d[d.repurposing_candidate]
comb = pd.DataFrame({
    "Drug set": ["All drugs", "Repurposing candidates", "Main list"],
    "gene-level call": [int((d.gene_level_call != "no call").sum()), int((cs.gene_level_call != "no call").sum()),
                        int((d[d.main_list].gene_level_call != "no call").sum())],
    "call only through pathways": [int((d.call_source == "pathway level only").sum()), int((cs.call_source == "pathway level only").sum()),
                                   int((d[d.main_list].call_source == "pathway level only").sum())],
    "combined: consistent": [int((d.combined_call == "consistent").sum()), int((cs.combined_call == "consistent").sum()),
                             int((d[d.main_list].combined_call == "consistent").sum())],
    "combined: inconsistent": [int((d.combined_call == "inconsistent").sum()), int((cs.combined_call == "inconsistent").sum()),
                               int((d[d.main_list].combined_call == "inconsistent").sum())],
})
agree = d[d.agreement != ""].agreement.value_counts()
top_rise = vote[vote.pathway_direction == "rising"].nlargest(8, "n_fibrosis_genes")[["pathway_name", "n_rising", "n_falling", "share_rising"]]
top_fall = vote[vote.pathway_direction == "falling"].nlargest(8, "n_fibrosis_genes")[["pathway_name", "n_rising", "n_falling", "share_rising"]]
ex = d[d.repurposing_candidate & (d.call_source == "pathway level only") & (d.pathway_level_call == "consistent")].nlargest(12, "pathway_level_consistent")
ex = ex[["drug_name", "pathway_level_consistent", "pathway_level_inconsistent", "consistent_pathways"]]
summary = f"""# Paper 2 — Task 7 (revised): drug direction judged through pathways

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph only (live Neo4j, read-only). Direction-consistency is a **repurposing hypothesis, not proof**.
Script: `code/task7_revised_pathway_direction.py`.

![Task 7 revised](Task7_revised_diagram.png)

## Why revise
The first Task 7 could only judge a drug when its target was itself a progression gene. Many drugs act on genes that are not progression genes but sit in the same pathways. Here each pathway gets a fibrosis direction from its Paper 1 genes, and the drug's push on its target is compared with the direction of the target's pathways.

## 1. Pathway direction (Reactome)
A pathway is **rising** (or **falling**) when at least {MIN_GENES} of its Paper 1 fibrosis genes are present and at least two thirds of them rise (or fall) with fibrosis; otherwise **mixed**, or **too few genes**.

{md(pd_tab, idx=True)}

Largest rising pathways:
{md(top_rise)}

Largest falling pathways:
{md(top_fall)}

## 2. Drug → target → pathway routes
All {len(r):,} routes (every ACTS_ON link, target in any Reactome pathway):

{md(rt.rename('routes').to_frame(), idx=True)}

**{len(new_info):,}** decided routes come from targets that are **not** progression genes. These drugs could not be judged at all in the first Task 7.

## 3. Gene level vs pathway level, per drug
{md(comb)}

Where both levels give a call, they **agree for {int(agree.get('agree', 0)):,} drugs and disagree for {int(agree.get('disagree', 0)):,}**. Combined call = gene level where it exists, otherwise the pathway majority.

### Repurposing candidates judged only through pathways, consistent (most pathways)
These candidates act on progression genes only through links of unknown direction, so the first Task 7 could not judge them. Their other targets have a known action, so they can be judged through pathways. The main list has none, because every main-list drug already has a gene-level call.
{md(ex)}

## Files
`pathway_direction.csv`, `drug_target_pathway_direction.csv` (every route), `drug_direction_gene_vs_pathway.csv` (per drug).

## Caveats
- A pathway's direction is a vote of its measured genes. Pathways contain activators and inhibitors, so a pathway vote is a simplification.
- The action labels still decide everything: TARGET / ENZYME / TRANSPORTER / CARRIER links stay unknown at both levels.
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
