# Task 8 — Final target and drug ranking

Plan: *"Final evidence chain: fibrosis progression evidence + fibrosis
specificity + F0–F4 trajectory evidence + pathway/biological-process evidence +
knowledge-graph relationships + drug-target mechanism + transcriptomic
drug-reversal evidence → prioritized therapeutic hypotheses… For each leading
candidate, provide an auditable evidence summary showing which of these layers
support or contradict the candidate and where evidence is missing."*

Built by `scripts/paper2_task8_final_ranking.py`, 13 October 2026.

> **These are therapeutic hypotheses, not treatments.** The plan is explicit:
> *"Unless supported by experimental or clinical validation, the final output
> should be described as therapeutic hypotheses or prioritized candidate
> relationships, not as proven anti-fibrotic treatments."* Nothing below has
> been tested in a cell, let alone a liver.

## Files

| File | Rows | What it is |
|---|---:|---|
| `task8_final_target_ranking.csv` | 6,222 | every gene, scored, banded, flagged for shortlist/Tier-1 |
| `task8_final_drug_ranking.csv` | 1,920 | every drug reaching a fibrosis-associated gene |
| `task8_leading_candidates.csv` | 30 | named drugs only, top of band 1 |
| `task8_evidence_summary.csv` | 210 | 7 evidence layers × 30 candidates |
| `task8_shortlist_support.csv` | 3 | shortlist vs broader support, as the plan asks |
| `task8_supporting.xlsx` | 2 sheets | verdict counts · inflammation-only targets |

## Six layers, not seven

The mentor's instruction of **13 October 2026** — *"repurposing not reversal"*,
*"focus only on the knowledge graph"* — puts the transcriptomic reversal layer
out of scope. It is **carried in the evidence summary as a row reading "out of
scope"** rather than silently dropped, because a layer the plan named and the
paper did not use should be visible to a reviewer.

## How drugs are ranked, and what was rejected

**Primary key: the single best-supported target a drug has.** Not the sum over
its targets, and not a count.

The obvious rule — add up target scores across everything a drug touches —
rewards promiscuity, and three tasks measured the damage: Task 4 found coverage
**negatively** correlated with coherence (ρ = −0.124) and its raw ranking led
with zinc salts; Task 5 found DWPC promoting proteasome and tubulin binders
because complex subunits share annotations.

> **A tie-break that had to be fixed.** 51 drugs tie at the maximum
> best-target score, so the tie-break decides the entire top of the list. The
> first version broke ties on the **number** of shortlist and Tier-1 targets —
> which put FOSTAMATINIB (82 targets, coherence 0.34) above NINTEDANIB
> (6 targets, coherence 0.43). That is the promiscuity bias re-entering through
> the back door. Ties now break on **coherence** and the **rate** of mechanism
> agreement. Counts are reported and never sorted on.

**Drugs sharing a best-target score form a band, and order within a band is
weakly determined.** Task 6 found exact ranks indefensible even with one
continuous score; with 51 ties they are more so. Read band 1 as a set.

## FINDING — band 1 is two genes

45 named drugs tie in band 1. They reach exactly **two** targets:

| Target | Drugs | What they are |
|---|---:|---|
| **CACNA1C** | 33 | L-type calcium channel blockers — amlodipine, diltiazem, verapamil, the dihydropyridines |
| **PDGFRA** | 12 | tyrosine kinase inhibitors — imatinib, sunitinib, **nintedanib**, pazopanib, midostaurin, regorafenib |

**Paper 2's final candidate list is, in substance, "drugs that inhibit PDGFRA
or block CACNA1C."** Both genes score a perfect 1.00 on all five Task 6
components, and both were independently flagged in Task 7 as reversal-consistent
fibrosis-only rising genes.

**PDGFRA** is the stronger of the two: Paper 1's only 9/9 gene, rho +0.417
across 5/5 studies, LOSO 5/5, and nintedanib is already approved for *lung*
fibrosis — the same mechanism in a different organ. That convergence is the
most defensible thing in this paper.

**CACNA1C** carries more drugs but a thinner story. It reaches band 1 on the
same five components, and calcium-channel blockers have been examined in
fibrosis, but nothing in this project speaks to whether blocking it helps the
liver.

### One artefact to know about

Coherence is **1.0 by construction** for a single-target drug, so those sort to
the top of the band. Only **4 of 45** band-1 drugs have one target, so the
effect is small — but barnidipine, clevidipine, diltiazem and levamlodipine
head the list partly for that reason rather than on strength of evidence.

## The auditable evidence summary

Seven layers × 30 leading candidates, in the plan's own hierarchy:

| Layer | supports | missing | out of scope |
|---|---:|---:|---:|
| L1 progression association | 30 | 0 | 0 |
| L2 fibrosis specificity | 30 | 0 | 0 |
| L3 trajectory / stage transition | 30 | 0 | 0 |
| L4 pathway / process context | 30 | 0 | 0 |
| L5 knowledge-graph relationship | 30 | 0 | 0 |
| **L6 drug-target mechanism** | **19** | **11** | 0 |
| **L7 transcriptomic reversal** | 0 | 0 | **30** |

Every leading candidate is supported on the five Paper-1-derived layers — which
follows from how they were selected, and is not independent confirmation.

**L6 is where candidates actually differ:** 19 of 30 have a drug whose recorded
action opposes the gene's direction of travel; for 11 the direction was never
recorded. No candidate is *contradicted* on mechanism, because a
reversal-inconsistent pair cannot reach a top band under this ranking.

**L7 is uniformly out of scope**, by the 13 October decision.

## Shortlist support — the plan asks for this by name

*"Report how many final drug candidates are supported by the shortlist versus
only by broader progression evidence."*

| set | drugs | supported by the 23-gene shortlist | Tier 1 only | broader evidence only |
|---|---:|---:|---:|---:|
| all ranked drugs | 1,920 | 184 | 416 | 1,320 |
| named drugs only | 1,391 | 128 | 313 | 950 |
| **top 30 candidates** | **30** | **30** | 0 | 0 |

**All 30 leading candidates rest on Paper 1's own 23-gene shortlist**, not on
broader progression evidence alone. That is the strongest statement available
about their provenance — and it is also circular in the sense that the ranking
weights shortlist genes highly, so it confirms the pipeline is consistent, not
that the candidates work.

The 1,320 drugs resting on broader evidence only are not dismissed; they are
the wider repurposing space, and the plan's instruction to use the shortlist as
a *prioritisation layer rather than a replacement* is why they remain in
`task8_final_drug_ranking.csv`.

## Scope

Candidates are drawn from **fibrosis-associated** genes. The 2,377
inflammation-only genes are scored on two components (Task 6), carry no
trajectory, pathway or tier evidence, and are reported separately in
`task8_supporting.xlsx` rather than mixed in — a candidate resting on them is
supported by strictly less.

## Limitations to carry into the manuscript

1. **No transcriptomic reversal evidence.** Out of scope by decision, not
   oversight. The plan placed it as the independent check on everything above;
   without it, every layer here derives from the same two sources.
2. **Band 1 is two genes.** The candidate list is less diverse than its length
   suggests.
3. **Unnamed drugs: a bounded limitation, measured.** 461 of the 1,920 ranked
   drugs (24%) have only a ChEMBL accession for a name, so we cannot tell a
   real therapeutic from a salt or a screening compound. Resolving them needs
   ChEMBL metadata, which the knowledge-graph-only scope excludes.

   **It does not reach the candidates.** Zero of the 51 drugs in band 1 are
   unnamed, and zero of the 30 leading candidates. The best-ranked unnamed drug
   sits at **band 3** (best-target score 0.90, rank 56). The problem lives
   entirely in the long tail.

   Two things were tried inside the graph before accepting it. Disease evidence
   rescues almost nothing: of 1,163 unnamed drugs graph-wide, only **27** have
   any `TREATS` / `OFF_LABEL_FOR` / `CONTRAINDICATED_IN` edge. Target-set
   containment (Task 4) catches duplicates but not identities. The highest
   unnamed drugs cluster on **SRC** and are most likely a kinase-inhibitor
   screening series rather than medicines, which is consistent with them
   ranking below every named candidate.
4. **Mechanism consistency is at chance overall** (Task 2: 52.7% against a
   55.9% null, p = 0.78). Only the fibrosis-only rising subgroup beats its null,
   and that subgroup is 32 genes of classic inhibitor-target families.
5. **Exact ranks are not defensible.** Read bands.
