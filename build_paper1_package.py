"""build_paper1_package.py
--------------------------
Assembles Paper1_Package/ -- one self-contained folder that someone who has
never seen this project can read, verify and write the manuscript from.

WHY THIS IS A SCRIPT AND NOT A HAND-COPIED FOLDER
A folder assembled by hand drifts the moment any analysis is re-run, and
nobody can tell which copy is stale. This script rebuilds the whole package
from the committed outputs in one pass, so the package is always a function of
the results rather than a snapshot of them. Re-run it after any analysis
changes.

WHAT IS DELIBERATELY NOT COPIED
  data/raw          104 MB of GEO downloads -- provenance is recorded in
                    06_PROVENANCE/DATA_SOURCES.md instead, with the exact
                    filename taken from each study.
  data/interim_full 197 MB, data/graph_full 2.1 GB, data/graph_all 1.6 GB,
                    data/primekg 937 MB, data/kg_triples 138 MB
                    -- regenerable, and no number in the paper is read from
                    them directly. REBUILD.md carries the commands.
  data/genesets     MSigDB gene sets. The KEGG-derived sets may not be
                    redistributed, so the download URL is given instead.
The result is ~90 MB: small enough to e-mail as a zip, complete enough that
every figure, table and statistic in the paper can be traced to a file in it.

FIGURE AND TABLE NUMBERING
The numbering lives HERE, in MAIN_FIGURES / SUPP_FIGURES / MAIN_TABLES, and
nowhere else. Captions are written from the same lists, so a figure cannot be
renumbered in one place and not the other.

Usage:
    python build_paper1_package.py
"""
import csv
import hashlib
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(ROOT, "Paper1_Package")

RESULTS = os.path.join(ROOT, "Paper1_Results")
HIGHCONF = os.path.join(ROOT, "Paper1_HighConfidence")
MANUSCRIPT = os.path.join(ROOT, "Paper1_Manuscript")
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------- figures
# (source path relative to ROOT, new name, short caption title, caption body)
MAIN_FIGURES = [
    ("Paper1_Results/Figure1/figure1_pipeline.png", "Figure1_pipeline.png",
     "Study design and analysis pipeline.",
     "Eight public GEO liver transcriptome studies parsed to a common long "
     "format, harmonised on the gene axis (identifier mapping to Ensembl) "
     "and the patient axis (fibrosis stage, disease group, patient "
     "identity), standardised within study, and loaded into a Neo4j "
     "property graph together with a curated knowledge layer. Every number "
     "shown on the figure is read from the committed outputs."),
    ("Paper1_Results/Task1/task1_venn.png", "Figure2_ladder_overlap.png",
     "Overlap between the two progression ladders.",
     "Genes significantly associated with fibrosis stage and with disease "
     "group, giving the fibrosis-only (1,953), inflammation-only (1,047) "
     "and shared (1,692) partitions used throughout the paper."),
    ("Paper1_Results/Task1/task1_shared_rho_scatter.png",
     "Figure3_shared_gene_agreement.png",
     "Agreement between ladders among shared genes.",
     "Fibrosis correlation against inflammation correlation for the 1,692 "
     "shared genes. The two clouds are concordantly rising and concordantly "
     "falling genes; one gene (GPD1) is discordant. Spearman rho = 0.725 "
     "overall, 0.453 within rising genes and 0.354 within falling genes."),
    ("Paper1_Results/Task2/task2_cluster_means.png",
     "Figure4_trajectory_shapes.png",
     "The five fibrosis trajectory shapes.",
     "Mean standardised expression of each cluster at fibrosis stages F0 to "
     "F4. Cluster names were assigned after clustering, from these curves; "
     "no gene was assigned to a pattern by hand."),
    ("Paper1_Results/Task2/task2_heatmap.png", "Figure5_stage_heatmap.png",
     "Stage profiles of all 3,645 fibrosis-associated genes.",
     "Genes in rows grouped by cluster, stages F0-F4 in columns. Values are "
     "mean standardised expression per stage."),
    ("Paper1_Results/Task2/task2_choosing_k.png",
     "Figure6_choosing_k.png",
     "Choice of cluster number.",
     "Silhouette score, gene-subsample stability and patient-bootstrap "
     "stability for k = 3 to 8. k = 5 is the largest k retaining a "
     "gene-subsample adjusted Rand index of at least 0.95."),
    ("Paper1_Results/Task3/task3_transition_comparison.png",
     "Figure7_stage_transitions.png",
     "Comparison of the four stage transitions.",
     "Counts of substantially changing genes on the full data, the same "
     "counts under the power-matched design of 30 patients per stage, and "
     "the distribution of effect sizes. Equalising power isolates F3-F4 as "
     "the transition carrying the largest transcriptional change."),
    ("Paper1_Results/Task4/task4_heatmap_hallmark.png",
     "Figure8_hallmark_enrichment.png",
     "Hallmark process enrichment across groups and clusters.",
     "All significantly enriched Hallmark processes (FDR < 0.05) by gene "
     "group and trajectory cluster, tested against the 14,794-gene "
     "eligible background."),
    ("Paper1_HighConfidence/12_mechanistic_subgraph.png",
     "Figure9_mechanism_subgraph.png",
     "Where the high-confidence fibrosis genes converge.",
     "The twelve mechanisms significantly over-represented among the 507 "
     "Tier 1 genes, with the genes reaching three or more of them plus "
     "every one of the final 25 reaching any: 46 genes, 12 mechanisms, 169 "
     "edges. Edges are INVOLVED_IN for biological processes (126) and "
     "IN_PATHWAY for pathways (43). Read the convergence as coming from "
     "Tier 1 as a whole, not from the final 25 -- see 05_LIMITATIONS.md."),
]

SUPP_FIGURES = [
    ("Paper1_Results/Task2/task2_cluster_trajectories.png",
     "FigureS1_all_gene_trajectories.png",
     "Every fibrosis gene's trajectory, by cluster.",
     "All 3,645 genes in grey with the cluster average overlaid, one panel "
     "per cluster. Shows the spread behind each averaged shape in Figure 4."),
    ("Paper1_Results/Task3/task3_delta_distributions.png",
     "FigureS2_transition_deltas.png",
     "Distribution of change per transition.",
     "Per-transition distribution of expression change, at stage-mean level "
     "and at patient level."),
    ("Paper1_Results/Task4/task4_heatmap_go_bp.png",
     "FigureS3_enrichment_GO_BP.png",
     "GO Biological Process enrichment across groups and clusters.",
     "Top five GO BP terms per group, FDR < 0.05, against the 14,794-gene "
     "background."),
    ("Paper1_Results/Task4/task4_heatmap_reactome.png",
     "FigureS4_enrichment_Reactome.png",
     "Reactome enrichment across groups and clusters.",
     "Top five Reactome terms per group, FDR < 0.05, against the "
     "14,794-gene background."),
    ("Paper1_Results/Task4/task4_heatmap_kegg.png",
     "FigureS5_enrichment_KEGG.png",
     "KEGG enrichment across groups and clusters.",
     "Top five KEGG terms per group, FDR < 0.05, against the 14,794-gene "
     "background."),
]
# the 15 dot plots, numbered S6 onward in a fixed order
_DOTS = [
    ("fibrosis_only_up", "fibrosis-only rising genes"),
    ("fibrosis_only_down", "fibrosis-only falling genes"),
    ("inflammation_only_up", "inflammation-only rising genes"),
    ("shared_up", "genes rising on both ladders"),
    ("shared_down", "genes falling on both ladders"),
    ("C1_all", "cluster C1 (early increase), all genes"),
    ("C1_core", "cluster C1, high-confidence members only"),
    ("C2_all", "cluster C2 (late increase), all genes"),
    ("C2_core", "cluster C2, high-confidence members only"),
    ("C3_all", "cluster C3 (early rise, then plateau), all genes"),
    ("C3_core", "cluster C3, high-confidence members only"),
    ("C4_all", "cluster C4 (mid decrease), all genes"),
    ("C4_core", "cluster C4, high-confidence members only"),
    ("C5_all", "cluster C5 (late decrease), all genes"),
    ("C5_core", "cluster C5, high-confidence members only"),
]
for _i, (_slug, _what) in enumerate(_DOTS, start=6):
    SUPP_FIGURES.append((
        "Paper1_Results/Task4/dot_plots/dot_%s.png" % _slug,
        "FigureS%d_dotplot_%s.png" % (_i, _slug),
        "Enrichment dot plot: %s." % _what,
        "Top five terms per database. x = gene ratio, point size = number of "
        "genes, colour = -log10 FDR. Tested against the 14,794-gene "
        "eligible background."))

# ----------------------------------------------------------------- tables
# (source relative to ROOT, new name, caption title, caption body)
# Table1 is generated by this script; see make_table1().
MAIN_TABLES = [
    (None, "Table1_cohort.csv",
     "The eight studies and what each contributes.",
     "Samples, patients, fibrosis staging, disease labels and demographic "
     "coverage per study. Generated by build_paper1_package.py from "
     "data/for_mentor/sample_demographics.csv, so it cannot drift from the "
     "harmonised clinical table."),
    ("Paper1_Results/Task1/task1_summary.csv", "Table2_gene_groups.csv",
     "Progression genes by group and direction.",
     "Counts and percentages for the fibrosis-only, inflammation-only and "
     "shared partitions, split by direction of change."),
    ("Paper1_Results/Task2/task2_cluster_sizes.csv",
     "Table3_trajectory_clusters.csv",
     "The five trajectory clusters.",
     "Genes per cluster with the cluster mean standardised expression at "
     "each fibrosis stage."),
    ("Paper1_Results/Task3/task3_transition_summary.csv",
     "Table4_stage_transitions.csv",
     "The four stage transitions compared.",
     "Patient counts, substantially changing genes, direction split, median "
     "effect size and power-matched counts for each transition."),
    ("Paper1_Results/Task4/task4_significant_counts.csv",
     "Table5_enrichment_counts.csv",
     "Significantly enriched terms per group.",
     "Counts of terms at FDR < 0.05 in each of the four databases, per gene "
     "group and per trajectory cluster."),
    ("Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv",
     "Table6_prioritised_25_genes.csv",
     "The 25 prioritised fibrosis genes.",
     "The five highest-scoring Tier 1 genes per trajectory cluster, ties "
     "broken by correlation magnitude, with all five evidence scores, the "
     "stage of largest change and the leave-one-study-out results."),
]

SUPP_TABLES = [
    ("Paper1_Results/Task1/task1_top20_fibrosis_genes.csv",
     "TableS1_top20_fibrosis_genes.csv",
     "Strongest fibrosis-associated genes.",
     "Top 20 rising and top 20 falling genes by cross-study fibrosis "
     "correlation."),
    ("Paper1_Results/Task2/task2_gene_clusters.csv",
     "TableS2_gene_cluster_assignments.csv",
     "Cluster assignment for every fibrosis gene.",
     "All 3,645 genes with stage means F0-F4, cluster, correlation to the "
     "cluster centroid and bootstrap membership confidence. Use "
     "membership_confidence >= 0.8 for any claim about an individual gene."),
    ("Paper1_Results/Task2/task2_representative_genes.csv",
     "TableS3_representative_genes.csv",
     "Representative genes per cluster.",
     "Fifteen genes per cluster ranked by membership confidence, then by "
     "closeness to the cluster shape."),
    ("Paper1_Results/Task2/task2_choosing_k.csv",
     "TableS4_choosing_k.csv",
     "Cluster-number diagnostics.",
     "Silhouette score and both stability measures for k = 3 to 8."),
    ("Paper1_Results/Task2/task2_robustness.csv",
     "TableS5_clustering_robustness.csv",
     "Clustering robustness.",
     "Study-adjustment and patient-bootstrap summary for the clustering."),
    ("Paper1_Results/Task3/task3_all_genes_all_transitions.csv",
     "TableS6_all_genes_all_transitions.csv",
     "Every gene at every transition.",
     "Per gene and transition: stage-mean difference, study-adjusted beta, "
     "standard error, p, q, patient counts, substantial flag and cluster."),
    ("Paper1_Results/Task3/task3_top_genes_per_transition.csv",
     "TableS7_top_genes_per_transition.csv",
     "Strongest genes per transition.",
     "Top 20 rising and falling genes per transition at q < 0.05, ranked by "
     "effect size."),
    ("Paper1_Results/Task4/task4_top_pathways_per_group.csv",
     "TableS8_top_pathways_per_group.csv",
     "Leading enriched terms per group.",
     "Top ten terms per group and database with the genes responsible."),
    ("Paper1_Results/Task4/task4_all_significant.csv",
     "TableS9_all_significant_terms.csv",
     "Every significantly enriched term.",
     "All terms at FDR < 0.05 across every group and database."),
    ("Paper1_Results/Task4/task4_cluster_core_check.csv",
     "TableS10_cluster_core_check.csv",
     "All-gene against high-confidence enrichment.",
     "Whether each cluster's leading biology survives when only "
     "high-confidence cluster members are used."),
    ("Paper1_HighConfidence/01_master_table.csv",
     "TableS11_evidence_scores_all_genes.csv",
     "Evidence scores for all 3,645 fibrosis genes.",
     "Every intermediate behind the five scores, the total and the tier, "
     "for every scored gene -- nothing hidden behind the selection."),
    ("Paper1_HighConfidence/11_final_tier1_507_genes.csv",
     "TableS12_tier1_507_genes.csv",
     "All 507 Tier 1 genes.",
     "The full high-confidence set, same columns as Table 6."),
    ("Paper1_HighConfidence/10_loso_summary.csv",
     "TableS13_leave_one_study_out.csv",
     "Leave-one-study-out results per gene.",
     "For each Tier 1 gene: direction retained, still significant, still "
     "above the correlation threshold, weakest median correlation and "
     "largest percentage loss, over the five fibrosis-staging studies."),
    ("Paper1_HighConfidence/08_tier_sensitivity.csv",
     "TableS14_tier_cutoff_sensitivity.csv",
     "Sensitivity of the Tier 1 boundary.",
     "Tier 1 membership at score cutoffs 6, 7 and 8, with overlap against "
     "the frozen choice of 7."),
    ("Paper1_HighConfidence/08_leave_one_score_out.csv",
     "TableS15_leave_one_score_out.csv",
     "Sensitivity of the ranking to each score.",
     "Dropping each of the five scores in turn: Spearman correlation "
     "against the full ranking and overlap of the top band."),
    ("Paper1_HighConfidence/09b_option_comparison.csv",
     "TableS16_shortlist_rule_comparison.csv",
     "The two shortlist rules considered.",
     "Composition of the chosen rule (top five per cluster) against the "
     "alternative (each cluster's own top score)."),
    ("Paper1_HighConfidence/12_KG_supplementary.xlsx",
     "TableS17_knowledge_graph_connections.xlsx",
     "Knowledge-graph connections and mechanism ranking.",
     "Seven sheets: per-gene connections for the 25 and for all 507, every "
     "mechanism ranked with fold enrichment and q, the drawn nodes and "
     "edges of Figure 9, and the collapsed near-duplicates."),
]

# ------------------------------------------------------------------- data
# (source dir relative to ROOT, destination subfolder)
DATA_COPIES = [
    ("data/for_mentor", "04_DATA/gene_tables"),
    ("data/progression_full", "04_DATA/progression_statistics"),
    ("data/processed", "04_DATA/harmonisation"),
    # BOTH knowledge layers ship, deliberately. data/graph_okg (OptimusKG) is
    # the layer actually loaded into Neo4j -- its counts match the graph
    # described in the paper exactly. data/graph_kg (PrimeKG) is superseded,
    # but hc4_kg_subgraph.py reads it, so Figure 9 cannot be reproduced
    # without it. See 05_LIMITATIONS.md section 14.
    ("data/graph_okg", "04_DATA/knowledge_layer_optimuskg"),
    ("data/graph_kg", "04_DATA/knowledge_layer_primekg_superseded"),
]
DATA_FILES = [
    ("data/graph_full/gene_progression_scores.csv",
     "04_DATA/graph_nodes/gene_progression_scores.csv"),
    ("data/graph_full/nodes_gene.csv", "04_DATA/graph_nodes/nodes_gene.csv"),
    ("data/graph_full/nodes_dataset.csv",
     "04_DATA/graph_nodes/nodes_dataset.csv"),
    ("data/interim_full/_parse_summary.csv",
     "04_DATA/harmonisation/_parse_summary.csv"),
]

# ------------------------------------------------------------------- code
CODE_COPIES = [
    # (source, destination) -- pipeline order is encoded in the filenames
    ("parse_expression.py", "05_CODE/pipeline/01_parse_expression.py"),
    ("map_gene_ids.py", "05_CODE/pipeline/02_map_gene_ids.py"),
    ("build_crosswalk.py", "05_CODE/pipeline/03_build_crosswalk.py"),
    ("normalize_clinical.py", "05_CODE/pipeline/04_normalize_clinical.py"),
    ("build_graph_all.py", "05_CODE/pipeline/05_build_graph_all.py"),
    ("build_optimuskg_layer.py",
     "05_CODE/pipeline/06_build_optimuskg_layer.py"),
    ("find_progression_genes.py",
     "05_CODE/pipeline/07_find_progression_genes.py"),
    ("export_for_mentor.py", "05_CODE/pipeline/08_export_for_mentor.py"),
    ("paper1_task1_groups.py", "05_CODE/analysis/task1_groups.py"),
    ("paper1_task2_trajectories.py",
     "05_CODE/analysis/task2_trajectories.py"),
    ("paper1_task3_transitions.py", "05_CODE/analysis/task3_transitions.py"),
    ("paper1_task4_enrichment.py", "05_CODE/analysis/task4_enrichment.py"),
    ("Paper1_Results/Figure1/make_fig1.py",
     "05_CODE/analysis/make_figure1.py"),
    ("Paper1_HighConfidence/powermatched_transitions.py",
     "05_CODE/analysis/hc1_powermatched_transitions.py"),
    ("Paper1_HighConfidence/high_confidence_genes.py",
     "05_CODE/analysis/hc2_high_confidence_genes.py"),
    ("Paper1_HighConfidence/loso_validation.py",
     "05_CODE/analysis/hc3_loso_validation.py"),
    ("Paper1_HighConfidence/kg_subgraph.py",
     "05_CODE/analysis/hc4_kg_subgraph.py"),
    ("Paper1_HighConfidence/00_all_4692_progression_genes.py",
     "05_CODE/analysis/hc0_all_progression_genes.py"),
    ("Paper1_HighConfidence/audit_handover.py",
     "05_CODE/analysis/hc5_audit_handover.py"),
    ("create_kg_constraints.cypher",
     "05_CODE/cypher/01_create_kg_constraints.cypher"),
    ("load_edges.cypher", "05_CODE/cypher/02_load_edges.cypher"),
    ("reload_expression.cypher",
     "05_CODE/cypher/03_reload_expression.cypher"),
    ("export_triples.py", "05_CODE/unresolved/export_triples.py"),
    ("train_link_prediction.py",
     "05_CODE/unresolved/train_link_prediction.py"),
    ("requirements.txt", "05_CODE/requirements.txt"),
    ("build_paper1_package.py", "05_CODE/build_paper1_package.py"),
]

RESULT_COPIES = [
    ("Paper1_Results/Task1", "03_RESULTS/Task1_gene_groups"),
    ("Paper1_Results/Task2", "03_RESULTS/Task2_trajectories"),
    ("Paper1_Results/Task3", "03_RESULTS/Task3_transitions"),
    ("Paper1_Results/Task4", "03_RESULTS/Task4_enrichment"),
    ("Paper1_HighConfidence", "03_RESULTS/Task5_high_confidence_genes"),
]

SKIP_IN_RESULTS = {".py"}          # code is collected under 05_CODE instead

CORRECTIONS = """CORRECTIONS TO README.txt IN THIS FOLDER
=======================================

README.txt is the committed record of this analysis and is copied here
unmodified. Three numbers in it are wrong. They are corrected below rather
than edited in place, so that both versions stay visible.

All three are in LIMITATION 9, "THE FINAL 25 BARELY CONVERGE".

  README.txt says                           Recomputed value
  ---------------------------------------   ----------------------------
  "168 of the 507 reach at least one"       166 of the 507
  "24 reach three or more"                  39 reach three or more
  "NOT ONE [of the 25] reaches three"       one does: PDGFRA reaches 3

Recomputed from 12_KG_supplementary.xlsx, which is correct, by matching
Mechanism_ID in sheets 1_shortlist_25_KG and 2_tier1_507_KG against the 12
rows of sheet 3_all_mechanisms_ranked where selected_for_figure is true.

The 39 is confirmed independently by the figure's own composition. The figure
draws genes reaching three or more mechanisms plus any of the final 25
reaching at least one, and sheet 5_figure_nodes holds 38 nodes of kind
"Tier 1 gene" plus 8 of kind "Final 25 gene". 38 + PDGFRA = 39.

Sheet 5 also gives PDGFRA a Degree_in_figure of 3, which is the same fact
from the other direction.

WHAT IS NOT AFFECTED
  The analysis, the figure and the workbook are all correct. So are the two
  other convergence statements in README.txt, both verified: among the 25,
  exactly 2 pathways connect two or more of them and none connects three or
  more; across all 507 Tier 1 genes, 328 pathways connect two or more and
  163 connect three or more.

  The direction of limitation 9 is unchanged and still holds: the final 25
  barely converge, and the convergence in the figure comes from the other
  Tier 1 genes. Only the three numbers above change.

USE THE NUMBERS IN
  00_START_HERE/03_STATISTICS.md  section 7
  00_START_HERE/05_LIMITATIONS.md section 7

A SEPARATE AND LARGER ISSUE
  This folder's figure (12_mechanistic_subgraph.png, shipped as Figure 9) was
  built from the superseded PrimeKG knowledge layer, not from the OptimusKG
  layer the graph actually holds, although kg_subgraph.py's docstring and the
  workbook's caveats sheet both state otherwise. That one needs resolving
  before submission, not just disclosing. See 00_START_HERE/05_LIMITATIONS.md
  section 14.
"""


# --------------------------------------------------------------- utilities
def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ensure(path):
    os.makedirs(path, exist_ok=True)
    return path


def copy(src_rel, dst_rel, missing):
    src = os.path.join(ROOT, src_rel)
    dst = os.path.join(PKG, dst_rel)
    if not os.path.exists(src):
        missing.append(src_rel)
        return False
    ensure(os.path.dirname(dst))
    shutil.copy2(src, dst)
    return True


def copy_tree(src_rel, dst_rel, missing, skip_ext=()):
    src = os.path.join(ROOT, src_rel)
    if not os.path.isdir(src):
        missing.append(src_rel + "/")
        return 0
    n = 0
    for dirpath, _dirs, files in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        for f in files:
            if os.path.splitext(f)[1] in skip_ext:
                continue
            out_rel = os.path.join(dst_rel, "" if rel == "." else rel, f)
            ensure(os.path.dirname(os.path.join(PKG, out_rel)))
            shutil.copy2(os.path.join(dirpath, f),
                         os.path.join(PKG, out_rel))
            n += 1
    return n


# ------------------------------------------------------------------ Table 1
def make_table1(dst_rel):
    """The cohort table, built from the harmonised clinical file.

    Written here rather than copied because no committed output holds it:
    it is the one table the paper needs that the analyses never produced.
    """
    src = os.path.join(DATA, "for_mentor", "sample_demographics.csv")
    if not os.path.exists(src):
        return False
    rows = list(csv.DictReader(open(src, newline="", encoding="utf-8-sig")))
    studies = {}
    for r in rows:
        s = studies.setdefault(r["dataset_id"], {
            "samples": 0, "patients": set(), "staged": 0, "grouped": 0,
            "age": 0, "sex": 0, "stages": {}, "groups": {}})
        s["samples"] += 1
        s["patients"].add(r["patient_id"])
        if r["fibrosis_stage"]:
            s["staged"] += 1
            k = int(float(r["fibrosis_stage"]))
            s["stages"][k] = s["stages"].get(k, 0) + 1
        if r["disease_group"]:
            s["grouped"] += 1
            s["groups"][r["disease_group"]] = \
                s["groups"].get(r["disease_group"], 0) + 1
        if r["age_years"]:
            s["age"] += 1
        if r["sex"]:
            s["sex"] += 1

    out = os.path.join(PKG, dst_rel)
    ensure(os.path.dirname(out))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["study", "samples", "patients", "repeat_biopsies",
                    "fibrosis_staged", "F0", "F1", "F2", "F3", "F4",
                    "disease_labelled", "disease_groups", "age_recorded",
                    "sex_recorded"])
        tot = dict(samples=0, patients=0, repeat=0, staged=0, grouped=0,
                   age=0, sex=0, stages={})
        for sid in sorted(studies):
            s = studies[sid]
            repeat = s["samples"] - len(s["patients"])
            groups = "; ".join("%s %d" % (g, n)
                               for g, n in sorted(s["groups"].items()))
            w.writerow([sid, s["samples"], len(s["patients"]), repeat,
                        s["staged"]]
                       + [s["stages"].get(k, 0) for k in range(5)]
                       + [s["grouped"], groups or "none", s["age"],
                          s["sex"]])
            tot["samples"] += s["samples"]
            tot["patients"] += len(s["patients"])
            tot["repeat"] += repeat
            tot["staged"] += s["staged"]
            tot["grouped"] += s["grouped"]
            tot["age"] += s["age"]
            tot["sex"] += s["sex"]
            for k, n in s["stages"].items():
                tot["stages"][k] = tot["stages"].get(k, 0) + n
        w.writerow(["TOTAL", tot["samples"], tot["patients"], tot["repeat"],
                    tot["staged"]]
                   + [tot["stages"].get(k, 0) for k in range(5)]
                   + [tot["grouped"], "", tot["age"], tot["sex"]])
    return True


# ----------------------------------------------------------------- captions
def write_captions(path, heading, intro, entries, kind):
    lines = ["# " + heading, "", intro, ""]
    for _src, name, title, bodytext in entries:
        label = os.path.splitext(name)[0].split("_")[0]
        label = label.replace("Figure", "Figure ").replace("Table", "Table ")
        lines += ["## %s" % label, "",
                  "**%s**" % title, "", bodytext, "",
                  "`%s`" % name, ""]
    lines += ["---", "",
              "Every %s above is reproduced by the script named for it in "
              "`05_CODE/`; the numbers quoted in the captions come from the "
              "committed result tables in `03_RESULTS/`, not from memory."
              % kind, ""]
    ensure(os.path.dirname(path))
    open(path, "w", encoding="utf-8").write("\n".join(lines))


# -------------------------------------------------------------------- main
def main():
    if os.path.exists(PKG):
        shutil.rmtree(PKG)
    ensure(PKG)
    missing = []
    counts = {}

    # figures
    for src, name, _t, _b in MAIN_FIGURES:
        copy(src, "01_FIGURES/main/" + name, missing)
    for src, name, _t, _b in SUPP_FIGURES:
        copy(src, "01_FIGURES/supplementary/" + name, missing)
    counts["figures"] = len(MAIN_FIGURES) + len(SUPP_FIGURES)

    write_captions(
        os.path.join(PKG, "01_FIGURES", "FIGURE_CAPTIONS.md"),
        "Figure captions",
        "Captions for every figure in this package, ready to paste. Main "
        "figures are in `main/`, supplementary in `supplementary/`. All are "
        "PNG at 300 dpi. The numbering is set in "
        "`build_paper1_package.py` and nowhere else, so figures cannot be "
        "renumbered in one place and not another.",
        MAIN_FIGURES + SUPP_FIGURES, "figure")

    # tables
    make_table1("02_TABLES/main/Table1_cohort.csv")
    for src, name, _t, _b in MAIN_TABLES:
        if src:
            copy(src, "02_TABLES/main/" + name, missing)
    for src, name, _t, _b in SUPP_TABLES:
        copy(src, "02_TABLES/supplementary/" + name, missing)
    counts["tables"] = len(MAIN_TABLES) + len(SUPP_TABLES)

    write_captions(
        os.path.join(PKG, "02_TABLES", "TABLE_CAPTIONS.md"),
        "Table captions",
        "Captions for every table in this package, ready to paste. Main "
        "tables are in `main/`, supplementary in `supplementary/`. Each is "
        "the committed analysis output, copied unmodified, except Table 1 "
        "which this package builds from the harmonised clinical table.",
        MAIN_TABLES + SUPP_TABLES, "table")

    # results, verbatim and with their own READMEs
    n = 0
    for src, dst in RESULT_COPIES:
        n += copy_tree(src, dst, missing, skip_ext=SKIP_IN_RESULTS)
    counts["result files"] = n

    # data
    n = 0
    for src, dst in DATA_COPIES:
        n += copy_tree(src, dst, missing)
    for src, dst in DATA_FILES:
        n += 1 if copy(src, dst, missing) else 0
    counts["data files"] = n

    # code
    n = 0
    for src, dst in CODE_COPIES:
        n += 1 if copy(src, dst, missing) else 0
    counts["code files"] = n

    # reference draft and session history
    copy("Paper1_Manuscript/Paper1_draft_v1.docx",
         "07_REFERENCE_DRAFT/Paper1_draft_v1.docx", missing)
    copy("Paper1_Manuscript/make_manuscript.py",
         "07_REFERENCE_DRAFT/make_manuscript.py", missing)
    copy("Paper1_HighConfidence/QUESTION_FOR_MENTOR.md",
         "07_REFERENCE_DRAFT/QUESTION_FOR_MENTOR.md", missing)
    counts["session history"] = copy_tree(
        "handover", "08_SESSION_HISTORY", missing)

    # the narrative documents live in docs/ beside this script
    counts["documents"] = copy_tree("docs/package", "00_START_HERE", missing)
    for src, dst in [("docs/package/README.md", "README.md"),
                     ("docs/provenance/DATA_SOURCES.md",
                      "06_PROVENANCE/DATA_SOURCES.md"),
                     ("docs/provenance/REBUILD.md",
                      "06_PROVENANCE/REBUILD.md"),
                     ("docs/package/DATA_DICTIONARY.md",
                      "04_DATA/DATA_DICTIONARY.md"),
                     ("docs/package/CODE_MAP.md", "05_CODE/CODE_MAP.md"),
                     ("docs/package/DRAFT_NOTE.md",
                      "07_REFERENCE_DRAFT/NOTE.md")]:
        copy(src, dst, missing)
    # README.md and the three above are copied out of 00_START_HERE again
    for stray in ("README.md", "DATA_DICTIONARY.md", "CODE_MAP.md",
                  "DRAFT_NOTE.md"):
        p = os.path.join(PKG, "00_START_HERE", stray)
        if os.path.exists(p):
            os.remove(p)

    # A correction notice beside the one result README with wrong numbers.
    # The README is copied verbatim because it is the committed record; the
    # correction sits next to it rather than silently editing it.
    open(os.path.join(PKG, "03_RESULTS",
                      "Task5_high_confidence_genes", "CORRECTIONS.txt"),
         "w", encoding="utf-8").write(CORRECTIONS)

    # manifest -- every file, its size and its checksum
    man = os.path.join(PKG, "00_START_HERE", "07_FILE_MANIFEST.csv")
    ensure(os.path.dirname(man))
    total = 0
    with open(man, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "bytes", "sha256"])
        for dirpath, _d, files in os.walk(PKG):
            for f in sorted(files):
                full = os.path.join(dirpath, f)
                if os.path.abspath(full) == os.path.abspath(man):
                    continue
                rel = os.path.relpath(full, PKG).replace(os.sep, "/")
                size = os.path.getsize(full)
                total += size
                w.writerow([rel, size, sha256(full)])

    print("Paper1_Package built at", PKG)
    for k, v in counts.items():
        print("  %-18s %d" % (k, v))
    print("  %-18s %.1f MB" % ("total size", total / 1048576))
    if missing:
        print("\nMISSING (not copied):")
        for m in missing:
            print("  -", m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
