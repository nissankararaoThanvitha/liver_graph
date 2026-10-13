# 4. Limitations

Stated here so they appear in the manuscript rather than in review.

## 1. No independent validation

The plan's publication-strengthening addition asks for leading candidates to be
checked against an independent fibrosis dataset or perturbational resource,
kept separate from Paper 1 feature selection and Paper 2 weight selection.
**Not done.** Both routes need data outside the knowledge graph, which the
13 October scope excludes.

This is the single largest limitation. Every layer of evidence in Paper 2
derives from the same two sources — this cohort and OptimusKG — so internal
agreement is consistency, not confirmation.

## 2. No transcriptomic reversal layer

The plan placed transcriptomic drug-reversal evidence immediately before the
final ranking, as an independent check. Ruled out of scope on 13 October
(*"repurposing not reversal"*). The evidence chain is six layers, not seven,
and `task8_evidence_summary.csv` carries L7 as an explicit "out of scope" row.

## 3. The candidate list is two genes, and the data cannot rank them

Thirty leading candidates reach **CACNA1C** (23 drugs) or **PDGFRA** (7). The
list is less diverse than its length implies.

**Neither target is stronger than the other on this project's evidence:**

| | PDGFRA | CACNA1C |
|---|---:|---:|
| Paper 1 score | 9/9 | **9/9** |
| fibrosis rho | +0.417 | **+0.447** |
| BH-q | 1.4e-18 | **5.9e-21** |
| studies | 5/5 | 5/5 |
| Task 6 components | 1.00 x 5 | **1.00 x 5** |
| reversal-inconsistent | 0 | 0 |

**Six genes reach 9/9** — CACNA1C, MYC, PDGFRA, PLK3, TAX1BP3 and TPM4 — so a
perfect Paper 1 score does not separate the two leading targets. CACNA1C holds
marginally better progression statistics than PDGFRA.

**PDGFRA is preferred on one external fact**: nintedanib is already approved for
*lung* fibrosis, the same mechanism in a different organ. That is a reasonable
argument and it is not a finding of this paper. Nothing here speaks to whether
blocking either target helps the liver.

## 4. Mechanism evidence is weak and narrow

Overall reversal consistency is indistinguishable from chance (52.7% against a
55.9% null, p = 0.78), robust to six classification schemes. The one subgroup
that beats its null rests on 32 genes dominated by classic inhibitor-target
families.

**Mechanism consistency is at chance overall, but it contributes half of the K
component; the sensitivity of the ranking to this choice is noted in §10b.**

## 5. Four fifths of drug–target relationships have no direction

Only 1,005 of 4,984 state both that a drug acts on a gene and which way. Any
direction-aware analysis runs on a fifth of the data, and the unknown bucket
must be reported as the majority it is.

## 6. Molecule type and clinical phase do not filter the drug vocabulary

Team 1's instruction was to filter on these. Both were recovered from
OptimusKG — **and they do not discriminate.** All 70 name-flagged entries are
`Small molecule`; ZINC ACETATE and ZINC CHLORIDE carry `max_phase 4.0` and
`is_approved True`, because they genuinely are approved small molecules. A
filter built on them flags **one** drug where a name heuristic flags seventy.

A formula-based rule (no carbon ⇒ not an organic therapeutic) is principled and
certain where it fires — ZnCl₂, MgSO₄, Na₂SO₄, AlCl₃, CaCl₂, NO — but caught
nothing the name rule had missed, and cannot reach organic nutrients since ATP,
FAD and glutamic acid all contain carbon. **The drug vocabulary is filtered by
heuristic, and that is a real weakness.**

## 7. 1,163 drugs have no name — and this is not recoverable

Their `name` in OptimusKG *is* their ChEMBL accession; 28 have synonyms, none
have trade names. ChEMBL was queried directly and supplied names for **16**.
They are genuinely unnamed research compounds.

**Bounded, and measured.** None reaches band 1 or the 30 leading candidates;
the best-ranked sits at **rank 56**. The problem lives in the long tail.

## 8. 2,989 drugs have no chemical structure

OptimusKG supplies SMILES for **9,036 of the graph's 12,025 drugs**. ChEMBL was
queried for the remaining 2,989 and **added none** — it holds records for 2,654
of them and has a structure for none, because they are biologics, antibodies and
mixtures that no SMILES can represent.

**All 2,404 drugs reaching a progression gene do have structures.** The gap and
the analysis do not overlap at all: the drugs without a structure are precisely
the ones no progression gene reaches, so no result is affected.

*(Both figures are denominator-sensitive. Against OptimusKG's 18,640 **raw**
records ChEMBL does add 2,638 structures, but 6,615 of those records never
reached the graph, so that figure does not describe the drugs Paper 2 uses.
Per-denominator figures are in
`03_RESULTS/Recovery2_ChEMBL/recovery2_marginal_contribution.csv`.)*

## 9. Per-edge evidence depth is uneven

Recovered provenance names the asserting databases for all 8,948 edges, but a
reference URL and a written mechanism are much rarer:

| | edges | of 8,948 | of the 4,984 therapeutic links |
|---|---:|---:|---:|
| asserting database named | 8,948 | 100% | 100% |
| reference URL | 1,028 | **11.5%** | **20.6%** |
| written mechanism of action | 1,030 | **11.5%** | **20.7%** |

**The denominator matters.** Across all 36,611 recovered OptimusKG evidence
records these fields reach 38%, but most of those records are for edges outside
Paper 2's gene set. For the 8,948 edges in this table the rate is 11.5%.

Only two sources assert drug–gene edges: DrugBank and Open Targets.
`relation_conflict` is set on 2 edges graph-wide, both outside the
progression-gene subset.

## 9b. "3,027 unique drugs" counts database entries, not distinct compounds

Raised in review, and correct. ChEMBL lists stereoisomers as separate entries,
so (-)-CAMPHOR and CAMPHOR are two of the 3,027.

| | drugs |
|---|---:|
| distinct database entries (the reported figure) | **3,027** |
| after collapsing stereoisomers | **3,020** |
| if salt and ester forms were also merged | **3,012** |

**The overstatement is at most 0.5%**, and nothing in Paper 2 turns on it: no
candidate, ranking or enrichment result changes. `parent_drug` is now a column
in `task2_drug_gene_edges.csv` and the 13 affected groups are listed in
`task2_near_duplicate_drugs.csv`.

**Only stereoisomers are collapsed, deliberately.** Those denote the same parent
compound by definition. Salt and ester forms — DEXAMETHASONE ACETATE against
DEXAMETHASONE, TEDIZOLID PHOSPHATE against TEDIZOLID — are a judgement call, so
they are flagged rather than merged. Naive suffix-stripping is worse than
leaving them: two attempts at it merged CALCIUM CHLORIDE with POTASSIUM CHLORIDE
and SODIUM CITRATE with SODIUM PHOSPHATE, which are genuinely different
substances.

3,027 remains the headline because it is the honest count of what the graph
holds — distinct ChEMBL and DrugBank entries — and because every per-drug
analysis in Paper 2 runs on those entries.

**One pair reaches the leading candidates.** LEVAMLODIPINE (rank 4) and
AMLODIPINE (rank 8) are the same compound, levamlodipine being the pure
S-enantiomer, so the thirty candidates are **29 distinct compounds**. `LEV-` is a
contracted prefix that no safe string rule separates from an ordinary name —
DEXAMETHASONE is not a `DEX-` enantiomer of anything — so the pair is recorded
rather than merged.

## 9c. Druggability depends on what counts as a drug

A gene counted as druggable because its only drug is zinc chloride, ATP or an
unnamed ChEMBL accession is not druggable in any sense the plan asks about.
**174 of the 958 drug-connected progression genes — 18% — reach such an entity
and nothing else.**

Both arms are filtered, and both definitions are reported:

| | published | filtered |
|---|---:|---:|
| background | 11.2% | **9.3%** |
| fibrosis-only / negative | 19.3% | **14.3%** |
| shared / negative | 22.7% | **17.2%** |
| shared / positive | 15.9% | **14.1%** |

Three groups beat the degree-matched null on the filtered definition:
`shared / negative`, `shared / positive` and `fibrosis-only / negative`. The
class-level rollup `[class] inflammation-only` does not (p = 0.081) and is not
claimed.

**The same condition applies to Task 6's K component**, which asks whether a
therapeutic drug acts on a gene. It honours the entity flag Task 7 carries on
every row, so the **172 genes** whose only drug is a mineral salt or unnamed
accession do not earn that credit.

Task 7's own summaries remain unfiltered by design: their question is what the
drug vocabulary asserts, not what could be prescribed.

**The filter is itself a heuristic**, for the reason in §6: molecule type and
clinical phase do not separate a mineral salt from a drug. So neither number is
the truth and both are shipped. A reader who rejects the name rule can use the
unfiltered column; the effect is larger there, not smaller.

## 10. Inflammation-only genes carry less evidence

Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes are scored on two
effective components against four, and are ranked separately for that reason.
Their rankings are not equally well-founded and must not be presented as if
they were. Their underlying axis also rests on 216 patients from three studies,
against 610 for fibrosis.

## 10b. Band 1 depends on recorded drug direction

**Band 1 depends on recorded drug direction.** PDGFRA and CACNA1C reach the top
band because each is a Paper 1 9/9 gene with a drug whose recorded action opposes
the gene's direction of change (K = 1.0). Three other 9/9 genes — MYC, PLK3 and
TPM4 — have a drug but no recorded direction (K = 0.5), so they rank in the next
band (score 0.9). TAX1BP3 has no drug (K = 0). Only 11% of drug–target
relationships carry a recorded direction, so this difference reflects
**annotation coverage, not evidence against these genes**. Candidate drugs for
them should be considered part of the wider repurposing space.

## 11. Exact ranks are not defensible

Only 29–32 of a top-50 survive a random reweighting (5th percentile as low as
16). Report bands or the stable core.

## 12. Circularity in the shortlist statistic

All 30 leading candidates rest on Paper 1's 23-gene shortlist. The ranking
weights shortlist genes highly, so this confirms the pipeline is internally
consistent — it is not independent support.

## 13. Scope of the OptimusKG and ChEMBL recoveries

The provenance recovery (§2 of METHODS) reads fields that
`build_optimuskg_layer.py` discarded at load. The mentor's instruction was that
both OptimusKG and ChEMBL be used to bring the required information, and that
**the two jobs be kept separate.** That separation is structural, not
editorial:

| | Recovery 1 | Recovery 2 |
|---|---|---|
| source | OptimusKG's own discarded fields | ChEMBL API |
| script | `paper2_recover_optimuskg_evidence.py` | `paper2_fetch_chembl_gaps.py` |
| data | `data/optimuskg_recovered/` | `data/chembl_recovered/` |
| report | `03_RESULTS/Recovery1_OptimusKG/` | `03_RESULTS/Recovery2_ChEMBL/` |

Neither folder cites the other's totals, and every recovered field in the
delivered tables carries a `*_source` column naming which recovery supplied it.
A plain merge would have pooled them into one "recovered" figure where nobody
could separate them again.

**The residual limitation is narrower but real.** Recovery 1 re-read a source
the graph was already built from; Recovery 2 left the knowledge graph. Only
Recovery 2 is arguably outside the original scope wording, and its entire
contribution to the delivered analysis is **25 field values across 2,404 drugs,
no structures, and no result changed.** Deleting it would alter nothing.
