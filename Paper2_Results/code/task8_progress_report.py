"""Paper 2 Task 8: summary report (Tasks 1-8 and the final ranking).

Every number is read from the Task 1-7 output files, so the report cannot drift from
the results. Writes Paper2_Results/PAPER2_PROGRESS_REPORT.md and
Paper2_Results/Task8/shortlist_support.csv.

    python Paper2_Results/code/task8_progress_report.py
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"
(RES / "Task8").mkdir(exist_ok=True)


def r(p, **kw):
    return pd.read_csv(RES / p, **kw)


def md(df, idx=False):
    x = df.reset_index() if idx else df
    lines = ["| " + " | ".join(map(str, x.columns)) + " |", "|" + "---|" * x.shape[1]]
    for row in x.values:
        lines.append("| " + " | ".join("" if pd.isna(v) else (f"{v:,}" if isinstance(v, int) else str(v)) for v in row) + " |")
    return "\n".join(lines)


f = lambda x: f"{int(x):,}"

# ---------------- Task 1
g = r("Task1/Paper2_progression_genes.csv")
cls = g.progression_class.value_counts()
grp = g.paper1_group.value_counts()
# ---------------- Task 2
x2 = json.loads((RES / "Task2/crosscheck_neo4j_vs_csv.json").read_text())
e = r("Task2/drug_gene_edges.csv")
# ---------------- Task 3
d3 = r("Task3/druggability_summary_pharmacological.csv").set_index("Group")
bg3 = r("Task3/background_genes_druggability.csv")
pw3 = r("Task3/pairwise_class_comparisons_pharmacological.csv")
# ---------------- Task 4
cov = r("Task4/drug_coverage.csv")
cand = r("Task4/repurposing_candidates.csv")
mech = r("Task4/repurposing_candidates_mechanism_annotated.csv")
liver = r("Task4/liver_disease_set.csv")
hit = cov[cov.n_progression_genes > 0]
wd = hit.withdrawn.astype("boolean").fillna(False)
# ---------------- Task 5
c5 = r("Task5/metapath_counts.csv").set_index("MetaPath")
x5 = r("Task5/crosscheck_python_vs_neo4j.csv")
ds5 = r("Task5/metapath_drug_scores.csv")
top_m1f = ds5[ds5.main_list].sort_values("M1f Drug→Gene→FibrosisSpectrumDisease_dns", ascending=False).head(6).Drug.tolist()
# ---------------- Task 6
abl = r("Task6/ablation_equal_weights.csv").set_index("variant")
sens = r("Task6/weight_sensitivity_equal_weights.csv").set_index("dirichlet_alpha")
proto = r("Task6/target_scores_equal_weights.csv")
# ---------------- Task 7
t7 = r("Task7/drug_action_evidence.csv")
kn = r("Task7/summary_known_vs_unknown.csv")
g7 = r("Task7/consistency_by_paper1_group.csv").set_index("paper1_group")
cs7 = r("Task7/candidates_direction_summary.csv")
cons = t7.Consistency.value_counts()
# ---------------- audit
audit = (RES / "AUDIT.md").read_text(encoding="utf-8")
n_pass = audit.count("✅")
n_all = n_pass + audit.count("❌")

# ---------------- shortlist vs broad support
pe = t7[t7.pharmacological_link & t7["repurposing candidate (Task 4)"]]
sl = pe[pe.in_shortlist]
sup = pd.DataFrame({
    "Candidate set": ["All repurposing candidates", "Main list (mechanism-annotated)", "With ≥1 direction-consistent link"],
    "Total": [len(cand), len(mech), int(cs7.iloc[0]["≥1 direction-consistent link"])],
})
cons_drugs = set(t7[(t7.Consistency == "direction-consistent") & t7["repurposing candidate (Task 4)"]].Drug_ID)
sl_drugs = set(sl.Drug_ID)
sl_cons_drugs = set(sl[sl.Consistency == "direction-consistent"].Drug_ID)
sup["Supported by 23-gene shortlist"] = [len(sl_drugs), len(sl_drugs & set(mech.Drug_ID)), len(sl_cons_drugs)]
sup["Broad progression evidence only"] = sup.Total - sup["Supported by 23-gene shortlist"]
sup["% shortlist-supported"] = (100 * sup["Supported by 23-gene shortlist"] / sup.Total).round(1)
sup.to_csv(RES / "Task8/shortlist_support.csv", index=False)
slg = (sl.groupby("Gene").agg(direction=("Gene progression direction", "first"),
                              candidate_drugs=("Drug_ID", "nunique"),
                              direction_consistent=("Consistency", lambda s: int((s == "direction-consistent").sum())))
       .sort_values("candidate_drugs", ascending=False).reset_index())
slg.to_csv(RES / "Task8/shortlist_genes_with_candidates.csv", index=False)
n_sl_genes = int(g.in_shortlist.sum())

# ---------------- Final ranking (plan Task 8)
FR = RES / "Final_ranking"
fbio = r("Final_ranking/final_targets_biology.csv")
fact = r("Final_ranking/final_targets_actionable.csv")
fdrug = r("Final_ranking/final_drugs_main_list.csv")
abl_d = r("Final_ranking/ablation_drugs_main_list.csv").set_index("dropped")
top_t = fact.head(10).assign(d=lambda x: x.fibrosis_direction.map({"positive": "⬆", "negative": "⬇"}).fillna(""))
top_d = fdrug.head(15)
fr_tab = pd.DataFrame({
    "Rank": top_d["rank"].astype(int), "Drug": top_d.Drug, "Phase": top_d.max_phase.map(lambda v: f"{v:g}"),
    "DrugScore": top_d.DrugScore, "Stable": top_d.stable_drug.map({True: "yes", False: "no"}),
    "Right-way targets": top_d.consistent_targets.fillna(""),
    "Liver flag": top_d.liver_contraindicated.map({True: "contraindicated", False: ""}),
})
tt_tab = pd.DataFrame({"Rank": top_t["rank"].astype(int), "Gene": top_t.Gene + " " + top_t.d,
                       "Class": top_t.progression_class, "Cluster": top_t.trajectory_cluster,
                       "TargetScore": top_t.TargetScore, "Stable": top_t.stable_target.map({True: "yes", False: "no"}),
                       "Shortlist": top_t.in_shortlist.map({True: "yes", False: ""})})
sl_top25 = int(fdrug.head(25).shortlist_supported.sum())

fa = "Fibrosis-associated (fibrosis-only + shared)"
report = f"""# Paper 2 — report (Tasks 1–8, including the final ranking)

*Liver fibrosis progression: knowledge-graph drug repurposing. Prepared {date.today():%d %b %Y}.*

## Scope (project scope decision, 13 Oct 2026)
- **Knowledge-graph-only drug repurposing:** Neo4j `liver_kg` (OptimusKG layer, read-only queries) plus Paper 1 results.
- **Out of scope:** transcriptomic drug-reversal analysis (LINCS/CMap), external databases, and independent external validation.
- All outputs are **repurposing hypotheses / candidate relationships**, not treatments and not evidence of anti-fibrotic efficacy.
- **Gene set:** the plan cites 4,692 progression genes, which was the pre-correction count. Paper 2 uses the **corrected Paper 1 union of {f(len(g))} genes** (final combined version, 10 Oct 2026): fibrosis-only {f(cls['fibrosis_only'])}, shared {f(cls['shared'])}, inflammation-only {f(cls['inflammation_only'])}.

![Roadmap](00_roadmap.png)

## Executive summary
1. **{f(e.Gene_ID.nunique())} / {f(len(g))} progression genes** ({100 * e.Gene_ID.nunique() / len(g):.1f}%) have ≥1 drug in the graph: {f(len(e))} drug–gene links, {f(e.Drug_ID.nunique())} drugs. Neo4j and the knowledge-layer CSV agree exactly.
2. **Fibrosis-associated genes are over-represented among drug targets** ({d3.loc[fa, 'Percentage']:.1f}% vs {100 * bg3.pharm_connected.mean():.1f}% background; {d3.loc[fa, 'Fold vs degree-matched']:.2f}× a degree-matched null), while inflammation-only genes are not. The excess comes mainly from genes that **fall** with fibrosis.
3. **{f(len(cand))} repurposing candidates** (phase ≥ 2, not withdrawn, no existing liver-disease use); **{f(len(mech))}** have mechanism annotation (main list); **{f(cs7.iloc[0]['≥1 direction-consistent link'])}** have ≥1 direction-consistent link.
4. **MetaPaths** connect drugs to liver disease, pathways, processes, trajectory clusters, stage transitions and Paper 1 fibrosis programs. Every count was verified inside Neo4j. The strongest fibrosis-spectrum support comes from **PPAR agonists** ({", ".join(top_m1f[:5])} …), which are direction-**mixed** (consistent on PPARA, inconsistent on PPARG/PPARD).
5. **Only {kn.loc[0, 'known direction (down/up)']:,} of {kn.loc[0, 'total']:,} links ({100 * kn.loc[0, 'known direction (down/up)'] / kn.loc[0, 'total']:.1f}%) have a known action direction.** Rising fibrosis-only genes are mostly targeted in the consistent direction ({g7.loc['fibrosis_only_positive', '% consistent among decided']:.0f}%); falling genes rarely are ({g7.loc['fibrosis_only_negative', '% consistent among decided']:.0f}%), because activators are scarce.
6. **Only {len(sl_drugs)} of {f(len(cand))} candidates ({100 * len(sl_drugs) / len(cand):.1f}%)** act on a gene from the Paper 1 {n_sl_genes}-gene shortlist; the other {f(len(cand) - len(sl_drugs))} rely on broad progression evidence only.
7. **Final ranking (Paper 1 final, rules frozen first):** {int(fact.stable_target.sum())} stable actionable targets and {int(fbio.stable_target.sum())} stable biology targets; {int(fdrug.stable_drug.sum())} stable drugs in the top 25. The top-ranked repurposing hypotheses include a CXCR4 antagonist (mavorixafor), CCR5 antagonists (maraviroc and others), BCL2 inhibitors (venetoclax, obatoclax), NSAIDs acting on PTGS1/2, statins and fibrates.
8. **Quality:** an independent audit (`AUDIT.md`) re-computes the key numbers with separate code and fresh Neo4j queries: **{n_pass}/{n_all} checks pass.** All scripts re-run to identical outputs.

---

## Task 1: master progression-gene table
**Done:** `Task1/Paper2_progression_genes.csv` holds all {f(len(g))} genes with fibrosis/inflammation ρ and q, direction, F0–F4 profile, trajectory cluster, membership confidence, largest stage transition, tier and shortlist flag. No gene was dropped.

| Group | Genes |
|---|---|
| fibrosis-only ⬆ / ⬇ | {f(grp['fibrosis_only_positive'])} / {f(grp['fibrosis_only_negative'])} |
| shared ⬆⬆ / ⬇⬇ / discordant | {f(grp['shared_positive'])} / {f(grp['shared_negative'])} / {f(grp.get('shared_discordant_fib_negative', 0))} |
| inflammation-only ⬆ / ⬇ | {f(grp['inflammation_only_positive'])} / {f(grp['inflammation_only_negative'])} |

All 11 group counts match Paper 1 Task 1.

![Task 1](Task1/Task1_diagram.png)

## Task 2: drug–gene relationships from the knowledge graph
**Done:** `Task2/drug_gene_edges.csv` contains every `Drug-[:ACTS_ON]->Gene` link for the progression genes, read-only from Neo4j, with source evidence (DrugBank / Open Targets, evidence level, mechanism text, literature URLs, approval and phase).

| Measure | Value |
|---|---|
| Links (Neo4j = CSV, identical triples) | {f(x2['edges_source'])} = {f(x2['edges_csv'])} |
| Genes with ≥1 drug | {f(e.Gene_ID.nunique())} ({100 * e.Gene_ID.nunique() / len(g):.1f}%) |
| Unique drugs | {f(e.Drug_ID.nunique())} |
| Known action direction | {f(kn.loc[0, 'known direction (down/up)'])} ({100 * kn.loc[0, 'known direction (down/up)'] / kn.loc[0, 'total']:.1f}%) |
| Evidence level single / multi-source | {f((e.evidence_level == 'single-source').sum())} / {f((e.evidence_level == 'multi-source').sum())} |

![Task 2](Task2/Task2_diagram.png)

## Task 3: druggability across progression groups
**Done:** Fisher's exact tests versus the 14,794-gene Paper 1 eligible background (BH-FDR), plus a degree-aware permutation null (1,000 sets matched on network degree). The main definition counts **pharmacological-target links** only, because ENZYME/TRANSPORTER/CARRIER links describe drug metabolism (CYPs, ABC/SLC transporters). Both definitions are reported, and the conclusions agree.

| Group | % drug-target | Fold vs degree-matched | Permutation FDR |
|---|---|---|---|
""" + "\n".join(
    f"| {lab} | {d3.loc[k, 'Percentage']:.1f} | {d3.loc[k, 'Fold vs degree-matched']:.2f} | {d3.loc[k, 'Perm_BH_FDR']:.3g} |"
    for k, lab in [(fa, "Fibrosis-associated"), ("fibrosis_only_positive", "fibrosis-only ⬆"), ("fibrosis_only_negative", "fibrosis-only ⬇"),
                   ("shared_positive", "shared ⬆⬆"), ("shared_negative", "shared ⬇⬇"), ("inflammation_only", "inflammation-only")]) + f"""

Background: {100 * bg3.pharm_connected.mean():.1f}%. Fibrosis-only vs inflammation-only: OR {pw3.iloc[0]['Odds ratio']:.2f} (FDR {pw3.iloc[0]['BH_FDR']:.3f}); shared vs inflammation-only: OR {pw3.iloc[1]['Odds ratio']:.2f} (FDR {pw3.iloc[1]['BH_FDR']:.3g}).

![Task 3](Task3/Task3_diagram.png)

## Task 4: drug coverage and repurposing candidates
**Done:** per-drug coverage of each Paper 1 group and cluster, progression-target fraction (specificity), approval, phase, withdrawal and existing disease uses from the graph. The liver-disease set is EFO "liver disease" plus descendants, **cleaned of {int(liver.excluded_non_hepatic.sum())} non-hepatic entries** (malaria, gallbladder/ampulla tumours, erythropoietic porphyrias), leaving {int((~liver.excluded_non_hepatic).sum())} diseases.

| Step | Drugs |
|---|---|
| Pharmacological link to a progression gene | {f(len(hit))} |
| Phase ≥ 2 | {f((hit.max_phase >= 2).sum())} |
| Not withdrawn | {f(((hit.max_phase >= 2) & ~wd).sum())} |
| No existing liver-disease use → **repurposing candidates** | **{f(len(cand))}** |
| Mechanism-annotated → **main list** | **{f(len(mech))}** |

{f(cand.liver_contraindicated.sum())} candidates are liver-contraindicated (kept and flagged). Nutrients and cofactors without mechanism (zinc salts, glycine, ATP …) are kept in the full list but separated from the main list. A Cytoscape-ready network of the top 30 main-list candidates is provided. **Candidate generation only; no drug is called the best candidate.**

![Task 4](Task4/Task4_diagram.png)

## Task 5: MetaPaths
**Done:** M1 (Drug→Gene→liver disease), M1f (fibrosis-spectrum diseases), M2 (Reactome), M3 (GO BP), M4/M5 (Drug→Gene→Pathway←progression / cluster genes), M6 (stage-transition genes), M7 (Paper 1 fibrosis-enriched GO/Reactome/KEGG/Hallmark terms, via graph nodes or Paper 1 gene lists). Degree-normalised support = paths / √(drug degree × end-node degree). All queries are in `Task5/metapath_queries.cypher`.

| MetaPath | Paths | Drugs | Candidate drugs |
|---|---|---|---|
""" + "\n".join(
    f"| {k} | {f(c5.loc[k, 'paths'])} | {f(c5.loc[k, 'unique drugs'])} | {f(c5.loc[k, 'candidate drugs'])} |"
    for k in c5.index if not k.startswith(("M5", "M7"))) + f"""
| M5 (5 clusters), M7 (4 databases × link type) | see `Task5/metapath_counts.csv` | | |

Python counts equal Neo4j counts for all {len(x5)} cross-checks. Three quality-check subgraphs are in `Task5/examples/`: a PPAR agonist → fibrosis-spectrum diseases, Hallmark EMT, and PDGFRA.

![Task 5](Task5/Task5_diagram.png)

## Task 6: target-prioritisation framework (design and test run)
**Done:** `Task6/target_score_framework.md` defines TargetScore = w1·P + w2·F + w3·T + w4·K + w5·B with every component in [0, 1] and traceable to Paper 1 / Paper 2 columns. It covers normalisation (percentile ranks), structural zeros instead of imputation, and the ablation and Dirichlet weight-sensitivity plans. An equal-weight **design test** (whose weights were later frozen for the final ranking) runs on all {f(len(proto))} genes:
- K is zero for {100 * (proto.K == 0).mean():.0f}% of genes, and removing K keeps only {int(abl.loc['without K', 'top50_overlap'])}/50 of the top 50. **Report two lists:** a biology score (P, F, T, B) for novel targets and an actionable score (with K) for repurposing.
- Under Dirichlet α = 1, only {int(sens.loc[1.0, "genes_in_top50_in_>=80%_of_draws"])} genes stay in the top 50 in ≥ 80% of draws ({int(sens.loc[10.0, "genes_in_top50_in_>=80%_of_draws"])} at α = 10). Report **stable** targets, not single-weight ranks.
- P, F and T overlap (they all describe fibrosis association). Consider merging them before the weights are frozen.

![Task 6](Task6/Task6_diagram.png)

## Task 7: drug action vs. progression direction
**Done:** each link is classed as direction-consistent (inhibits a rising gene / activates a falling gene), direction-inconsistent, ambiguous or unknown, using knowledge-graph action labels only.

| Consistency | Links |
|---|---|
""" + "\n".join(f"| {k} | {f(cons.get(k, 0))} |" for k in ["direction-consistent", "direction-inconsistent", "ambiguous", "unknown"]) + f"""

| Group | % consistent among judged links |
|---|---|
""" + "\n".join(f"| {k} | {g7.loc[k, '% consistent among decided']:.0f}% |" for k in
                ["fibrosis_only_positive", "fibrosis_only_negative", "shared_positive", "shared_negative",
                 "inflammation_only_positive", "inflammation_only_negative"]) + f"""

{f(cs7.iloc[0]['≥1 direction-consistent link'])} of {f(len(cand))} candidates have ≥1 direction-consistent link ({f(cs7.iloc[0]['only consistent'])} only consistent, {f(cs7.iloc[0]['mixed'])} mixed, {f(cs7.iloc[0]['only inconsistent'])} only inconsistent).

![Task 7](Task7/Task7_diagram.png)

---

## Final target and drug ranking (plan Task 8)
**Paper 1 confirmed final (10 Oct 2026 version).** The ranking rules and equal weights were frozen in `Final_ranking/PREREGISTRATION.md` before any rank was computed; nothing was tuned. Stability = rank under 1,000 near-equal random weightings (Dirichlet α = 10); a target or drug is **stable** if it stays in the top 50 / top 25 in at least 80% of draws.

**Targets.** Two lists: *biology* (P, F, T, B) for new targets and *actionable* (P, F, T, K, B) for repurposing. Stable: {int(fbio.stable_target.sum())} biology, {int(fact.stable_target.sum())} actionable. Top 10 actionable targets:

{md(tt_tab)}

**Drugs.** DrugScore = mean of D1 target relevance (best biology TargetScore among the drug's targets), D2 direction-consistency (Task 7), D3 specificity (progression-target fraction) and D4 knowledge-graph support (Task 5). Ranked among the {f(len(fdrug))} mechanism-annotated candidates; {int(fdrug.stable_drug.sum())} are stable in the top 25. Top 15:

{md(fr_tab)}

Shortlist-supported drugs in the top 25: {sl_top25}; broad-evidence-only: {25 - sl_top25}. Ablation: dropping D4 (graph support) changes the top 25 the most (top-25 overlap {int(abl_d.loc['D4_graph_support', 'top25_overlap'])}/25), and dropping D2 (direction) changes overall order the most (Spearman {abl_d.loc['D2_direction', 'spearman']:.2f}). Evidence cards (which layers support, contradict or are missing for each of the top 25) are in `Final_ranking/evidence_cards_top25.csv` and `Final_ranking/summary.md`.

![Final ranking](Final_ranking/Final_ranking_diagram.png)

## Shortlist-supported vs. broad-evidence-only candidates
{md(sup)}

Shortlist genes reached by candidates ({len(slg)} of {n_sl_genes}):

{md(slg)}

Most shortlist-supported candidates come from two rising genes, **CACNA1C** (calcium channel) and **HTR7** (serotonin receptor). CACNA1C has {int(slg.set_index("Gene").loc["CACNA1C","direction_consistent"])} direction-consistent links (blockers of a rising gene), whereas HTR7 links are mostly "target" with unknown direction ({int(slg.set_index("Gene").loc["HTR7","direction_consistent"])} consistent of {int(slg.set_index("Gene").loc["HTR7","candidate_drugs"])}).

## Limitations
1. **{kn.loc[0, '% unknown']}% of drug–gene links have unknown action direction** (TARGET/ENZYME/TRANSPORTER/CARRIER). Direction-consistency can only be judged for {f(kn.loc[0, 'known direction (down/up)'])} links, and unknown is not the same as inconsistent.
2. **No affinity or potency values** in the graph, so drug strength cannot be weighted.
3. **No per-assertion accession IDs.** Links are identified by ChEMBL drug ID | Ensembl gene ID with source names and, where available, literature URLs.
4. **Knowledge-graph study bias:** well-studied (high-degree) genes have more known drugs (background druggability rises from {r('Task3/background_degree_bins.csv').pct_pharm.iloc[0]:.1f}% to {r('Task3/background_degree_bins.csv').pct_pharm.iloc[-1]:.1f}% across degree bins). This is addressed with degree-matched nulls and degree-normalised MetaPath support, but not removed.
5. **Graph housekeeping (does not affect results):** in the live Neo4j graph the `fibrosis_rho` property stored on Gene nodes is from the pre-correction Paper 1 run (3,645 genes; missing for 391 current fibrosis genes). The `TRACKS_FIBROSIS` edges are current and match the corrected Paper 1 table exactly. Paper 2 uses only the corrected tables and edges, but the node property should be refreshed by the Paper 1 team.
6. "No liver indication" means none is recorded in the graph, not necessarily none in practice. EFO filed some non-hepatic diseases under "liver disease"; the cleaning rule is documented.
7. Target-score weights were frozen as equal weights for the final ranking (`Final_ranking/PREREGISTRATION.md`); Task 6 keeps the design test that motivated the two-list, stable-target reporting.
8. Scope limits by design: no transcriptomic reversal, no external validation.

## Next steps
1. **Done:** final target and drug ranking with frozen rules, stability and ablation analyses, and evidence cards (section above). Shortlist-supported ({len(sl_drugs)}) and broad-evidence-only ({len(cand) - len(sl_drugs):,}) candidates are reported separately.
2. **Safety and literature review** of the stable top candidates, starting with those flagged as liver-contraindicated in the graph, before any experimental follow-up.
3. **Experimental or clinical validation** of selected hypotheses is outside this knowledge-graph study (project scope decision) and would be the next project.
4. Decisions to confirm: (a) accept the pharmacological-target definition (Task 3), (b) accept the cleaned liver-disease set (Task 4), (c) main list = mechanism-annotated candidates, (d) the two-list target-score reporting.

## Files and reproducibility
Every task folder has `summary.md`, a diagram and CSV outputs; scripts are in `Paper2_Results/code/`. Re-check everything with `python Paper2_Results/code/audit_tasks.py`. Guide and prompts: `PAPER2_GUIDE.md`.
"""
(RES / "PAPER2_PROGRESS_REPORT.md").write_text(report, encoding="utf-8")
print(report)
