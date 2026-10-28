"""Paper 2 — FINAL target and drug ranking (plan Task 8), Paper 1 final (10 Oct 2026 version).

Rules are frozen in RULES below and written to Final_ranking/PREREGISTRATION.md before any
rank is computed. Nothing is tuned to obtain a ranking. Knowledge graph + Paper 1 only
(project scope decision: repurposing, not reversal). Outputs are repurposing hypotheses.

TARGETS (6,222 genes), components from Task6/target_components.csv (definitions in
Task6/target_score_framework.md):
  Biology list    = mean(P, F, T, B)        -> new-target view (no drug evidence)
  Actionable list = mean(P, F, T, K, B)     -> repurposing view
  Stable target   = in the top 50 in >= 80% of 1,000 Dirichlet(alpha=10) weight draws.

DRUGS (1,109 repurposing candidates; primary list = 559 mechanism-annotated), each in [0, 1]:
  D1 target relevance  = highest BIOLOGY TargetScore among the drug's pharmacological
                         progression targets (biology, not actionable, so drug evidence is not
                         counted twice with D4)
  D2 direction         = (consistent - inconsistent) / (consistent + inconsistent) mapped to
                         [0, 1]; 0.5 when no link has a known direction (Task 7)
  D3 specificity       = progression_target_fraction (Task 4)
  D4 graph support     = mean percentile (among candidates, zeros stay 0) of Task 5 DNS for
                         M1f (fibrosis-spectrum disease), M6 (stage transitions, summed) and
                         M7 (Paper 1 fibrosis programs, summed)
  DrugScore = mean(D1, D2, D3, D4); stable drug = in the top 25 in >= 80% of 1,000
  Dirichlet(alpha=10) draws. Ablation: drop each component.

    python Paper2_Results_Idea1/code/final_ranking.py
"""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Paper2_Results_Idea1"
OUT = RES / "Final_ranking"
OUT.mkdir(exist_ok=True)

RULES = {
    "paper1_version": "final combined version, 10 Oct 2026 (confirmed final by the Paper 1 team)",
    "target_components": ["P", "F", "T", "K", "B"],
    "biology_list": ["P", "F", "T", "B"],
    "actionable_list": ["P", "F", "T", "K", "B"],
    "target_weights": "equal (the default named in the Task 6 framework; not tuned)",
    "drug_components": ["D1_target_relevance", "D2_direction", "D3_specificity", "D4_graph_support"],
    "drug_weights": "equal",
    "drug_universe": "Task 4 repurposing candidates (1,109); primary ranking = mechanism-annotated main list (559)",
    "stability": "1,000 Dirichlet(alpha=10) weight draws, seed 42; stable = P(top-N) >= 0.8; N = 50 targets, 25 drugs",
    "stress_test": "Dirichlet(alpha=1) also reported",
    "ablation": "drop each component, renormalise; Spearman, Kendall, top-N overlap",
    "never": "no weight tuning after seeing ranks; no external data; no efficacy claims",
}
TOP_T, TOP_D, N_DRAWS, SEED, STABLE = 50, 25, 1000, 42, 0.8

prereg = f"""# Final ranking — pre-registered rules (written before ranks were computed)

Date: {date.today():%d %b %Y}. Paper 1: {RULES['paper1_version']}.

| Rule | Frozen value |
|---|---|
""" + "\n".join(f"| {k} | {', '.join(v) if isinstance(v, list) else v} |" for k, v in RULES.items()) + """

Component definitions: `Task6/target_score_framework.md` (targets) and the docstring of
`code/final_ranking.py` (drugs). The equal-weight Task 6 prototype was seen before this
freeze; equal weights were already named there as the default, and the stability analysis
below is the safeguard against relying on any single weight choice.
"""
(OUT / "PREREGISTRATION.md").write_text(prereg, encoding="utf-8")

# ------------------------------------------------------------------ targets
comp = pd.read_csv(RES / "Task6/target_components.csv").set_index("ensembl_id")
rng = np.random.default_rng(SEED)


def rank_desc(s):
    return s.rank(ascending=False, method="min").astype(int)


def stability(C, top_n, names, rng):
    out = {}
    for alpha in (10.0, 1.0):
        W = rng.dirichlet([alpha] * C.shape[1], size=N_DRAWS)
        R = np.vstack([pd.Series(C @ w).rank(ascending=False, method="min").values for w in W])
        out[alpha] = pd.DataFrame({
            f"p_top{top_n}_a{alpha:g}": (R <= top_n).mean(axis=0),
            f"median_rank_a{alpha:g}": np.median(R, axis=0),
            f"rank_p05_a{alpha:g}": np.percentile(R, 5, axis=0),
            f"rank_p95_a{alpha:g}": np.percentile(R, 95, axis=0)}, index=names)
    return out


def ablation(df, cols, base, top_n):
    rows = []
    rb = rank_desc(base)
    top = set(rb.nsmallest(top_n).index)
    for c in cols:
        keep = [x for x in cols if x != c]
        r = rank_desc(df[keep].mean(axis=1))
        rows.append({"dropped": c, "spearman": round(spearmanr(rb, r)[0], 4), "kendall": round(kendalltau(rb, r)[0], 4),
                     f"top{top_n}_overlap": len(top & set(r.nsmallest(top_n).index))})
    return pd.DataFrame(rows)


tables = {}
for name, cols in [("biology", RULES["biology_list"]), ("actionable", RULES["actionable_list"])]:
    s = comp[cols].mean(axis=1)
    t = comp[["Gene", "progression_class", "paper1_group", "trajectory_cluster", "fibrosis_direction", "Tier",
              "in_shortlist"] + cols].copy()
    t["TargetScore"] = s.round(4)
    t["rank"] = rank_desc(s)
    st = stability(comp[cols].values, TOP_T, comp.index, rng)
    t = t.join(st[10.0]).join(st[1.0])
    t["stable_target"] = t[f"p_top{TOP_T}_a10"] >= STABLE
    t = t.sort_values("rank")
    t.to_csv(OUT / f"final_targets_{name}.csv")
    ablation(comp, cols, s, TOP_T).to_csv(OUT / f"ablation_targets_{name}.csv", index=False)
    tables[name] = t
bio, act = tables["biology"], tables["actionable"]

# stage-stratified biology view (top 5 per F0-F4 trajectory cluster, as in Paper 1)
per_cluster = (bio[bio.trajectory_cluster.notna()].sort_values(["trajectory_cluster", "rank"])
               .groupby("trajectory_cluster").head(5))
per_cluster.to_csv(OUT / "final_targets_biology_top5_per_cluster.csv")

# ------------------------------------------------------------------ drugs
cand = pd.read_csv(RES / "Task4/repurposing_candidates.csv").set_index("Drug_ID")
mech_ids = set(pd.read_csv(RES / "Task4/repurposing_candidates_mechanism_annotated.csv").Drug_ID)
ev = pd.read_csv(RES / "Task7/drug_action_evidence.csv")
ev = ev[ev.pharmacological_link & ev.Drug_ID.isin(cand.index)]
ds = pd.read_csv(RES / "Task5/metapath_drug_scores.csv").set_index("Drug_ID").reindex(cand.index).fillna(0)

ev["bio_score"] = ev.Gene_ID.map(bio.TargetScore)
ev["bio_rank"] = ev.Gene_ID.map(bio["rank"])
ev["stable_bio"] = ev.Gene_ID.map(bio.stable_target)
ev["stable_act"] = ev.Gene_ID.map(act.stable_target)
g = ev.groupby("Drug_ID")
D = pd.DataFrame(index=cand.index)
D["D1_target_relevance"] = g.bio_score.max()
n_c = g.Consistency.apply(lambda s: (s == "direction-consistent").sum())
n_i = g.Consistency.apply(lambda s: (s == "direction-inconsistent").sum())
dec = (n_c + n_i).reindex(cand.index).fillna(0)
D["D2_direction"] = np.where(dec > 0, ((n_c - n_i).reindex(cand.index).fillna(0) / dec.replace(0, np.nan) + 1) / 2, 0.5)
D["D3_specificity"] = cand.progression_target_fraction.clip(0, 1)


def pct_pos(s):
    out = pd.Series(0.0, index=s.index)
    out[s > 0] = s[s > 0].rank(pct=True)
    return out


m6 = ds.filter(regex=r"^M6 .*_dns$").sum(axis=1)
m7 = ds.filter(regex=r"^M7 .*_dns$").sum(axis=1)
D["D4_graph_support"] = (pct_pos(ds["M1f Drug→Gene→FibrosisSpectrumDisease_dns"]) + pct_pos(m6) + pct_pos(m7)) / 3
D = D.fillna(0)
assert D.min().min() >= 0 and D.max().max() <= 1

dcols = RULES["drug_components"]


def build(universe, tag):
    Dx = D.loc[universe]
    s = Dx[dcols].mean(axis=1)
    out = cand.loc[universe, ["Drug", "max_phase", "is_approved", "liver_contraindicated", "n_progression_genes",
                              "n_fibrosis_genes", "pharm_targets_graph", "current_indications_examples"]].join(Dx.round(4))
    out["DrugScore"] = s.round(4)
    out["rank"] = rank_desc(s)
    st = stability(Dx[dcols].values, TOP_D, Dx.index, rng)
    out = out.join(st[10.0]).join(st[1.0])
    out["stable_drug"] = out[f"p_top{TOP_D}_a10"] >= STABLE
    gg = g.get_group
    out["n_consistent"] = n_c.reindex(universe).fillna(0).astype(int)
    out["n_inconsistent"] = n_i.reindex(universe).fillna(0).astype(int)
    out["shortlist_supported"] = [bool(ev[(ev.Drug_ID == d) & ev.in_shortlist].shape[0]) for d in universe]
    out["best_target"] = [gg(d).sort_values("bio_score", ascending=False).Gene.iloc[0] for d in universe]
    out["best_target_bio_rank"] = [int(gg(d).bio_rank.min()) for d in universe]
    out["consistent_targets"] = [";".join(sorted(set(gg(d).loc[gg(d).Consistency == "direction-consistent", "Gene"]))) for d in universe]
    out["inconsistent_targets"] = [";".join(sorted(set(gg(d).loc[gg(d).Consistency == "direction-inconsistent", "Gene"]))) for d in universe]
    out = out.sort_values("rank")
    out.to_csv(OUT / f"final_drugs_{tag}.csv")
    ablation(Dx, dcols, s, TOP_D).to_csv(OUT / f"ablation_drugs_{tag}.csv", index=False)
    return out


main = build([d for d in cand.index if d in mech_ids], "main_list")
allc = build(list(cand.index), "all_candidates")


# ------------------------------------------------------------------ evidence cards (auditable layers)
def layer_marks(r):
    t = bio.loc[bio.Gene == r.best_target].iloc[0]
    m = {
        "Progression (P)": "✔" if t.P >= 0.75 else ("–" if t.P >= 0.5 else "✘ weak"),
        "Fibrosis specificity (F)": {1.0: "✔ fibrosis-only", 0.6667: "✔ shared", 0.3333: "~ discordant", 0.0: "✘ inflammation-only"}.get(round(t.F, 4), "?"),
        "Trajectory / transition (T)": "✔" if t["T"] >= 0.6 else ("–" if t["T"] > 0 else "✘ none"),
        "Pathway (B)": "✔" if t.B >= 0.5 else ("–" if t.B > 0 else "✘ none"),
        "Drug mechanism direction": ("✔ consistent" if r.n_consistent and not r.n_inconsistent else
                                     "~ mixed" if r.n_consistent and r.n_inconsistent else
                                     "✘ inconsistent" if r.n_inconsistent else "– unknown"),
        "Graph support (MetaPaths)": "✔" if r.D4_graph_support >= 0.6 else ("–" if r.D4_graph_support > 0 else "✘ none"),
        "Liver safety flag": "✘ contraindicated" if r.liver_contraindicated else "✔ none recorded",
        "Paper 1 shortlist": "✔" if r.shortlist_supported else "–",
    }
    return m


cards = []
for d, r in main.head(TOP_D).iterrows():
    row = {"rank": int(r["rank"]), "Drug": r.Drug, "phase": r.max_phase, "DrugScore": r.DrugScore,
           "stable": "yes" if r.stable_drug else "no", "best target": f"{r.best_target} (#{r.best_target_bio_rank})"}
    row.update(layer_marks(r))
    cards.append(row)
cards = pd.DataFrame(cards)
cards.to_csv(OUT / "evidence_cards_top25.csv", index=False)

# ------------------------------------------------------------------ summary
def md(df):
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * df.shape[1]]
    for row in df.values:
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


def tshow(t, n=20):
    x = t.head(n).copy()
    x["dir"] = x.fibrosis_direction.map({"positive": "⬆", "negative": "⬇"}).fillna("")
    x["P(top50)"] = x[f"p_top{TOP_T}_a10"].round(2)
    return x[["rank", "Gene", "progression_class", "trajectory_cluster", "dir", "TargetScore", "P(top50)", "in_shortlist"]]


def dshow(t, n=25):
    x = t.head(n).copy()
    x["P(top25)"] = x[f"p_top{TOP_D}_a10"].round(2)
    x["liver CI"] = x.liver_contraindicated.map({True: "⚠️", False: ""})
    x["phase"] = x.max_phase.map(lambda v: f"{v:g}")
    x = x.rename(columns={"best_target": "top-scoring target (any link)", "consistent_targets": "right-way targets",
                          "inconsistent_targets": "wrong-way targets"})
    return x[["rank", "Drug", "phase", "DrugScore", "P(top25)", "top-scoring target (any link)", "right-way targets",
              "wrong-way targets", "liver CI"]]


abl_t = pd.read_csv(OUT / "ablation_targets_actionable.csv")
abl_d = pd.read_csv(OUT / "ablation_drugs_main_list.csv")
top_main = main.head(TOP_D)
sl_top = int(top_main.shortlist_supported.sum())
pc = per_cluster.reset_index()[["trajectory_cluster", "Gene", "progression_class", "TargetScore", "rank"]]
summary = f"""# Paper 2 — Final target and drug ranking

**Paper 1:** {RULES['paper1_version']}. **Gene set:** corrected Paper 1 union of {len(comp):,} genes (the plan's 4,692 was the pre-correction count).
**Scope:** knowledge graph + Paper 1 only (project scope decision: repurposing, not reversal). **All results are repurposing hypotheses, not treatments.**
Rules were frozen before ranking: `PREREGISTRATION.md`. Script: `Paper2_Results_Idea1/code/final_ranking.py`.

![Final ranking diagram](Final_ranking_diagram.png)

## 1. Final targets
Two lists, as decided in Task 6: **biology** (P, F, T, B; finds new targets with or without drugs) and **actionable** (P, F, T, K, B; targets with drug evidence, for repurposing). Equal weights. A target is **stable** if it stays in the top 50 in ≥ 80% of 1,000 near-equal weight draws (Dirichlet α = 10).

| List | Stable targets (top 50 in ≥ 80% of draws) | Stable at α = 1 (stress test) | Shortlist genes in top 50 |
|---|---|---|---|
| Biology | {int(bio.stable_target.sum())} | {int((bio[f'p_top{TOP_T}_a1'] >= STABLE).sum())} | {int(bio.head(TOP_T).in_shortlist.sum())} |
| Actionable | {int(act.stable_target.sum())} | {int((act[f'p_top{TOP_T}_a1'] >= STABLE).sum())} | {int(act.head(TOP_T).in_shortlist.sum())} |

### Actionable list, top 20
{md(tshow(act))}

### Biology list, top 20
{md(tshow(bio))}

### Stage-informed view: top 5 biology targets per F0–F4 trajectory cluster
{md(pc)}

### Target ablation (actionable; drop one component)
{md(abl_t)}

## 2. Final drugs (repurposing candidates)
DrugScore = mean of D1 target relevance (best biology TargetScore of the drug's targets), D2 direction-consistency (Task 7), D3 specificity (progression-target fraction) and D4 knowledge-graph support (Task 5 MetaPaths). Primary list: the {len(main)} mechanism-annotated candidates (`final_drugs_main_list.csv`); all {len(allc):,} candidates are in `final_drugs_all_candidates.csv`.

**Stable drugs** (top 25 in ≥ 80% of draws, α = 10): **{int(main.stable_drug.sum())}**. Shortlist-supported drugs in the top 25: **{sl_top}**; broad-evidence-only: **{TOP_D - sl_top}**.

### Main list, top 25
{md(dshow(main))}

### Evidence cards: which layers support (✔), contradict (✘) or are missing (–) for the top 25
{md(cards)}

### Drug ablation (drop one component)
{md(abl_d)}

## 3. How to read this
- A high rank means **several independent knowledge-graph and Paper 1 layers agree**. It does not show that a drug would help patients. Every candidate remains a **repurposing hypothesis**.
- D2 = 0.5 means the graph does not say which way the drug pushes its targets (unknown, not wrong).
- ⚠️ = contraindicated in some liver disease in the graph: high priority for safety review, not automatically excluded.
- Independent validation and transcriptomic reversal are out of scope by the project scope decision.
"""
(OUT / "summary.md").write_text(summary, encoding="utf-8")
print(summary)
