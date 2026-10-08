# 5. Limitations — state these, never paper over them

Read this before writing any claim. Several results are narrower than they
first appear, and two tests in this project **cannot fail by construction**
and are labelled as such. Every limit here is measured, not speculative, and
each names the file where the measurement lives.

A limitation stated plainly in the paper costs a sentence. The same
limitation found by a reviewer costs the paper.

---

## 1. The cohort is cross-sectional, and F4 is underpowered

**Stage F4 has only 35 samples (34 usable patients)** against 127–186 for
every other stage. Its stage means are the noisiest in the study, and every
estimate involving F4 is the least precise.

The power-matched design (stage 12) addresses the *comparison* between
transitions by giving all four equal power. It does not make the F3→F4
estimate itself precise. Say "the transition into cirrhosis carries the
largest change", not "we precisely quantified the F3→F4 change".

There is also **no outcome, survival or longitudinal analysis** here. The 58
repeat biopsies in GSE193066 are handled as a pseudo-replication problem, not
as a time series. Nothing in this project establishes that a patient
*progresses* along these trajectories; it establishes that patients *at*
different stages differ. The trajectory language is about stage ordering, not
about followed individuals.

---

## 2. Demographic coverage is partial — 385 samples, not 1,085

Sex is recorded by five of the eight studies (540 samples) and age by four
(483 samples). Only **three studies record demographics and also stage
fibrosis**, so any analysis crossing stage with age or sex rests on **385
samples from GSE130970, GSE162694 and GSE193066**.

The per-stage gene table itself uses all **668** staged samples; only the
demographic splits are restricted. Every output file carries its own n so the
limit stays visible rather than assumed.

Sex is missing for 545 samples and age for 602. Sex was also written six ways
across studies (Female / female / F / Male / male / M) and is harmonised to
M/F. Grouping on the raw value silently splits every
group in two — the same class of bug as the F4/`4` fibrosis mismatch.

Files: `04_DATA/gene_tables/genes_by_stage_and_age.csv`,
`genes_by_stage_and_sex.csv`, `sample_demographics.csv`.

---

## 3. Label rulers differ per study, and the raw fields will mislead you

Each study recorded fibrosis on its own ruler: `"0".."4"`, `"F0".."F4"`,
`"normal liver histology"`. **Querying `fibrosis_stage_raw = '4'` returns 29
of the 35 real cirrhosis samples and reports no error.**

**Always use the harmonised `fibrosis_stage` / `disease_group` fields.** The
raw fields are retained only so the translation is auditable.

Four studies carry no disease label at all, deliberately (see
`04_DECISIONS.md` §7). Three of the five staged studies are the only ones
with both stage and demographics. Do not assume any field is populated for
all 1,085 samples — check.

---

## 4. Significant-gene counts are inflated by selection; the comparisons are not

The genes analysed in stages 11–14 were selected *because* they correlate
with fibrosis stage **in these same data**. Absolute counts of significant
genes are therefore inflated by selection and must not be read as unbiased
estimates of how many genes change.

**The comparisons remain fair**, because all four transitions and all five
clusters use the same gene set and carry the same inflation. The claim "the
largest change is at F3→F4" is valid; the claim "936 genes change at F3→F4"
is a count within a pre-selected set and should be phrased as such.

There is **no held-out validation cohort.** Leave-one-study-out (stage 14) is
internal cross-validation across the five staging studies, not external
replication.

---

## 5. Cluster shapes are solid; individual gene membership is not

**The five shapes are reproducible**: recovered at median correlation
0.97–0.997 across 100 patient bootstraps, and not created by study mix
(ARI 0.84 after study adjustment).

**Individual membership is much weaker.** Under patient bootstrap many genes
move between neighbouring clusters, mostly among the three increasing
clusters (C1/C2/C3), which differ only in timing. C2 and C5 have large stable
cores; **C1, C3 and C4 are dominated by borderline genes.**

**The rule:** report the shapes with confidence; for any statement about a
specific gene in a cluster, use `membership_confidence ≥ 0.8`
(`02_TABLES/supplementary/TableS2_gene_cluster_assignments.csv`).

Also note the clustering choice itself: **silhouette alone favours k = 3**,
and the ARI ≥ 0.95 rule that selected k = 5 was set after inspecting the
k = 3–6 solutions. That ordering should be disclosed in the Methods.

---

## 6. Two cluster-level biology claims must be narrowed

Repeating every enrichment with high-confidence members only:

| Cluster | Verdict |
|---|---|
| C2, C3, C5 | Hold up. Most top-10 terms stay significant. **State with confidence.** |
| **C1** | **Only partly.** 8 of 10 top GO BP immune terms survive, but with just 47 core genes its Hallmark, KEGG and Reactome terms do not. **State at the level of "immune activation" only.** |
| **C4** | **Too weak to judge.** 10 significant terms in total across all four databases, against 542 for C2. **Claim no theme.** |

File: `02_TABLES/supplementary/TableS10_cluster_core_check.csv`.

---

## 7. Figure 9 must not be read as if the 25 genes converge

This is the limitation most likely to be misread, because the figure looks
like convergence and the shortlist is what the paper foregrounds.

**Of the final 25, only 8 reach any of the twelve mechanisms, and only one
(PDGFRA) reaches three.** Among the 25, just two pathways connect two or more
of them, and **none connects three or more.**

This follows directly from the selection rule, which chose genes to be as
*unlike* each other as possible. Asking that set to converge is asking it to
undo its own design.

**The convergence visible in the figure comes from the other Tier 1 genes**:
166 of the 507 reach at least one of the twelve and 39 reach three or more;
across all Tier 1, 328 pathways connect two or more genes and 163 connect
three or more. The hubs doing that connecting are **COL1A1, COL1A2, COL3A1,
COL4A1/2/4, COL16A1, ITGAX, ITGB2, ITGB8 and TGFB1** — Tier 1 genes the
per-cluster cap kept *out* of the shortlist.

So: **the prioritised set and the mechanistically central set are not the
same set**, and that is a property of the selection rule, not of the biology.
Caption Figure 9 as the Tier 1 mechanism network with the 25 marked inside
it, which is what it is.

> **A correction to carry forward.** The README inside
> `03_RESULTS/Task5_high_confidence_genes/` states "168 of the 507 reach at
> least one of the twelve, and 24 reach three or more", and that none of the
> 25 reaches three. Recomputed from the supplementary workbook, the correct
> figures are **166**, **39**, and **one gene (PDGFRA) reaching three**. The
> 39 is confirmed independently by the figure's own composition: 38 Tier-1
> gene nodes plus PDGFRA. The analysis, the figure and the workbook are
> right; those three numbers in that one README are wrong. **Use the numbers
> in this file and in `03_STATISTICS.md` §7.**

---

## 8. Two validation tests cannot fail, and are labelled

**Leave-one-study-out on direction.** Every Tier 1 gene already has all five
studies agreeing on direction, so dropping one leaves four that still agree
and the median keeps its sign **by arithmetic**. All 507 genes score 5/5
without anything being tested. Significance on the remaining four studies,
and whether median |rho| stays ≥ 0.30, *can* fail and are reported beside it
— as is `LOSO_max_pct_drop_in_rho`, the column that actually discriminates
(MYC 2.6% against CACNA1C 37.3%).

**The power-matched analysis cannot carry significance.** At 30 patients per
stage with FDR across 3,645 genes, the number of genes significant in ≥ 50%
of draws is 0, 0, 0 and 297 across the four transitions. Scoring on that
would have handed every point to F3→F4. The X score therefore measures
**reproducibility**, not significance, and the strict counts are carried in
the table as `Matched_frac_significant_NOT_scored`, scoring nothing.

**Do not report either as if it were a passed test.** Report what was
measured.

---

## 9. Leave-one-study-out is 5 runs, not 8

Only five of the eight studies stage fibrosis (GSE130970, GSE135251,
GSE162694, GSE193066, GSE240729). The other three carry no F0–F4 labels, so
there is nothing to leave out. Robustness is reported as n/5.

The power-matched design uses **four** studies, not five: GSE193066 lacks
patients at some stage and cannot contribute an equal cell to every
transition.

---

## 10. The scoring scheme has two known structural biases

**T favours late-changing genes.** It reads F4 − F0 and ignores F1–F3, so a
gene that rises sharply at F0→F1 and then plateaus has a real early
trajectory but a small endpoint delta. C3 (early rise, then plateau) has 1
gene at T=2 out of 197; C4 has 9 of 309. X is the corrective — it finds the
largest jump wherever it falls, and 1,133 genes earn X=2 from a jump before
F3→F4 — but **T itself was left as defined rather than tuned.**

**At the top of the ranking, P does most of the work.** Dropping each score
and re-ranking gives Spearman ≥ 0.83 overall, so no single score drives the
ranking as a whole. But among the 135 genes scoring 8–9, removing P retains
only 49 (Jaccard 0.21). **The elite end of this list is more
effect-size-driven than "five kinds of evidence agree" suggests.**

**C4 is weak on two scores at once** — thinnest enrichment of any cluster and
61% of its genes scoring B=0 — so only 5 of 309 C4 genes reached Tier 1
(1.6%, against 22% for C2). The shortlist includes all five. **They are there
to represent mid-decreasing biology, not because that cluster is as well
supported as the others.**

---

## 11. The canonical collagens are in Tier 1 but not in the 25

Nine collagens reached Tier 1 (COL16A1, COL5A1, COL1A1, COL1A2, COL3A1,
COL4A1, COL4A2, COL4A4, COL8A2; scores 7–8), which confirms the method
recovers established fibrosis biology. **None are in the shortlist**: they sit
just below the top five of C1 and C2 on |rho| (COL1A1 0.448 against UNC5B
0.490).

If a reader asks why the best-known fibrosis genes are absent from the
headline list, this is the answer, and it is the cluster cap rather than a
judgement on them. Anticipate the question in the text.

---

## 12. No predictive model was built or validated

The project's stated aim is to predict disease stage. **No classifier was
trained, cross-validated or reported.** What this project delivers is the
stage-resolved gene sets and the quantified stage structure that such a model
would be built *from*.

Do not describe any output here as a predictor, a signature with known
accuracy, or a validated panel. There is no AUC, no sensitivity, no
specificity, no held-out test set anywhere in these results.

---

## 13. Link prediction is unresolved

The pipeline is built (`05_CODE/unresolved/`) but **the first model failed its
own validation**. Any drug-repurposing output is unverified. If the paper
mentions this direction, it belongs in future work, not results.

---

## 14. Figure 9 was built on the superseded knowledge layer — now fixed

**Resolved on 2026-10-08.** Recorded here because the error reached a
committed figure, and because the way it survived is worth knowing.

`hc4_kg_subgraph.py` read `data/graph_kg`, the PrimeKG layer this project
replaced, while its own docstring and the workbook's caveats sheet both said
it read "the same CSVs that were loaded into Neo4j". The counts had said
otherwise all along:

| | OptimusKG (`graph_okg`) | PrimeKG (`graph_kg`) | The graph |
|---|---|---|---|
| BioProcess nodes | **12,203** | 12,430 | 12,203 |
| Pathway nodes | **2,220** | 2,516 | 2,220 |
| INVOLVED_IN edges | **157,081** | 143,156 | 157,081 |
| IN_PATHWAY edges | **46,751** | 42,478 | 46,751 |

Nothing caught it because nothing compared the two.

**What the fix changed.** Seven of the twelve mechanisms are the same on
either layer, and the conclusion — convergence on extracellular matrix,
integrin signalling and inflammation — is unchanged. The three that left the
top twelve are still eligible on the correct layer, at ranks 14 (Signaling by
PDGF), 18 (Neutrophil degranulation) and 21 (collagen fibril organization).
Nothing disappeared; the ranking moved.

**One new mechanism needs a caption, not deletion.** "Developmental Lineage
of Pancreatic Ductal Cells" reads oddly in a liver paper. Its sixteen Tier 1
genes are ANXA2, AQP1, CD74, CLDN10, COL1A1, COL1A2, COL3A1, COL5A1, KRT23,
KRT7, LAMA2, LAMC2, LAMC3, PDX1, PROM1 and SOX9 — KRT7, SOX9, PROM1, AQP1 and
CLDN10 being cholangiocyte markers. Liver and pancreas share a foregut
origin, so the Reactome set is largely the generic ductal-epithelial
programme, which in liver is the **ductular reaction**, a known feature of
advancing fibrosis. The biology is apt; say so in the caption.

**The check that should have existed now does.** `verify_against_neo4j.py`
queries the live database and diffs it against the CSVs at four levels: node
counts, edge counts, gene counts per mechanism, and the gene IDs themselves —
the last being the one that matters, since counts can agree while sets
differ. Run on 2026-10-08, every level passed; the pancreatic pathway, for
instance, holds the same 48 genes in both, and the same 16 Tier 1 genes among
them. So Figure 9's provenance is now **checked**, not assumed, and a Methods
sentence saying it was filtered from the project's knowledge graph is correct
as written.


## 15. Four genes have internally inconsistent direction

DNPH1, FST, SLC5A10 and FUNDC2 disagree between the sign of their correlation
and their F0→F4 endpoint difference. All four have both a weak rho
(|rho| ≤ 0.18) and a near-zero delta, so this is two noise signals rather
than two strong signals in conflict. They are **flagged in the tables and were
not relabelled.** Direction agrees for 3,641 of 3,645 genes (99.9%).
