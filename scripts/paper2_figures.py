"""
paper2_figures.py
-----------------
Figures for Paper 2 Tasks 1 and 2, matching Paper 1's convention of one or more
PNGs per task rather than CSVs alone.

Deliberately plain. These are working figures for reading the result, not
manuscript figures; the Paper 1 package builds those separately at the end.

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
    t = pd.read_excel(f"{T2}/task2_supporting.xlsx",
                      sheet_name="consistency_permutation_test").iloc[0]
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


def task3_druggability():
    """The bar plot the plan asks for, with the background drawn as the line
    everything is compared against rather than as another bar."""
    T3 = "Paper2_Results/Task3"
    s = pd.read_csv(f"{T3}/task3_druggability_summary.csv")
    t = pd.read_csv(f"{T3}/task3_enrichment_tests.csv").set_index("group")

    bg = float(s.loc[s.group == "NOT progression (background)", "percent"].iloc[0])
    order = ["fibrosis-only / positive", "fibrosis-only / negative",
             "inflammation-only / positive", "inflammation-only / negative",
             "shared / positive", "shared / negative", "shared / discordant"]
    s = s.set_index("group").loc[order].reset_index()

    # Colour by direction, not by class: the direction is where the signal is.
    colours = [BLUE if "positive" in grp else
               (ORANGE if "negative" in grp else GREY) for grp in s.group]
    survives = [t.loc[grp, "survives_degree_aware"] if grp in t.index else "no"
                for grp in s.group]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = np.arange(len(s))
    bars = ax.bar(x, s.percent, color=colours, width=.66,
                  edgecolor=["#15202b" if v == "yes" else "none" for v in survives],
                  linewidth=1.6)
    ax.axhline(bg, color=RED, ls="--", lw=1.4)
    ax.text(len(s) - .4, bg + .45, f"background {bg}%", color=RED, fontsize=8.5,
            ha="right")

    for b, pct, n, v in zip(bars, s.percent, s.total_genes, survives):
        ax.text(b.get_x() + b.get_width()/2, pct + .35,
                f"{pct}%" + ("  *" if v == "yes" else ""),
                ha="center", fontsize=9,
                fontweight="bold" if v == "yes" else "normal")
        ax.text(b.get_x() + b.get_width()/2, .6, f"n={n:,}", ha="center",
                fontsize=7.5, color="white")

    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(" / ", "\n") for g in s.group], fontsize=8.5)
    ax.set_ylabel("genes with a therapeutic drug edge (%)")
    ax.set_ylim(0, max(s.percent) * 1.22)
    ax.set_title("Druggability by progression group  "
                 "(* survives a degree-matched null; bold outline = same)",
                 fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{T3}/task3_druggability_by_group.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T3}/task3_druggability_by_group.png")


def task4_coverage():
    """Coverage against coherence.

    The plan warns twice not to read high coverage as candidate quality. The
    scatter makes the reason visible: the drugs furthest right hit the most
    progression genes and sit LOW on coherence, meaning those genes belong to
    different programmes. The two measures are slightly negatively correlated.
    """
    T4 = "Paper2_Results/Task4"
    d = pd.read_csv(f"{T4}/task4_drug_coverage.csv")
    d = d[d.n_progression_genes >= 3]
    ok = d[~d.likely_non_therapeutic]
    flagged = d[d.likely_non_therapeutic]

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.scatter(flagged.n_progression_genes, flagged.dominant_class_fraction,
               s=18, c=GREY, alpha=.5, label="flagged non-therapeutic "
               f"(n={len(flagged)})", zorder=2)
    sc = ax.scatter(ok.n_progression_genes, ok.dominant_class_fraction,
                    s=24, c=ok.progression_fraction_lower95, cmap="viridis",
                    edgecolor="none", zorder=3)
    # A legend swatch for a colour-mapped series would show one arbitrary
    # colour from the ramp and read as a category. A hollow proxy does not.
    ax.scatter([], [], s=24, facecolor="none", edgecolor="#15202b",
               label=f"named drugs (n={len(ok)}), coloured by specificity")
    cb = fig.colorbar(sc, ax=ax, pad=.015)
    cb.set_label("specificity (Wilson lower bound)", fontsize=8)

    for name in ["FOSTAMATINIB", "MARIMASTAT", "TRAPIDIL", "GLYCYRRHIZIN",
                 "ASPIRIN", "SPIRONOLACTONE"]:
        r = ok[ok.Drug == name]
        if len(r):
            r = r.iloc[0]
            # the rightmost point would run its label off the axis
            right = r.n_progression_genes > ok.n_progression_genes.quantile(.98)
            ax.annotate(name, (r.n_progression_genes, r.dominant_class_fraction),
                        xytext=(-6 if right else 6, 5),
                        ha="right" if right else "left",
                        textcoords="offset points", fontsize=8, color="#15202b")
    ax.set_xscale("log")
    ax.set_xlabel("progression genes reached  (log scale)")
    ax.set_ylabel("coherence\n(largest share in one group)")
    ax.set_title("Coverage is not quality: the widest-reaching drugs are the "
                 "least coherent", fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper right", framealpha=.95)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{T4}/task4_coverage_vs_coherence.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T4}/task4_coverage_vs_coherence.png")


def task4_network():
    """A readable slice of the bipartite network, grouped by biology.

    The full network is 376 drugs and 610 genes -- a hairball at any size that
    fits on a page. Drawn instead: the most coherent named drugs reaching at
    least five progression genes.

    Genes are ordered by their major fibrosis-associated process rather than
    alphabetically, which is the point of carrying that annotation: it turns a
    list of symbols into blocks, and MARIMASTAT's fan into the matrix
    metallopeptidases becomes visible as a block rather than a coincidence of
    names starting with MMP.
    """
    T4 = "Paper2_Results/Task4"
    d = pd.read_csv(f"{T4}/task4_drug_coverage.csv")
    e = pd.read_csv(f"{T4}/task4_network_edges.csv")
    n = pd.read_csv(f"{T4}/task4_network_nodes.csv")

    pick = (d[(~d.likely_non_therapeutic) & (d.n_progression_genes >= 5)]
            .nlargest(8, "dominant_class_fraction").Drug.tolist())
    sub = e[e.Drug.isin(pick)]
    genes = n[(n.node_type == "gene") & (n.label.isin(sub.Gene))].copy()
    genes["major_pathway"] = genes.major_pathway.fillna("(no enriched process)")

    # order genes by pathway block, largest block first, alphabetical within
    size = genes.major_pathway.value_counts()
    genes["block"] = genes.major_pathway.map(size)
    genes = genes.sort_values(["block", "major_pathway", "label"],
                              ascending=[False, True, True])
    gene_list = genes.label.tolist()
    gmeta = genes.set_index("label")["group"].to_dict()
    pmeta = genes.set_index("label")["major_pathway"].to_dict()

    gy = {g: i for i, g in enumerate(gene_list)}
    dy = {dr: i * (len(gene_list) - 1) / max(len(pick) - 1, 1)
          for i, dr in enumerate(pick)}

    fig, ax = plt.subplots(figsize=(12, max(6, len(gene_list) * .19)))
    for _, r in sub.iterrows():
        ax.plot([0, 1], [dy[r.Drug], gy[r.Gene]], lw=.7, color="#c7d4e0",
                zorder=1)
    ax.scatter([0] * len(pick), [dy[p] for p in pick], s=95, c=PURPLE_OK,
               zorder=3)
    for p in pick:
        ax.text(-.02, dy[p], p, ha="right", va="center", fontsize=8.5,
                fontweight="bold")
    cols = [RED if "positive" in gmeta.get(g, "") else
            (BLUE if "negative" in gmeta.get(g, "") else GREY)
            for g in gene_list]
    ax.scatter([1] * len(gene_list), [gy[g] for g in gene_list], s=26, c=cols,
               zorder=3)
    for g in gene_list:
        ax.text(1.015, gy[g], g, ha="left", va="center", fontsize=7)

    # bracket and label each pathway block on the far right
    seen, start = None, 0
    for i, g in enumerate(gene_list + [None]):
        pw = pmeta.get(g) if g else None
        if pw != seen:
            if seen is not None and i - start >= 2:
                ax.plot([1.145, 1.145], [start - .3, i - 1 + .3], lw=1.6,
                        color="#8a97a5", zorder=2)
                ax.text(1.165, (start + i - 1) / 2,
                        seen if len(seen) < 42 else seen[:40] + "...",
                        ha="left", va="center", fontsize=7.2, color="#4a5a6a")
            seen, start = pw, i
    ax.set_xlim(-.36, 1.78)
    ax.axis("off")
    ax.set_title("Most coherent drugs and the progression genes they reach\n"
                 "red = gene rises with disease   blue = gene falls   "
                 "right-hand brackets = major fibrosis-associated process",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(f"{T4}/task4_network.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T4}/task4_network.png")




def task5_metapaths():
    """How many paths each metapath makes, and how much of that the cap removes.

    Log scale, because the span runs from 60 thousand to 14 million. The point
    of the figure is the pair of bars for MP4 and MP5: the same metapath shape
    through Reactome and through GO BP, where GO makes eleven times the paths
    and loses three quarters of them to a size cap that costs Reactome a fifth.
    """
    T5 = "Paper2_Results/Task5"
    c = pd.read_csv(f"{T5}/task5_metapath_counts.csv")
    raw = c[c.terms_filtered == "no"].set_index("metapath").paths
    cap = c[c.terms_filtered != "no"].set_index("metapath").paths
    order = [m for m in raw.index if m in cap.index]

    x = np.arange(len(order)); w = .38
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.bar(x - w/2, raw[order], w, color=GREY, label="all terms")
    ax.bar(x + w/2, cap[order], w, color=BLUE, label="terms capped to 5-200 genes")
    for i, m in enumerate(order):
        drop = 100 * (1 - cap[m] / raw[m])
        ax.text(i, max(raw[m], cap[m]) * 1.35, f"-{drop:.0f}%", ha="center",
                fontsize=8, color=RED if drop > 50 else "#5a6b7c",
                fontweight="bold" if drop > 50 else "normal")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace(" ", "\n", 1) for m in order], fontsize=8)
    ax.set_ylabel("paths (log scale)")
    ax.set_ylim(top=raw.max() * 9)
    ax.set_title("MetaPath size, and how much of it is annotation breadth\n"
                 "percentages = share of paths removed by the term-size cap",
                 fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper left", framealpha=.95)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{T5}/task5_metapath_sizes.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T5}/task5_metapath_sizes.png")


PURPLE_OK = "#6b4bd6"

if __name__ == "__main__":
    task2_actions()
    task2_null()
    task3_druggability()
    task4_coverage()
    task4_network()
    task5_metapaths()
