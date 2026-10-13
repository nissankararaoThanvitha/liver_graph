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
    # Computed, not typed. Three numbers were hardcoded here -- 1,072 genes,
    # 3,027 drugs and "1,005 edges, 11.2%". They were all still correct, but
    # the coverage-vs-coherence figure of -0.124 was hardcoded in the same
    # spirit and had silently gone stale, so these are derived now.
    n_genes, n_drugs = e.Gene_ID.nunique(), e.Drug_ID.nunique()
    n_dir = int(e.action_class.isin(["therapeutic-lowers",
                                     "therapeutic-raises"]).sum())
    pct_dir = 100 * n_dir / len(e)
    ax.set_title(f"What the {len(e):,} drug-gene edges are  "
                 f"({n_genes:,} genes, {n_drugs:,} drugs)",
                 fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate(f"only these two carry a usable direction: "
                f"{n_dir:,} edges, {pct_dir:.1f}%",
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



def task6_stability():
    """Why an exact top-50 is not defensible.

    The table reports a median of 29 of 50 top genes retained. That hides the
    spread, which is the actual finding: under 2,000 weightings drawn from the
    whole simplex the number ranges from the high teens to the low forties.
    Rank bands survive; a named top-50 does not.
    """
    T6 = "Paper2_Results/Task6"
    s = pd.read_csv(f"{T6}/task6_weight_sensitivity.csv")
    core = pd.read_csv(f"{T6}/task6_stable_core.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.1),
                                   gridspec_kw={"width_ratios": [1, 1.25]})

    y = np.arange(len(s))
    ax1.barh(y, s.median_top50_retained, .55, color=BLUE, label="median retained")
    for i, r in s.iterrows():
        ax1.plot([r.top50_retained_5th_pct, 50], [i, i], color="#8a97a5", lw=1.4,
                 zorder=1)
        ax1.plot(r.top50_retained_5th_pct, i, "|", color=RED, ms=11, mew=2)
        ax1.text(r.median_top50_retained + 1, i,
                 f"{int(r.median_top50_retained)}", va="center", fontsize=9)
    ax1.axvline(50, color="#15202b", lw=1, ls=":")
    ax1.text(50, len(s) - .35, " all 50", fontsize=8, color="#15202b")
    ax1.set_yticks(y); ax1.set_yticklabels(s.progression_class, fontsize=9)
    ax1.set_xlim(0, 58); ax1.set_xlabel("top-50 genes retained")
    ax1.set_title("How much of a top-50 survives a reweighting\n"
                  "red mark = 5th percentile across 2,000 weightings",
                  fontsize=9.5, loc="left")
    ax1.spines[["top", "right"]].set_visible(False)

    # the defensible alternative: genes that keep their place most of the time
    for cls, colour in zip(sorted(core.progression_class.unique()),
                           [BLUE, ORANGE, GREEN]):
        sub = core[core.progression_class == cls].nlargest(25, "top50_frequency")
        ax2.plot(range(1, len(sub) + 1), 100 * sub.top50_frequency.values,
                 marker="o", ms=3.5, lw=1.4, color=colour, label=cls)
    ax2.axhline(80, color=RED, ls="--", lw=1.2)
    ax2.text(24.5, 81.5, "80%", color=RED, fontsize=8, ha="right")
    ax2.set_xlabel("gene, ranked by stability within its class")
    ax2.set_ylabel("% of weightings keeping it in the top 50")
    ax2.set_ylim(0, 105)
    ax2.set_title("The stable core: genes that hold their place\n"
                  "regardless of how the components are weighted",
                  fontsize=9.5, loc="left")
    ax2.legend(fontsize=8, loc="lower left", framealpha=.95)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{T6}/task6_weight_stability.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T6}/task6_weight_stability.png")


def task7_consistency():
    """One group beats chance -- but only against the right baseline.

    Three numbers per group: what was observed, what the drug vocabulary gives
    for free (68% of directional drugs lower their target, so a rising gene is
    consistent 67.6% of the time by accident), and what a gene-level
    permutation gives. Eighteen numbers in a table; one glance as a figure.
    """
    T7 = "Paper2_Results/Task7"
    t = pd.read_csv(f"{T7}/task7_consistency_significance.csv")
    t = t.sort_values("observed_percent", ascending=False)

    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(10, 4.6))
    cols = [GREEN if v == "yes" else GREY for v in t.survives_gene_permutation]
    ax.barh(y, t.observed_percent, .52, color=cols, zorder=3, label="observed")
    ax.scatter(t.expected_from_vocabulary, y, marker="D", s=42, color=ORANGE,
               zorder=4, label="expected from the drug vocabulary")
    ax.scatter(t.gene_permutation_null, y, marker="o", s=42,
               facecolor="white", edgecolor=RED, lw=1.6, zorder=4,
               label="gene-permuted null")

    # Labels sit inside the bar: outside they collide with the two marker
    # series, and the markers are the comparison the figure exists to show.
    for i, r in enumerate(t.itertuples()):
        inside = r.observed_percent > 25
        ax.text(r.observed_percent - 1.5 if inside else r.observed_percent + 1.5,
                i, f"{r.observed_percent:.1f}%",
                va="center", ha="right" if inside else "left", fontsize=8.5,
                color="white" if inside else "#15202b",
                fontweight="bold" if r.survives_gene_permutation == "yes" else "normal")
        if r.survives_gene_permutation == "yes":
            ax.text(r.observed_percent + 2, i, f"p = {r.gene_permutation_p}",
                    va="center", fontsize=8, color=GREEN, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(t.paper1_group, fontsize=9)
    ax.set_xlabel("reversal-consistent relationships (%)")
    ax.set_xlim(0, 100)
    ax.set_title("Only one group beats its own null\n"
                 "green = survives a gene-level permutation; the baseline is "
                 "not 50%", fontsize=10, loc="left", pad=26)
    ax.legend(fontsize=8, ncol=3, framealpha=.95,
              loc="lower center", bbox_to_anchor=(.5, 1.02))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{T7}/task7_consistency_vs_null.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T7}/task7_consistency_vs_null.png")


PURPLE_OK = "#6b4bd6"

def task1_gene_set():
    """Task 1 had no figure, which left the starting set as three numbers in a
    README. Two panels: what the 6,222 genes are, and what the shared class
    actually looks like when both ladders are plotted against each other.

    The right panel is the one worth having. 1,822 genes move on both ladders,
    and the interesting claim is not that they agree -- it is that 30 of them
    disagree on direction, which a bar chart cannot show at all.
    """
    t = pd.read_csv(f"{T1}/Paper2_progression_genes.csv", low_memory=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.4),
                                   gridspec_kw={"width_ratios": [1, 1.15]})

    # ---- panel A: the three classes, split by direction -------------------
    classes = [("fibrosis-only", "fibrosis_direction"),
               ("inflammation-only", "inflammation_direction"),
               ("both", None)]
    labels, rises, falls, mixed = [], [], [], []
    for cls, dcol in classes:
        sub = t[t.progression_class == cls]
        shown = "shared" if cls == "both" else cls          # never print "both"
        labels.append(f"{shown}\nn={len(sub):,}")
        if dcol:
            rises.append(int((sub[dcol] == "increasing").sum()))
            falls.append(int((sub[dcol] == "decreasing").sum()))
            mixed.append(0)
        else:
            f, i = sub.fibrosis_direction, sub.inflammation_direction
            rises.append(int(((f == "increasing") & (i == "increasing")).sum()))
            falls.append(int(((f == "decreasing") & (i == "decreasing")).sum()))
            mixed.append(int((f != i).sum()))

    x = np.arange(len(labels))
    b1 = ax1.bar(x, rises, color=BLUE, width=.6, label="rises as disease worsens")
    b2 = ax1.bar(x, falls, bottom=rises, color=ORANGE, width=.6,
                 label="falls as disease worsens")
    b3 = ax1.bar(x, mixed, bottom=np.array(rises) + np.array(falls),
                 color=RED, width=.6, label="disagrees between ladders")
    for xi, (r, f, m) in enumerate(zip(rises, falls, mixed)):
        if r: ax1.text(xi, r/2, f"{r:,}", ha="center", color="white", fontsize=9)
        if f: ax1.text(xi, r + f/2, f"{f:,}", ha="center", color="white", fontsize=9)
        if m: ax1.text(xi, r + f + m + 60, f"{m}", ha="center", color=RED,
                       fontsize=9, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("genes")
    ax1.set_title(f"The starting set: {len(t):,} progression genes",
                  fontsize=10, loc="left")
    ax1.legend(fontsize=7.6, framealpha=.95, loc="upper left")
    ax1.spines[["top", "right"]].set_visible(False)

    # ---- panel B: the two ladders against each other ----------------------
    sh = t[t.progression_class == "both"]
    disc = sh[sh.fibrosis_direction != sh.inflammation_direction]
    agree = sh[sh.fibrosis_direction == sh.inflammation_direction]
    ax2.axhline(0, color=GREY, lw=.8)
    ax2.axvline(0, color=GREY, lw=.8)
    ax2.scatter(agree.fibrosis_rho, agree.inflammation_rho, s=7,
                color=BLUE, alpha=.32, linewidths=0,
                label=f"agree on direction  ({len(agree):,})")
    ax2.scatter(disc.fibrosis_rho, disc.inflammation_rho, s=30, color=RED,
                edgecolor="#15202b", linewidths=.6,
                label=f"disagree  ({len(disc)})", zorder=3)
    ax2.set_xlabel("fibrosis rho  (F0 to F4)")
    ax2.set_ylabel("inflammation rho  (control to NASH)")
    ax2.set_title(f"The {len(sh):,} shared genes, and the {len(disc)} that "
                  "disagree", fontsize=10, loc="left")
    ax2.legend(fontsize=8, framealpha=.95, loc="upper left")
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(f"{T1}/task1_gene_set.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T1}/task1_gene_set.png")


def task8_candidates():
    """Task 8 had no figure either, which is the worst place to lack one: the
    headline result is that thirty candidates reach only two genes, and a
    thirty-row table makes the list look more diverse than it is. The figure
    exists to make that collapse impossible to miss.
    """
    T8 = "Paper2_Results/Task8"
    lc = pd.read_csv(f"{T8}/task8_leading_candidates.csv", low_memory=False)

    by_target = lc.best_target.value_counts()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.6),
                                   gridspec_kw={"width_ratios": [.8, 1.25]})

    # ---- panel A: thirty candidates, two targets -------------------------
    cols = [BLUE, ORANGE, GREEN, GREY][:len(by_target)]
    bars = ax1.bar(np.arange(len(by_target)), by_target.values, color=cols,
                   width=.58)
    for b, v in zip(bars, by_target.values):
        ax1.text(b.get_x() + b.get_width()/2, v + .35, f"{v} drugs",
                 ha="center", fontsize=9, fontweight="bold")
    ax1.set_xticks(np.arange(len(by_target)))
    ax1.set_xticklabels(by_target.index, fontsize=10)
    ax1.set_ylabel("leading candidates")
    ax1.set_ylim(0, max(by_target.values) * 1.25)
    ax1.set_title(f"{len(lc)} candidates reach {len(by_target)} targets",
                  fontsize=10, loc="left")
    ax1.spines[["top", "right"]].set_visible(False)

    # ---- panel B: mechanism support, which mostly is not there -----------
    lc2 = lc.sort_values("mechanism_consistent_rate", ascending=True)
    y = np.arange(len(lc2))
    known = lc2.n_mechanism_consistent + lc2.n_mechanism_inconsistent
    ax2.barh(y, lc2.n_mechanism_unknown, color=GREY, height=.74,
             label="direction not recorded")
    ax2.barh(y, lc2.n_mechanism_consistent, left=lc2.n_mechanism_unknown,
             color=GREEN, height=.74, label="reversal-consistent")
    ax2.barh(y, lc2.n_mechanism_inconsistent,
             left=lc2.n_mechanism_unknown + lc2.n_mechanism_consistent,
             color=RED, height=.74, label="reversal-inconsistent")
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{d[:22]}  ({t})" for d, t in
                         zip(lc2.Drug, lc2.best_target)], fontsize=6.4)

    # One drug has 82 targets and would flatten the other 29 into nothing. Cap
    # the axis and label it instead of letting it dominate: that drug is
    # FOSTAMATINIB, the promiscuous kinase inhibitor the Task 8 tie-break fix
    # demoted, so the outlier IS the point rather than a nuisance.
    cap = int(np.percentile(lc2.n_targets, 90)) + 4
    big = lc2[lc2.n_targets > cap]
    ax2.set_xlim(0, cap)
    for yi, (_, r) in zip(y, lc2.iterrows()):
        if r.n_targets > cap:
            ax2.text(cap * .985, yi, f"  {int(r.n_targets)} targets →",
                     va="center", ha="right", fontsize=7, color="#15202b",
                     fontweight="bold")
    ax2.set_xlabel("drug-target relationships"
                   + (f"   (axis capped at {cap}; "
                      f"{len(big)} drug exceeds it)" if len(big) else ""))
    ax2.set_title("Mechanism evidence per candidate\n"
                  f"grey dominates: {int(lc.n_mechanism_unknown.sum()):,} of "
                  f"{int(lc.n_targets.sum()):,} relationships record no direction",
                  fontsize=10, loc="left")
    ax2.legend(fontsize=7.6, framealpha=.95, loc="lower right")
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(f"{T8}/task8_candidates.png", dpi=200)
    plt.close(fig)
    print(f"wrote {T8}/task8_candidates.png")


if __name__ == "__main__":
    task1_gene_set()
    task2_actions()
    task2_null()
    task3_druggability()
    task4_coverage()
    task4_network()
    task5_metapaths()
    task6_stability()
    task7_consistency()
    task8_candidates()
