"""compare_repeat_policy.py
---------------------------
Shows exactly what changes when the 58 twice-biopsied GSE193066 patients are
handled by first biopsy instead of by averaging the two.

It makes two comparisons, and the first one matters as much as the second:

  1. COMMITTED vs AVERAGE -- the refactor check. Re-running the old policy
     through the new code must reproduce the committed numbers exactly. If it
     does not, the comparison below is measuring a bug in the refactor rather
     than the effect of the policy.

  2. AVERAGE vs FIRST -- the real question. How many genes enter, how many
     leave, and do the named results survive.

Nothing here writes to a committed folder.

Usage:
    python compare_repeat_policy.py
"""
import os
import sys

import pandas as pd

COMMITTED = "data/progression_full"
AVERAGE = "data/progression_repeat_average"
FIRST = "data/progression_repeat_first"

# Genes the paper names, which must be checked individually rather than
# trusted to a count: the prioritised 25, plus the collagens that confirm the
# method recovers known fibrosis biology.
SHORTLIST_25 = [
    "IL32", "UNC5B", "NFASC", "ADAMTSL2", "PLPP4", "PDGFRA", "MYC",
    "CACNA1C", "TPM4", "TAX1BP3", "TREM2", "CDC45", "HTR7", "FABP5", "TYMS",
    "CYP2C19", "OAT", "NAAA", "CLPX", "F2", "DGAT2", "SLC38A4", "NCAM2",
    "CYP4F3", "ACADSB",
]
COLLAGENS = ["COL1A1", "COL1A2", "COL3A1", "COL4A1", "COL4A2", "COL4A4",
             "COL5A1", "COL8A2", "COL16A1"]


def load(folder, axis):
    path = os.path.join(folder, "progression_%s.csv" % axis)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def significant(df, q=0.05):
    """The gene set the paper calls progression-associated on this ladder.

    Two conditions, not one. q < 0.05 alone returns ~10,900 genes; the
    published 3,645 fibrosis genes also require every study that tested the
    gene to agree on the direction of change, which is the cross-study
    validation rule the whole project rests on.
    """
    return set(df.loc[(df.q_value < q) & (df.n_agree == df.n_studies),
                      "ensembl_id"])


def rule(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def compare_sets(a, b, name_a, name_b, label):
    only_a, only_b = a - b, b - a
    both = a & b
    denom = len(a) if a else 1
    print("  %-28s %6d" % (name_a + " " + label, len(a)))
    print("  %-28s %6d" % (name_b + " " + label, len(b)))
    print("  %-28s %6d   (%.1f%% of %s)"
          % ("kept in both", len(both), 100 * len(both) / denom, name_a))
    print("  %-28s %6d   left" % ("only in " + name_a, len(only_a)))
    print("  %-28s %6d   entered" % ("only in " + name_b, len(only_b)))
    return only_a, only_b


def main():
    for folder in (COMMITTED, AVERAGE, FIRST):
        if not os.path.isdir(folder):
            sys.exit("missing folder: %s -- run find_progression_genes.py "
                     "for that policy first" % folder)

    # ---------------------------------------------- 1. the refactor check
    rule("1. REFACTOR CHECK -- committed vs the same policy re-run")
    clean = True
    for axis in ("fibrosis", "disease"):
        c, a = load(COMMITTED, axis), load(AVERAGE, axis)
        if c is None or a is None:
            continue
        m = c.merge(a, on="ensembl_id", suffixes=("_c", "_a"))
        same_n = len(c) == len(a) == len(m)
        drho = (m.median_rho_c - m.median_rho_a).abs().max()
        dq = (m.q_value_c - m.q_value_a).abs().max()
        same_set = significant(c) == significant(a)
        ok = same_n and drho < 1e-9 and same_set
        clean &= ok
        print("  %-10s rows %5d vs %5d | max |d rho| %.2e | max |d q| %.2e "
              "| same gene set %s  -> %s"
              % (axis, len(c), len(a), drho, dq, same_set,
                 "OK" if ok else "MISMATCH"))
    if not clean:
        print("\n  The refactor does NOT reproduce the committed numbers.")
        print("  Fix that before reading anything below.")
        return 1
    print("\n  Clean. The old policy re-run through the new code is identical")
    print("  to what is committed, so anything below is the policy, not a bug.")

    # ------------------------------------------- 2. what the policy changes
    rule("2. THE REAL COMPARISON -- averaging both biopsies vs first only")

    sets = {}
    for axis in ("fibrosis", "disease"):
        a, f = load(AVERAGE, axis), load(FIRST, axis)
        if a is None or f is None:
            continue
        sa, sf = significant(a), significant(f)
        sets[axis] = (sa, sf, a, f)
        print("\n  %s ladder" % axis.upper())
        compare_sets(sa, sf, "average", "first", "genes")

    if "fibrosis" in sets:
        sa, sf, a, f = sets["fibrosis"]
        m = a.merge(f, on="ensembl_id", suffixes=("_a", "_f"))
        both = m[m.ensembl_id.isin(sa & sf)]
        d = (both.median_rho_a - both.median_rho_f).abs()
        print("\n  Correlation shift among genes significant in both:")
        print("    median |change in rho|  %.4f" % d.median())
        print("    90th percentile         %.4f" % d.quantile(0.90))
        print("    largest                 %.4f" % d.max())
        flip = both[(both.median_rho_a > 0) != (both.median_rho_f > 0)]
        print("    genes that changed DIRECTION: %d" % len(flip))
        if len(flip):
            print("      " + ", ".join(
                str(s) for s in flip.get("symbol_a", flip.get("symbol"))
                .head(20)))

    # --------------------------------------- 3. do the named results hold
    rule("3. DO THE PAPER'S NAMED GENES SURVIVE?")
    if "fibrosis" in sets:
        sa, sf, a, f = sets["fibrosis"]
        fsym = f.set_index("symbol")["ensembl_id"].to_dict()
        asym = a.set_index("symbol")["ensembl_id"].to_dict()
        for label, genes in (("the prioritised 25", SHORTLIST_25),
                             ("the nine collagens", COLLAGENS)):
            kept, lost = [], []
            for g in genes:
                eid_a, eid_f = asym.get(g), fsym.get(g)
                in_a = eid_a in sa if eid_a else False
                in_f = eid_f in sf if eid_f else False
                (kept if (in_f or not in_a) else lost).append(g)
            print("\n  %s: %d of %d still fibrosis-associated"
                  % (label, len(genes) - len(lost), len(genes)))
            if lost:
                print("    LOST: " + ", ".join(lost))
            else:
                print("    none lost")

    # ------------------------------------------------- 4. the bottom line
    rule("4. BOTTOM LINE")
    if "fibrosis" in sets:
        sa, sf, _a, _f = sets["fibrosis"]
        churn = len(sa ^ sf)
        pct = 100 * len(sa & sf) / (len(sa) or 1)
        print("  Fibrosis gene set is %.1f%% unchanged; %d genes move in or "
              "out." % (pct, churn))
        if pct >= 99:
            print("  -> Effectively unchanged. Keep the committed results and")
            print("     report this as a sensitivity check.")
        elif pct >= 95:
            print("  -> Small change. Adopting 'first' is still the right")
            print("     call, but downstream steps should be re-run.")
        else:
            print("  -> Material change. Adopt 'first' and re-run every")
            print("     downstream step before using any current number.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
