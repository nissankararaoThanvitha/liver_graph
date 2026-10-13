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

## 3. The candidate list is two genes

Thirty leading candidates reach **CACNA1C** (22 drugs) or **PDGFRA** (8). The
list is less diverse than its length implies. PDGFRA carries a strong,
convergent story; CACNA1C reaches the same band on the same measures with a
thinner one, and nothing here speaks to whether blocking it helps the liver.

## 4. Mechanism evidence is weak and narrow

Overall reversal consistency is indistinguishable from chance (52.7% against a
55.9% null, p = 0.78), robust to six classification schemes. The one subgroup
that beats its null rests on 32 genes dominated by classic inhibitor-target
families. Mechanism should not carry weight in any ranking.

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

OptimusKG supplies SMILES for 9,036 of 12,025. ChEMBL was queried for the rest
and **added none** — it holds records for 2,654 of them and has no structure
for any, because they are biologics, antibodies and mixtures that no SMILES can
represent.

*(A 60-drug pilot suggested ChEMBL would fill 57 of 59. That pilot sampled all
18,640 OptimusKG records rather than the 12,025 in use, and overstated the
benefit. The full run is the honest number.)*

All 2,404 drugs reaching a progression gene do have structures.

## 9. Per-edge evidence depth is uneven

Recovered provenance names the asserting databases for all 8,948 edges, but a
reference URL and written mechanism exist for only 38%. Only two sources assert
drug–gene edges: DrugBank and Open Targets. `relation_conflict` is set on 2
edges graph-wide.

## 10. Inflammation-only genes carry less evidence

Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes are scored on two
effective components against four, and are ranked separately for that reason.
Their rankings are not equally well-founded and must not be presented as if
they were. Their underlying axis also rests on 216 patients from three studies,
against 610 for fibrosis.

## 11. Exact ranks are not defensible

Only 29–32 of a top-50 survive a random reweighting (5th percentile as low as
16). Report bands or the stable core.

## 12. Circularity in the shortlist statistic

All 30 leading candidates rest on Paper 1's 23-gene shortlist. The ranking
weights shortlist genes highly, so this confirms the pipeline is internally
consistent — it is not independent support.

## 13. Scope decision taken ahead of confirmation

The OptimusKG provenance recovery (§2 of METHODS) was carried out on the
researcher's instruction of 13 October, **before the mentor replied** on
whether *"focus only on the knowledge graph"* permits reading OptimusKG's own
discarded fields. Recorded so the provenance is visible if that answer differs.
