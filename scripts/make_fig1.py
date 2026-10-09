"""Figure 1 -- the study pipeline, first step to last.

The mentor asked for one figure that makes the objective and the order of work
legible on its own: where the data came from, what was harmonised, how the
graph was built, and which four analyses it fed. Numbers on the figure are the
real ones from the committed outputs, so the figure cannot drift from Results.

Layout rules learned from two bad renders:
  * every annotation lives INSIDE a box -- free-floating text collides with
    arrows and band labels as soon as spacing changes;
  * DejaVu Sans runs ~0.55 em per character, so a line wider than
    box_width_units * 4.9 pt overflows. Split long lines rather than shrinking.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.2})

INK, EDGE = "#1a1a1a", "#4a4a4a"
BANDS = {            # muted fills; text stays near-black so colour is never load-bearing
    "data":  "#e8eef4", "harm": "#e9f0e8", "graph": "#f3ecf7",
    "disc":  "#fdf0e3", "anal": "#eaf1f5", "out":   "#f0f0f0",
}


# ---------------------------------------------------------- live numbers
# Read from the committed outputs at draw time. These counts have each
# changed at least once; typed into the figure they go stale silently.
import csv as _csv
from pathlib import Path as _Path

_ROOT = _Path(__file__).resolve().parent.parent
_RES = _ROOT / "Paper1_Results"
_PG = _RES / "00_progression_genes"


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(_csv.DictReader(fh))


_g = {r["group"]: int(r["n_genes"]) for r in
      _rows(_RES / "Task1/task1_summary.csv") if r["direction"] == "all"}
N_FIB_ONLY, N_INFL_ONLY, N_SHARED = (_g["fibrosis_only"],
                                     _g["inflammation_only"], _g["shared"])
N_PROGRESSION = N_FIB_ONLY + N_INFL_ONLY + N_SHARED
N_FIBROSIS = N_FIB_ONLY + N_SHARED
N_ELIGIBLE = len(_rows(_PG / "progression_fibrosis.csv"))
_samples = _rows(_PG / "sample_demographics.csv")
N_SAMPLES = len(_samples)
N_PATIENTS = len({r["patient_id"] for r in _samples})
N_STAGED = sum(1 for r in _samples if r["fibrosis_stage"])
N_CLUSTERS = len(_rows(_RES / "Task2/task2_cluster_sizes.csv"))
N_GENES = len(_rows(_ROOT / "data/graph_full/nodes_gene.csv"))

fig, ax = plt.subplots(figsize=(7.4, 9.5))
ax.set_xlim(-9, 100); ax.set_ylim(0, 124)
ax.axis("off")


def box(x, y, w, h, text, fill, fs=8.2, bold_first=True, italic_last=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.4",
        linewidth=0.8, edgecolor=EDGE, facecolor=fill, zorder=2))
    lines = text.split("\n")
    n = len(lines)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h / 2 + (n - 1 - 2 * i) * (fs * 0.158), ln,
                ha="center", va="center", color=INK, zorder=3, fontsize=fs,
                fontweight="bold" if (i == 0 and bold_first) else "normal",
                style="italic" if (italic_last and i == n - 1) else "normal")


def arrow(x0, y0, x1, y1, style="-|>", lw=0.9):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=9, linewidth=lw, color=EDGE,
                                 zorder=1, shrinkA=0, shrinkB=0))


def band(y, label):
    ax.text(-7.5, y, label, ha="center", va="center", rotation=90,
            fontsize=7.4, color="#8a8a8a", fontweight="bold")

# ------------------------------------------------------------------ DATA
ax.text(48, 122.3, "Eight public human liver transcriptome studies (GEO)",
        ha="center", va="center", fontsize=9.4, fontweight="bold", color=INK)
ax.text(48, 119.2, f"{N_SAMPLES:,} samples from {N_PATIENTS:,} patients",
        ha="center", va="center", fontsize=8.4, color="#555")

band(113.8, "DATA")
studies = [("GSE126848", 57), ("GSE130970", 78), ("GSE135251", 216),
           ("GSE162694", 143), ("GSE167523", 98), ("GSE193066", 164),
           ("GSE240729", 67), ("GSE269412", 262)]
bw, gap = 10.6, 1.3
x0 = (96 - (len(studies) * bw + (len(studies) - 1) * gap)) / 2
for i, (gse, n) in enumerate(studies):
    box(x0 + i * (bw + gap), 110.6, bw, 6.4, gse + "\nn = " + str(n),
        BANDS["data"], fs=6.6)
for i in range(len(studies)):
    arrow(x0 + i * (bw + gap) + bw / 2, 110.6, 48, 106.6, lw=0.5)

# -------------------------------------------------------- HARMONISATION
band(84, "HARMONISATION")
box(4, 99.0, 88, 7.0,
    "Expression parsing   ·   parse_expression.py\n"
    "every supplementary file → long format; measured zeros retained",
    BANDS["harm"])
arrow(48, 99.0, 48, 95.8)

hb = [f"Gene identifiers\nHGNC → Ensembl\n{N_GENES:,} genes\nmap_gene_ids.py",
      "Sample crosswalk\nsample_key → GSM\nmatch rate checked\nbuild_crosswalk.py",
      "Clinical labels\nfibrosis 0–4, disease group\n*_raw never modified\nnormalize_clinical.py"]
w3 = 28.0
for i, txt in enumerate(hb):
    xx = 4 + i * (w3 + 2.0)
    box(xx, 85.0, w3, 10.8, txt, BANDS["harm"], fs=7.3, italic_last=True)
    arrow(xx + w3 / 2, 85.0, 48, 81.4, lw=0.6)

box(18, 74.4, 60, 7.0,
    "Per-study standardisation   →   value_z\n"
    "expression z-scored per gene within each study", BANDS["harm"])
arrow(48, 74.4, 48, 71.2)

# ----------------------------------------------------------- INTEGRATION
band(56, "INTEGRATION")
box(4, 58.0, 42, 12.6,
    "Measurement layer\nbuild_graph_all.py\nSample –EXPRESSES→ Gene\n"
    "32.5M edges   ·   n_datasets 1–8", BANDS["graph"], fs=7.4)
box(50, 58.0, 42, 12.6,
    "Knowledge layer\nbuild_optimuskg_layer.py\nDisease, Pathway, Drug, Phenotype\n"
    "Open Targets score ≥ 0.1", BANDS["graph"], fs=7.4)
arrow(46.5, 64.3, 49.5, 64.3, style="<|-|>")
box(6, 47.0, 84, 7.2,
    f"Neo4j property graph   ·   {N_GENES:,} genes   ·   {N_STAGED:,} staged samples\n"
    "measurement and curated knowledge queryable together", BANDS["graph"], fs=7.5)
arrow(25, 58.0, 40, 54.4, lw=0.6)
arrow(71, 58.0, 56, 54.4, lw=0.6)
arrow(48, 47.0, 48, 43.6)

# ------------------------------------------------------------- DISCOVERY
band(37, "DISCOVERY")
box(6, 30.0, 84, 13.6,
    "Progression-gene identification   ·   find_progression_genes.py\n"
    "per-study Spearman ρ against each ladder → median ρ, Fisher combination,\n"
    f"BH q < 0.05, all studies agreeing on direction   →   {N_PROGRESSION:,} genes\n"
    "two ladders scored separately — fibrosis F0→F4 (scarring)\n"
    "and disease control→NAFL→NASH (inflammation)",
    BANDS["disc"], fs=7.4)
arrow(48, 30.0, 48, 27.0)

# -------------------------------------------------------------- ANALYSES
band(19.6, "ANALYSES")
an = [f"Task 1\nProgression groups\nfibrosis-only {N_FIB_ONLY:,}\ninflammation-only {N_INFL_ONLY:,}\nshared {N_SHARED:,}",
      f"Task 2\nF0–F4 trajectories\n{N_FIBROSIS:,} fibrosis genes\nk-means, k = {N_CLUSTERS}\n{N_CLUSTERS} shapes",
      "Task 3\nStage transitions\nvalue_z ~ stage + study\npower-matched design\nF3→F4 largest",
      f"Task 4\nPathway enrichment\nGO, KEGG, Reactome\nand Hallmark\nbackground = {N_ELIGIBLE:,}"]
w4, g4 = 21.6, 1.8
x4 = (96 - (4 * w4 + 3 * g4)) / 2
for i, txt in enumerate(an):
    xx = x4 + i * (w4 + g4)
    box(xx, 13.0, w4, 13.0, txt, BANDS["anal"], fs=6.6)
    arrow(48, 27.0, xx + w4 / 2, 26.0, lw=0.5)
    arrow(xx + w4 / 2, 13.0, 48, 9.0, lw=0.5)

# ---------------------------------------------------------------- OUTPUT
band(4.4, "OUTPUT")
box(12, 0.8, 72, 7.2,
    "Stage-resolved map of fibrosis progression\n"
    "gene sets, trajectory clusters, transition statistics\n"
    "and pathway context, released as per-analysis CSVs",
    BANDS["out"], fs=7.6)

out = _RES / "Figure1" / "figure1_pipeline.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
print("wrote", out)
