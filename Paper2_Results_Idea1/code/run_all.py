"""Run the whole Paper 2 pipeline (Tasks 1–8 + final ranking) for the Idea 1 rerun, without diagrams.

Idea 1: only drugs already used for a fibrosis-type liver disease are excluded from the repurposing
candidates (Task 4 / Task 5 revised). Everything else is the original method.

Each script runs in its own process with matplotlib's savefig switched off, so no pictures are made;
markdown image links are then removed from the summaries. Results go to Paper2_Results_Idea1/.
Needs NEO4J_PASSWORD in the environment (read-only queries).

    python Paper2_Results_Idea1/code/run_all.py
"""
import re
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parent
RES = CODE.parent
STEPS = ["task1_master_gene_table", "task2_drug_gene_edges", "task3_druggability", "task4_drug_coverage",
         "task5_prep_pathway_map", "task5_metapaths", "task5_revised_metapaths", "task6_target_score_prototype",
         "task7_direction_consistency", "task7_revised_pathway_direction", "final_ranking",
         "audit_tasks", "task8_progress_report", "audit_tasks"]
WRAP = ("import matplotlib; matplotlib.use('Agg'); import matplotlib.figure as f, matplotlib.pyplot as p; "
        "f.Figure.savefig = lambda *a, **k: None; p.savefig = lambda *a, **k: None; "
        "import runpy, sys; sys.argv = [sys.argv[1]]; runpy.run_path(sys.argv[0], run_name='__main__')")
LOG = RES / "run_log.txt"
log = open(LOG, "w", encoding="utf-8")
for step in STEPS:
    t = time.time()
    r = subprocess.run([sys.executable, "-c", WRAP, str(CODE / f"{step}.py")], cwd=RES.parent,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"})
    log.write(f"\n===== {step} (exit {r.returncode}, {time.time() - t:.0f}s)\n{r.stdout[-4000:]}\n{r.stderr[-4000:]}\n")
    log.flush()
    print(f"{step}: exit {r.returncode} ({time.time() - t:.0f}s)", flush=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        sys.exit(1)

# no diagrams in this rerun: drop markdown image lines that point at pictures
for md in RES.rglob("*.md"):
    txt = md.read_text(encoding="utf-8")
    new = re.sub(r"(?m)^!\[[^\]]*\]\([^)]*\.png\)\s*\n?", "", txt)
    if new != txt:
        md.write_text(new, encoding="utf-8")
pngs = list(RES.rglob("*.png"))
print("pictures in output folder:", len(pngs))
