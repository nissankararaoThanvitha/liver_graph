"""Rank fibrosis-associated genes using complementary evidence features.

P/T/X/F/B scores and cutoff constants are unchanged. Input discovery, stage
profiles, clusters, transitions and enrichment use corrected patient handling.
These features share data and are not independent validation experiments.
Select Tier1 at score>=7. Top25 is five Tier1 genes per cluster, descending
score then absolute rho; alternative cluster-top-score list is not selected.
LOSO is merged after refitting and is deliberately not part of the score.
"""
import pathlib
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
import argparse as _argparse
import sys as _sys

_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default=None,
                 help="folder for this script's own numbered outputs")
_ap.add_argument("--results", default=None,
                 help="Paper1_Results folder to read Task2/3/4 from")
_args, _rest = _ap.parse_known_args()
_sys.argv = [_sys.argv[0]] + _rest
# These scripts used to live inside the results folder, so HERE was
# both 'where the code is' and 'where results go'. They now live in
# scripts/, so the output location has to be named rather than
# inherited from the file's own position.
HERE = (pathlib.Path(_args.out).resolve() if _args.out
        else ROOT / "Paper1_HighConfidence")
HERE.mkdir(parents=True, exist_ok=True)
RESULTS = pathlib.Path(_args.results) if _args.results else ROOT / "Paper1_Results"


STAGE_FILE = ROOT / "data/for_mentor/genes_by_fibrosis_stage.csv"
CLUSTERS = RESULTS / "Task2/task2_gene_clusters.csv"
TRANSITION_FILE = RESULTS / "Task3/task3_all_genes_all_transitions.csv"
MATCHED_FILE = HERE / "05_powermatched_per_gene.csv"
ENRICHMENT_FILE = RESULTS / "Task4/task4_all_significant.csv"

STAGES = ["F0", "F1", "F2", "F3", "F4"]
# Derived from the input, not hardcoded. The literal 3645 was the v1
# count; the corrected pipeline gives 3,681 and the assertion below
# then fired on a correct run. The check still does its job -- it
# catches a join that silently drops or duplicates genes -- but the
# expected number now comes from the data rather than from memory.
N_FIBROSIS_GENES = None  # set in master_table() from the stage file


# ---------------------------------------------------------------- step 1
def master_table():
    """One row per fibrosis-associated gene, every known column attached.

    Nothing is computed here. Tasks 1-4 already produced all of these numbers;
    they just live in different files. This is the single sheet every scoring
    step afterwards reads from.

    The fibrosis set is ladder in {fibrosis_only, both} -- 1,953 + 1,692 =
    3,645. Those are the same genes the TRACKS_FIBROSIS edges carry in the
    graph and the same genes Task 2 clustered. The 1,047 inflammation-only
    genes are left out: they do not track fibrosis.

    A silent bad join here would corrupt every later score while still looking
    like a valid table, so the three assertions below stop the run instead.
    """
    g = pd.read_csv(STAGE_FILE)
    g = g[g.ladder.isin(["fibrosis_only", "both"])].copy()
    g["fibrosis_specificity"] = np.where(
        g.ladder.eq("fibrosis_only"), "fibrosis_only", "shared")
    g = g.rename(columns={f"stage_{i}": f"F{i}" for i in range(5)})

    c = pd.read_csv(CLUSTERS)[["ensembl_id", "cluster", "cluster_name",
                               "membership_confidence"]]
    c["cluster"] = "C" + c.cluster.astype(str)

    m = g.merge(c, on="ensembl_id", how="left", validate="1:1")

    expected = len(g)
    assert len(m) == expected, (
        f"join changed the row count: {expected:,} fibrosis genes in "
        f"but {len(m):,} out")
    assert m.cluster.notna().all(), "gene with no trajectory cluster"
    assert (m.fibrosis_q < 0.05).all(), "gene failing the entry FDR"

    cols = (["ensembl_id", "symbol", "fibrosis_rho", "fibrosis_q",
             "inflammation_rho", "inflammation_q", "fibrosis_specificity"]
            + STAGES + ["cluster", "cluster_name", "membership_confidence",
                        "n_studies"])
    return m[cols]


# ---------------------------------------------------------------- step 2
# C1-C3 are rising shapes, C4-C5 falling ones (Task 2 cluster means). Kept as
# background support only -- the cluster never overrules the sign of rho.
CLUSTER_DIRECTION = {"C1": "increasing", "C2": "increasing", "C3": "increasing",
                     "C4": "decreasing", "C5": "decreasing"}


def assign_direction(t):
    """Label each gene increasing or decreasing with fibrosis stage.

    Three numbers in the table hint at direction and they can disagree, so
    they are ranked rather than combined:

      1. sign(fibrosis_rho)  DECIDES. Fitted across all 668 staged patients
         within study, so it is the steadiest estimate available.
      2. sign(Delta_F0_F4)   CHECKS. Reads only the stage-0 and stage-4 means
         and ignores the three stages between them; F4 is the smallest stage
         group, so the endpoint is the wobbly one. Disagreement flags the
         gene. It does not relabel it and does not remove it.
      3. cluster C1-C5       SUPPORTS. Recorded, never decisive.

    Deliberately not called up/downregulated. That phrasing means a
    differential-expression comparison between two groups, which is not what
    was done: this is a correlation along an ordered stage ladder. The column
    carries the words the manuscript should use.
    """
    t = t.copy()
    t["direction"] = np.where(t.fibrosis_rho > 0, "increasing", "decreasing")
    t["delta_F0_F4"] = (t.F4 - t.F0).round(3)
    t["delta_direction"] = np.where(t.delta_F0_F4 > 0, "increasing", "decreasing")
    t["cluster_direction"] = t.cluster.map(CLUSTER_DIRECTION)
    t["delta_agrees"] = t.delta_direction == t.direction
    t["cluster_agrees"] = t.cluster_direction == t.direction
    return t


# ---------------------------------------------------------------- step 3
# FROZEN before any ranked list was inspected.
RHO_STRONG, RHO_MODERATE = 0.40, 0.30
# Reported only. These never change a score; they exist so the paper can state
# how much the shortlist depends on the choice above instead of hoping nobody
# asks.
RHO_SENSITIVITY = [(0.35, 0.25), (0.40, 0.30), (0.45, 0.35)]


def score_progression(t):
    """P in 0-2: how steeply the gene follows the fibrosis stages.

        |rho| >= 0.40  ->  2
        |rho| >= 0.30  ->  1
        otherwise      ->  0

    Size of rho, not its sign -- direction was settled in step 2, and a gene
    at -0.55 is exactly as strong as one at +0.55.

    Not scored on the p-value: every gene here already passes fibrosis
    FDR < 0.05, which is how it entered the set, so ranking by q-value would
    re-read the same test. Effect size is what still separates them. A gene
    can be very certainly weak.

    Buckets, not a ranking. Hundreds of genes share each score on purpose;
    P is one of five and is added to the rest, so a gene scoring 0 here can
    still reach the shortlist on the other four.
    """
    t = t.copy()
    a = t.fibrosis_rho.abs()
    t["abs_rho"] = a.round(3)
    t["P"] = np.select([a >= RHO_STRONG, a >= RHO_MODERATE], [2, 1], default=0)
    return t


def rho_sensitivity(t):
    """How many genes each plausible cutoff pair would have awarded."""
    a = t.fibrosis_rho.abs()
    rows = []
    for strong, moderate in RHO_SENSITIVITY:
        rows.append({
            "strong_cutoff": strong, "moderate_cutoff": moderate,
            "n_P2": int((a >= strong).sum()),
            "n_P1": int(((a >= moderate) & (a < strong)).sum()),
            "n_P0": int((a < moderate).sum()),
            "frozen_choice": (strong, moderate) == (RHO_STRONG, RHO_MODERATE),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- step 4
# FROZEN before any ranked list was inspected.
# value_z is expression standardised per gene within each study, so
# Delta_F0_F4 is already in standard deviations: 1.0 means the gene travels a
# full SD across the disease. 1.0 and 0.5 are the conventional large and
# moderate effect anchors, not quantiles read off this distribution.
DELTA_STRONG, DELTA_MODERATE = 1.0, 0.5
DELTA_SENSITIVITY = [(0.8, 0.4), (1.0, 0.5), (1.2, 0.6)]


def score_trajectory(t):
    """T in 0-2: how far the gene travels from stage 0 to stage 4.

        direction disagrees with step 2  ->  0   (checked first)
        |Delta_F0_F4| >= 1.0 SD          ->  2
        |Delta_F0_F4| >= 0.5 SD          ->  1
        otherwise                        ->  0

    Disagreement is read before magnitude on purpose: if a gene is labelled
    increasing and its F4 sits below its F0, a large move is evidence against
    the gene, not for it.

    Quantitative by construction -- no cluster is called strong or weak by
    looking at its plot.

    Known bias, left visible rather than tuned away: this reads only the two
    endpoints and ignores F1-F3, so a gene that rises sharply at F0->F1 and
    then flattens has a real early trajectory but a small F4-F0, and scores
    low. T therefore favours late-changing genes. Step 5 is the corrective --
    it finds the largest jump wherever it happens.
    """
    t = t.copy()
    a = t.delta_F0_F4.abs()
    t["T"] = np.where(
        ~t.delta_agrees, 0,
        np.select([a >= DELTA_STRONG, a >= DELTA_MODERATE], [2, 1], default=0))
    return t


def delta_sensitivity(t):
    """How many genes each plausible cutoff pair would have awarded."""
    a, ok = t.delta_F0_F4.abs(), t.delta_agrees
    rows = []
    for strong, moderate in DELTA_SENSITIVITY:
        rows.append({
            "strong_cutoff": strong, "moderate_cutoff": moderate,
            "n_T2": int((ok & (a >= strong)).sum()),
            "n_T1": int((ok & (a >= moderate) & (a < strong)).sum()),
            "n_T0": int((~ok | (a < moderate)).sum()),
            "frozen_choice": (strong, moderate) == (DELTA_STRONG, DELTA_MODERATE),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- step 5
# FROZEN before any ranked list was inspected. The first two are Task 3's own
# thresholds for "substantially changing", so X does not invent a second
# standard. The third is a simple majority of the 50 equal-power draws.
TRANS_Q, TRANS_BETA, MATCHED_FRAC = 0.05, 0.2, 0.5


def score_transition(t):
    """X in 0-2 from the gene's single largest stage transition.

    T measured how far the gene travels end to end and is blind to where the
    move happens. X finds the largest of the four consecutive jumps -- F0->F1,
    F1->F2, F2->F3, F3->F4 -- and asks whether it holds up.

    Two independent pieces of evidence about that jump:

      full-patient fit   value_z ~ stage + study on all available patients:
                         is it statistically real and substantial
                         (q < 0.05 and |beta| >= 0.2)?
      matched draws      in >= 50% of 50 equal-power redraws, did the jump
                         stay big and keep its direction?

        both            ->  2
        exactly one     ->  1
        neither         ->  0

    Why reproducibility rather than matched significance. The matched design
    cuts every stage to 30 patients to make the comparison fair, then corrects
    across 3,645 genes. Measured, not assumed: significance in >= 50% of draws
    is reached by 0, 0, 0 and 297 genes at the four transitions. Scoring on it
    would hand every available point to F3->F4 and exclude the earlier
    transitions outright, which is the opposite of preserving early biology.
    Reproducibility answers the same question -- a fluke depends on which
    patients were drawn, so redrawing kills it -- and the design can deliver
    it: 1,522 / 1,856 / 1,713 / 2,790 genes. The strict count is carried into
    the final table as its own column, scoring nothing: it is evidence about
    this study's power, not about these genes.

    The winning transition is kept as a column so step 9 can check the
    shortlist did not collapse onto F3->F4.
    """
    x = pd.read_csv(TRANSITION_FILE)
    x["abs_beta"] = x.beta_adjusted.abs()
    # one row per gene: its largest-magnitude transition
    best = x.loc[x.groupby("ensembl_id").abs_beta.idxmax()]

    mt = pd.read_csv(MATCHED_FILE)
    best = best.merge(mt, on=["ensembl_id", "transition"], how="left",
                      validate="1:1")
    assert best.matched_frac_reproducible.notna().all(), "gene missing matched result"

    full_ok = (best.q_value < TRANS_Q) & (best.abs_beta >= TRANS_BETA)
    matched_ok = best.matched_frac_reproducible >= MATCHED_FRAC
    best = best.assign(
        X=np.select([full_ok & matched_ok, full_ok ^ matched_ok], [2, 1],
                    default=0),
        full_fit_substantial=full_ok, matched_reproducible=matched_ok)

    best = best[["ensembl_id", "transition", "beta_adjusted", "q_value",
                 "matched_frac_reproducible", "matched_frac_significant",
                 "full_fit_substantial", "matched_reproducible", "X"]].rename(
        columns={"transition": "largest_transition",
                 "beta_adjusted": "transition_beta",
                 "q_value": "transition_q"})
    m = t.merge(best, on="ensembl_id", how="left", validate="1:1")
    assert m.X.notna().all(), "gene with no transition result"
    m["X"] = m.X.astype(int)
    return m


# ---------------------------------------------------------------- step 6
def score_specificity(t):
    """F in 0-1: 1 if the gene tracks fibrosis only, 0 if shared.

    Worth one point where the others are worth two, deliberately. The other
    four scores measure how strong the evidence is; this one measures what
    kind of gene it is. At two points a weak fibrosis-only gene could outrank
    a strong shared one, which is not the intent. One point makes it a
    tie-breaker, which is its proper weight.

    A bonus, never a filter. Shared genes keep every other point they earn --
    a gene rising with both scarring and inflammation may well be the more
    important one, sitting where inflammation turns into scarring. It just
    starts one point behind. Whether that is too heavy is checked against the
    final tiers in step 9: if Tier 1 comes back all fibrosis-only, F is doing
    more work than one point should.
    """
    t = t.copy()
    t["F"] = (t.fibrosis_specificity == "fibrosis_only").astype(int)
    return t


# ---------------------------------------------------------------- step 7
DATABASES = ["GO_BP", "KEGG", "Reactome", "Hallmark"]
# FROZEN: a gene is checked against the enrichment of its own peers by two
# routes, its Task 1 group and its trajectory cluster, and either counts.
# The "_all" cluster groups, not "_core": core is the subset with cluster
# membership confidence >= 0.8, which answers a different question and would
# double-count the same genes.
CLUSTER_GROUP = "{cluster}_all"


def score_biology(t):
    """B in 0-2: in how many of four databases the gene sits in an ENRICHED
    process.

        >= 2 databases  ->  2
        1 database      ->  1
        none            ->  0

    Enriched, not merely present. Almost every gene in the genome belongs to
    some GO term, so membership of any pathway would score 3,645 genes at 2
    and separate nothing. Task 4 found the processes that are
    over-represented among fibrosis genes against the 14,794-gene eligible
    background; only those count.

    All 3,532 significant terms are used, not the top-N display tables -- a
    gene should not score 0 because its process missed a summary list.

    Capped at 2, and deliberately not worth 4. GO, KEGG and Reactome all
    describe collagen biology: a collagen gene found in three of them has
    been confirmed once by three textbooks drawing on the same underlying
    biology, not three independent times. B says "this gene has a biological
    story", and nothing stronger.

    Known weak spot, left visible: C4 (mid decrease) has only 10 enriched
    terms in total across all four databases, so its genes depend almost
    entirely on the Task 1 group route. C4 is also the weakest cluster on T.
    Step 9 counts how many C4 genes reach Tier 1 rather than assuming the
    shortlist is balanced.
    """
    e = pd.read_csv(ENRICHMENT_FILE)
    # group x database -> set of genes named in any significant term
    members = {}
    for (grp, db), sub in e.groupby(["group", "database"]):
        s = set()
        for g in sub.genes.dropna():
            s.update(x.strip() for x in g.split(","))
        members[(grp, db)] = s

    # route 1: the Task 1 group, defined exactly as Task 4 defined it
    f, i = t.fibrosis_rho, t.inflammation_rho
    task1_group = np.select(
        [(t.fibrosis_specificity == "fibrosis_only") & (f > 0),
         (t.fibrosis_specificity == "fibrosis_only") & (f < 0),
         (t.fibrosis_specificity == "shared") & (f > 0) & (i > 0),
         (t.fibrosis_specificity == "shared") & (f < 0) & (i < 0)],
        ["fibrosis_only_up", "fibrosis_only_down", "shared_up", "shared_down"],
        default="")   # the one discordant shared gene has no Task 1 group
    # route 2: the trajectory cluster
    cluster_group = [CLUSTER_GROUP.format(cluster=c) for c in t.cluster]

    t = t.copy()
    t["task1_group"] = task1_group
    for db in DATABASES:
        t[db] = [
            (sym in members.get((g1, db), ())) or (sym in members.get((g2, db), ()))
            for sym, g1, g2 in zip(t.symbol, task1_group, cluster_group)]
    t["n_databases"] = t[DATABASES].sum(axis=1)
    t["B"] = np.select([t.n_databases >= 2, t.n_databases == 1], [2, 1],
                       default=0)
    return t


# ---------------------------------------------------------------- step 8
SCORES = ["P", "T", "X", "F", "B"]
# FROZEN. Administrative lines, not biology: nothing changes in a cell at 7
# points. Their virtue is being visible, so a reader can disagree and move
# them. Sensitivity to exactly that is measured below.
TIER1_MIN, TIER2_MIN = 7, 5


def total_score(t):
    """HighConfidenceScore = P + T + X + F + B, max 9, then three tiers.

    Unweighted on purpose. Weighting would need a principled reason for each
    multiplier and there is none; a plain sum says only "how many kinds of
    evidence agree", which is the question being asked.

    Tier 1 (7-9) cannot be reached on one strong number. A gene with a steep
    correlation but no reproducible jump and no biology caps out near 5. That
    is the whole design: the score rewards agreement across evidence types,
    not excellence on any single one.
    """
    t = t.copy()
    t["HighConfidenceScore"] = t[SCORES].sum(axis=1)
    t["tier"] = np.select(
        [t.HighConfidenceScore >= TIER1_MIN, t.HighConfidenceScore >= TIER2_MIN],
        ["Tier 1 - high confidence", "Tier 2 - moderate confidence"],
        default="Tier 3")
    return t


def tier_sensitivity(t):
    """How Tier 1 membership moves if the line is drawn one point either way.

    Required by the brief: the main candidates should not change drastically
    under reasonable threshold choices. Reported, never acted on.
    """
    base = set(t.ensembl_id[t.HighConfidenceScore >= TIER1_MIN])
    rows = []
    for cut in (6, 7, 8):
        s = set(t.ensembl_id[t.HighConfidenceScore >= cut])
        rows.append({
            "tier1_cutoff": cut, "n_genes": len(s),
            "shared_with_frozen": len(s & base),
            "pct_of_frozen_retained": (round(100 * len(s & base) / len(base), 1)
                                       if base else np.nan),
            "frozen_choice": cut == TIER1_MIN,
        })
    return pd.DataFrame(rows)


def leave_one_score_out(t):
    """Recompute the total five times, dropping one score each time.

    Not in the brief. It is here because it tests this method's central claim
    directly: if dropping one score reshuffles the top of the list, that score
    was driving the ranking and "five independent evidence types" means less
    than it sounds. Spearman correlation of the full ranking against each
    reduced one, plus overlap of the top 50.
    """
    def top_band(ids, s, n=50):
        """Highest-scoring genes down to the score that first reaches n.

        Not "the top 50": the scores are small integers, so hundreds of genes
        tie at every value and any top-n cut would be split arbitrarily
        mid-tie. The band therefore includes every gene at the cutting score,
        and its size is reported rather than assumed.
        """
        cut = s.sort_values(ascending=False).iloc[:n].min()
        return set(ids[s >= cut])

    full = t[SCORES].sum(axis=1)
    top_full = top_band(t.ensembl_id, full)
    rows = []
    for drop in SCORES:
        kept = [s for s in SCORES if s != drop]
        red = t[kept].sum(axis=1)
        top_red = top_band(t.ensembl_id, red)
        rows.append({
            "score_dropped": drop,
            "spearman_vs_full": round(full.corr(red, method="spearman"), 3),
            "n_top_band_full": len(top_full),
            "n_top_band_reduced": len(top_red),
            "overlap": len(top_full & top_red),
            "jaccard": round(len(top_full & top_red)
                             / len(top_full | top_red), 3),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- step 9a
def audit_tier1(t):
    """Profile the Tier 1 genes before any shortlist rule is chosen.

    The brief asks, in this order, to EXAMINE whether the Tier 1 list carries
    both increasing and decreasing programmes and several trajectory
    patterns, and only then to select. So this reports composition and
    selects nothing. The scoring rules are already frozen and cannot move;
    what is still open is how to sample from the 507.

    Pathway dominance is counted here too, against the brief's specific
    worry: a shortlist that is entirely extracellular matrix would be true
    and useless.
    """
    t1 = t[t.tier.str.startswith("Tier 1")].copy()
    out = {"n": len(t1)}
    out["direction"] = t1.direction.value_counts()
    out["cluster"] = (t1.groupby(["cluster", "cluster_name"]).size()
                      .rename("tier1_genes").reset_index())
    out["cluster"]["all_fibrosis_genes"] = [
        int((t.cluster == c).sum()) for c in out["cluster"].cluster]
    out["cluster"]["pct_of_cluster"] = (
        100 * out["cluster"].tier1_genes
        / out["cluster"].all_fibrosis_genes).round(1)
    out["transition"] = t1.largest_transition.value_counts().sort_index()
    out["specificity"] = t1.fibrosis_specificity.value_counts()
    out["score"] = t1.HighConfidenceScore.value_counts().sort_index()
    return t1, out


def pathway_dominance(t1, top_n=15):
    """Which enriched processes the Tier 1 genes actually sit in.

    Counts each significant term from Task 4 that names a Tier 1 gene, so a
    shortlist dominated by one programme is visible as a number rather than
    an impression.
    """
    e = pd.read_csv(ENRICHMENT_FILE)
    syms = set(t1.symbol)
    rows = []
    for _, r in e.iterrows():
        if pd.isna(r.genes):
            continue
        hit = syms & {x.strip() for x in r.genes.split(",")}
        if hit:
            rows.append({"database": r.database, "term": r.term_label,
                         "n_tier1_genes": len(hit)})
    d = (pd.DataFrame(rows)
         .groupby(["database", "term"], as_index=False).n_tier1_genes.max()
         .sort_values("n_tier1_genes", ascending=False))
    d["pct_of_tier1"] = (100 * d.n_tier1_genes / len(t1)).round(1)
    return d.head(top_n).reset_index(drop=True), d


# ---------------------------------------------------------------- step 9b
# Two selection rules, both built so the mentor can compare them. Neither
# lowers the Tier 1 bar: only the sampling differs, never the quality
# threshold.
TOP_K = 5   # the largest k at which all five clusters still contribute k:
            # C4 has exactly 5 Tier 1 genes, C3 has 6. Beyond k=5 only
            # C1/C2/C5 can grow, so a larger set is a less balanced one.

SHORTLIST_COLS = [
    "symbol", "ensembl_id", "cluster", "cluster_name", "direction",
    "fibrosis_specificity", "fibrosis_rho", "fibrosis_q", "delta_F0_F4",
    "largest_transition", "transition_beta", "transition_q",
    "matched_frac_reproducible", "matched_frac_significant",
    "GO_BP", "KEGG", "Reactome", "Hallmark", "n_databases",
    "P", "T", "X", "F", "B", "HighConfidenceScore", "tier",
] + STAGES


def shortlist_a(t1, k=TOP_K):
    """Option A -- top k Tier 1 genes per cluster, ties broken by |rho|.

    Equal cells, the same reasoning the power-matched design already uses:
    the quota is set by the limiting group rather than chosen. C2 is capped
    at k despite having 333 qualifying genes; C4 contributes everything it
    has. The cap is the point -- without it C2 takes the list.
    """
    out = (t1.sort_values(["HighConfidenceScore", "abs_rho"],
                          ascending=[False, False])
             .groupby("cluster", group_keys=False).head(k))
    return out.sort_values(["cluster", "HighConfidenceScore", "abs_rho"],
                           ascending=[True, False, False])


def shortlist_b(t1):
    """Option B -- every Tier 1 gene at its own cluster's top score.

    Lets each cluster contribute as many as it genuinely supports. In
    practice that is not the diversity-preserving choice it sounds like:
    a cluster with many genes sitting at one score contributes all of them,
    so the count follows cluster size rather than biological breadth.
    """
    top = t1.groupby("cluster").HighConfidenceScore.transform("max")
    out = t1[t1.HighConfidenceScore == top]
    return out.sort_values(["cluster", "HighConfidenceScore", "abs_rho"],
                           ascending=[True, False, False])


def shortlist_profile(name, s, t1):
    """One row summarising what a shortlist actually contains."""
    e = pd.read_csv(ENRICHMENT_FILE)
    syms = set(s.symbol)
    best_term, best_n = "", 0
    for _, r in e.iterrows():
        if pd.isna(r.genes):
            continue
        n = len(syms & {x.strip() for x in r.genes.split(",")})
        if n > best_n:
            best_term, best_n = r.term_label, n
    return {
        "option": name, "n_genes": len(s),
        **{f"n_{c}": int((s.cluster == c).sum())
           for c in sorted(t1.cluster.unique())},
        "n_increasing": int((s.direction == "increasing").sum()),
        "n_decreasing": int((s.direction == "decreasing").sum()),
        "n_fibrosis_only": int((s.fibrosis_specificity == "fibrosis_only").sum()),
        "n_shared": int((s.fibrosis_specificity == "shared").sum()),
        **{f"n_{tr}": int((s.largest_transition == tr).sum())
           for tr in ["F0→F1", "F1→F2", "F2→F3", "F3→F4"]},
        "min_score": int(s.HighConfidenceScore.min()),
        "max_score": int(s.HighConfidenceScore.max()),
        "top_pathway": best_term,
        "top_pathway_n": best_n,
        "top_pathway_pct": round(100 * best_n / len(s), 1),
    }


# ---------------------------------------------------------------- step 11
LOSO_FILE = HERE / "10_loso_summary.csv"

# The column list the brief asks for, in its order, with three additions.
FINAL_COLS = [
    ("symbol", "Gene"),
    ("ensembl_id", "Ensembl_ID"),
    ("fibrosis_rho", "Fibrosis_rho"),
    ("fibrosis_q", "Fibrosis_q_FDR"),
    ("direction", "Direction"),
    ("fibrosis_specificity", "Fibrosis_only_or_shared"),
    ("cluster", "Cluster"),
    ("cluster_name", "Cluster_pattern"),
    ("F0", "F0"), ("F1", "F1"), ("F2", "F2"), ("F3", "F3"), ("F4", "F4"),
    ("delta_F0_F4", "Delta_F0_F4"),
    ("largest_transition", "Largest_transition"),
    ("transition_beta", "Transition_beta"),
    ("transition_q", "Transition_q"),
    # addition 1: the matched evidence, both halves, scored and unscored
    ("matched_frac_reproducible", "Matched_frac_reproducible_scored"),
    ("matched_frac_significant", "Matched_frac_significant_NOT_scored"),
    ("GO_BP", "GO"), ("KEGG", "KEGG"), ("Reactome", "Reactome"),
    ("Hallmark", "Hallmark"), ("n_databases", "N_databases"),
    ("P", "P"), ("T", "T"), ("X", "X"), ("F", "F"), ("B", "B"),
    ("HighConfidenceScore", "Total_score"),
    ("tier", "Tier"),
    # addition 2: LOSO as three measures, not one -- direction cannot fail.
    # Plain integers, with the denominator in the column name: written as
    # "5/5" Excel silently reads the value as a date and shows 05-May.
    ("loso_direction_kept", "LOSO_direction_kept_of_5_guaranteed"),
    ("loso_still_significant", "LOSO_still_significant_of_5"),
    ("loso_still_strong", "LOSO_still_strong_rho0.30_of_5"),
    ("loso_min_median_rho", "LOSO_weakest_median_rho"),
    ("loso_pct_drop", "LOSO_max_pct_drop_in_rho"),
]


def final_table(t):
    """Assemble the brief's output table. No new analysis, only assembly.

    Three additions to the requested columns, each one a caveat this analysis
    uncovered and should not hide:

      LOSO as three measures rather than one. Every Tier 1 gene already has
      all five studies agreeing on direction, so the brief's R is 5/5 by
      arithmetic for every gene. Reporting that single number would read as
      validation when nothing was tested. Significance and strength can fail,
      so they are reported beside it, with the largest percentage drop in
      median rho across the five runs -- the measure that separates MYC
      (2.6%) from TPM4 (27.6%), which the direction test scores identically.

      Both matched columns, the scored and the unscored. Reproducibility is
      what X uses; strict significance scores nothing and is carried so the
      brief's own instruction is visible as data rather than argued about.

      Cluster_pattern in words beside the C1-C5 code, so the table is
      readable without the Task 2 legend.
    """
    loso = pd.read_csv(LOSO_FILE)
    m = t.merge(loso.drop(columns=["symbol", "cluster", "direction",
                                   "HighConfidenceScore"]),
                on="ensembl_id", how="left")
    m["loso_pct_drop"] = (
        100 * (1 - m.loso_min_median_rho / m.fibrosis_rho.abs())).round(1)
    # nullable Int64, not float: only Tier 1 genes have LOSO results, and the
    # resulting NaNs would otherwise render every count as "5.0"
    for c in ("loso_direction_kept", "loso_still_significant",
              "loso_still_strong"):
        m[c] = m[c].astype("Int64")
    have = [(c, n) for c, n in FINAL_COLS if c in m.columns]
    return m[[c for c, _ in have]].rename(columns=dict(have))


if __name__ == "__main__":
    t = master_table()

    print(f"step 1  master table: {len(t):,} genes x {t.shape[1]} columns")
    print(f"        fibrosis-only "
          f"{(t.fibrosis_specificity == 'fibrosis_only').sum():,}"
          f"   shared {(t.fibrosis_specificity == 'shared').sum():,}")
    print("        trajectory clusters")
    for cl, n in t.cluster.value_counts().sort_index().items():
        print(f"          {cl}  {n:>5,}  "
              f"{t.loc[t.cluster == cl, 'cluster_name'].iloc[0]}")
    print("        all genes enter at fibrosis FDR < 0.05 "
          f"(largest q = {t.fibrosis_q.max():.4f})")

    t = assign_direction(t)
    inc = (t.direction == "increasing").sum()
    dec = (t.direction == "decreasing").sum()
    print(f"\nstep 2  direction, from the sign of fibrosis_rho")
    print(f"          increasing with fibrosis stage  {inc:>5,}")
    print(f"          decreasing with fibrosis stage  {dec:>5,}")
    print(f"        cross-checks (these do not change any label)")
    print(f"          Delta_F0_F4 agrees  {t.delta_agrees.sum():>5,} / "
          f"{len(t):,}  ({100 * t.delta_agrees.mean():.1f}%)")
    print(f"          cluster shape agrees {t.cluster_agrees.sum():>5,} / "
          f"{len(t):,}  ({100 * t.cluster_agrees.mean():.1f}%)")
    bad = t[~t.delta_agrees]
    if len(bad):
        print(f"        {len(bad)} gene(s) where F4-F0 points the other way "
              f"-- flagged, label kept:")
        print(bad[["symbol", "fibrosis_rho", "delta_F0_F4", "cluster",
                   "direction"]].to_string(index=False)
              .replace("\n", "\n          "))

    t = score_progression(t)
    print(f"\nstep 3  progression strength P  "
          f"(|rho| >= {RHO_STRONG} -> 2,  >= {RHO_MODERATE} -> 1)")
    for p in (2, 1, 0):
        n = (t.P == p).sum()
        print(f"          P={p}  {n:>5,}  ({100 * n / len(t):4.1f}%)")
    sens = rho_sensitivity(t)
    sens.to_csv(HERE / "03_rho_sensitivity.csv", index=False)
    print("        if the cutoff had been chosen differently (reported, "
          "not acted on):")
    print("          " + sens.to_string(index=False).replace("\n", "\n          "))

    t = score_trajectory(t)
    print(f"\nstep 4  trajectory T  (|F4 - F0| >= {DELTA_STRONG} SD -> 2,  "
          f">= {DELTA_MODERATE} -> 1,  wrong direction -> 0)")
    for s in (2, 1, 0):
        n = (t["T"] == s).sum()   # t["T"], never t.T -- that is the transpose
        print(f"          T={s}  {n:>5,}  ({100 * n / len(t):4.1f}%)")
    print("        T by trajectory cluster -- the late-change bias is visible "
          "here:")
    print("          " + pd.crosstab(t.cluster, t["T"])
          .to_string().replace("\n", "\n          "))
    dsens = delta_sensitivity(t)
    dsens.to_csv(HERE / "04_delta_sensitivity.csv", index=False)
    print("        if the cutoff had been chosen differently (reported, "
          "not acted on):")
    print("          " + dsens.to_string(index=False).replace("\n", "\n          "))

    t = score_transition(t)
    print(f"\nstep 5  transition X  (real in the full fit AND reproducible in "
          f">= {MATCHED_FRAC:.0%} of 50 equal-power draws -> 2, one -> 1)")
    for s in (2, 1, 0):
        n = (t.X == s).sum()
        print(f"          X={s}  {n:>5,}  ({100 * n / len(t):4.1f}%)")
    print("        which of the two pieces of evidence each gene has:")
    ev = pd.crosstab(t.full_fit_substantial, t.matched_reproducible)
    ev.index.name, ev.columns.name = "full fit", "reproducible"
    print("          " + ev.to_string().replace("\n", "\n          "))
    print("        where each gene's largest jump falls -- early biology kept:")
    print("          " + pd.crosstab(t.largest_transition, t.X, margins=True)
          .to_string().replace("\n", "\n          "))

    t = score_specificity(t)
    print("\nstep 6  fibrosis specificity F  (fibrosis-only -> 1, shared -> 0)")
    for s in (1, 0):
        n = (t.F == s).sum()
        lab = "fibrosis-only" if s else "shared"
        print(f"          F={s}  {n:>5,}  ({100 * n / len(t):4.1f}%)  {lab}")
    print("        running score so far, P+T+X+F (max 7 of the eventual 9):")
    running = t.P + t["T"] + t.X + t.F
    print("          " + running.value_counts().sort_index()
          .rename_axis("score").rename("genes").to_frame()
          .to_string().replace("\n", "\n          "))

    t = score_biology(t)
    print("\nstep 7  biological support B  (enriched in >= 2 databases -> 2, "
          "1 -> 1)")
    for s in (2, 1, 0):
        n = (t.B == s).sum()
        print(f"          B={s}  {n:>5,}  ({100 * n / len(t):4.1f}%)")
    print("        genes found in each database (overlapping, not "
          "independent):")
    for db in DATABASES:
        print(f"          {db:9s} {t[db].sum():>5,}")
    print("        B by trajectory cluster -- C4's thin enrichment shows here:")
    print("          " + pd.crosstab(t.cluster, t.B)
          .to_string().replace("\n", "\n          "))

    t = total_score(t)
    print("\nstep 8  HighConfidenceScore = P + T + X + F + B  (max 9)")
    print("          " + t.HighConfidenceScore.value_counts().sort_index()
          .rename_axis("score").rename("genes").to_frame()
          .to_string().replace("\n", "\n          "))
    print("        tiers:")
    for tier, n in t.tier.value_counts().reindex(
            ["Tier 1 - high confidence", "Tier 2 - moderate confidence",
             "Tier 3"]).items():
        print(f"          {tier:32s} {n:>5,}  ({100 * n / len(t):4.1f}%)")

    ts = tier_sensitivity(t)
    ts.to_csv(HERE / "08_tier_sensitivity.csv", index=False)
    print("        if the Tier 1 line were drawn elsewhere:")
    print("          " + ts.to_string(index=False).replace("\n", "\n          "))

    lo = leave_one_score_out(t)
    lo.to_csv(HERE / "08_leave_one_score_out.csv", index=False)
    print("        dropping one score at a time (is any one driving the "
          "ranking?):")
    print("          " + lo.to_string(index=False).replace("\n", "\n          "))

    t1, a = audit_tier1(t)
    print(f"\nstep 9a  examining the {a['n']:,} Tier 1 genes (no selection yet)")
    print("        direction:")
    for k, v in a["direction"].items():
        print(f"          {k:12s} {v:>4,}  ({100 * v / a['n']:4.1f}%)")
    print("        fibrosis specificity:")
    for k, v in a["specificity"].items():
        print(f"          {k:14s} {v:>4,}  ({100 * v / a['n']:4.1f}%)")
    print("        by trajectory cluster:")
    print("          " + a["cluster"].to_string(index=False)
          .replace("\n", "\n          "))
    print("        where the largest jump falls:")
    for k, v in a["transition"].items():
        print(f"          {k:8s} {v:>4,}  ({100 * v / a['n']:4.1f}%)")
    print("        score within Tier 1:")
    for k, v in a["score"].items():
        print(f"          score {k}  {v:>4,}")

    top, full_dom = pathway_dominance(t1)
    full_dom.to_csv(HERE / "09a_tier1_pathway_dominance.csv", index=False)
    print("        most common enriched processes among Tier 1 genes:")
    print("          " + top.to_string(index=False).replace("\n", "\n          "))
    t1.to_csv(HERE / "09a_tier1_genes.csv", index=False)

    sa, sb = shortlist_a(t1), shortlist_b(t1)
    sa[SHORTLIST_COLS].to_csv(HERE / "09b_option_A_top5_per_cluster.csv",
                              index=False)
    sb[SHORTLIST_COLS].to_csv(HERE / "09b_option_B_cluster_top_score.csv",
                              index=False)
    prof = pd.DataFrame([shortlist_profile("A - top 5 per cluster", sa, t1),
                         shortlist_profile("B - cluster top score", sb, t1)])
    prof.to_csv(HERE / "09b_option_comparison.csv", index=False)

    print(f"\nstep 9b  two candidate shortlists, neither lowering the Tier 1 bar")
    print(f"        A  top {TOP_K} per cluster     {len(sa):>3} genes")
    print(f"        B  each cluster's top score {len(sb):>3} genes")
    print("        side by side:")
    print("          " + prof.set_index("option").T.to_string()
          .replace("\n", "\n          "))
    for nm, s in (("A", sa), ("B", sb)):
        print(f"\n        OPTION {nm} -- {len(s)} genes")
        print("          " + s[["symbol", "cluster", "direction",
                                "fibrosis_specificity", "fibrosis_rho",
                                "largest_transition", "HighConfidenceScore"]]
              .to_string(index=False).replace("\n", "\n          "))

    out = HERE / "01_master_table.csv"
    t.to_csv(out, index=False)
    print(f"\n-> {out.relative_to(ROOT)}  ({len(t):,} x {t.shape[1]})")

    if LOSO_FILE.exists():
        shortlist_ids = set(sa.ensembl_id)
        tier1_ids = set(t1.ensembl_id)
        ft = final_table(t)
        sel = ft[ft.Ensembl_ID.isin(shortlist_ids)].copy()
        sel["__c"] = sel.Cluster
        sel = sel.sort_values(["__c", "Total_score"],
                              ascending=[True, False]).drop(columns="__c")
        sel.to_csv(HERE / "11_FINAL_shortlist_25_genes.csv", index=False)
        ft[ft.Ensembl_ID.isin(tier1_ids)].to_csv(
            HERE / "11_final_tier1_genes.csv", index=False)
        ft.to_csv(HERE / f"11_final_all_{len(ft):,}_genes.csv".replace(",", ""), index=False)
        print(f"\nstep 11  final tables ({len(sel.columns)} columns)")
        print(f"          11_FINAL_shortlist_25_genes.csv   {len(sel):>5}")
        print(f"          11_final_tier1_genes.csv          "
              f"{ft.Ensembl_ID.isin(tier1_ids).sum():>5}")
        print(f"          11_final_all_<n>_genes.csv         {len(ft):>5}")
    else:
        print(f"\nstep 11  skipped: run loso_validation.py first")
