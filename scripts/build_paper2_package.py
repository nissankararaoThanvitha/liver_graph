"""
build_paper2_package.py
-----------------------
Assemble Paper2_Package: a self-contained record of Paper 2, mirroring the
layout Paper 1 settled on.

WHY A PACKAGE, AND WHY NOW
Paper 1 built its package only after its tasks were finished, so the documents
described a stable thing rather than chasing one. Paper 2's eight tasks are
complete, so the same applies.

WHAT IS AND IS NOT COPIED
Figures, the key tables, every task's results and README, and the analysis code
are copied so the package stands alone. The two large working tables -- the
8,948-row edge table and the 1,920-row drug ranking -- are copied because a
reader cannot check a candidate without them.

The two recoveries ship as two folders, Recovery1_OptimusKG and
Recovery2_ChEMBL, because the mentor asked on 13 October that the two jobs be
kept separate -- and a package handed to a third reader is exactly where that
separation would otherwise be lost. Their bulk intermediates are not copied:
11 MB, regenerable in a minute, and the provenance they carry is already folded
into the task outputs with a *_source column naming which recovery supplied it.

Usage:
    python scripts/build_paper2_package.py
"""

import csv
import hashlib
import os
import shutil

PKG = "Paper2_Package"
RESULTS = "Paper2_Results"

TASK_DIRS = {
    "Task1": "Task1_master_gene_table",
    "Task2": "Task2_drug_gene_extraction",
    "Task3": "Task3_druggability",
    "Task4": "Task4_drug_coverage",
    "Task5": "Task5_metapaths",
    "Task6": "Task6_target_scoring",
    "Task7": "Task7_action_direction",
    "Task8": "Task8_final_ranking",
    # The two recoveries, kept apart on the mentor's instruction of 13 October.
    # Separate folders in the package as well as in the repo, so the separation
    # survives being handed to someone who only ever sees the package.
    "Recovery1_OptimusKG": "Recovery1_OptimusKG",
    "Recovery2_ChEMBL": "Recovery2_ChEMBL",
}

# figure -> (destination, caption)
FIGURES = {
    "Task2/task2_action_classes.png": (
        "main",
        "What the 8,948 drug-gene links are. Two of the four bars -- "
        "pharmacokinetic and direction-not-recorded -- carry no usable "
        "mechanism between them, leaving 1,005 links (11.2%) that state both "
        "that a drug acts on a gene and which way it pushes."),
    "Task2/task2_consistency_null.png": (
        "main",
        "Mechanism consistency against its null. Observed 52.7% sits inside a "
        "null centred on 55.9%, permutation p = 0.78. The null is above 50% "
        "because 68% of directional drugs lower their target and 68% of these "
        "genes rise, so the right-way pairing is common by accident."),
    "Task3/task3_druggability_by_group.png": (
        "main",
        "Druggability by progression group against an 11.2% background. Genes "
        "that fall as disease worsens are roughly twice as drug-connected as "
        "genes that rise. Starred groups survive a null matched on non-drug "
        "degree."),
    "Task4/task4_coverage_vs_coherence.png": (
        "main",
        "Coverage against coherence, one point per drug. The widest-reaching "
        "drugs are the least coherent; the two measures correlate at -0.268 (p = 0.001), "
        "so ranking by target count selects promiscuity."),
    "Task4/task4_network.png": (
        "main",
        "The most coherent drugs and the progression genes they reach, with "
        "genes grouped by their major fibrosis-associated process. "
        "MARIMASTAT's fan into the matrix metallopeptidases reads as one "
        "block rather than a coincidence of symbols."),
    "Task5/task5_metapath_sizes.png": (
        "supplementary",
        "Path volume per metapath, with and without a 5-200 gene term cap. "
        "Capping costs Reactome 18% of its paths and GO 75%, which is the "
        "measure of how much of GO's volume is annotation breadth."),
    "Task6/task6_weight_stability.png": (
        "supplementary",
        "Left: how little of a top-50 survives a random reweighting -- a "
        "median of 29 to 32 of 50. Right: the stable core, the genes holding "
        "their place across 80% of weightings."),
    "Task7/task7_consistency_vs_null.png": (
        "main",
        "Reversal consistency per progression group against two baselines: "
        "what the drug vocabulary gives for free, and a gene-level "
        "permutation. Only fibrosis-only rising genes beat their own null."),
}

# table -> (destination, caption)
TABLES = {
    "Task1/Paper2_progression_genes.csv": (
        "main", "The master table: 6,222 progression genes, both ladders' rho "
        "and q, progression class, and F0-F4 stage means. Nothing filtered."),
    "Task1/task1_class_summary.csv": (
        "main", "Gene counts per progression class, with direction counted per "
        "ladder."),
    "Task2/task2_summary.csv": (
        "main", "The drug-gene extraction in seven numbers."),
    "Task3/task3_druggability_summary.csv": (
        "main", "Druggability per group: total genes, drug-connected genes, "
        "percentage, unique drugs."),
    "Task3/task3_enrichment_tests.csv": (
        "main", "Odds ratios, Fisher p, BH-q and the degree-matched "
        "permutation p for each group."),
    "Task4/task4_top_drugs_by_coherence.csv": (
        "main", "Drugs ranked by whether they hit a coherent programme rather "
        "than many unrelated genes. Read this before the coverage ranking."),
    "Task4/task4_top_drugs_raw_coverage.csv": (
        "supplementary", "The top 50 by raw coverage, as the plan requires. "
        "Included to show why coverage is the wrong sort key."),
    "Task5/task5_metapath_definitions.csv": (
        "main", "The seven metapaths, their schema, and why each is run."),
    "Task5/task5_metapath_counts.csv": (
        "main", "Paths, drugs, genes and terms per metapath, capped and "
        "uncapped."),
    "Task6/task6_ablation.csv": (
        "main", "How far the target ranking moves when each score component "
        "is removed. F moves it not at all."),
    "Task6/task6_weight_sensitivity.csv": (
        "main", "Rank stability across 2,000 weightings drawn from the whole "
        "simplex."),
    "Task6/task6_stable_core.csv": (
        "main", "Genes holding a top-50 place across most weightings -- the "
        "defensible alternative to a named top-50."),
    "Task7/task7_known_vs_unknown_direction.csv": (
        "main", "Known versus unknown drug-action direction."),
    "Task7/task7_consistency_significance.csv": (
        "main", "Reversal consistency per group against the vocabulary "
        "baseline and a gene-level permutation null."),
    "Task8/task8_leading_candidates.csv": (
        "main", "The 30 leading candidates. Therapeutic hypotheses, not "
        "treatments."),
    "Task8/task8_evidence_summary.csv": (
        "main", "Seven evidence layers by candidate: supports, missing, or "
        "out of scope."),
    "Task8/task8_shortlist_support.csv": (
        "main", "How many candidates rest on Paper 1's 23-gene shortlist "
        "versus broader progression evidence."),
    "Task2/task2_drug_gene_edges.csv": (
        "supplementary", "All 8,948 drug-gene relationships with recovered "
        "provenance. Large, but a candidate cannot be checked without it."),
    "Task8/task8_final_drug_ranking.csv": (
        "supplementary", "All 1,920 ranked drugs, with score band, coherence "
        "and flags."),
}

CODE = {
    "pipeline": ["paper2_task1_master_table.py", "paper2_task2_drug_gene_edges.py",
                 "paper2_io.py", "paper2_manifest.py"],
    "analysis": ["paper2_task3_druggability.py", "paper2_task4_drug_coverage.py",
                 "paper2_task5_metapaths.py",
                 "paper2_task5_transition_convergence.py",
                 "paper2_task6_target_score.py",
                 "paper2_task7_action_direction.py",
                 "paper2_task8_final_ranking.py"],
    "validation": ["paper2_task1_verify_against_neo4j.py",
                   "paper2_task1_verify_stage_means.py",
                   "paper2_task2_robustness.py"],
    # Recovery 1 and Recovery 2 each own their extraction and their report.
    "recovery1_optimuskg": ["paper2_recover_optimuskg_evidence.py",
                            "paper2_recovery_optimuskg_report.py"],
    "recovery2_chembl": ["paper2_fetch_chembl_gaps.py",
                         "paper2_recovery_chembl_report.py"],
    "recovery_shared": ["paper2_integrate_recovered_evidence.py",
                        "paper2_write_recovered_to_graph.py"],
    "figures": ["paper2_figures.py"],
}


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.isdir(PKG):
        shutil.rmtree(PKG)

    # ---- 01 figures --------------------------------------------------------
    cap = ["# Figure captions", ""]
    for rel, (where, caption) in FIGURES.items():
        src = f"{RESULTS}/{rel}"
        if not os.path.exists(src):
            print(f"   missing figure, skipped: {rel}")
            continue
        name = os.path.basename(rel)
        copy(src, f"{PKG}/01_FIGURES/{where}/{name}")
        cap += [f"**{name}** _({where})_", "", caption, ""]
    os.makedirs(f"{PKG}/01_FIGURES", exist_ok=True)
    open(f"{PKG}/01_FIGURES/FIGURE_CAPTIONS.md", "w",
         encoding="utf-8").write("\n".join(cap))

    # ---- 02 tables ---------------------------------------------------------
    cap = ["# Table captions", ""]
    for rel, (where, caption) in TABLES.items():
        src = f"{RESULTS}/{rel}"
        if not os.path.exists(src):
            print(f"   missing table, skipped: {rel}")
            continue
        name = os.path.basename(rel)
        copy(src, f"{PKG}/02_TABLES/{where}/{name}")
        cap += [f"**{name}** _({where})_", "", caption, ""]
    open(f"{PKG}/02_TABLES/TABLE_CAPTIONS.md", "w",
         encoding="utf-8").write("\n".join(cap))

    # ---- 03 results: every task, whole ------------------------------------
    for task, folder in TASK_DIRS.items():
        src = f"{RESULTS}/{task}"
        if not os.path.isdir(src):
            continue
        for f in sorted(os.listdir(src)):
            copy(f"{src}/{f}", f"{PKG}/03_RESULTS/{folder}/{f}")

    # ---- 05 code -----------------------------------------------------------
    for group, files in CODE.items():
        for f in files:
            src = f"scripts/{f}"
            if os.path.exists(src):
                copy(src, f"{PKG}/05_CODE/{group}/{f}")

    # ---- 00 start here: the prose, written once and copied in -------------
    # Kept in docs/paper2_package/ rather than inside the package, so that
    # rebuilding (which clears the package) cannot lose them.
    src_docs = "docs/paper2_package"
    for f in ["01_OVERVIEW.md", "02_METHODS.md", "03_STATISTICS.md",
              "04_LIMITATIONS.md", "05_HOW_TO_VERIFY.md"]:
        if os.path.exists(f"{src_docs}/{f}"):
            copy(f"{src_docs}/{f}", f"{PKG}/00_START_HERE/{f}")
        else:
            print(f"   missing document: {f}")
    if os.path.exists(f"{src_docs}/README.md"):
        copy(f"{src_docs}/README.md", f"{PKG}/README.md")

    # ---- 06 provenance -----------------------------------------------------
    for f in ["BIOPSY_CORRECTION.md", "CLAUDE.md"]:
        if os.path.exists(f):
            copy(f, f"{PKG}/06_PROVENANCE/{f}")

    # ---- manifest ----------------------------------------------------------
    rows = []
    for dirpath, _, filenames in os.walk(PKG):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, PKG).replace("\\", "/")
            rows.append({"path": rel, "bytes": os.path.getsize(full),
                         "sha256": sha256(full)})
    rows.sort(key=lambda r: r["path"])
    os.makedirs(f"{PKG}/00_START_HERE", exist_ok=True)
    with open(f"{PKG}/00_START_HERE/06_FILE_MANIFEST.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256"])
        w.writeheader()
        w.writerows(rows)

    total = sum(r["bytes"] for r in rows)
    print(f"{PKG}: {len(rows)} files, {total/1e6:.1f} MB")
    for d in sorted(os.listdir(PKG)):
        print(f"   {d}")


if __name__ == "__main__":
    main()
