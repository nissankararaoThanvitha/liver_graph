"""Simple explanatory diagrams for Paper 2 (roadmap + one per task).

Run from the repository root:
    python Paper2_Results/code/diagrams.py            # all available diagrams
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results"

INK = "#1f2933"
MUTED = "#616e7c"
COL = {
    "fib": "#c0392b", "inf": "#2471a3", "shared": "#7d3c98",
    "data": "#e8eef5", "task": "#fdf2e9", "wait": "#eeeeee", "done": "#e3f4e6",
    "up": "#c0392b", "down": "#2471a3",
}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK})


def box(ax, x, y, w, h, text, fc, ec=INK, fs=10, bold=False, lw=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=MUTED, style="-|>", lw=1.4, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 color=color, lw=lw, linestyle=ls))


def canvas(w, h, title, subtitle=None):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.text(0.3, h - 0.45, title, fontsize=16, fontweight="bold", va="top")
    if subtitle:
        ax.text(0.3, h - 0.95, subtitle, fontsize=10.5, color=MUTED, va="top")
    return fig, ax


# ---------------------------------------------------------------- roadmap
def roadmap():
    fig, ax = canvas(15, 8.6, "Paper 2 roadmap: knowledge-graph drug repurposing",
                     "Each box is one task. Arrows show what needs to be finished first. Green = done.")
    done = {t for t in range(1, 9) if (RES / f"Task{t}").exists() and any((RES / f"Task{t}").iterdir())}

    # Inputs
    box(ax, 0.4, 5.6, 2.6, 1.3, "Paper 1 results\n6,222 genes\nup/down, F0–F4,\nclusters, pathways", COL["data"], fs=9.5)
    box(ax, 0.4, 3.2, 2.6, 1.3, "Knowledge graph\n(Neo4j / OptimusKG)\ndrugs, genes,\npathways, diseases", COL["data"], fs=9.5)

    def t(n, x, y, title, kid, w=2.9, h=1.3, fc=None):
        fc = fc or (COL["done"] if n in done else COL["task"])
        box(ax, x, y, w, h, "", fc)
        ax.text(x + w / 2, y + h - 0.28, f"Task {n}: {title}", ha="center", va="center", fontsize=10, fontweight="bold")
        ax.text(x + w / 2, y + 0.5, kid, ha="center", va="center", fontsize=8.8, color=MUTED)

    t(1, 3.8, 5.6, "Gene list", "one big register of\nall trouble-maker genes")
    t(2, 3.8, 3.2, "Drug–gene links", "which medicines touch\nwhich genes, and how")
    t(3, 7.5, 5.9, "Druggability", "which gene team has\nmore medicines?")
    t(4, 7.5, 4.25, "Drug coverage", "medicines that touch\nmany genes")
    t(7, 7.5, 2.6, "Push direction", "does the medicine push\nthe switch the right way?")
    t(5, 7.5, 0.95, "MetaPaths", "follow roads on the map:\ndrug→gene→pathway")
    t(6, 11.3, 4.25, "Target score", "a fair points system\nfor genes (design)")
    t(8, 11.3, 2.0, "Report", "summary report\nof all results")
    fr_done = (RES / "Final_ranking/final_drugs_main_list.csv").exists()
    box(ax, 11.3, 0.25, 2.9, 1.1, ("FINAL (Paper 1 final):\ntarget + drug ranking\ndone" if fr_done else
                                   "LATER (wait for Paper 1):\nfinal target + drug\nrepurposing ranking"),
        COL["done"] if fr_done else COL["wait"], fs=8.8)

    arrow(ax, 3.0, 6.25, 3.8, 6.25)
    arrow(ax, 3.0, 3.85, 3.8, 3.85)
    arrow(ax, 5.25, 5.6, 5.25, 4.5)
    for y in (6.55, 4.9, 3.25, 1.6):
        arrow(ax, 6.7, 3.85, 7.5, y)
    arrow(ax, 10.4, 4.9, 11.3, 4.9)
    for y in (6.55, 4.9, 3.25, 1.6):
        arrow(ax, 10.4, y, 11.3, 2.65, color="#b0b8c1", lw=1)
    arrow(ax, 12.75, 4.25, 12.75, 3.3)
    arrow(ax, 12.75, 2.0, 12.75, 1.35, ls="--")

    ax.text(14.7, 8.0, "Scope: repurposing, not reversal.\nKnowledge graph only.\nResults = repurposing hypotheses.",
            ha="right", va="top", fontsize=9, color=COL["fib"], style="italic")
    fig.savefig(RES / "00_roadmap.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 1
def task1():
    df = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
    g = df.paper1_group.value_counts()
    fig = plt.figure(figsize=(15, 8.8))

    # Left: data flow
    ax = fig.add_axes([0.0, 0.0, 0.5, 1.0])
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 8.8); ax.axis("off")
    ax.text(0.3, 8.4, "Task 1: building the gene register", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 7.9, "Four Paper 1 files are glued together into one table. No gene is thrown away.",
            fontsize=10.5, color=MUTED, va="top")
    srcs = [
        ("00_all_progression_genes.csv", "6,222 genes: rho, q, up/down, F0–F4", 6.4),
        ("task2_gene_clusters.csv", "shape group C1–C5 (3,845 genes)", 5.1),
        ("01_master_table.csv", "biggest stage jump + Tier (3,845 genes)", 3.8),
        ("11_FINAL_shortlist_25_genes.csv", "23 VIP genes", 2.5),
    ]
    for name, desc, y in srcs:
        box(ax, 0.3, y, 3.6, 1.0, "", COL["data"])
        ax.text(2.1, y + 0.66, name, ha="center", fontsize=9, fontweight="bold")
        ax.text(2.1, y + 0.3, desc, ha="center", fontsize=8.8, color=MUTED)
        arrow(ax, 3.9, y + 0.5, 4.8, 4.45)
    box(ax, 4.8, 3.5, 2.5, 1.9, "Paper2_\nprogression_\ngenes.csv\n\n6,222 rows", COL["done"], fs=10.5, bold=True)
    ax.text(0.3, 1.6, "Like a class register: every gene gets a name tag with\n"
                      "its team, which way it moves, its score at each stage,\n"
                      "its shape group, its star level, and whether it is a VIP.",
            fontsize=10, va="top")
    ax.text(0.3, 0.45, "Check: all 11 group counts match Paper 1 exactly ✓", fontsize=10, color="#1e8449", fontweight="bold")

    # Right: gene teams tree
    ax = fig.add_axes([0.5, 0.0, 0.5, 1.0])
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 8.8); ax.axis("off")
    ax.text(0.2, 8.4, "The three gene teams", fontsize=16, fontweight="bold", va="top")
    ax.text(0.2, 7.9, "⬆ = goes up as the liver gets sicker    ⬇ = goes down", fontsize=10.5, color=MUTED, va="top")
    box(ax, 2.5, 6.3, 2.5, 0.9, "All genes\n6,222", "#ffffff", bold=True, fs=11)
    teams = [
        ("Fibrosis only\n(scarring)", COL["fib"], 0.2,
         [("⬆", g.get("fibrosis_only_positive", 0)), ("⬇", g.get("fibrosis_only_negative", 0))]),
        ("Shared\n(both)", COL["shared"], 2.65,
         [("⬆⬆", g.get("shared_positive", 0)), ("⬇⬇", g.get("shared_negative", 0)),
          ("mixed", g.get("shared_discordant_fib_negative", 0) + g.get("shared_discordant_fib_positive", 0))]),
        ("Inflammation\nonly", COL["inf"], 5.1,
         [("⬆", g.get("inflammation_only_positive", 0)), ("⬇", g.get("inflammation_only_negative", 0))]),
    ]
    for label, c, x, subs in teams:
        n = sum(v for _, v in subs)
        box(ax, x, 4.4, 2.2, 1.1, f"{label}\n{n:,}", c + "22", ec=c, bold=True, fs=10)
        arrow(ax, 3.75, 6.3, x + 1.1, 5.5)
        sw = 2.2 / len(subs)
        for i, (s, v) in enumerate(subs):
            sx = x + i * sw
            box(ax, sx + 0.05, 2.7, sw - 0.1, 1.0, f"{s}\n{v:,}", "#ffffff", ec=c, fs=9.5)
            arrow(ax, x + 1.1, 4.4, sx + sw / 2, 3.7, color=c, lw=1)
    ax.text(0.2, 2.1, "Only the 3,845 scarring genes (fibrosis-only + shared) have\n"
                      "a shape group, stage jump and Tier. Inflammation-only genes\n"
                      "are left blank on purpose: Paper 1 scored only scarring genes.",
            fontsize=10, va="top")
    ax.text(0.2, 0.75, "Gene count: the plan says 4,692 (old). The corrected count is 6,222.",
            fontsize=9.5, color=COL["fib"], style="italic")
    fig.savefig(RES / "Task1/Task1_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 2
def task2():
    e = pd.read_csv(RES / "Task2/drug_gene_edges.csv")
    genes = pd.read_csv(RES / "Task1/Paper2_progression_genes.csv")
    n = len(e)
    d = e.Action_direction.value_counts()
    fig = plt.figure(figsize=(15, 9.2))

    # Left: how the links were found
    ax = fig.add_axes([0.0, 0.0, 0.5, 1.0])
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 9.2); ax.axis("off")
    ax.text(0.3, 8.8, "Task 2: which medicines touch our genes?", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 8.3, "We asked the Neo4j map for every Drug —ACTS_ON→ Gene line.", fontsize=10.5, color=MUTED, va="top")

    box(ax, 0.3, 6.3, 2.6, 1.3, f"Task 1 register\n{len(genes):,} genes", COL["data"], bold=True)
    box(ax, 4.5, 6.3, 2.7, 1.3, "Neo4j map\n12,025 drugs\n20,674 drug→gene lines", COL["data"], fs=9.5)
    arrow(ax, 2.9, 6.95, 4.5, 6.95)
    ax.text(3.7, 7.15, "ask", ha="center", fontsize=9, color=MUTED)
    box(ax, 1.8, 3.7, 4.0, 1.6, f"drug_gene_edges.csv\n{n:,} lines\n{e.Drug_ID.nunique():,} drugs  ·  {e.Gene_ID.nunique():,} genes",
        COL["done"], bold=True, fs=10.5)
    arrow(ax, 1.6, 6.3, 3.0, 5.3)
    arrow(ax, 5.85, 6.3, 4.6, 5.3)

    # mini example: a drug touching genes
    ax.text(0.3, 3.0, "Example of one line:", fontsize=10, fontweight="bold", va="top")
    box(ax, 0.3, 1.5, 2.0, 0.9, "OSI-930\n(drug)", "#fff7e6", ec="#b9770e", fs=9.5)
    box(ax, 4.9, 1.5, 2.0, 0.9, "KIT\n(gene)", COL["shared"] + "22", ec=COL["shared"], fs=9.5)
    arrow(ax, 2.3, 1.95, 4.9, 1.95, color=COL["down"], lw=2)
    ax.text(3.6, 2.15, "INHIBITOR (pushes ⬇)", ha="center", fontsize=9, color=COL["down"])
    ax.text(3.6, 1.55, "DrugBank + Open Targets\nmulti-source", ha="center", fontsize=8.5, color=MUTED, va="top")
    ax.text(0.3, 0.45, "Check: Neo4j and the CSV give the exact same 8,948 lines ✓",
            fontsize=10, color="#1e8449", fontweight="bold")

    # Right: how the drugs push
    ax = fig.add_axes([0.66, 0.52, 0.32, 0.38])
    order = ["unknown", "down", "up", "mixed"]
    vals = [d.get(k, 0) for k in order]
    colors = ["#b0b8c1", COL["down"], COL["up"], "#d4ac0d"]
    labels = ["Unknown", "Pushes ⬇", "Pushes ⬆", "Mixed"]
    bars = ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
    for b, v in zip(bars, vals[::-1]):
        ax.text(b.get_width() + n * 0.01, b.get_y() + b.get_height() / 2, f"{v:,}  ({100 * v / n:.1f}%)",
                va="center", fontsize=9.5)
    ax.set_xlim(0, n * 1.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("How does the medicine push the switch?", fontsize=13, fontweight="bold", loc="right")
    ax.text(0, -0.06, "⬇ inhibitor, antagonist, blocker…   ⬆ agonist, activator…\nUnknown = TARGET, ENZYME, TRANSPORTER, CARRIER",
            transform=ax.transAxes, fontsize=8.5, color=MUTED, va="top")
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xticks([])

    ax = fig.add_axes([0.58, 0.07, 0.40, 0.30])
    cls = ["fibrosis_only", "shared", "inflammation_only"]
    tot = genes.progression_class.value_counts()
    con = e.groupby("progression_class").Gene_ID.nunique()
    pcts = [100 * con.get(c, 0) / tot[c] for c in cls]
    bars = ax.bar(["Fibrosis only", "Shared", "Inflammation only"], pcts,
                  color=[COL["fib"], COL["shared"], COL["inf"]])
    for b, c, p in zip(bars, cls, pcts):
        ax.text(b.get_x() + b.get_width() / 2, p + 0.5, f"{p:.1f}%\n{con.get(c, 0):,} of {tot[c]:,}",
                ha="center", fontsize=9.5)
    ax.set_ylim(0, max(pcts) * 1.45)
    ax.set_ylabel("% genes with ≥1 drug")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Which team has more medicines? (stats in Task 3)", fontsize=13, fontweight="bold", loc="right")

    fig.text(0.58, 0.005, "Only ~1 in 9 lines says which way the drug pushes. That limits Task 7.",
             fontsize=9.5, color=COL["fib"], style="italic")
    fig.savefig(RES / "Task2/Task2_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 3
def task3():
    df = pd.read_csv(RES / "Task3/druggability_summary_pharmacological.csv").set_index("Group")
    bgdf = pd.read_csv(RES / "Task3/background_genes_druggability.csv")
    bg_pct = 100 * bgdf.pharm_connected.mean()
    fig = plt.figure(figsize=(15, 9.4))

    # Left: the method in pictures
    ax = fig.add_axes([0.0, 0.0, 0.47, 1.0])
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 9.4); ax.axis("off")
    ax.text(0.3, 9.0, "Task 3: does one gene team have more medicines?", fontsize=15.5, fontweight="bold", va="top")
    ax.text(0.3, 8.5, "Compare each team with 'normal' genes, fairly.", fontsize=10.5, color=MUTED, va="top")

    steps = [
        ("1  Count", "For each team: what % of its genes\nhave a real drug target link?", 6.9),
        ("2  Compare with all genes", f"14,794 Paper 1 genes = the 'normal' class.\n{bg_pct:.0f}% of them have a drug (Fisher test).", 5.45),
        ("3  Be fair about famous genes", "Famous (well-studied) genes get more drugs.\nSo we draw 1,000 random teams with equally\nfamous genes and see what they get.", 3.8),
        ("4  Remove 'drug-processing' genes", "Liver enzymes like CYP1A2 break drugs down.\nThat is not a drug target, so ENZYME /\nTRANSPORTER / CARRIER links are removed.", 2.15),
    ]
    for title, body, y in steps:
        box(ax, 0.3, y, 6.9, 1.3, "", "#ffffff")
        ax.text(0.55, y + 1.05, title, fontsize=10.5, fontweight="bold", va="top")
        ax.text(0.55, y + 0.68, body, fontsize=9, color=MUTED, va="top")
    for y in (6.9, 5.45, 3.8):
        arrow(ax, 3.75, y, 3.75, y - 0.15)
    ax.text(0.3, 1.5, "Like checking if one class has more\nsports stars: compare with the whole school,\n"
                      "and only count real athletes.", fontsize=10, va="top")

    # Right: results
    ax = fig.add_axes([0.53, 0.40, 0.45, 0.48])
    groups = [("fibrosis_only_positive", "Scarring\nonly ⬆", COL["fib"]),
              ("fibrosis_only_negative", "Scarring\nonly ⬇", COL["fib"]),
              ("shared_positive", "Shared\n⬆⬆", COL["shared"]),
              ("shared_negative", "Shared\n⬇⬇", COL["shared"]),
              ("inflammation_only_positive", "Inflam.\nonly ⬆", COL["inf"]),
              ("inflammation_only_negative", "Inflam.\nonly ⬇", COL["inf"])]
    xs = np.arange(len(groups))
    for x, (g, lab, c) in zip(xs, groups):
        r = df.loc[g]
        sig = r.Perm_BH_FDR < 0.05
        ax.bar(x, r.Percentage, color=c, alpha=1.0 if sig else 0.35)
        ax.text(x, r.Percentage + 0.6, f"{r.Percentage:.0f}%" + (" ★" if sig else ""), ha="center", fontsize=10,
                fontweight="bold" if sig else "normal")
    ax.axhline(bg_pct, color=MUTED, ls="--", lw=1.2)
    ax.text(len(groups) - 0.45, bg_pct - 1.6, f"normal genes {bg_pct:.0f}%", ha="right", fontsize=9, color=MUTED)
    ax.set_xticks(xs, [g[1] for g in groups], fontsize=9.5)
    ax.set_ylim(0, 27)
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_title("% genes with a real drug target  (★ = more than fair chance)", fontsize=12, fontweight="bold", loc="left")

    ax = fig.add_axes([0.53, 0.0, 0.45, 0.33])
    ax.set_xlim(0, 7); ax.set_ylim(0, 3.3); ax.axis("off")
    box(ax, 0.0, 1.75, 7.0, 1.4, "", COL["done"])
    ax.text(0.2, 2.95, "What we found", fontsize=11, fontweight="bold", va="top")
    ax.text(0.2, 2.55, "Scarring genes (fibrosis-only + shared) have more drugs than normal:\n"
                       f"{df.loc['Fibrosis-associated (fibrosis-only + shared)', 'Percentage']:.1f}% vs {bg_pct:.1f}%. "
                       "Inflammation-only genes are just normal.", fontsize=9.5, va="top")
    box(ax, 0.0, 0.05, 7.0, 1.5, "", "#fdf2e9", ec="#b9770e")
    ax.text(0.2, 1.35, "But look closely", fontsize=11, fontweight="bold", va="top")
    ax.text(0.2, 0.95, "Most extra drugs sit on genes that go DOWN (⬇) as the liver scars.\n"
                       "Rising scarring-only genes are just normal; rising shared genes a little more.\n"
                       "A falling gene needs a drug that pushes it UP, and those are rarer (Task 7).",
            fontsize=9.5, va="top")
    fig.savefig(RES / "Task3/Task3_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 4
def task4():
    cov = pd.read_csv(RES / "Task4/drug_coverage.csv")
    cand = pd.read_csv(RES / "Task4/repurposing_candidates.csv")
    mech = pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv")
    hit = cov[cov.n_progression_genes > 0]
    wd = hit.withdrawn.astype("boolean").fillna(False).astype(bool)
    steps = [
        ("All drugs touching our genes (Task 2)", len(cov), "any link"),
        ("Real drug-target link (not enzyme/transporter)", len(hit), "Task 3 rule"),
        ("Tested in people (phase ≥ 2)", int((hit.max_phase >= 2).sum()), "trial or approved"),
        ("Not withdrawn from the market", int(((hit.max_phase >= 2) & ~wd).sum()), "still allowed"),
        ("Not already used for liver disease", len(cand), "= repurposing candidates"),
        ("We know HOW it acts (mechanism)", len(mech), "= main list"),
    ]
    fig = plt.figure(figsize=(15, 9.6))
    ax = fig.add_axes([0.0, 0.0, 0.55, 1.0])
    ax.set_xlim(0, 8); ax.set_ylim(0, 9.6); ax.axis("off")
    ax.text(0.3, 9.25, "Task 4: finding old medicines for a new job", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 8.75, "A funnel: each step keeps only the drugs that pass a rule.", fontsize=10.5, color=MUTED, va="top")
    top_n = steps[0][1]
    for i, (lab, n, note) in enumerate(steps):
        y = 7.6 - i * 1.18
        w = 1.6 + 4.4 * (n / top_n) ** 0.5
        x = 3.3 - w / 2
        fc = COL["done"] if i == len(steps) - 1 else ("#e8f4ea" if i == len(steps) - 2 else COL["data"])
        box(ax, x, y, w, 0.95, "", fc)
        ax.text(3.3, y + 0.62, f"{n:,} drugs", ha="center", fontsize=11.5, fontweight="bold")
        ax.text(3.3, y + 0.25, lab, ha="center", fontsize=9, color=MUTED)
        ax.text(x + w + 0.12, y + 0.47, note, fontsize=8.5, color=MUTED, va="center", style="italic")
    ax.text(0.3, 0.3, "Liver disease list = graph's 'liver disease' family, cleaned of malaria\nand gallbladder tumours that EFO files under it (161 diseases).",
            fontsize=9, color=MUTED)

    ax = fig.add_axes([0.63, 0.40, 0.35, 0.50])
    show = mech.head(12).iloc[::-1]
    ax.barh(show.Drug.str.title(), show.n_fibrosis_genes, color=COL["fib"], alpha=0.85, label="scarring genes hit")
    for y, (_, r) in enumerate(show.iterrows()):
        ax.text(r.n_fibrosis_genes + 0.8, y, f"{int(r.n_fibrosis_genes)}" + ("  ⚠ liver caution" if r.liver_contraindicated else ""),
                va="center", fontsize=8.5)
    ax.set_xlim(0, show.n_fibrosis_genes.max() * 1.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlabel("number of scarring (fibrosis-associated) genes the drug touches")
    ax.set_title("Main list: first 12 (NOT a ranking)", fontsize=12.5, fontweight="bold", loc="left")

    ax = fig.add_axes([0.57, 0.0, 0.41, 0.31])
    ax.set_xlim(0, 7); ax.set_ylim(0, 3.1); ax.axis("off")
    box(ax, 0.0, 1.6, 7.0, 1.4, "", "#fdf2e9", ec="#b9770e")
    ax.text(0.2, 2.8, "Watch out", fontsize=11, fontweight="bold", va="top")
    ax.text(0.2, 2.4, "A drug that touches many genes is like a key that opens many doors:\n"
                      "not automatically good. Fostamatinib touches 82 scarring genes,\nbut the graph links it to 302 targets in total.",
            fontsize=9.2, va="top")
    box(ax, 0.0, 0.0, 7.0, 1.45, "", COL["done"])
    ax.text(0.2, 1.25, "Interesting pattern", fontsize=11, fontweight="bold", va="top")
    ax.text(0.2, 0.85, "Many CNS drugs share serotonin/adrenaline receptor genes\n(HTR2A, HTR2B, HTR7, ADRA1A) that change with scarring.\n"
                       "Whether they push the right way is Task 7.", fontsize=9.2, va="top")
    fig.savefig(RES / "Task4/Task4_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 5
def task5():
    c = pd.read_csv(RES / "Task5/metapath_counts.csv").set_index("MetaPath")
    get = lambda k: c.loc[[i for i in c.index if i.startswith(k)][0]]
    fig = plt.figure(figsize=(15, 11.2))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 15); ax.set_ylim(0, 11.2); ax.axis("off")
    ax.text(0.3, 10.85, "Task 5: following roads on the map (MetaPaths)", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 10.35, "Start at a medicine, walk to a gene it touches, then see where that gene leads. "
                       "More roads = more connection, NOT proof the medicine works.", fontsize=10.5, color=MUTED, va="top")
    box(ax, 0.3, 5.7, 2.2, 1.4, "MEDICINE\n2,407 drugs", "#fff7e6", ec="#b9770e", bold=True)
    box(ax, 3.6, 5.7, 2.4, 1.4, "GENE it touches\n(real drug-target\nlink only)", COL["shared"] + "22", ec=COL["shared"], fs=9.5)
    arrow(ax, 2.5, 6.4, 3.6, 6.4, lw=2)
    roads = [
        ("M1", "Liver disease", f"{int(get('M1 ').loc['unique drugs']):,} drugs reach a liver disease\n"
                                f"{int(get('M1f').loc['unique drugs']):,} reach fatty liver / NASH / cirrhosis"),
        ("M2–M3", "Pathway / process", f"{int(get('M2').loc['unique drugs']):,} drugs → {int(get('M2').loc['unique end nodes']):,} Reactome pathways\n"
                                       f"{int(get('M3').loc['unique drugs']):,} drugs → {int(get('M3').loc['unique end nodes']):,} GO processes"),
        ("M4–M5", "Pathway shared with a\nscarring gene (C1–C5)", "a gene in the same pathway as our\nscarring genes, per shape group"),
        ("M6", "Stage-jump gene\n(F0→F1 … F3→F4)", "drugs touching genes that jump\nat a fibrosis stage step"),
        ("M7", "Paper 1 scarring program\n(GO, Reactome, KEGG, Hallmark)", "every Paper 1 pathway is reachable\n(graph node or Paper 1 gene list)"),
    ]
    for i, (code, end, note) in enumerate(roads):
        y = 8.8 - i * 1.35
        box(ax, 7.4, y, 2.8, 1.1, f"{end}", "#d5f5e3", fs=9.3)
        ax.text(7.25, y + 0.55, code, ha="right", va="center", fontsize=10, fontweight="bold", color=COL["fib"])
        arrow(ax, 6.0, 6.4, 7.4, y + 0.55, lw=1.4)
        ax.text(10.4, y + 0.55, note, va="center", fontsize=9, color=INK)
    box(ax, 0.3, 0.35, 6.4, 2.9, "", "#ffffff")
    ax.text(0.5, 3.05, "Fair counting (DNS)", fontsize=11, fontweight="bold", va="top")
    ax.text(0.5, 2.65, "A medicine with 300 targets finds many roads just by chance.\n"
                       "So each road count is divided by √(drug's targets × end's size).\n"
                       "Small, focused medicines are not drowned out by big ones.\n\n"
                       "Checked: Python counts = Neo4j counts for M1–M4, M6 ✓", fontsize=9.5, va="top")
    box(ax, 7.4, 0.35, 7.3, 2.9, "", COL["done"])
    ax.text(7.6, 3.05, "What popped out", fontsize=11, fontweight="bold", va="top")
    ax.text(7.6, 2.65, "The strongest fair road to fatty liver / NASH / cirrhosis comes from\n"
                       "PPAR medicines (indeglitazar, tesaglitazar, fenofibric acid …)\n"
                       "via PPARA / PPARG / PPARD. The graph found this by itself.\n\n"
                       "But: PPARA goes DOWN in scarring, PPARG/PPARD go UP, and these\n"
                       "drugs push all three UP, so only PPARA is the 'right way' (Task 7).", fontsize=9.5, va="top")
    fig.savefig(RES / "Task5/Task5_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 6
def task6():
    abl = pd.read_csv(RES / "Task6/ablation_equal_weights.csv")
    sens = pd.read_csv(RES / "Task6/weight_sensitivity_equal_weights.csv").set_index("dirichlet_alpha")
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 15); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(0.3, 9.65, "Task 6: a fair points system for genes (design + test run)", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 9.15, "Like scoring football players before picking a team: five scores, each from 0 to 1, added up with weights.",
            fontsize=10.5, color=MUTED, va="top")
    parts = [("P", "Progress", "How strongly the gene\nchanges with scarring,\nand does it hold in\nevery study?", COL["fib"]),
             ("F", "Fibrosis-only", "Scarring-only = 1\nshared = 0.67\ninflammation-only = 0", COL["shared"]),
             ("T", "Timing", "Clear F0→F4 path,\nstable shape group,\nreal stage jump", "#b9770e"),
             ("K", "Knowledge graph", "Drugs exist? Tested\nin people? Linked to\nfatty liver / cirrhosis?", "#1e8449"),
             ("B", "Biology", "Inside Paper 1's\nscarring pathways\n(GO/Reactome/KEGG/Hallmark)", COL["inf"])]
    for i, (code, name, body, c) in enumerate(parts):
        x = 0.3 + i * 2.95
        box(ax, x, 5.9, 2.7, 2.7, "", c + "18", ec=c)
        ax.text(x + 1.35, 8.3, code, ha="center", fontsize=22, fontweight="bold", color=c)
        ax.text(x + 1.35, 7.65, name, ha="center", fontsize=10.5, fontweight="bold")
        ax.text(x + 1.35, 7.25, body, ha="center", va="top", fontsize=9)
    ax.text(7.5, 5.45, "TargetScore = w1·P + w2·F + w3·T + w4·K + w5·B     (weights decided only after Paper 1 is final)",
            ha="center", fontsize=12, fontweight="bold")

    a2 = fig.add_axes([0.05, 0.07, 0.42, 0.38])
    sub = abl[abl.variant != "full (equal weights)"]
    a2.barh(sub.variant.str.replace("without ", "remove "), sub.top50_overlap, color=["#b0b8c1"] * (len(sub) - 1) + [COL["fib"]])
    for y, v in enumerate(sub.top50_overlap):
        a2.text(v + 0.5, y, f"{int(v)}/50", va="center", fontsize=9)
    a2.set_xlim(0, 55)
    a2.invert_yaxis()
    a2.spines[["top", "right"]].set_visible(False)
    a2.set_xlabel("how many of the top 50 genes stay in the top 50")
    a2.set_title("Take one score away: does the team change?", fontsize=12, fontweight="bold", loc="left")

    a3 = fig.add_axes([0.53, 0.04, 0.45, 0.42])
    a3.set_xlim(0, 7); a3.set_ylim(0, 4.2); a3.axis("off")
    box(a3, 0.0, 2.25, 7.0, 1.85, "", COL["done"])
    a3.text(0.2, 3.9, "Lesson 1: make two lists", fontsize=11, fontweight="bold", va="top")
    a3.text(0.2, 3.5, "Most genes (83%) have no drug link, so K acts like a gate.\n"
                      "Biology list (P, F, T, B) finds NEW targets;\nactionable list (with K) finds repurposing targets.",
            fontsize=9.5, va="top")
    box(a3, 0.0, 0.1, 7.0, 1.95, "", "#fdf2e9", ec="#b9770e")
    a3.text(0.2, 1.85, "Lesson 2: weights matter, so report stable genes", fontsize=11, fontweight="bold", va="top")
    a3.text(0.2, 1.45, f"1,000 random weight sets: only {int(sens.loc[1.0, 'genes_in_top50_in_>=80%_of_draws'])} genes stay in the top 50 almost always\n"
                       f"(wild weights), {int(sens.loc[10.0, 'genes_in_top50_in_>=80%_of_draws'])} with near-equal weights. "
                       "P, F and T also overlap\n(they all measure scarring), so they may need merging.", fontsize=9.5, va="top")
    fig.savefig(RES / "Task6/Task6_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Task 7
def task7():
    grp = pd.read_csv(RES / "Task7/consistency_by_paper1_group.csv").set_index("paper1_group")
    kn = pd.read_csv(RES / "Task7/summary_known_vs_unknown.csv")
    cd = pd.read_csv(RES / "Task7/candidates_direction_summary.csv")
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 15); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(0.3, 9.65, "Task 7: does the medicine push the switch the right way?", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 9.15, "Right way = a hypothesis worth testing, not proof the medicine helps.", fontsize=10.5, color=MUTED, va="top")
    # 2x2 rule grid
    ax.text(0.3, 8.45, "The rule", fontsize=12, fontweight="bold")
    ax.text(2.9, 8.0, "medicine pushes ⬇", ha="center", fontsize=10, fontweight="bold", color=COL["down"])
    ax.text(5.3, 8.0, "medicine pushes ⬆", ha="center", fontsize=10, fontweight="bold", color=COL["up"])
    for i, (row, good) in enumerate([("gene goes ⬆\nwith scarring", 0), ("gene goes ⬇\nwith scarring", 1)]):
        y = 6.6 - i * 1.4
        ax.text(1.55, y + 0.6, row, ha="right", va="center", fontsize=9.5)
        for j in range(2):
            ok = j == good
            box(ax, 1.75 + j * 2.4, y, 2.3, 1.2, "✔ right way" if ok else "✘ wrong way",
                COL["done"] if ok else "#fdecea", ec="#1e8449" if ok else COL["fib"], fs=10.5, bold=True)
    ax.text(0.3, 4.75, "Mixed action → ambiguous.   TARGET / ENZYME / TRANSPORTER / CARRIER → unknown.",
            fontsize=9, color=MUTED)
    # unknown limitation
    unk = float(kn.loc[0, "% unknown"])
    box(ax, 0.3, 3.0, 6.6, 1.45, "", "#fdf2e9", ec="#b9770e")
    ax.text(0.5, 4.25, f"Big limitation: {unk:.1f}% of links say only 'touches', not which way", fontsize=10.5, fontweight="bold", va="top")
    ax.text(0.5, 3.85, f"{int(kn.loc[0, 'known direction (down/up)']):,} of {int(kn.loc[0, 'total']):,} links can be judged; "
                       "the rest stay 'unknown' (not 'wrong').", fontsize=9.5, va="top")
    # candidate funnel
    c0 = cd.iloc[0]
    box(ax, 0.3, 0.3, 6.6, 2.4, "", COL["done"])
    ax.text(0.5, 2.5, "Repurposing candidates (Task 4)", fontsize=10.5, fontweight="bold", va="top")
    ax.text(0.5, 2.1, f"1,109 candidates → {int(c0['≥1 direction-consistent link'])} have ≥1 right-way link\n"
                      f"   {int(c0['only consistent'])} only right-way   ·   {int(c0['mixed'])} mixed   ·   "
                      f"{int(c0['only inconsistent'])} only wrong-way\n\n"
                      "PPAR medicines: right way on PPARA, wrong way on PPARG / PPARD → mixed.",
            fontsize=9.5, va="top")
    # bar chart by group
    a2 = fig.add_axes([0.53, 0.12, 0.44, 0.7])
    order = [("fibrosis_only_positive", "Scarring-only ⬆", COL["fib"], 1.0), ("fibrosis_only_negative", "Scarring-only ⬇", COL["fib"], 0.5),
             ("shared_positive", "Shared ⬆⬆", COL["shared"], 1.0), ("shared_negative", "Shared ⬇⬇", COL["shared"], 0.5),
             ("inflammation_only_positive", "Inflam.-only ⬆", COL["inf"], 1.0), ("inflammation_only_negative", "Inflam.-only ⬇", COL["inf"], 0.5)]
    for y, (g, lab, c, al) in enumerate(order):
        r = grp.loc[g]
        n_dec = int(r["direction-consistent"] + r["direction-inconsistent"])
        a2.barh(y, r["% consistent among decided"], color=c, alpha=al)
        a2.text(r["% consistent among decided"] + 1.5, y, f"{r['% consistent among decided']:.0f}%  (n={n_dec})", va="center", fontsize=9.5)
    a2.axvline(50, color=MUTED, ls="--", lw=1)
    a2.set_yticks(range(len(order)), [o[1] for o in order], fontsize=10)
    a2.invert_yaxis()
    a2.set_xlim(0, 110)
    a2.spines[["top", "right"]].set_visible(False)
    a2.set_xlabel("% of judged links that push the right way")
    a2.set_title("Rising genes: mostly pushed the right way.\nFalling genes: mostly pushed the wrong way (few boosters exist).",
                 fontsize=11.5, fontweight="bold", loc="left")
    fig.savefig(RES / "Task7/Task7_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Final ranking
def final_ranking():
    F = RES / "Final_ranking"
    act = pd.read_csv(F / "final_targets_actionable.csv")
    drugs = pd.read_csv(F / "final_drugs_main_list.csv")
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 15); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(0.3, 9.65, "Final ranking: best targets, then best old medicines", fontsize=16, fontweight="bold", va="top")
    ax.text(0.3, 9.15, "Rules were frozen BEFORE ranking. Dark bar = stays near the top under 1,000 different weightings (stable). "
                       "These are ideas to test, not treatments.", fontsize=10, color=MUTED, va="top")
    ax.text(0.3, 8.8, "✔ after a medicine = genes it pushes the right way (blocks a rising gene or boosts a falling one).",
            fontsize=10, color=MUTED, va="top")

    def bars(axb, names, vals, stable, labels, color, title, xlab):
        y = np.arange(len(names))
        axb.barh(y, vals, color=[color if s else color + "55" for s in stable])
        for yi, v, lab in zip(y, vals, labels):
            axb.text(v + 0.005, yi, lab, va="center", fontsize=8.5, color=INK)
        axb.set_yticks(y, names, fontsize=9.5)
        axb.invert_yaxis()
        axb.set_xlim(min(vals) - 0.08, max(vals) + 0.12)
        axb.spines[["top", "right"]].set_visible(False)
        axb.set_title(title, fontsize=12, fontweight="bold", loc="left")
        axb.set_xlabel(xlab, fontsize=9)

    t = act.head(15)
    a1 = fig.add_axes([0.07, 0.08, 0.36, 0.76])
    bars(a1, [f"{g} {'⬆' if d == 'positive' else '⬇'}" for g, d in zip(t.Gene, t.fibrosis_direction)], t.TargetScore,
         t.stable_target, [("★ VIP" if s else "") for s in t.in_shortlist], COL["fib"],
         "Top 15 targets (actionable list)", "TargetScore (0–1): progress + fibrosis-only + timing + graph + biology")
    d = drugs.head(15)
    a2 = fig.add_axes([0.58, 0.08, 0.40, 0.76])
    bars(a2, d.Drug.str.title(), d.DrugScore, d.stable_drug,
         [("✔ " + ", ".join(str(c).split(";")[:2]) if isinstance(c, str) and c else "") + ("  ⚠ liver" if ci else "")
          for c, ci in zip(d.consistent_targets, d.liver_contraindicated)], "#1e8449",
         "Top 15 repurposing candidates (main list)", "DrugScore (0–1): target + right-way push + focus + graph roads")
    fig.savefig(F / "Final_ranking_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    roadmap()
    if (RES / "Task1/Paper2_progression_genes.csv").exists():
        task1()
    if (RES / "Task2/drug_gene_edges.csv").exists():
        task2()
    if (RES / "Task3/druggability_summary_pharmacological.csv").exists():
        task3()
    if (RES / "Task4/repurposing_candidates_mechanism_annotated.csv").exists():
        task4()
    if (RES / "Task5/metapath_counts.csv").exists():
        task5()
    if (RES / "Task6/ablation_equal_weights.csv").exists():
        task6()
    if (RES / "Task7/consistency_by_paper1_group.csv").exists():
        task7()
    if (RES / "Final_ranking/final_drugs_main_list.csv").exists():
        final_ranking()
    print("diagrams written")
