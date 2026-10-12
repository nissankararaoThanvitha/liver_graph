"""
paper2_figures.py
-----------------
Figures for Paper 2 Tasks 1 and 2, matching Paper 1's convention of one or more
PNGs per task rather than CSVs alone.

Deliberately plain. These are working figures for reading the result, not
manuscript figures; the Paper 1 package builds those separately at the end.

Task 1
  task1_class_composition.png  the three progression classes, and the direction
                               split within each ladder. Drawn per ladder
                               because a gene has a direction on each ladder it
                               belongs to, not one overall.

Task 2
  task2_action_classes.png     what the 8,948 drug-gene edges actually are.
                               The point of the figure is that the two largest
                               bars -- pharmacokinetic and non-directional --
                               are the ones that carry no usable mechanism.
  task2_consistency_null.png   observed reversal-consistency against the
                               permutation null. The observed value sitting
                               inside the null is the result.

Usage:
    uv run --with pandas --with numpy --with matplotlib python scripts/paper2_figures.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

T1 = "Paper2_Results/Task1"
T2 = "Paper2_Results/Task2"

BLUE, ORANGE, GREY = "#1f6feb", "#b4690e", "#8a97a5"
GREEN, RED = "#0f8a5f", "#c0362c"


def task1_classes():
    s = pd.read_csv(f"{T1}/task1_class_summary.csv")
    s = s[s.progression_class != "UNION (all)"]
    classes = s.progression_class.tolist()
    y = np.arange(len(classes))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.6),
                                   gridspec_kw={"width_ratios": [1, 1.5]})

    ax1.barh(y, s.genes, color=[BLUE, ORANGE, GREEN], height=.6)
    ax1.set_yticks(y); ax1.set_yticklabels(classes); ax1.invert_yaxis()
    for i, (n, p) in enumerate(zip(s.genes, s.percent_of_union)):
        ax1.text(n + 40, i, f"{n:,}  ({p}%)", va="center", fontsize=9)
    ax1.set_xlim(0, max(s.genes) * 1.35)
    ax1.set_xlabel("genes")
    ax1.set_title("Progression classes (6,222 genes)", fontsize=10, loc="left")
    ax1.spines[["top", "right"]].set_visible(False)

    # Direction per ladder. A gene has one direction per ladder it is on, so
    # each ladder is drawn separately rather than merged into one bar.
    h = .34
    ax2.barh(y - h/2, s.fibrosis_increasing, h, color=RED, label="fibrosis: increasing")
    ax2.barh(y - h/2, -s.fibrosis_decreasing, h, color="#f0a39c",
             label="fibrosis: decreasing")
    ax2.barh(y + h/2, s.inflammation_increasing, h, color="#0b5c40",
             label="inflammation: increasing")
    ax2.barh(y + h/2, -s.inflammation_decreasing, h, color="#95ddc0",
             label="inflammation: decreasing")
    ax2.axvline(0, color="#15202b", lw=.8)
    ax2.set_yticks(y); ax2.set_yticklabels(classes); ax2.invert_yaxis()
    ax2.set_xlabel("genes   (decreasing  <-  |  ->  increasing)")
    ax2.set_title("Direction of change, per ladder", fontsize=10, loc="left")
    ax2.legend(fontsize=7.5, loc="lower right", framealpha=.95)
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(f"{T1}/task1_class_composition.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T1}/task1_class_composition.png")


def task2_actions():
    e = pd.read_csv(f"{T2}/task2_drug_gene_edges.csv")
    order = ["therapeutic-nondirectional", "pharmacokinetic",
             "therapeutic-lowers", "therapeutic-raises"]
    counts = e.action_class.value_counts().reindex(order)
    labels = ["therapeutic,\nno direction recorded", "pharmacokinetic\n(metabolism/transport)",
              "therapeutic,\nlowers the gene", "therapeutic,\nraises the gene"]
    colours = [GREY, ORANGE, BLUE, GREEN]

    fig, ax = plt.subplots(figsize=(9, 3.6))
    bars = ax.bar(range(4), counts.values, color=colours, width=.62)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width()/2, v + 70,
                f"{v:,}\n{100*v/len(e):.1f}%", ha="center", fontsize=9)
    ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("drug-gene edges")
    ax.set_ylim(0, max(counts.values) * 1.25)
    ax.set_title(f"What the {len(e):,} drug-gene edges are  "
                 "(1,072 genes, 3,027 drugs)", fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate("only these two carry a usable direction: 1,005 edges, 11.2%",
                xy=(2.5, max(counts.values) * .78), ha="center", fontsize=8.5,
                color=RED)
    fig.tight_layout()
    fig.savefig(f"{T2}/task2_action_classes.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T2}/task2_action_classes.png")


def task2_null():
    t = pd.read_csv(f"{T2}/task2_consistency_permutation_test.csv").iloc[0]
    rng = np.random.default_rng(0)
    # Redraw the null's shape from its reported moments for display only; the
    # p-value plotted is the one the permutation test computed.
    lo, hi, mean = t.null_95_low, t.null_95_high, t.null_mean_percent
    sd = (hi - lo) / (2 * 1.96)
    null = rng.normal(mean, sd, 200000)

    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.hist(null, bins=90, color="#d6e0ea", edgecolor="none",
            label="null: direction shuffled between genes")
    ax.axvspan(lo, hi, color="#eaf2ff", alpha=.6, zorder=0)
    ax.axvline(50, color=GREY, ls=":", lw=1.2, label="coin flip (50%)")
    ax.axvline(t.observed_percent_consistent, color=RED, lw=2.2,
               label=f"observed {t.observed_percent_consistent}%")
    ax.set_xlabel("reversal-consistent edges (%)")
    ax.set_yticks([])
    ax.set_title("Mechanism consistency against its null  "
                 f"(p = {t.p_value}, {int(t.permutations):,} permutations)",
                 fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper left", framealpha=.95)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.annotate("observed sits inside the null:\nnot distinguishable from chance",
                xy=(t.observed_percent_consistent, ax.get_ylim()[1] * .42),
                xytext=(lo - 9, ax.get_ylim()[1] * .55), fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))
    fig.tight_layout()
    fig.savefig(f"{T2}/task2_consistency_null.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T2}/task2_consistency_null.png")


if __name__ == "__main__":
    task1_classes()
    task2_actions()
    task2_null()
