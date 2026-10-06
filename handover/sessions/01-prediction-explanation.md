# Prediction explanation

*Claude Code session — last active 2026-09-06*


---

## for the 1st one how are u predicting it...explain me in simple words clearly

for the 1st one how are u predicting it...explain me in simple words clearly

I'll look at what's actually in your prediction code so I explain your setup, not a generic one.


<sub>ran — Bash: List repo and triples dir · Bash: Read export_triples.py · Bash: Read training script · Bash: Count drug-liver disease edges · Bash: Look for 111 in reports · Bash: Check if prediction output exists · Bash: Inspect prediction outputs</sub>

Short answer: nothing is "predicted" by a rule — the model learns coordinates for every node, and a drug that lands *near* liver disease without an arrow to it becomes the prediction. Here's the whole thing step by step.

## 1. What that arrow actually is

In your graph, "drug → liver disease" is the `INDICATION` edge. Right now it exists only this many times:

| disease | drugs with a known INDICATION arrow |
|---|---|
| NAFLD (EFO_0003095) | 95 |
| NASH (EFO_1001249) | 74 |
| cirrhosis (EFO_0001422) | 71 |

There are **12,025 drugs** in the graph. So ~11,900 of them have no arrow to NAFLD. The job isn't "find 111 missing arrows" — it's **score every one of the 12,025 drugs for how much the graph *implies* that arrow should exist**, then look at the top of the list.

(I couldn't trace the `111` in your screenshot to any file in the repo — none of the counts I can compute equal 111. If you tell me what that column was counting I'll check it.)

## 2. How the model learns — the simple version

`train_link_prediction.py` uses **ComplEx** (via PyKEEN). Think of it like this:

- Every entity — each drug, each gene, each disease — gets a **list of 128 numbers**. Call it a position on a map.
- Every relation type (`ACTS_ON`, `ASSOCIATED_WITH`, `TRACKS_FIBROSIS`, `INDICATION`) also gets its own list of numbers. Think of it as a **lens** you look through.
- A "score" is just: put head and tail through the relation's lens, see how well they line up.

Training is 40 rounds of the same two nudges over 2.9M training triples:

1. For a **real** triple (aspirin → ACTS_ON → PTGS1): nudge the numbers so that score goes **up**.
2. For 8 **fake** triples made by swapping in a random node (aspirin → ACTS_ON → some random gene): nudge so that score goes **down**.

That's it. Nobody tells the model what a gene is. After millions of nudges, things that are wired together the same way drift to the same neighbourhood.

## 3. Why a drug ends up near liver disease with no direct arrow

Because of chains like this:

```
drug ──ACTS_ON──▶ gene ──TRACKS_FIBROSIS──▶ NAFLD
```

The model never sees that path as a path. But to satisfy both edges at once, it has to place the drug and NAFLD near each other. Once ~11,900 drugs are placed by their gene wiring, a handful land in the same spot as NAFLD — and *those* are the ones the `INDICATION` lens scores high.

This is exactly why your own patient edges matter, and it's the honest core of the project: NAFLD has only **47** literature `ASSOCIATED_WITH` gene edges, but **3,645** `TRACKS_FIBROSIS` edges from your cohort. Without your edges, NAFLD is a nearly-isolated dot and every drug is equally far away. Your 6,384 patient-derived edges are what pull it into the middle of the gene map where drugs live.

## 4. The actual prediction step

In [train_link_prediction.py:120](train_link_prediction.py:120):

- Pin the relation to `INDICATION` and the tail to `dis:EFO_0003095`.
- Ask the model to score **every entity** as the head.
- Keep only entities starting with `drug:` → 12,025 scores.
- Sort high to low, flag the ones already known, and the unflagged ones at the top are the new candidates.

## 5. Why you'd believe any of it

Two checks, both in the script:

- **Held-out test**: 10% of all triples were never shown during training. Hits@10 = how often the true answer is in the model's top 10. If this is bad, the map is junk.
- **Liver-specific check**: where do the 95 already-known NAFLD drugs rank among all 12,025? If known treatments don't float to the top, the new names below them are noise.

One honesty caveat on that second check: ~80% of those 95 known drugs were in the *training* set, so the model was literally taught them — they'll rank high partly by memory. The cleaner version is to check only the known drugs that landed in `test.tsv`. Worth doing before quoting the number anywhere.

## 6. Where you actually are

`data/prediction/` is empty — the script is written but **hasn't been run yet**, so no scores exist right now. Want me to run it? On CPU with 2.9M training triples × 40 epochs it will take a while, so I'd suggest a quick `--epochs 5` smoke run first to confirm it trains end-to-end before committing to the full one.
