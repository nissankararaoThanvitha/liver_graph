# 4. What the results do and do not support

Read this before writing any claim. Several results are narrower than they
first appear, and two validation measures cannot fail by construction — they
are marked. Every limit here is measured, and each names the file where the
measurement lives.

A limitation stated plainly in the paper costs a sentence. The same
limitation found by a reviewer costs the paper.

---

## 1. The cohort is cross-sectional, and F4 is underpowered

**Stage F4 has 35 samples (34 usable patients)** against 127–186 at every
other stage. Its stage means are the noisiest in the study, and every
estimate involving F4 is the least precise.

The power-matched design addresses the *comparison* between transitions by
giving all four equal power. It does not make the F3→F4 estimate itself
precise. Say "the transition into cirrhosis carries the largest change", not
"we precisely quantified the F3→F4 change".

**There is no outcome, survival or longitudinal analysis.** Nothing here
establishes that a patient *progresses* along these trajectories; it
establishes that patients *at* different stages differ. The trajectory
language is about stage ordering, not about followed individuals.

**One number to quote carefully:** the power-matched count for F3→F4 has a
median of 287 and a standard deviation of 412 across draws. The *ranking* is
safe — 287 against 0, 0 and 2 is not close — but do not present 287 as a
precise estimate. "Hundreds of genes, against essentially none at earlier
transitions" is the honest phrasing.

---

## 2. The disease ladder rests on three studies and 221 patients

This is the limit most likely to be missed, because the cohort is 1,085
samples and the disease analysis uses a fraction of them.

Of the eight studies, five carry disease labels. Two of those five —
GSE135251 (206 patients) and GSE162694 (112) — label patients as **NAFLD
without stating the NAFL/NASH subtype**. GEO records no diagnosis field for
either. NAFLD is true of those patients but does not place them on a
control → NAFL → NASH ordering, so neither study contributes to the disease
ladder.

**What remains: GSE126848 (45), GSE130970 (78), GSE167523 (98) = 221
patients.**

Two consequences:

**Inflammation-only gene counts are not comparable with fibrosis-only
counts.** A gene must satisfy three agreeing studies on the disease ladder
and five on the fibrosis ladder. The disease side is a less stringent test on
a smaller cohort, and its larger gene count reflects that, not stronger
biology.

**A third of the disease ladder uses labels derived rather than stated.**
GSE130970's diagnoses were derived by applying the standard NASH-CRN
definition to the study's own Kleiner scores. That is a recognised clinical
rule applied to the histology a pathologist recorded, not a guess — but it is
a derivation, it is flagged `derived_from_histology` in the data, and it
should be disclosed.

---

## 3. The two ladders are measured on largely different patients

Of the 668 staged samples, **119 carry a usable disease label, and only
GSE130970's 78 vary** — the other 41 are all controls.

So "shared" genes are not genes shown to track both things *in the same
patients*. They are genes that independently passed two tests run on
**nearly separate cohorts**: 668 samples from five studies for fibrosis, 221
patients from three for disease, overlapping in one study.

That is still a legitimate finding, but it is a weaker statement than
"shared" sounds like.

---

## 4. F0 is not a control group

Of 152 samples at fibrosis stage 0: **46 are healthy controls, 73 have fatty
liver disease without scarring, 5 have NASH without scarring**, and 15 carry
no diagnosis.

Stage 0 means "no scarring". It does not mean healthy. Comparing F4 against
F0 is not comparing disease against health.

Three controls are not at F0 at all — one at F2 in GSE130970, one each at F1
and F2 in GSE135251.

---

## 5. Demographic coverage is partial — 385 samples, not 1,085

Sex is recorded for 540 samples and age for 483. Only **three studies record
demographics *and* stage fibrosis**, so any analysis crossing stage with age
or sex rests on **385 samples from GSE130970, GSE162694 and GSE193066**.

The per-stage gene table itself uses all 668 staged samples; only the
demographic splits are restricted. Every output file carries its own n.

---

## 6. Significant-gene counts are inflated by selection; the comparisons are not

The genes analysed in stages 11–14 were selected *because* they correlate
with fibrosis stage **in these same data**. Absolute counts of significant
genes are therefore inflated and must not be read as unbiased estimates of
how many genes change.

**The comparisons remain fair**, because all four transitions and all five
clusters use the same gene set and carry the same inflation. "The largest
change is at F3→F4" is valid; "934 genes change at F3→F4" is a count within a
pre-selected set and should be phrased as such.

There is **no held-out validation cohort.** Leave-one-study-out is internal
cross-validation across the five staging studies, not external replication.

---

## 7. Cluster shapes are solid; membership is not, for two clusters

**The five shapes are reproducible** — recovered at median correlation
0.96–0.996 across 100 patient bootstraps, and not created by study mix
(ARI 0.82 after study adjustment).

**Individual membership is another matter:**

| Cluster | Genes | Confidently assigned |
|---|---|---|
| C1 Early increase | 948 | **3** |
| C2 Late increase | 1,528 | 772 |
| C3 Early rise, then plateau | 209 | **1** |
| C4 Mid decrease | 313 | 130 |
| C5 Late decrease | 683 | 510 |

**Report the shapes with confidence. Gene-level claims are defensible for
C2, C4 and C5 only.** For C1 and C3, describe the shape; do not name genes as
belonging to them. The three increasing clusters differ only in the timing of
a rise, and genes move freely between them under resampling.

This also bounds Task 4's cluster-core check: C2 and C5 are confirmed on
confidently assigned members, C4 is testable and yields no enriched terms —
so its lack of pathway signal is a tested result rather than an untested gap
— and **C1 and C3 cannot be assessed at all**, having too few confident
members to enrich.

---

## 8. The cluster number is a reported choice, not a rule's output

The pre-specified rule — largest k whose gene-subsample ARI stays at or above
0.95 — returned **k = 6**, clearing the threshold by **0.0006** against a
standard deviation of 0.026.

**k = 5 is reported**, because it is better on every measure that does not
depend on label matching:

| | k = 5 | k = 6 |
|---|---|---|
| Silhouette | **0.334** | 0.294 |
| Gene-subsample ARI | **0.964** | 0.951 |
| Patient-bootstrap ARI | **0.519** | 0.461 |
| Confidently assigned genes | **1,416** | 1,235 |

The rule takes the *largest* k above a bar, which rewards more clusters by
construction rather than better ones.

**State the rule, its result, the departure and the reason in the Methods.**
Do not report k = 5 as though the rule chose it. The k = 6 solution splits the
increasing programme into early, mid and late components and is reproducible
with `python task2_trajectories.py --out <folder> 6`.

---

## 9. Two validation measures cannot fail, and are labelled

**Leave-one-study-out on direction.** Every Tier 1 gene already has all five
studies agreeing on direction — that is how it entered — so dropping one
leaves four that still agree and the median keeps its sign **by arithmetic**.
All 525 genes score 5/5 without anything being tested.

Two measures that *can* fail are reported beside it, and these are the ones
to quote:

- **521 of 525** stay significant on the remaining four studies
- **263 of 525** keep median |rho| ≥ 0.30 in every refit, and **76 fail in
  all five** — their effect size depends on having all five studies present

`LOSO_max_pct_drop_in_rho` is the column that actually discriminates.

**The power-matched analysis cannot carry significance**, as measured in
stage 14. The X score therefore measures reproducibility, and the strict
counts score nothing.

**Do not report either as a passed test.** Report what was measured.

---

## 10. Leave-one-study-out is five runs, not eight

Only five of the eight studies stage fibrosis. The other three carry no
F0–F4 labels, so there is nothing to leave out. Robustness is reported as
n/5.

The power-matched design uses **four** studies, not five: GSE193066 lacks
patients at some stage and cannot contribute an equal cell to every
transition.

---

## 11. The scoring scheme has two known structural biases

**T favours late-changing genes.** It reads F4 − F0 and ignores F1–F3, so a
gene that rises sharply at F0→F1 and then plateaus has a real early
trajectory but a small endpoint delta. X is the corrective — it finds the
largest jump wherever it falls — but T itself was left as defined rather than
tuned.

**At the top of the ranking, P does most of the work.** Dropping each score
and re-ranking gives Spearman ≥ 0.83 overall, so no single score drives the
ranking as a whole. But in the top band, removing P retains a minority of it.
The elite end of the list is more effect-size-driven than "five kinds of
evidence agree" suggests.

---

## 12. Figure 9 must not be read as the shortlist converging

**Only 6 of the 25 shortlisted genes reach any of the twelve mechanisms.**

This follows directly from the selection rule, which chose genes to be as
*unlike* one another as possible — one set per trajectory pattern, both
directions, no pathway dominating. Asking that set to converge is asking it
to undo its own design.

**The convergence visible in the figure is carried by the other Tier 1
genes.** Caption it as the Tier 1 mechanism network with the shortlist marked
inside it, which is what it is.

One mechanism in the twelve — a pancreatic ductal developmental pathway —
passes the statistics but is biologically implausible here and is likely an
annotation artifact. Check what drives it before putting it in a figure
legend.

---

## 13. No predictive model was built or validated

The stated aim is to predict disease stage. **No classifier was trained,
cross-validated or reported.** What this work delivers is the stage-resolved
gene sets and the quantified stage structure that such a model would be built
*from*.

Do not describe any output here as a predictor, a signature with known
accuracy, or a validated panel. There is no AUC, sensitivity, specificity or
held-out test set anywhere in these results.

---

## 14. Independent verification of the staging covers one study

The fibrosis stages come from each study's own GEO characteristics field, and
the harmonisation is verified: zero mismatches between the GEO field and the
stored value across all 1,085 samples.

Stage counts were additionally checked against the source publication for
**GSE162694**, and match exactly (31 normal histology, then 35/30/27/8/12).
The equivalent check against the published tables of the other four staging
studies has not been done.

---

## 15. Four genes have internally inconsistent direction

Two genes disagree between the sign of their correlation and their F0→F4
endpoint difference. Both have a weak correlation and a near-zero delta, so
this is two noise signals rather than two strong signals in conflict. They
are flagged in the tables and were not relabelled.
