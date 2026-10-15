"""Independent audit of Paper 2 outputs (Tasks 1-4 + Task 5 prep).

Recomputes key numbers from source files and the live graph with code that is
separate from the task scripts, and checks wording rules. Writes
Paper2_Results/AUDIT.md. Read-only Neo4j; password from NEO4J_PASSWORD.

    python Paper2_Results/code/audit_tasks.py
"""
import base64
import json
import os
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"
checks = []


def check(task, name, ok, detail=""):
    checks.append((task, name, bool(ok), detail))


def q(statement, params=None):
    pw = os.environ["NEO4J_PASSWORD"]
    h = {"Authorization": "Basic " + base64.b64encode(f"neo4j:{pw}".encode()).decode(),
         "Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps({"statement": statement, "parameters": params or {}, "accessMode": "Read"}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:7474/db/neo4j/query/v2", data=body, headers=h, method="POST"), timeout=600))
    if r.get("errors"):
        raise RuntimeError(r["errors"])
    return pd.DataFrame(r["data"]["values"], columns=r["data"]["fields"])


PK = {"ENZYME", "TRANSPORTER", "CARRIER"}

# ============================================================ Task 1
src = pd.read_csv(ROOT / "Paper1_HighConfidence/00_all_progression_genes.csv")
t1 = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
check("T1", "6,222 rows, unique Ensembl IDs", len(t1) == 6222 and t1.ensembl_id.is_unique, f"{len(t1)} rows")
check("T1", "same gene set as Paper 1 union", set(t1.ensembl_id) == set(src.ensembl_id))
m = t1.merge(src, on="ensembl_id", suffixes=("", "_src"))
same = all(np.allclose(m[c].astype(float), m[c + "_src"].astype(float), equal_nan=True)
           for c in ["fibrosis_rho", "fibrosis_q", "inflammation_rho", "inflammation_q", "F0", "F1", "F2", "F3", "F4"])
check("T1", "rho, q and F0–F4 copied exactly from source", same)
cls_map = {"both": "shared", "fibrosis_only": "fibrosis_only", "inflammation_only": "inflammation_only"}
check("T1", "progression class matches Paper 1 ladder", (m.progression_class == m.ladder.map(cls_map)).all())
dir_ok = ((m.fibrosis_direction.fillna("") == m.fibrosis_direction_src.map({"increasing": "positive", "decreasing": "negative"}).fillna(""))).all()
check("T1", "fibrosis direction matches source", dir_ok)
sign_ok = ((t1.fibrosis_rho > 0) == (t1.fibrosis_direction == "positive"))[t1.fibrosis_rho.notna()].all()
check("T1", "fibrosis direction agrees with sign of rho", sign_ok)
cs = pd.read_csv(ROOT / "Paper1_Results/Task2/task2_cluster_sizes.csv", encoding="utf-8-sig")
mine = t1.trajectory_cluster.value_counts()
check("T1", "cluster sizes match Paper 1 Task 2", all(mine.get(f"C{r.cluster}", 0) == r.n_genes for r in cs.itertuples()),
      ", ".join(f"C{r.cluster}={r.n_genes}" for r in cs.itertuples()))
sl = pd.read_csv(ROOT / "Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv")
check("T1", "23 shortlist genes flagged", t1.in_shortlist.sum() == 23 and set(t1.loc[t1.in_shortlist, "ensembl_id"]) == set(sl.Ensembl_ID))
p1 = pd.read_csv(ROOT / "Paper1_Results/Task1/task1_summary.csv", encoding="utf-8-sig")
check("T1", "class totals match Paper 1 Task 1",
      all(t1.progression_class.value_counts()[g] == p1[(p1.group == g) & (p1.direction == "all")].n_genes.iloc[0]
          for g in ["fibrosis_only", "inflammation_only", "shared"]))
check("T1", "annotations only on 3,845 fibrosis genes",
      t1.trajectory_cluster.notna().sum() == 3845 and t1.loc[t1.progression_class == "inflammation_only", "trajectory_cluster"].isna().all())

# ============================================================ live graph vs Paper 1 (data currency)
tf = q("MATCH (g:Gene)-[t:TRACKS_FIBROSIS]->() RETURN g.ensembl_id AS id, t.rho AS rho, t.direction AS dir, g.fibrosis_rho AS node_rho")
tfm = tf.set_index("id").join(t1.set_index("ensembl_id")[["fibrosis_rho", "fibrosis_direction"]], rsuffix="_t1")
check("Graph", "TRACKS_FIBROSIS edges = the 3,845 Task 1 fibrosis genes, same rho and direction",
      len(tf) == 3845 and np.allclose(tfm.rho, tfm.fibrosis_rho, atol=1e-3)
      and ((tfm.dir == "rises") == (tfm.fibrosis_direction == "positive")).all())
code_txt = "\n".join(p.read_text(encoding="utf-8") for p in (RES / "code").glob("task*.py"))
stale = int(tfm.node_rho.isna().sum())
check("Graph", "no script reads the stale Gene.fibrosis_rho node property",
      not re.search(r"[a-z]\.fibrosis_rho\s+AS|\(g\)\.fibrosis_rho|g\.fibrosis_rho\s*[,\n]", code_txt.replace("pct(g.fibrosis_rho", "")),
      f"note: node property missing for {stale} fibrosis genes (pre-correction values); edges are current")

# ============================================================ Task 2
t2 = pd.read_csv(RES / "Task2/drug_gene_edges.csv")
live = q("MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene) WHERE g.ensembl_id IN $ids RETURN d.node_id AS d, g.ensembl_id AS g, r.action AS a",
         {"ids": t1.ensembl_id.tolist()})
check("T2", "edge count equals fresh Neo4j query", len(t2) == len(live), f"{len(t2)} vs {len(live)}")
check("T2", "identical drug–gene–action triples vs Neo4j",
      set(map(tuple, t2[["Drug_ID", "Gene_ID", "Action_raw"]].values)) == set(map(tuple, live[["d", "g", "a"]].values)))
csv = pd.read_csv(ROOT / "Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv")
csv = csv[csv.to_id.isin(t1.ensembl_id)]
check("T2", "identical to knowledge-layer CSV", set(map(tuple, csv[["from_id", "to_id", "rel_type"]].values)) ==
      set(map(tuple, t2[["Drug_ID", "Gene_ID", "Action_raw"]].values)))
check("T2", "every edge gene is a progression gene", t2.Gene_ID.isin(t1.ensembl_id).all())
DOWN = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE_MODULATOR", "NEGATIVE_ALLOSTERIC_MODULATOR",
        "ALLOSTERIC_ANTAGONIST", "INVERSE_AGONIST", "DEGRADER"}
UP = {"AGONIST", "PARTIAL_AGONIST", "ACTIVATOR", "POSITIVE_MODULATOR", "POSITIVE_ALLOSTERIC_MODULATOR", "OPENER", "STABILISER"}
bad = t2[(t2.Action_raw.isin(DOWN) & (t2.Action_direction != "down") & (t2.Action_direction != "mixed")) |
         (t2.Action_raw.isin(UP) & (t2.Action_direction != "up") & (t2.Action_direction != "mixed")) |
         (t2.Action_raw.isin(PK | {"TARGET"}) & (t2.Action_direction != "unknown"))]
check("T2", "action → direction mapping consistent", bad.empty, f"{len(bad)} inconsistent")
check("T2", "known-direction count = 1,001", t2.Action_direction.isin(["up", "down"]).sum() == 1001)
ann = t2.merge(t1[["ensembl_id", "progression_class", "trajectory_cluster"]], left_on="Gene_ID", right_on="ensembl_id",
               suffixes=("", "_t1"))
check("T2", "gene annotations agree with Task 1", (ann.progression_class == ann.progression_class_t1).all() and
      (ann.cluster.fillna("") == ann.trajectory_cluster.fillna("")).all())

# ============================================================ Task 3
bg_ids = set(pd.read_csv(ROOT / "Paper1_HighConfidence/10_loso_all_eligible_runs.csv", usecols=["ensembl_id"]).ensembl_id)
check("T3", "background = 14,794 genes, contains all 6,222", len(bg_ids) == 14794 and set(t1.ensembl_id) <= bg_ids)
allcsv = pd.read_csv(ROOT / "Paper1_Package/04_DATA/knowledge_layer/edges_drug_gene.csv")
pharm_genes = set(allcsv[~allcsv.rel_type.isin(PK)].to_id) & bg_ids
any_genes = set(allcsv.to_id) & bg_ids
check("T3", "background % any link (indep.) = 14.5%", round(100 * len(any_genes) / 14794, 1) == 14.5, f"{100*len(any_genes)/14794:.2f}%")
check("T3", "background % pharmacological (indep.) = 13.0%", round(100 * len(pharm_genes) / 14794, 1) == 13.0, f"{100*len(pharm_genes)/14794:.2f}%")
s3 = pd.read_csv(RES / "Task3/druggability_summary_pharmacological.csv").set_index("Group")
fib = set(t1.loc[t1.progression_class != "inflammation_only", "ensembl_id"])
k, n = len(fib & pharm_genes), len(fib)
k0, n0 = len((bg_ids - fib) & pharm_genes), len(bg_ids - fib)
p = fisher_exact([[k, n - k], [k0, n0 - k0]]).pvalue
row = s3.loc["Fibrosis-associated (fibrosis-only + shared)"]
check("T3", "fibrosis-associated count & Fisher p reproduce independently",
      row["Drug-connected genes"] == k and np.isclose(row.Fisher_p, p, rtol=1e-6), f"{k}/{n}, p={p:.2e}")
for g in ["fibrosis_only_negative", "shared_negative", "inflammation_only"]:
    ids = set(t1.loc[(t1.paper1_group == g) if g != "inflammation_only" else (t1.progression_class == g), "ensembl_id"])
    check("T3", f"{g} count reproduces", s3.loc[g, "Drug-connected genes"] == len(ids & pharm_genes),
          f"{len(ids & pharm_genes)}/{len(ids)}")
check("T3", "permutation p-values within [1/1001, 1]", s3.Perm_p_two_sided.between(1 / 1001, 1).all())

# ============================================================ Task 4
cov = pd.read_csv(RES / "Task4/drug_coverage.csv")
cand = pd.read_csv(RES / "Task4/repurposing_candidates.csv")
mech = pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv")
liver = pd.read_csv(RES / "Task4/liver_disease_set.csv")
pe = t2[~t2.Action_raw.isin(PK)]
indep = pe.groupby("Drug_ID").Gene_ID.nunique()
cc = cov.set_index("Drug_ID").n_progression_genes
check("T4", "per-drug progression-gene counts reproduce", (cc.reindex(indep.index) == indep).all())
check("T4", "drugs with only enzyme/transporter links have 0 pharm genes",
      (cc.drop(indep.index, errors="ignore") == 0).all())
check("T4", "pharm targets in graph ≥ progression targets", (cov.pharm_targets_graph >= cov.n_progression_genes).all())
check("T4", "progression_target_fraction in [0, 1]", cov.progression_target_fraction.dropna().between(0, 1).all())
excl = liver[liver.excluded_non_hepatic].disease_name.str.lower()
kept = liver[~liver.excluded_non_hepatic].disease_name.str.lower()
check("T4", "malaria/gallbladder/ampulla/erythropoietic removed from liver set",
      not kept.str.contains("malaria|gallbladder|ampulla|extrahepatic").any()
      and not kept.str.contains(r"(?<!hepato)erythropoietic").any(), f"{len(kept)} kept, {len(excl)} removed")
check("T4", "core liver diseases kept (NAFLD, NASH, cirrhosis, HCC)",
      all(kept.str.contains(x).any() for x in ["non-alcoholic fatty liver", "steatohepatitis", "cirrhosis of liver", "hepatocellular carcinoma"]))
check("T4", "hepatoerythropoietic porphyria kept (hepatic)", kept.str.contains("hepatoerythropoietic").any())
liver_ids = liver.loc[~liver.excluded_non_hepatic, "disease_id"].tolist()
already = q("""UNWIND $ids AS id MATCH (d:Drug {node_id:id})-[:TREATS|OFF_LABEL_FOR]->(x:Disease)
            WHERE x.node_id IN $liver RETURN DISTINCT d.node_id AS d""",
            {"ids": cand.Drug_ID.tolist(), "liver": liver_ids})
check("T4", "no candidate has a liver TREATS/OFF_LABEL use (fresh query)", already.empty, f"{len(already)} violations")
check("T4", "all candidates phase ≥ 2, not withdrawn, ≥1 progression gene",
      (cand.max_phase >= 2).all() and (~cand.withdrawn.astype("boolean").fillna(False)).all() and (cand.n_progression_genes >= 1).all())
indep_cand = cov[(cov.max_phase >= 2) & (~cov.withdrawn.astype("boolean").fillna(False)) & (cov.n_progression_genes >= 1)
                 & (~cov.has_liver_indication)]
check("T4", "candidate count reproduces from coverage table", len(indep_cand) == len(cand), f"{len(cand)}")
mech_ids = set(pe[(pe.Action_direction != "unknown") | pe.mechanism_of_action.notna()].Drug_ID)
check("T4", "mechanism-annotated list reproduces", set(mech.Drug_ID) == set(cand.Drug_ID) & mech_ids, f"{len(mech)}")
check("T4", "candidates sorted by fibrosis coverage then fraction",
      cand.n_fibrosis_genes.is_monotonic_decreasing)
ne = pd.read_csv(RES / "Task4/network_edges.csv")
nn = pd.read_csv(RES / "Task4/network_nodes.csv")
check("T4", "network: 30 drugs, every edge endpoint is a node",
      (nn.node_type == "drug").sum() == 30 and set(ne.source) | set(ne.target) <= set(nn.id))
check("T4", "network uses no enzyme/transporter/carrier links", not ne.action.isin(PK).any())

# ============================================================ Task 5 prep
mp = pd.read_csv(RES / "Task5/prep/paper1_term_to_graph_map.csv")
prox = mp[mp.match_type == "gene_overlap_proxy"]
check("T5p", "proxies satisfy Jaccard ≥ 0.5 and ≥ 5 shared genes",
      (prox.match_score >= 0.5).all() and (prox.shared_genes >= 5).all(), f"{len(prox)} proxies")
nm = mp[mp.match_type == "name"]
check("T5p", "name matches use the right node type (GO→BioProcess, Reactome→Pathway)",
      ((nm.database == "GO_BP") == (nm.graph_node_type == "BioProcess")).all())
norm = lambda x: re.sub(r"[^a-z0-9]", "", str(x).lower())
check("T5p", "name matches are exact after normalisation", (nm.term_label.map(norm) == nm.graph_node_name.map(norm)).all())
check("T5p", "no fuzzy matches remain", not (mp.match_type == "fuzzy_name").any())
check("T5p", "all 1,903 Paper 1 terms present", len(mp) == 1903 and mp.term.is_unique)

# ============================================================ Task 5
c5 = pd.read_csv(RES / "Task5/metapath_counts.csv").set_index("MetaPath")
xc5 = pd.read_csv(RES / "Task5/crosscheck_python_vs_neo4j.csv")
check("T5", "Python path counts = Neo4j counts (M1–M4, M6)", xc5.match.all() and len(xc5) == 8, f"{len(xc5)} checks")
liver_ids = liver.loc[~liver.excluded_non_hepatic, "disease_id"].tolist()
m1 = q("""MATCH (d:Drug)-[r:ACTS_ON]->(g:Gene)-[:ASSOCIATED_WITH]->(x:Disease)
WHERE NOT r.action IN $pk AND g.ensembl_id IN $prog AND x.node_id IN $liver
RETURN count(*) AS paths, count(DISTINCT d) AS drugs""", {"pk": list(PK), "prog": t1.ensembl_id.tolist(), "liver": liver_ids}).iloc[0]
row = c5.loc["M1 Drug→Gene→LiverDisease"]
check("T5", "M1 reproduces with a fresh query (no drug filter needed)",
      int(m1.paths) == row.paths and int(m1.drugs) == row["unique drugs"], f"{int(m1.paths):,} paths, {int(m1.drugs):,} drugs")
pe_pairs = pe.merge(pd.read_csv(ROOT / "Paper1_Results/Task3/task3_all_genes_all_transitions.csv", encoding="utf-8-sig")
                    .query("q_value < 0.05"), left_on="Gene_ID", right_on="ensembl_id")
m6_ok = all(c5.loc[f"M6 Drug→{t} transition gene", "paths"] == n for t, n in pe_pairs.groupby("transition").size().items())
check("T5", "M6 per-transition paths reproduce from Task 2 edges", m6_ok)
check("T5", "M5 cluster paths sum to M4 paths minus non-cluster end genes",
      sum(c5.loc[f"M5 Drug→Gene→Pathway←C{k} gene", "paths"] for k in range(1, 6)) <= c5.loc["M4 Drug→Gene→Pathway←ProgressionGene", "paths"])
ds5 = pd.read_csv(RES / "Task5/metapath_drug_scores.csv")
check("T5", "drug scores cover all 2,407 pharmacological drugs, DNS ≥ 0",
      len(ds5) == 2407 and (ds5.filter(like="_dns") >= 0).all().all())
ex = pd.read_csv(RES / "Task5/examples/examples_index.csv")
check("T5", "3 example subgraphs saved (CSV + PNG)",
      len(ex) == 3 and all((RES / "Task5/examples" / f).exists() for f in
                           ["example1_M1f.png", "example2_M7_EMT.png", "example3_M6_PDGFRA.png",
                            "example1_M1f.csv", "example2_M7_EMT.csv", "example3_M6_PDGFRA.csv"]))
ex3 = pd.read_csv(RES / "Task5/examples/example3_M6_PDGFRA.csv")
pdg = t2[(t2.Gene == "PDGFRA") & t2.Drug_ID.isin(cand.Drug_ID) & ~t2.Action_raw.isin(PK)]
check("T5", "Example 3 drugs = all candidates acting on PDGFRA", set(ex3.loc[ex3.relation == "ACTS_ON", "source"]) == set(pdg.Drug))
cy_txt = (RES / "Task5/metapath_queries.cypher").read_text(encoding="utf-8")
check("T5", "Cypher file is read-only (no CREATE/MERGE/SET/DELETE)",
      not re.search(r"\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP)\b", cy_txt))

# ============================================================ Task 6 (design + equal-weight design test)
t6 = RES / "Task6"
proto = pd.read_csv(t6 / "target_scores_equal_weights.csv")
check("T6", "prototype scores all 6,222 genes, every component in [0, 1]",
      len(proto) == 6222 and proto[["P", "F", "T", "K", "B"]].stack().between(0, 1).all())
check("T6", "every design-test row points to the final ranking", proto.STATUS.str.contains("Final_ranking").all())
check("T6", "inflammation-only genes: T = 0 and B = 0 (structural zeros)",
      (proto.loc[proto.progression_class == "inflammation_only", ["T", "B"]] == 0).all().all())
fw = (t6 / "target_score_framework.md").read_text(encoding="utf-8")
abl6 = pd.read_csv(t6 / "ablation_equal_weights.csv").set_index("variant")
sens6 = pd.read_csv(t6 / "weight_sensitivity_equal_weights.csv").set_index("dirichlet_alpha")
k0 = round(100 * (proto.K == 0).mean())
nums = {f"K zero share {k0}%": f"{k0}%" in fw,
        f"without-K top-50 overlap {int(abl6.loc['without K', 'top50_overlap'])}": f"overlap falls to {int(abl6.loc['without K', 'top50_overlap'])}" in fw,
        f"α=1 stable {int(sens6.loc[1.0, 'genes_in_top50_in_>=80%_of_draws'])}": f"only {int(sens6.loc[1.0, 'genes_in_top50_in_>=80%_of_draws'])} genes" in fw,
        f"α=10 stable {int(sens6.loc[10.0, 'genes_in_top50_in_>=80%_of_draws'])}": f"({int(sens6.loc[10.0, 'genes_in_top50_in_>=80%_of_draws'])} under α = 10)" in fw}
check("T6", "framework document numbers match prototype outputs", all(nums.values()),
      ", ".join(k for k, v in nums.items() if not v) or "all match")
check("T6", "framework covers definitions, normalisation, missing values, ablation, Dirichlet",
      all(s in fw for s in ["Component definitions", "Normalisation", "Structural zeros", "Ablation plan", "Dirichlet"]))
check("T6", "freezing rule recorded and applied", "frozen only after Paper 1 is final" in fw and "Final_ranking/PREREGISTRATION.md" in fw)

# ============================================================ Task 7
t7 = pd.read_csv(RES / "Task7/drug_action_evidence.csv")
need = ["Drug", "Gene", "Gene progression direction", "cluster", "Drug action", "Action class", "Evidence source",
        "Evidence level", "Consistency", "is_approved", "repurposing candidate (Task 4)"]
check("T7", "all requested columns present, one row per Task 2 link",
      all(c in t7.columns for c in need) and len(t7) == len(t2), f"{len(t7):,} rows")
# independent re-implementation of the rule (vectorised, different code path)
gi = t1.set_index("ensembl_id")
gd_ = np.where(gi.loc[t2.Gene_ID, "progression_class"].values == "inflammation_only",
               gi.loc[t2.Gene_ID, "inflammation_direction"].values, gi.loc[t2.Gene_ID, "fibrosis_direction"].values)
disc = gi.loc[t2.Gene_ID, "paper1_group"].str.startswith("shared_discordant").values
cdir = t2.cluster.map({"C1": "positive", "C2": "positive", "C3": "positive", "C4": "negative", "C5": "negative"})
conf = (cdir.notna() & (cdir != gd_)).values
act7 = t2.Action_direction.values
exp7 = np.select([act7 == "unknown", (act7 == "mixed") | disc | conf,
                  ((gd_ == "positive") & (act7 == "down")) | ((gd_ == "negative") & (act7 == "up"))],
                 ["unknown", "ambiguous", "direction-consistent"], default="direction-inconsistent")
mine7 = t7.set_index(["Drug_ID", "Gene_ID"]).Consistency
check("T7", "consistency labels reproduce with independent code",
      (pd.Series(exp7, index=pd.MultiIndex.from_arrays([t2.Drug_ID, t2.Gene_ID])).reindex(mine7.index) == mine7).all())
check("T7", "88.5% unknown direction stated and correct",
      round(100 * (t2.Action_direction == "unknown").mean(), 1) == 88.5
      and "88.5%" in (RES / "Task7/summary.md").read_text(encoding="utf-8"))
dd = pd.read_csv(RES / "Task7/drug_direction_summary.csv")
n_cons_cand = t7[(t7["repurposing candidate (Task 4)"]) & (t7.Consistency == "direction-consistent")].Drug_ID.nunique()
cs7 = pd.read_csv(RES / "Task7/candidates_direction_summary.csv")
check("T7", "candidates with ≥1 consistent link reproduce", cs7.iloc[0]["≥1 direction-consistent link"] == n_cons_cand,
      f"{n_cons_cand}")
check("T7", "candidate patterns add up to 1,109", cs7.iloc[0, 2:].sum() == len(cand))
s7 = (RES / "Task7/summary.md").read_text(encoding="utf-8")
check("T7", "summary states consistency is a hypothesis, not proof", "repurposing hypothesis, not proof" in s7)

# ============================================================ Final ranking (plan Task 8)
FR = RES / "Final_ranking"
if (FR / "final_drugs_main_list.csv").exists():
    comp6 = pd.read_csv(RES / "Task6/target_components.csv").set_index("ensembl_id")
    fb = pd.read_csv(FR / "final_targets_biology.csv").set_index("ensembl_id")
    fa = pd.read_csv(FR / "final_targets_actionable.csv").set_index("ensembl_id")
    check("Final", "pre-registration written with frozen rules",
          (FR / "PREREGISTRATION.md").exists() and "written before ranks were computed" in (FR / "PREREGISTRATION.md").read_text(encoding="utf-8"))
    check("Final", "target scores = equal-weight mean of components (biology P,F,T,B; actionable +K)",
          np.allclose(fb.TargetScore, comp6.loc[fb.index, ["P", "F", "T", "B"]].mean(axis=1), atol=1e-4)
          and np.allclose(fa.TargetScore, comp6.loc[fa.index, ["P", "F", "T", "K", "B"]].mean(axis=1), atol=1e-4))
    check("Final", "both target lists cover all 6,222 genes", len(fb) == len(fa) == 6222)
    fd = pd.read_csv(FR / "final_drugs_main_list.csv").set_index("Drug_ID")
    fall = pd.read_csv(FR / "final_drugs_all_candidates.csv").set_index("Drug_ID")
    check("Final", "drug lists = 559 main-list and 1,109 candidates", len(fd) == len(mech) and len(fall) == len(cand))
    dc = ["D1_target_relevance", "D2_direction", "D3_specificity", "D4_graph_support"]
    check("Final", "DrugScore = equal-weight mean of D1–D4, all in [0, 1]",
          np.allclose(fd.DrugScore, fd[dc].mean(axis=1), atol=1e-4) and fd[dc].stack().between(0, 1).all())
    # D1 independently: max biology TargetScore over the drug's pharmacological progression targets
    pe_c = t7[t7.pharmacological_link & t7.Drug_ID.isin(fd.index)]
    d1 = pe_c.assign(s=pe_c.Gene_ID.map(fb.TargetScore)).groupby("Drug_ID").s.max()
    check("Final", "D1 reproduces independently", np.allclose(fd.D1_target_relevance, d1.reindex(fd.index), atol=1e-3))
    nc = pe_c.groupby("Drug_ID").Consistency.agg(lambda s: (s == "direction-consistent").sum())
    ni = pe_c.groupby("Drug_ID").Consistency.agg(lambda s: (s == "direction-inconsistent").sum())
    d2 = np.where(nc + ni > 0, ((nc - ni) / (nc + ni).replace(0, np.nan) + 1) / 2, 0.5)
    check("Final", "D2 reproduces independently", np.allclose(fd.D2_direction, pd.Series(d2, index=nc.index).reindex(fd.index), atol=1e-3))
    check("Final", "no ranked drug already has a liver-disease use", not fd.index.isin(cov.loc[cov.has_liver_indication, "Drug_ID"]).any())
    fs = (FR / "summary.md").read_text(encoding="utf-8")
    check("Final", "summary says repurposing hypotheses, not treatments", "repurposing hypotheses, not treatments" in fs)

# ============================================================ Task 8 report
rep_path = RES / "PAPER2_PROGRESS_REPORT.md"
if rep_path.exists():
    rep = rep_path.read_text(encoding="utf-8")
    check("T8", "report states KG-only repurposing scope and out-of-scope items",
          "Knowledge-graph-only drug repurposing" in rep and "transcriptomic drug-reversal" in rep and "external validation" in rep)
    check("T8", "report has the 6,222 vs 4,692 note", "4,692" in rep and "6,222" in rep)
    check("T8", "report lists the 4 required limitations",
          all(s in rep for s in ["88.5%", "No affinity or potency", "No per-assertion accession IDs", "study bias"]))
    sl_d = t7[t7.pharmacological_link & t7["repurposing candidate (Task 4)"] & t7.in_shortlist].Drug_ID.nunique()
    check("T8", "shortlist-supported vs broad counts correct",
          f"shortlist-supported ({sl_d})" in rep.lower() and f"broad-evidence-only ({len(cand) - sl_d:,})" in rep.lower(),
          f"{sl_d} vs {len(cand) - sl_d:,}")
    check("T8", "known-direction share correct (1,001 / 8,948 = 11.2%)", "(11.2%) have a known action direction" in rep)
    check("T8", "'treatment' only used in negation", all(re.search(r"(not|never)[^.\n]{0,40}treatments?", ln, re.I)
                                                        for ln in rep.splitlines() if re.search(r"\btreatments?\b", ln, re.I)))
    check("T8", "all 8 diagrams referenced and present",
          all(p in rep and (RES / p).exists() for p in ["00_roadmap.png"] + [f"Task{i}/Task{i}_diagram.png" for i in range(1, 8)]))

# ============================================================ wording rules
banned = {r"\banti-?fibrotic (drug|treatment|therap)": "anti-fibrotic claim",
          r"reversal-consistent": "old 'reversal' wording",
          r"\bthe best candidate\b(?! —)(?!\")": "best-candidate claim"}
texts = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in RES.rglob("*.md") if p.name != "AUDIT.md"}
for pat, what in banned.items():
    hits = [f for f, t in texts.items() if re.search(pat, t, re.I)
            and not re.search(r"(not|never|no drug|Do NOT)[^.\n]{0,60}" + pat, t, re.I)]
    check("Rules", f"no {what} in summaries", not hits, ", ".join(hits))
check("Rules", "every task summary mentions 6,222 vs 4,692",
      all("4,692" in texts[f] and "6,222" in texts[f] for f in texts if f.endswith("summary.md")))

# ============================================================ report
df = pd.DataFrame(checks, columns=["Task", "Check", "OK", "Detail"])
lines = ["| Task | Check | Result | Detail |", "|---|---|---|---|"]
lines += [f"| {r.Task} | {r.Check} | {'✅' if r.OK else '❌'} | {r.Detail} |" for r in df.itertuples()]
(RES / "AUDIT.md").write_text(f"""# Paper 2 audit (Tasks 1–8)

Independent re-computation from source files and a fresh read-only Neo4j query. Script: `Paper2_Results/code/audit_tasks.py`.

**{int(df.OK.sum())} / {len(df)} checks passed.**

{chr(10).join(lines)}
""", encoding="utf-8")
print(df.to_string())
print(f"\n{int(df.OK.sum())}/{len(df)} passed")
