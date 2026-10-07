# Paper 2 — Team 2

Output folder for Team 2's analyses, mirroring
[`Paper1_Results/`](../Paper1_Results).

**Nothing here yet.** No Paper 2 brief has been written. Team 2's scope, as the
handover sessions record it, is **drug repurposing**: link prediction over the
knowledge layer, and the handoff to an LLM. The mentor's split is that Team 1
owns staging and the relationships between genes and stages, Team 2 owns
repurposing. Two scripts already exist for it —
[`export_triples.py`](../export_triples.py) and
[`train_link_prediction.py`](../train_link_prediction.py) — but the first model
**failed its own validation**, so there is no verified result to build on yet.

---

## Layout

One folder per analysis, each carrying its own `README.txt`:

```
Paper2_Results/
├── README.md        this file
├── <Analysis1>/
│   ├── README.txt   method, headline numbers, and what it does NOT support
│   └── ...          CSVs and figures
└── <Analysis2>/
```

Create the subfolders as the brief defines them. Scripts that produce them take
the `paper2_` prefix, matching `paper1_task1_groups.py` and its siblings — the
prefix keeps the two teams' scripts in separate blocks when the file list sorts
alphabetically.

**The per-analysis `README.txt` is not optional.** It is why Paper 1's numbers
can still be quoted months later: each one states the method, the real n, and the
limits in the same place as the results. Read any of
`../Paper1_Results/Task*/README.txt` for the format.

---

## Working rules

### Treat Team 1's outputs as read-only

| Do not modify or overwrite | Why |
|---|---|
| `Paper1_Results/` | Team 1's committed deliverable |
| `data/for_mentor/` | the stage-wise tables Paper 1 is computed from |
| `data/progression_full/` | the 4,692 progression genes |
| `data/interim_full/` | the parse everything upstream depends on |
| `parse_expression.py`, `build_graph_all.py`, `find_progression_genes.py`, `export_for_mentor.py` | re-running these overwrites the folders above |

**The failure mode to avoid:** re-running a pipeline script into its default
output directory silently changes the inputs Paper 1's published numbers rest on.
Nothing errors, and because those folders are gitignored nothing shows in
`git status` either — Paper 1 just quietly stops being reproducible.

If you need a variant, send it somewhere new:

```bash
python parse_expression.py --raw-dir data/raw --out-dir data/interim_paper2
```

### Bulk outputs are gitignored, with a rebuild command

`data/kg_triples/`, `data/prediction/` and `data/paper2/` are already excluded.
Add new bulk folders the same way — size and rebuild command above the path, so
a missing folder is obviously regenerable rather than lost:

```
# data/paper2_embeddings  420M  rebuild: python paper2_train.py
data/paper2_embeddings/
```

### Files that conflict even on a branch

- **`requirements.txt`** — `pykeen` and `torch` are already pinned. Append new
  dependencies at the bottom under a `# Paper 2` comment; do not reorder.
- **`CLAUDE.md`, `README.md`** — add a new marked section rather than rewriting
  Team 1's prose. Same-line edits are what produce merge conflicts.
- **The Neo4j database** — a shared server, not a file, so no branch isolates it.
  Write only *new* relationship types; never modify or delete existing nodes or
  edges. Team 1's 6,384 `TRACKS_*` edges and the 32.5M `EXPRESSES` edges are
  load-bearing.

### Branch, then merge

Work on `paper2-repurposing` and merge to `main` when a piece is finished, so
`main` never carries half-done Team 2 state. Team 1 worked the same way —
`harmonize-clinical-metadata` merged as PR #1.

---

## Before building on link prediction

`train_link_prediction.py` already states how its output must be judged, and the
first run did not pass. Both checks have to hold before any candidate means
anything:

1. **Held-out test set** — 10% of triples never seen in training. Hits@10 says how
   often the true answer lands in the top ten.
2. **A liver-specific check** — ask where the 95 drugs already known to treat
   NAFLD rank among all 12,025. If known drugs do not float to the top, the novel
   predictions are noise and must be discarded.

Even when both hold, the output is a hypothesis for a lab to test, not a finding.
Say so in the `README.txt`.
