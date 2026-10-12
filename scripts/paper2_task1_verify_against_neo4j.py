"""
paper2_task1_verify_against_neo4j.py
------------------------------------
Audit Paper 2 Task 1 against the live graph, gene by gene, not count by count.

Matching totals prove very little: two sets of 6,222 genes can agree on size and
disagree on membership. This checks set equality, then every value it can.

Checked:
  1. the gene SET matches (symmetric difference must be empty)
  2. the progression class per gene matches the TRACKS edges present
  3. fibrosis rho / q / n_studies / direction match TRACKS_FIBROSIS
  4. inflammation rho / q / n_studies / direction match TRACKS_INFLAMMATION
  5. structural blanks are blank in the graph too

Direction is spelled differently on each side: the graph stores rises / falls,
Paper 1's CSVs store increasing / decreasing. That is a vocabulary difference,
not a disagreement, so it is mapped rather than flagged.

Floating point is compared with a tolerance, because the CSV is rounded for
publication and the graph is not.

Usage:
    uv run --with neo4j --with pandas python scripts/paper2_task1_verify_against_neo4j.py
"""

import json
import os
import sys

import pandas as pd
from neo4j import GraphDatabase

TABLE = "Paper2_Results/Task1/Paper2_progression_genes.csv"
TOL = 5e-4          # the CSV carries 4 decimal places
DIRECTION = {"rises": "increasing", "falls": "decreasing"}


def driver():
    """Credentials come from the MCP server config, never from source."""
    cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
    for scope in cfg.get("projects", {}).values():
        srv = (scope.get("mcpServers") or {}).get("neo4j")
        if srv:
            env = srv["env"]
            return (GraphDatabase.driver(env["NEO4J_URI"],
                                         auth=(env["NEO4J_USERNAME"],
                                               env["NEO4J_PASSWORD"])),
                    env.get("NEO4J_DATABASE", "neo4j"))
    raise SystemExit("no neo4j MCP config found")


def main():
    drv, db = driver()
    with drv.session(database=db) as s:
        inst = s.run("CALL dbms.listConfig('server.directories.data') "
                     "YIELD value RETURN value").single()["value"]
        print(f"instance: {inst}")
        print(f"database: {db}\n")

        rows = s.run("""
            MATCH (g:Gene)
            WHERE (g)-[:TRACKS_FIBROSIS]->() OR (g)-[:TRACKS_INFLAMMATION]->()
            OPTIONAL MATCH (g)-[f:TRACKS_FIBROSIS]->()
            OPTIONAL MATCH (g)-[i:TRACKS_INFLAMMATION]->()
            RETURN g.ensembl_id AS Ensembl_ID, g.symbol AS graph_symbol,
                   f.rho AS g_fib_rho, f.q AS g_fib_q,
                   f.n_studies AS g_fib_n, f.direction AS g_fib_dir,
                   i.rho AS g_inf_rho, i.q AS g_inf_q,
                   i.n_studies AS g_inf_n, i.direction AS g_inf_dir
        """).data()
    drv.close()

    graph = pd.DataFrame(rows)
    table = pd.read_csv(TABLE)
    print(f"graph progression genes: {len(graph):,}")
    print(f"Task 1 table rows:       {len(table):,}\n")

    failures = []

    # ---- 1. set equality -------------------------------------------------
    g_ids, t_ids = set(graph.Ensembl_ID), set(table.Ensembl_ID)
    only_graph, only_table = g_ids - t_ids, t_ids - g_ids
    if only_graph or only_table:
        failures.append(f"gene sets differ: {len(only_graph)} only in graph, "
                        f"{len(only_table)} only in table")
        print("  only in graph:", sorted(only_graph)[:5])
        print("  only in table:", sorted(only_table)[:5])
    else:
        print(f"[OK] gene sets identical ({len(g_ids):,} genes, "
              f"symmetric difference empty)")

    m = table.merge(graph, on="Ensembl_ID", how="inner")
    print(f"[--] joined on Ensembl_ID: {len(m):,} rows\n")

    # ---- 2. class vs the edges that actually exist ------------------------
    expected = m.apply(
        lambda r: "both" if pd.notna(r.g_fib_rho) and pd.notna(r.g_inf_rho)
        else ("fibrosis-only" if pd.notna(r.g_fib_rho) else "inflammation-only"),
        axis=1)
    bad = m[expected != m.progression_class]
    if len(bad):
        failures.append(f"{len(bad)} genes whose class disagrees with the graph")
        print(bad[["Gene", "progression_class"]].head().to_string(index=False))
    else:
        print(f"[OK] progression_class matches the TRACKS edges for all {len(m):,}")

    # ---- 3/4. numeric and categorical values -----------------------------
    def check(label, csv_col, graph_col, is_float=True):
        both = m[m[csv_col].notna() & m[graph_col].notna()]
        if is_float:
            diff = (both[csv_col] - both[graph_col]).abs()
            off = both[diff > TOL]
        else:
            off = both[both[csv_col] != both[graph_col]]
        # a value present on one side only is a real mismatch
        onesided = m[m[csv_col].isna() ^ m[graph_col].isna()]
        if len(off) or len(onesided):
            failures.append(f"{label}: {len(off)} value mismatches, "
                            f"{len(onesided)} present on one side only")
            if len(off):
                print(off[["Gene", csv_col, graph_col]].head(3).to_string(index=False))
        else:
            print(f"[OK] {label:<28} {len(both):>6,} compared, max diff "
                  f"{(diff.max() if is_float and len(both) else 0):.2e}")

    m["g_fib_dir"] = m.g_fib_dir.map(DIRECTION)
    m["g_inf_dir"] = m.g_inf_dir.map(DIRECTION)

    check("fibrosis_rho", "fibrosis_rho", "g_fib_rho")
    check("fibrosis_q_FDR", "fibrosis_q_FDR", "g_fib_q")
    check("fibrosis_n_studies", "fibrosis_n_studies", "g_fib_n")
    check("fibrosis_direction", "fibrosis_direction", "g_fib_dir", is_float=False)
    check("inflammation_rho", "inflammation_rho", "g_inf_rho")
    check("inflammation_q_FDR", "inflammation_q_FDR", "g_inf_q")
    check("inflammation_n_studies", "inflammation_n_studies", "g_inf_n")
    check("inflammation_direction", "inflammation_direction", "g_inf_dir",
          is_float=False)

    # ---- 5. symbols ------------------------------------------------------
    sym = m[m.Gene.fillna("") != m.graph_symbol.fillna("")]
    if len(sym):
        failures.append(f"{len(sym)} gene symbols differ from the graph")
        print(sym[["Ensembl_ID", "Gene", "graph_symbol"]].head().to_string(index=False))
    else:
        print(f"[OK] gene symbols match the graph for all {len(m):,}")

    print()
    if failures:
        print("FAILED:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("PASS - Task 1 reproduces the live graph exactly.")


if __name__ == "__main__":
    main()
