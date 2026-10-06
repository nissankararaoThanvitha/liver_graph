# Handover

Context that the code itself does not carry: the Claude Code sessions in which
the project's decisions were actually argued out.

`../CLAUDE.md` is the distillation — conclusions, pipeline order, settled
decisions, known limits. Read that first; it takes five minutes and it is what
you need to *work* on the project.

See `SETUP.md` to get Neo4j, the code and the data running from scratch.

These transcripts are the reasoning behind those conclusions, including the
things that were tried and rejected. Read them when you want to know *why*
something is the way it is, or before reopening a decision.

## Reading order

| | Session | When | Size | What it covers |
|---|---|---|---|---|
| 01 | Prediction explanation | 2026-09-06 | 5 KB | How link prediction works here, in plain language: ComplEx embeddings, why a drug lands near a disease with no edge between them, and why the project's own patient-derived edges are what make NAFLD reachable at all. Best starting point. |
| 02 | Problem statement clarification | 2026-10-02 | 53 KB | What the project is actually trying to answer, and the framing behind it. |
| 03 | Paper 1 work steps | 2026-10-06 | 187 KB | The four Paper 1 analyses as they were built — grouping, F0→F4 trajectories, transitions, enrichment. Read alongside `Paper1_Results/Task*/README.txt`. |
| 04 | GEO dispatch and unmapped genes | 2026-10-06 | 507 KB | Per-study file-format handling and what failed to map, with the decisions about what to keep. The longest and most technical. |

## How to read them

Each file is the conversation: headings are the prompts, the prose beneath is
the answer. Tool calls are collapsed to one grey line each (`ran — Bash: ...`)
so the reasoning stays legible; the full tool output is not reproduced. Each
prompt currently appears twice, as heading and as body — cosmetic, ignore it.

The original `.jsonl` exports, which include the complete tool output, are in
`C:\Users\nissa\Downloads\session-export-*.zip` on the original machine if
anything needs checking at full fidelity.

## These are snapshots, not current truth

They record what was believed on the date at the top of each file. Details have
moved since. For example, session 01 discusses an `INDICATION` edge; that
relationship is now called `TREATS`. Where a transcript and `CLAUDE.md`
disagree, `CLAUDE.md` wins — and where `CLAUDE.md` and the code disagree, the
code wins.
