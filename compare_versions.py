"""compare_versions.py
----------------------
Compares a v2 task folder against its v1 counterpart and prints what moved.

Counts alone hide churn. Task 1's shared group went 1,692 -> 1,815, which
looks like 123 genes arriving; in fact 258 arrived and 168 left. This reports
membership, not just totals.

Usage:
    python compare_versions.py task1
    python compare_versions.py task2
    python compare_versions.py all
"""
import os
import sys

import pandas as pd

# Set these to the two result folders you want compared. They are
# deliberately not defaulted to anything that exists: this tool is for
# comparing a re-run against what it replaced, and silently comparing
# a folder with itself would report "nothing changed" and be believed.
#
# It earned its keep once already: when Task 4 was re-run, its cluster
# rows came back byte-identical to the previous version, which is how
# we found the script was still reading the OLD cluster file.
V1 = "Paper1_Results_previous"
V2 = "Paper1_Results"


def read(folder, task, name):
    p = os.path.join(folder, task, name)
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, encoding="utf-8-sig")
    d.columns = [c.lstrip("﻿") for c in d.columns]
    return d


def rule(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def movement(a, b, label_a="v1", label_b="v2"):
    """Sets in, out and kept -- the part a count comparison hides."""
    kept, left, came = a & b, a - b, b - a
    print("    %-22s %6d" % ("in " + label_a, len(a)))
    print("    %-22s %6d" % ("in " + label_b, len(b)))
    print("    %-22s %6d" % ("kept in both", len(kept)))
    print("    %-22s %6d" % ("left", len(left)))
    print("    %-22s %6d" % ("arrived", len(came)))
    print("    %-22s %6d" % ("TOTAL MOVED", len(left) + len(came)))
    return kept, left, came


def compare_task1():
    rule("TASK 1 -- progression groups")
    a, b = read(V1, "Task1", "task1_summary.csv"), \
        read(V2, "Task1", "task1_summary.csv")
    if a is None or b is None:
        print("  missing input")
        return
    ca = [c for c in a.columns if c.startswith("pct_of_all")][0]
    cb = [c for c in b.columns if c.startswith("pct_of_all")][0]
    m = a[a.direction == "all"][["group", "n_genes", ca]].merge(
        b[b.direction == "all"][["group", "n_genes", cb]],
        on="group", suffixes=("_v1", "_v2"))
    m["change"] = m.n_genes_v2 - m.n_genes_v1
    print("\n  group counts")
    print(m.to_string(index=False))
    print("\n  total progression genes: %s -> %s"
          % (ca.replace("pct_of_all_", ""), cb.replace("pct_of_all_", "")))

    print("\n  direction split")
    d = a[a.direction != "all"][["group", "direction", "n_genes"]].merge(
        b[b.direction != "all"][["group", "direction", "n_genes"]],
        on=["group", "direction"], how="outer", suffixes=("_v1", "_v2"))
    d = d.fillna(0)
    d["change"] = d.n_genes_v2 - d.n_genes_v1
    print(d.to_string(index=False))

    # membership churn, from the underlying gene tables
    t1 = read(V1, "Task1", "task1_top20_fibrosis_genes.csv")
    t2 = read(V2, "Task1", "task1_top20_fibrosis_genes.csv")
    if t1 is not None and t2 is not None and "symbol" in t1.columns:
        for d_ in ("positive", "negative"):
            col = "direction" if "direction" in t1.columns else None
            if col is None:
                break
            s1 = set(t1[t1[col] == d_].symbol)
            s2 = set(t2[t2[col] == d_].symbol)
            if not s1:
                continue
            print("\n  top 20 %s fibrosis genes: %d of 20 unchanged"
                  % (d_, len(s1 & s2)))
            if s1 - s2:
                print("    dropped out: " + ", ".join(sorted(s1 - s2)))
            if s2 - s1:
                print("    new:         " + ", ".join(sorted(s2 - s1)))


def compare_task2():
    rule("TASK 2 -- trajectory clusters")
    a, b = read(V1, "Task2", "task2_choosing_k.csv"), \
        read(V2, "Task2", "task2_choosing_k.csv")
    if a is not None and b is not None:
        m = a[["k", "silhouette", "stability_ARI_mean"]].merge(
            b[["k", "silhouette", "stability_ARI_mean"]], on="k",
            suffixes=("_v1", "_v2"))
        print("\n  choosing k (stability >= 0.95 is the rule)")
        print(m.round(4).to_string(index=False))

    a, b = read(V1, "Task2", "task2_cluster_sizes.csv"), \
        read(V2, "Task2", "task2_cluster_sizes.csv")
    if a is not None and b is not None:
        print("\n  clusters found: v1 %d, v2 %d" % (len(a), len(b)))
        for lab, d in (("v1", a), ("v2", b)):
            cols = [c for c in d.columns
                    if c.lower() in ("cluster", "cluster_name", "n_genes")]
            print("\n   %s" % lab)
            print(d[cols].to_string(index=False))

    a, b = read(V1, "Task2", "task2_gene_clusters.csv"), \
        read(V2, "Task2", "task2_gene_clusters.csv")
    if a is not None and b is not None and "Gene" in a.columns:
        print("\n  gene membership")
        movement(set(a.Gene), set(b.Gene))
        m = a[["Gene", "cluster"]].merge(b[["Gene", "cluster"]], on="Gene",
                                         suffixes=("_v1", "_v2"))
        same = (m.cluster_v1 == m.cluster_v2).sum()
        print("    %-22s %6d of %d (%.1f%%)"
              % ("same cluster id", same, len(m), 100 * same / max(len(m), 1)))
        print("\n    v1 cluster -> v2 cluster")
        print(pd.crosstab(m.cluster_v1, m.cluster_v2).to_string())


def compare_task3():
    rule("TASK 3 -- stage transitions")
    a, b = read(V1, "Task3", "task3_transition_summary.csv"), \
        read(V2, "Task3", "task3_transition_summary.csv")
    if a is None or b is None:
        print("  missing input")
        return
    key = a.columns[0]
    m = a.merge(b, on=key, suffixes=("_v1", "_v2"))
    for c in [c for c in a.columns if c != key]:
        if c + "_v1" in m.columns and pd.api.types.is_numeric_dtype(
                m[c + "_v1"]):
            print("\n  %s" % c)
            print(m[[key, c + "_v1", c + "_v2"]].to_string(index=False))


def compare_task4():
    rule("TASK 4 -- pathway enrichment")
    a, b = read(V1, "Task4", "task4_significant_counts.csv"), \
        read(V2, "Task4", "task4_significant_counts.csv")
    if a is None or b is None:
        print("  missing input")
        return
    key = a.columns[0]
    m = a.merge(b, on=key, how="outer", suffixes=("_v1", "_v2")).fillna(0)
    print("\n  significant terms per group and database")
    print(m.to_string(index=False))

    a, b = read(V1, "Task4", "task4_all_significant.csv"), \
        read(V2, "Task4", "task4_all_significant.csv")
    if a is not None and b is not None:
        cols = set(a.columns) & set(b.columns)
        gc = next((c for c in ("group", "Group") if c in cols), None)
        tc = next((c for c in ("term", "Term") if c in cols), None)
        if gc and tc:
            print("\n  significant (group, term) pairs")
            movement(set(zip(a[gc], a[tc])), set(zip(b[gc], b[tc])))


def main():
    which = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    jobs = {"task1": compare_task1, "task2": compare_task2,
            "task3": compare_task3, "task4": compare_task4}
    if which == "all":
        for f in jobs.values():
            f()
    elif which in jobs:
        jobs[which]()
    else:
        sys.exit("usage: python compare_versions.py [task1|task2|task3|task4|all]")
    print()


if __name__ == "__main__":
    main()
