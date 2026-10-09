"""Paper 1, Task 1 -- divide the 4,692 progression genes into groups.

Groups come from the `ladder` column of genes_by_fibrosis_stage.csv:
fibrosis_only / inflammation_only / both (shared). Each group is split by
direction of its rho. Outputs go to Paper1_Results/Task1/.
"""
import sys
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd
from scipy.stats import spearmanr

SRC = Path("data/for_mentor/genes_by_fibrosis_stage.csv")
# Output folder. Defaults to the committed location; --out redirects
# it so a re-run can be compared against the previous version instead
# of overwriting it.
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--out", default="Paper1_Results/Task1")
_args, _rest = _ap.parse_known_args()
sys.argv = [sys.argv[0]] + _rest
OUT = Path(_args.out)
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC)
total = len(df)
fib_only = df[df.ladder == "fibrosis_only"]
inf_only = df[df.ladder == "inflammation_only"]
shared = df[df.ladder == "both"]


def row(group, subset, direction, n):
    return {"group": group, "direction": direction, "n_genes": n,
            "pct_of_group": round(100 * n / len(subset), 1) if len(subset) else 0,
            # Named from `total`, not hardcoded: the gene count has
            # changed twice already and a frozen name in the header
            # silently misreports which denominator was used.
            f"pct_of_all_{total}": round(100 * n / total, 1)}


rows = []
for name, sub, col in [("fibrosis_only", fib_only, "fibrosis_rho"),
                       ("inflammation_only", inf_only, "inflammation_rho")]:
    rows.append(row(name, sub, "all", len(sub)))
    rows.append(row(name, sub, "positive", int((sub[col] > 0).sum())))
    rows.append(row(name, sub, "negative", int((sub[col] < 0).sum())))

f, i = shared.fibrosis_rho, shared.inflammation_rho
rows.append(row("shared", shared, "all", len(shared)))
rows.append(row("shared", shared, "positive (both up)", int(((f > 0) & (i > 0)).sum())))
rows.append(row("shared", shared, "negative (both down)", int(((f < 0) & (i < 0)).sum())))
rows.append(row("shared", shared, "discordant (fib up, inf down)", int(((f > 0) & (i < 0)).sum())))
rows.append(row("shared", shared, "discordant (fib down, inf up)", int(((f < 0) & (i > 0)).sum())))

summary = pd.DataFrame(rows)
summary.to_csv(OUT / "task1_summary.csv", index=False, encoding="utf-8-sig")
print(summary.to_string(index=False))

# --- Venn (two sets: fibrosis-associated vs inflammation-associated) ---
fig, ax = plt.subplots(figsize=(7, 5))
ax.add_patch(Circle((-0.6, 0), 1.3, alpha=0.35, color="#c0392b"))
ax.add_patch(Circle((0.6, 0), 1.3, alpha=0.35, color="#2471a3"))
ax.text(-1.15, 0, f"{len(fib_only):,}\n({100*len(fib_only)/total:.1f}%)", ha="center", va="center", fontsize=12)
ax.text(1.15, 0, f"{len(inf_only):,}\n({100*len(inf_only)/total:.1f}%)", ha="center", va="center", fontsize=12)
ax.text(0, 0, f"{len(shared):,}\n({100*len(shared)/total:.1f}%)", ha="center", va="center", fontsize=12, weight="bold")
ax.text(-1.1, 1.5, f"Fibrosis-associated\n(n={len(fib_only)+len(shared):,})", ha="center", fontsize=11)
ax.text(1.1, 1.5, f"Inflammation-associated\n(n={len(inf_only)+len(shared):,})", ha="center", fontsize=11)
ax.set_xlim(-2.2, 2.2); ax.set_ylim(-1.6, 2.1); ax.set_aspect("equal"); ax.axis("off")
ax.set_title(f"{total:,} progression genes", fontsize=13)
fig.savefig(OUT / "task1_venn.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# --- shared genes: fibrosis rho vs inflammation rho ---
rho, p = spearmanr(f, i)
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(f, i, s=6, alpha=0.5, color="#555")
ax.axhline(0, color="grey", lw=0.8); ax.axvline(0, color="grey", lw=0.8)
ax.set_xlabel("Fibrosis ρ (F0 → F4)"); ax.set_ylabel("Inflammation ρ (control → NAFL → NASH)")
ax.set_title(f"Shared genes (n={len(shared):,})\nSpearman ρ = {rho:.3f}, p = {p:.1e}")
fig.savefig(OUT / "task1_shared_rho_scatter.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"\nShared genes: Spearman rho(fibrosis_rho, inflammation_rho) = {rho:.3f}, p = {p:.2e}")

# --- top 20 positive / negative fibrosis-associated genes ---
fib = df[df.fibrosis_rho.notna()]
cols = ["symbol", "ensembl_id", "fibrosis_rho", "fibrosis_q", "inflammation_rho", "ladder"]
top_pos = fib.nlargest(20, "fibrosis_rho")[cols].assign(direction="positive")
top_neg = fib.nsmallest(20, "fibrosis_rho")[cols].assign(direction="negative")
top = pd.concat([top_pos, top_neg])
top.insert(0, "rank", list(range(1, 21)) * 2)
top.to_csv(OUT / "task1_top20_fibrosis_genes.csv", index=False, encoding="utf-8-sig")
print("\nTop 20 positive:", ", ".join(top_pos.symbol))
print("Top 20 negative:", ", ".join(top_neg.symbol))
