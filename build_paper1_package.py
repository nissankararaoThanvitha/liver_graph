"""build_paper1_package.py
--------------------------
Assembles Paper1_Package/ -- one folder a collaborator can take to their own
machine and write the manuscript from, without access to this machine, the
database, or anyone to ask.

Rebuilt by script rather than copied by hand, so the package is a function of
the committed results rather than a snapshot that silently goes stale. Figure
and table numbering lives in MAIN_FIGURES / SUPP_FIGURES / MAIN_TABLES below
and nowhere else, so nothing can be renumbered in one place and not another.

NOT INCLUDED, DELIBERATELY
  data/raw            104 MB of GEO downloads. Provenance, including the exact
                      filename taken from each study, is in 06_PROVENANCE.
  data/interim_full   197 MB, data/graph_full 2.1 GB -- regenerable, and no
                      number in the paper is read from them directly.
  data/genesets       MSigDB. The KEGG-derived sets may not be redistributed,
                      so the download URL is given instead.

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
RES = "Paper1_Results"
HC = "Paper1_HighConfidence"

# ---------------------------------------------------------------- figures
MAIN_FIGURES = [
    (f"{RES}/Figure1/figure1_pipeline.png", "Figure1_study_design.png",
     "Study design and analysis pipeline.",
     "Eight public GEO liver transcriptome studies parsed to a common long "
     "format, harmonised on the gene axis (identifier mapping to Ensembl) and "
     "the patient axis (fibrosis stage, disease group, patient identity), "
     "standardised within study, and integrated with a curated knowledge "
     "layer. Every count shown is read from the committed outputs at draw "
     "time."),
    (f"{RES}/Task1/task1_venn.png", "Figure2_ladder_overlap.png",
     "Overlap between the two progression ladders.",
     "Genes significantly associated with fibrosis stage and with disease "
     "group, giving the fibrosis-only, inflammation-only and shared "
     "partitions used throughout."),
    (f"{RES}/Task1/task1_shared_rho_scatter.png",
     "Figure3_shared_gene_agreement.png",
     "Agreement between ladders among shared genes.",
     "Fibrosis correlation against inflammation correlation for genes "
     "significant on both ladders. The two clouds are concordantly rising and "
     "concordantly falling genes."),
    (f"{RES}/Task2/task2_cluster_means.png", "Figure4_trajectory_shapes.png",
     "The five fibrosis trajectory shapes.",
     "Mean standardised expression of each cluster at fibrosis stages F0 to "
     "F4. Cluster names were assigned after clustering, from these curves; no "
     "gene was assigned to a pattern by hand."),
    (f"{RES}/Task2/task2_heatmap.png", "Figure5_stage_heatmap.png",
     "Stage profiles of all fibrosis-associated genes.",
     "Genes in rows grouped by cluster, stages F0-F4 in columns. Values are "
     "mean standardised expression per stage."),
    (f"{RES}/Task2/task2_choosing_k.png", "Figure6_choosing_k.png",
     "Selection of the cluster number.",
     "Silhouette score, gene-subsample stability and patient-bootstrap "
     "stability for k = 3 to 8. See 04_LIMITATIONS.md for the basis of the "
     "k = 5 choice, which must be stated in the Methods."),
    (f"{RES}/Task3/task3_transition_comparison.png",
     "Figure7_stage_transitions.png",
     "Comparison of the four stage transitions.",
     "Numbers of substantially changing genes on the full data, the same "
     "counts under the power-matched design of 30 patients per stage, and the "
     "distribution of effect sizes. Equalising power isolates F3-F4 as the "
     "transition carrying the largest transcriptional change."),
    (f"{RES}/Task4/task4_heatmap_hallmark.png",
     "Figure8_hallmark_enrichment.png",
     "Hallmark process enrichment across groups and clusters.",
     "All significantly enriched Hallmark processes (false-discovery rate "
     "below 0.05) by gene group and trajectory cluster, tested against the "
     "eligible-gene background."),
    (f"{HC}/12_mechanistic_subgraph.png", "Figure9_mechanism_network.png",
     "Mechanisms shared by the high-confidence fibrosis genes.",
     "The twelve mechanisms significantly over-represented among the Tier 1 "
     "genes, with the genes reaching three or more of them and every "
     "shortlisted gene reaching any. Read the convergence as a property of "
     "Tier 1 as a whole, not of the shortlist -- see 04_LIMITATIONS.md."),
]

SUPP_FIGURES = [
    (f"{RES}/Task2/task2_cluster_trajectories.png",
     "FigureS1_all_gene_trajectories.png",
     "Every fibrosis gene's trajectory, by cluster.",
     "All genes in grey with the cluster average overlaid, one panel per "
     "cluster. Shows the spread behind each averaged shape in Figure 4."),
    (f"{RES}/Task3/task3_delta_distributions.png",
     "FigureS2_transition_deltas.png",
     "Distribution of change per transition.",
     "Per-transition distribution of expression change, at stage-mean level "
     "and at patient level."),
    (f"{RES}/Task4/task4_heatmap_go_bp.png", "FigureS3_enrichment_GO_BP.png",
     "GO Biological Process enrichment across groups and clusters.",
     "Top five GO BP terms per group at FDR < 0.05."),
    (f"{RES}/Task4/task4_heatmap_reactome.png",
     "FigureS4_enrichment_Reactome.png",
     "Reactome enrichment across groups and clusters.",
     "Top five Reactome terms per group at FDR < 0.05."),
    (f"{RES}/Task4/task4_heatmap_kegg.png", "FigureS5_enrichment_KEGG.png",
     "KEGG enrichment across groups and clusters.",
     "Top five KEGG terms per group at FDR < 0.05."),
]
_DOTS = [
    ("fibrosis_only_up", "fibrosis-only increasing genes"),
    ("fibrosis_only_down", "fibrosis-only decreasing genes"),
    ("inflammation_only_up", "inflammation-only increasing genes"),
    ("inflammation_only_down", "inflammation-only decreasing genes"),
    ("shared_up", "genes increasing on both ladders"),
    ("shared_down", "genes decreasing on both ladders"),
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
        f"{RES}/Task4/dot_plots/dot_{_slug}.png",
        "FigureS%d_dotplot_%s.png" % (_i, _slug),
        "Enrichment dot plot: %s." % _what,
        "Top five terms per database. x = gene ratio, point size = number of "
        "genes, colour = -log10 FDR."))

# ----------------------------------------------------------------- tables
MAIN_TABLES = [
    (None, "Table1_cohort.csv",
     "The eight studies and what each contributes.",
     "Samples, patients, fibrosis staging, disease labels and demographic "
     "coverage per study. Built by build_paper1_package.py from the "
     "harmonised clinical table, so it cannot drift from it."),
    (f"{RES}/Task1/task1_summary.csv", "Table2_gene_groups.csv",
     "Progression genes by group and direction.",
     "Counts and percentages for the fibrosis-only, inflammation-only and "
     "shared partitions, split by direction of change."),
    (f"{RES}/Task2/task2_cluster_sizes.csv", "Table3_trajectory_clusters.csv",
     "The five trajectory clusters.",
     "Genes per cluster with the cluster mean standardised expression at each "
     "fibrosis stage."),
    (f"{RES}/Task3/task3_transition_summary.csv",
     "Table4_stage_transitions.csv",
     "The four stage transitions compared.",
     "Patient counts, substantially changing genes, direction split, median "
     "effect size and power-matched counts for each transition."),
    (f"{RES}/Task4/task4_significant_counts.csv",
     "Table5_enrichment_counts.csv",
     "Significantly enriched terms per group.",
     "Counts of terms at FDR < 0.05 in each database, per gene group and per "
     "trajectory cluster."),
    (f"{HC}/11_FINAL_shortlist_25_genes.csv",
     "Table6_prioritised_genes.csv",
     "The prioritised fibrosis genes.",
     "The five highest-scoring Tier 1 genes per trajectory cluster, ties "
     "broken by correlation magnitude, with all five evidence scores, the "
     "stage of largest change and the leave-one-study-out results."),
]

SUPP_TABLES = [
    (f"{RES}/Task1/task1_top20_fibrosis_genes.csv",
     "TableS1_top20_fibrosis_genes.csv",
     "Strongest fibrosis-associated genes.",
     "Top 20 increasing and top 20 decreasing genes by cross-study fibrosis "
     "correlation."),
    (f"{RES}/Task2/task2_gene_clusters.csv",
     "TableS2_gene_cluster_assignments.csv",
     "Cluster assignment for every fibrosis gene.",
     "Stage means F0-F4, cluster, correlation to the cluster centroid, "
     "bootstrap membership confidence and the number of bootstraps each gene "
     "was assessed in. Use membership_confidence for any claim about an "
     "individual gene."),
    (f"{RES}/Task2/task2_representative_genes.csv",
     "TableS3_representative_genes.csv",
     "Representative genes per cluster.",
     "Fifteen genes per cluster ranked by membership confidence, then by "
     "closeness to the cluster shape."),
    (f"{RES}/Task2/task2_choosing_k.csv", "TableS4_choosing_k.csv",
     "Cluster-number diagnostics.",
     "Silhouette score and both stability measures for k = 3 to 8."),
    (f"{RES}/Task2/task2_bootstrap_shape_stability.csv",
     "TableS5_cluster_stability.csv",
     "Shape reproducibility and membership confidence per cluster.",
     "Median and minimum correlation of each cluster's shape across 100 "
     "patient bootstraps, and how many of its genes are confidently "
     "assigned."),
    (f"{RES}/Task3/task3_all_genes_all_transitions.csv",
     "TableS6_all_genes_all_transitions.csv",
     "Every gene at every transition.",
     "Per gene and transition: stage-mean difference, study-adjusted beta, "
     "standard error, p, q, patient counts, substantial flag and cluster."),
    (f"{RES}/Task3/task3_top_genes_per_transition.csv",
     "TableS7_top_genes_per_transition.csv",
     "Strongest genes per transition.",
     "Top 20 increasing and decreasing genes per transition at q < 0.05."),
    (f"{RES}/Task4/task4_top_pathways_per_group.csv",
     "TableS8_top_pathways_per_group.csv",
     "Leading enriched terms per group.",
     "Top ten terms per group and database with the genes responsible."),
    (f"{RES}/Task4/task4_all_significant.csv",
     "TableS9_all_significant_terms.csv",
     "Every significantly enriched term.",
     "All terms at FDR < 0.05 across every group and database."),
    (f"{RES}/Task4/task4_cluster_core_check.csv",
     "TableS10_cluster_core_check.csv",
     "Enrichment on all genes against high-confidence members.",
     "Whether each cluster's leading biology survives when only confidently "
     "assigned members are used. Clusters with too few confident members to "
     "test are recorded as such."),
    (f"{HC}/01_master_table.csv", "TableS11_evidence_scores_all_genes.csv",
     "Evidence scores for every fibrosis gene.",
     "Every intermediate behind the five scores, the total and the tier, for "
     "every scored gene."),
    (f"{HC}/11_final_tier1_genes.csv", "TableS12_tier1_genes.csv",
     "All Tier 1 genes.",
     "The full high-confidence set, same columns as Table 6."),
    (f"{HC}/10_loso_summary.csv", "TableS13_leave_one_study_out.csv",
     "Leave-one-study-out results per gene.",
     "Direction retained, still significant, still above the correlation "
     "threshold, weakest median correlation and largest percentage loss, over "
     "the five fibrosis-staging studies."),
    (f"{HC}/08_tier_sensitivity.csv", "TableS14_tier_cutoff_sensitivity.csv",
     "Sensitivity of the Tier 1 boundary.",
     "Tier 1 membership at score cutoffs 6, 7 and 8."),
    (f"{HC}/08_leave_one_score_out.csv", "TableS15_leave_one_score_out.csv",
     "Sensitivity of the ranking to each score.",
     "Dropping each of the five scores in turn: Spearman correlation against "
     "the full ranking and overlap of the top band."),
    (f"{HC}/03_rho_sensitivity.csv", "TableS16_rho_cutoff_sensitivity.csv",
     "Sensitivity of the progression-strength cutoffs.",
     "How many genes score 2, 1 and 0 at three choices of the correlation "
     "thresholds."),
    (f"{HC}/04_delta_sensitivity.csv", "TableS17_trajectory_cutoff.csv",
     "Sensitivity of the trajectory cutoffs.",
     "How many genes score 2, 1 and 0 at three choices of the F0-F4 "
     "difference thresholds."),
    (f"{HC}/09b_option_comparison.csv", "TableS18_shortlist_rule.csv",
     "The two shortlist rules considered.",
     "Composition of the chosen rule (top five per cluster) against the "
     "alternative (each cluster's own top score)."),
    (f"{HC}/12_KG_supplementary.xlsx",
     "TableS19_knowledge_graph_connections.xlsx",
     "Knowledge-graph connections and mechanism ranking.",
     "Per-gene connections for the shortlist and for all Tier 1 genes, every "
     "mechanism ranked with fold enrichment and q, and the nodes and edges "
     "drawn in Figure 9."),
]

DATA_COPIES = [
    (f"{RES}/00_progression_genes", "04_DATA/progression_genes"),
    ("data/for_mentor", "04_DATA/gene_tables"),
    ("data/processed", "04_DATA/harmonisation"),
    ("data/graph_okg", "04_DATA/knowledge_layer"),
]
DATA_FILES = [
    ("data/graph_full/nodes_gene.csv", "04_DATA/graph_nodes/nodes_gene.csv"),
    ("data/graph_full/nodes_dataset.csv",
     "04_DATA/graph_nodes/nodes_dataset.csv"),
    ("data/graph_full/gene_progression_scores.csv",
     "04_DATA/graph_nodes/gene_progression_scores.csv"),
    ("data/graph_full/edges_my_progression.csv",
     "04_DATA/graph_nodes/edges_my_progression.csv"),
    ("data/graph/nodes_sample_clinical.csv",
     "04_DATA/harmonisation/nodes_sample_clinical.csv"),
    ("data/interim_full/_parse_summary.csv",
     "04_DATA/harmonisation/_parse_summary.csv"),
]

CODE_COPIES = [
    ("parse_expression.py", "05_CODE/pipeline/01_parse_expression.py"),
    ("map_gene_ids.py", "05_CODE/pipeline/02_map_gene_ids.py"),
    ("build_crosswalk.py", "05_CODE/pipeline/03_build_crosswalk.py"),
    ("normalize_clinical.py", "05_CODE/pipeline/04_normalize_clinical.py"),
    ("build_graph_all.py", "05_CODE/pipeline/05_build_graph_all.py"),
    ("build_optimuskg_layer.py",
     "05_CODE/pipeline/06_build_optimuskg_layer.py"),
    ("find_progression_genes.py",
     "05_CODE/pipeline/07_find_progression_genes.py"),
    ("export_for_mentor.py", "05_CODE/pipeline/08_export_gene_tables.py"),
    ("build_progression_edges.py",
     "05_CODE/pipeline/09_build_progression_edges.py"),
    ("paper1_task1_groups.py", "05_CODE/analysis/task1_groups.py"),
    ("paper1_task2_trajectories.py", "05_CODE/analysis/task2_trajectories.py"),
    ("paper1_task3_transitions.py", "05_CODE/analysis/task3_transitions.py"),
    ("paper1_task4_enrichment.py", "05_CODE/analysis/task4_enrichment.py"),
    ("scripts/make_fig1.py", "05_CODE/analysis/make_figure1.py"),
    ("scripts/00_all_4692_progression_genes.py",
     "05_CODE/prioritisation/hc0_master_gene_table.py"),
    ("scripts/powermatched_transitions.py",
     "05_CODE/prioritisation/hc1_powermatched_transitions.py"),
    ("scripts/high_confidence_genes.py",
     "05_CODE/prioritisation/hc2_evidence_scores.py"),
    ("scripts/loso_validation.py",
     "05_CODE/prioritisation/hc3_leave_one_study_out.py"),
    ("scripts/kg_subgraph.py",
     "05_CODE/prioritisation/hc4_mechanism_subgraph.py"),
    ("check_mapping.py", "05_CODE/validation/check_gene_mapping.py"),
    ("inspect_parsed.py", "05_CODE/validation/inspect_parsed_files.py"),
    ("scripts/verify_against_neo4j.py",
     "05_CODE/validation/verify_subgraph_against_neo4j.py"),
    ("verify_graph_counts.py", "05_CODE/validation/verify_graph_counts.py"),
    ("diagnose_membership_confidence.py",
     "05_CODE/validation/diagnose_membership_confidence.py"),
    ("compare_versions.py", "05_CODE/validation/compare_result_versions.py"),
    ("create_kg_constraints.cypher",
     "05_CODE/cypher/01_create_constraints.cypher"),
    ("reload_expression.cypher",
     "05_CODE/cypher/02_load_expression_edges.cypher"),
    ("load_knowledge_layer.cypher",
     "05_CODE/cypher/03_load_knowledge_layer.cypher"),
    ("scripts/expected_graph_counts.py",
     "05_CODE/validation/expected_graph_counts.py"),
    ("requirements.txt", "05_CODE/requirements.txt"),
    ("build_paper1_package.py", "05_CODE/build_paper1_package.py"),
]

RESULT_COPIES = [
    (f"{RES}/Task1", "03_RESULTS/Task1_gene_groups"),
    (f"{RES}/Task2", "03_RESULTS/Task2_trajectories"),
    (f"{RES}/Task3", "03_RESULTS/Task3_transitions"),
    (f"{RES}/Task4", "03_RESULTS/Task4_enrichment"),
    (HC, "03_RESULTS/Task5_gene_prioritisation"),
]
SKIP_IN_RESULTS = {".py"}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def ensure(p):
    os.makedirs(p, exist_ok=True)
    return p


def copy(src_rel, dst_rel, missing):
    src, dst = os.path.join(ROOT, src_rel), os.path.join(PKG, dst_rel)
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
    for dirpath, _d, files in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        for f in files:
            if os.path.splitext(f)[1] in skip_ext:
                continue
            out = os.path.join(dst_rel, "" if rel == "." else rel, f)
            ensure(os.path.dirname(os.path.join(PKG, out)))
            shutil.copy2(os.path.join(dirpath, f), os.path.join(PKG, out))
            n += 1
    return n


def make_table1(dst_rel):
    """The cohort table. No analysis produces it, so it is built here."""
    src = os.path.join(ROOT, RES, "00_progression_genes",
                       "sample_demographics.csv")
    if not os.path.exists(src):
        return False
    with open(src, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    st = {}
    for r in rows:
        s = st.setdefault(r["dataset_id"], {
            "n": 0, "pat": set(), "staged": 0, "grp": {}, "stages": {},
            "age": 0, "sex": 0})
        s["n"] += 1
        s["pat"].add(r["patient_id"])
        if r["fibrosis_stage"]:
            s["staged"] += 1
            k = int(float(r["fibrosis_stage"]))
            s["stages"][k] = s["stages"].get(k, 0) + 1
        if r["disease_group"]:
            s["grp"][r["disease_group"]] = s["grp"].get(
                r["disease_group"], 0) + 1
        s["age"] += 1 if r["age_years"] else 0
        s["sex"] += 1 if r["sex"] else 0

    out = os.path.join(PKG, dst_rel)
    ensure(os.path.dirname(out))
    tot = dict(n=0, pat=0, rep=0, staged=0, grp=0, age=0, sex=0, stages={})
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["study", "samples", "patients", "repeat_biopsies",
                    "fibrosis_staged", "F0", "F1", "F2", "F3", "F4",
                    "disease_labelled", "disease_groups", "age_recorded",
                    "sex_recorded"])
        for sid in sorted(st):
            s = st[sid]
            rep = s["n"] - len(s["pat"])
            grp = sum(s["grp"].values())
            w.writerow(
                [sid, s["n"], len(s["pat"]), rep, s["staged"]]
                + [s["stages"].get(k, 0) for k in range(5)]
                + [grp, "; ".join("%s %d" % kv for kv in sorted(
                    s["grp"].items())) or "none", s["age"], s["sex"]])
            tot["n"] += s["n"]
            tot["pat"] += len(s["pat"])
            tot["rep"] += rep
            tot["staged"] += s["staged"]
            tot["grp"] += grp
            tot["age"] += s["age"]
            tot["sex"] += s["sex"]
            for k, v in s["stages"].items():
                tot["stages"][k] = tot["stages"].get(k, 0) + v
        w.writerow(["TOTAL", tot["n"], tot["pat"], tot["rep"], tot["staged"]]
                   + [tot["stages"].get(k, 0) for k in range(5)]
                   + [tot["grp"], "", tot["age"], tot["sex"]])
    return True


def write_captions(path, heading, intro, entries, kind):
    out = ["# " + heading, "", intro, ""]
    for _s, name, title, body in entries:
        label = os.path.splitext(name)[0].split("_")[0]
        label = label.replace("Figure", "Figure ").replace("Table", "Table ")
        out += ["## %s" % label, "", "**%s**" % title, "", body, "",
                "`%s`" % name, ""]
    out += ["---", "",
            "Each %s is produced by the script named for it in `05_CODE/`, "
            "and the numbering is set in one place in "
            "`build_paper1_package.py`." % kind, ""]
    ensure(os.path.dirname(path))
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main():
    if os.path.exists(PKG):
        shutil.rmtree(PKG)
    ensure(PKG)
    missing, counts = [], {}

    for src, name, _t, _b in MAIN_FIGURES:
        copy(src, "01_FIGURES/main/" + name, missing)
    for src, name, _t, _b in SUPP_FIGURES:
        copy(src, "01_FIGURES/supplementary/" + name, missing)
    counts["figures"] = len(MAIN_FIGURES) + len(SUPP_FIGURES)
    write_captions(
        os.path.join(PKG, "01_FIGURES", "FIGURE_CAPTIONS.md"),
        "Figure captions",
        "Captions for every figure, ready to paste. Main figures are in "
        "`main/`, supplementary in `supplementary/`. All are PNG at 300 dpi.",
        MAIN_FIGURES + SUPP_FIGURES, "figure")

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
        "Captions for every table, ready to paste. Each is the committed "
        "analysis output copied unmodified, except Table 1, which this "
        "package builds from the harmonised clinical table.",
        MAIN_TABLES + SUPP_TABLES, "table")

    n = 0
    for src, dst in RESULT_COPIES:
        n += copy_tree(src, dst, missing, skip_ext=SKIP_IN_RESULTS)
    counts["result files"] = n

    n = 0
    for src, dst in DATA_COPIES:
        n += copy_tree(src, dst, missing)
    for src, dst in DATA_FILES:
        n += 1 if copy(src, dst, missing) else 0
    counts["data files"] = n

    counts["code files"] = sum(
        1 for s, d in CODE_COPIES if copy(s, d, missing))

    counts["documents"] = copy_tree("docs/package", "00_START_HERE", missing)
    for src, dst in [("docs/package/README.md", "README.md"),
                     ("docs/provenance/DATA_SOURCES.md",
                      "06_PROVENANCE/DATA_SOURCES.md"),
                     ("docs/provenance/REBUILD.md",
                      "06_PROVENANCE/REBUILD.md"),
                     ("docs/package/DATA_DICTIONARY.md",
                      "04_DATA/DATA_DICTIONARY.md"),
                     ("docs/package/CODE_MAP.md", "05_CODE/CODE_MAP.md")]:
        copy(src, dst, missing)
    for stray in ("README.md", "DATA_DICTIONARY.md", "CODE_MAP.md"):
        p = os.path.join(PKG, "00_START_HERE", stray)
        if os.path.exists(p):
            os.remove(p)

    man = os.path.join(PKG, "00_START_HERE", "06_FILE_MANIFEST.csv")
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
                total += os.path.getsize(full)
                w.writerow([rel, os.path.getsize(full), sha256(full)])

    print("Paper1_Package built at", PKG)
    for k, v in counts.items():
        print("  %-16s %d" % (k, v))
    print("  %-16s %.1f MB" % ("total size", total / 1048576))
    if missing:
        print("\nMISSING:")
        for m in missing:
            print("  -", m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
