# 4. The decisions, and the evidence for each

The non-obvious choices in this project, each with the evidence that settled
it. These are **settled**, not open questions: each was argued out, tested
where testable, and the losing option was kept in the record. If you are
writing the Methods, these are the choices that need a sentence of
justification, and the justification is here.

---

## 1. Measured zeros are kept

**The choice.** A gene measured at zero in a sample is kept as a zero, not
discarded as missing.

**Why.** Dropping zeros removes the switching-on that *is* the progression
signal. **IL6 is detected in 10% of stage-1 patients and 64% of stage-4
patients.** A gene going from absent to present is exactly the kind of change
a stage model should see; treating absence as missing data deletes it.

**What it cost and what it bought.** Keeping zeros added **9.1 million
measurements** and **514 additional progression genes** — and it is how TREM2
was found, which is now one of the prioritised 25.

**Consequence for the files.** The analyses read `data/interim_full` (parsed
without `--drop-zeros`), not `data/interim`. If you re-run the parse, do not
pass that flag.

---

## 2. Two ladders, never one

**The choice.** Fibrosis stage (F0–F4, scarring, largely permanent) and
disease group (control → NAFL → NASH, inflammation, reversible) are scored
separately by pathologists and are analysed separately here. They are never
combined into a single severity score.

**Why.** They measure different things, and collapsing them hides the most
clinically interesting patients. **40 NASH patients in this cohort sit at
fibrosis stage 0** — inflamed but not yet scarred, the most treatable moment
in the disease, and completely invisible on the fibrosis ladder alone.

**What it bought.** The fibrosis-only / inflammation-only / shared partition
(stage 10) is only definable because both ladders were run, and that
partition turned out to carry sharply different biology (stage 13).

---

## 3. Per-study correlation, then combine — never pool patients

**The choice.** Every statistic is computed within each study and then
combined across studies. Patients from different studies are never pooled
into one sample.

**Why.** Studies differ in cohort, sequencing depth, platform and centre. A
gene that climbs beautifully in one study and does nothing in the other four
is a quirk of that cohort, not biology — and pooling lets the largest study
drive the result on its own. Requiring **agreement across independent
studies** is the validation rule of the whole project.

**It has already caught real errors.** It validated the recovered GSE162694
labels (the title suffix agreed with the staging on all 143 samples) and it
caught the bad GSE193066 ones (the apparent diagnosis ran backwards against
every other study — see decision 7).

---

## 4. `value_z` — standardise per gene within study

**The choice.** Expression is standardised per gene within each study, and
that standardised value is what every analysis uses.

**Why.** The studies report raw counts, TPM and one unknown unit, at
different depths. Raw values are not comparable between them at all.
Standardising within study removes the study-level offset and scale and
leaves a comparable quantity.

**Why not a batch-correction algorithm.** Per-study standardisation cannot
leak information between cohorts the way a fitted correction can, and it
keeps each study's contribution auditable. Where a stage comparison needed
more, `study` was added as a model term instead (stage 12).

---

## 5. `n_datasets` is carried on every gene, and must be checked

**The choice.** The graph keeps every mapped gene (53,993), not just the ones
measured everywhere — but each Gene node carries `n_datasets` (1–8).

**Why.** Filtering at load time forecloses every question not anticipated
when the filter was written. Keeping the union moves filtering to query time,
where it can be revisited. But the consequence has to stay visible: **39,199
of the 53,993 genes are missing from at least one study, and 10,621 appear in
exactly one.**

**The rule this creates.** A gene backed by one cohort is not evidence of the
same weight as one backed by eight. **Never average across genes without
checking `n_datasets`.** The progression analysis tests only the 14,794 genes
with `n_datasets = 8`.

---

## 6. Raw clinical fields are never modified

**The choice.** `normalize_clinical.py` **adds** `fibrosis_stage`,
`disease_group`, `patient_id` and `biopsy_number` beside the `*_raw`
originals. It never overwrites them.

**Why.** Every translation stays auditable — anyone can check what
`"normal liver histology"` was mapped to, and disagree with it.

**The rule this creates.** **Always query the harmonised field.** Querying
`fibrosis_stage_raw = '4'` returns **29 of the 35 real cirrhosis samples and
reports no error**, because GSE240729 writes `"F4"`. A silent 17% undercount
with no warning is the bug this decision exists to prevent.

---

## 7. A blank label beats a guessed one

**The choice.** Where a study's diagnosis cannot be established, the field is
left blank. Four studies are deliberately unlabelled.

**Why.** A blank field is a known unknown. A guessed label is an unknown
unknown that quietly contaminates every group comparison built on it.

**The case that proves it.** GSE193066's `sample_description` looks like a
diagnosis (`NAFLD.HUn106.gct` / `NASH.*`). Reading it that way produced a
group that was *more* fibrotic (mean stage 2.16 against 1.78) yet had *lower*
COL1A1 than its NAFL group — backwards for collagen, and contradicting that
study's own fibrosis staging, while every other study runs the correct
direction. Its 106/58 split also matches the processed-file batches rather
than the 116/48 split of the sample titles. **It encodes a file batch, not a
diagnosis**, and the study is left unlabelled.

**One label set was recovered**, under the same standard of proof: GSE162694's
title suffixes (`nash12_F3` → NASH) were cross-checked against
`fibrosis_stage_raw` for all 143 samples and agreed on every one.

**One was derived and flagged as derived**: GSE130970 has no stated diagnosis
but GEO carries its full Kleiner panel, which is what a diagnosis is scored
*from*. The standard NASH-CRN definition was applied and the result marked
`derived_from_histology`, so it can be removed with one filter.

---

## 8. OptimusKG replaced PrimeKG

**The choice.** The knowledge layer is built from OptimusKG. PrimeKG was used
first and dropped.

**Why — one table decided it.** Drugs recorded as treating liver disease:

| | NASH | NAFLD | Cirrhosis |
|---|---|---|---|
| PrimeKG | 0 | 0 | 0 |
| OptimusKG | 74 | 95 | 71 |

Link prediction learns from examples. With zero known drug–disease links for
liver disease there was nothing to learn from. PrimeKG's own project page also
states it has been superseded.

**Three further gains.** OptimusKG identifies genes by **Ensembl ID** — the
namespace this pipeline already standardised on — so 50,725 of 53,993 genes
join directly (94%) against 26,223 (49%) for PrimeKG. Its drug–gene edges
carry a **mode of action** (INHIBITOR, AGONIST, BLOCKER and 20 more) where
PrimeKG had one untyped "acts on"; for repurposing that is the whole point.
And it carries drugs approved after PrimeKG was built, including Resmetirom
(first approved NASH drug, March 2024) and Belapectin, which targets
galectin-3 — LGALS3, a gene this project found independently.

---

## 9. Gene–disease links are cut at score ≥ 0.1

**The choice.** Of OptimusKG's 9,734,774 gene–disease associations, only those
scoring ≥ 0.1 are loaded — and the score is stored on every edge.

**Why.** OptimusKG includes every Open Targets association however weak.
Median score is 0.026; a score of 0.0015 means one paper mentioned the pair
once. Taken whole, **5,568 genes "link" to NAFLD — a third of the genome**,
and a graph where everything connects to everything cannot support
prediction.

**What survives the cut.** NAFLD keeps 274 genes and cirrhosis 234 —
comparable to PrimeKG's 139 and 104, but each properly evidenced — and
PNPLA3 (1,900 studies), TM6SF2 and PPARG all remain. Because the score is on
the edge, a query can tighten further without a reload.

---

## 10. The enrichment background is 14,794 genes, not the genome

**The choice.** Enrichment is tested against the 14,794 genes eligible for
cross-study analysis, not all ~20,000 human genes.

**Why.** Using the whole genome overstates enrichment for any term whose
members are preferentially well measured across studies — and it materially
changes which terms reach significance. **Using the wrong background
invalidates stage 13 and the mechanism ranking of stage 14.**

This is the single most likely methodological question a reviewer will ask
about the enrichment, and the answer is that the background is the tested
universe, which is the correct choice.

---

## 11. The ranking in stage 14 is by agreement, not by p-value

**The choice.** The 3,645 fibrosis genes are re-ranked by how many
independent kinds of evidence agree, not by q-value.

**Why.** Every gene in that set already passes fibrosis FDR < 0.05 — that is
how it entered. Ranking by q again only re-reads the same number. Agreement
between *different* measurements is new information; a smaller p-value is
not.

**Discipline applied.** All cutoffs were frozen as named constants **before
any ranked list was inspected**, and sensitivity to each was measured
afterwards and reported rather than used to choose it (see `03_STATISTICS.md`
§6).

---

## 12. The shortlist is balanced across trajectory clusters, not top-ranked

**The choice.** The final 25 are the top five Tier 1 genes per trajectory
cluster, not the top 25 by score.

**Why.** Tier 1 is very uneven: C2 alone holds 333 of the 507 genes and all
six perfect scores. Sorting by score gives a list that is 87% increasing
genes with 75% of their largest change at F3→F4 — **the early and decreasing
programmes would disappear entirely.**

**Why five.** C4 has exactly five Tier 1 genes, so five is the largest number
at which all five clusters still contribute equally. Beyond it only C1, C2
and C5 can grow, so a larger set is a *less* balanced one.

**The alternative is reported, not hidden.** Taking each cluster's own top
score gives 43 genes, of which 29 come from C1 and C3 and C4 contribute one
gene each
(`02_TABLES/supplementary/TableS16_shortlist_rule_comparison.csv`).

**The quality bar never moves.** Every selected gene still clears Tier 1;
only the sampling within Tier 1 changes.

---

## 13. Say "increasing / decreasing with stage", not "up/downregulated"

**The choice.** A wording rule, enforced in every output table's `Direction`
column.

**Why.** "Upregulated" and "downregulated" denote a differential-expression
comparison between two groups. This project measured **correlation along an
ordered stage ladder**, which is a different quantity arrived at by a
different test. Using the DE vocabulary invites a reader to assume a DE
analysis that was never run.

---

## 14. Mentor's constraints on the deliverable gene tables

From the 2026-09-07 meeting, and reflected in
`05_CODE/pipeline/08_export_for_mentor.py`: stage-wise gene CSVs, **age and
sex only** (no other phenotypes), **no pathway information**, and not all
53,993 genes — the 4,692 progression genes.

These constraints shape `04_DATA/gene_tables/` only. They are a request about
what to send, not a claim about what was analysed; the pathway analysis of
stage 13 exists and is in `03_RESULTS/Task4_enrichment/`.
