# 2. Methods, stage by stage

Each stage states what it does, why it is done that way, what it reads, what
it writes, and the numbers it produced. The script for each is named in its
heading and is in `05_CODE/`; commands are in `06_PROVENANCE/REBUILD.md`.

---

## Stage 1 — Data collection

Eight human liver transcriptome studies from GEO, each with bulk RNA-seq of
human liver biopsies and clinical severity information.

For every study two things were retrieved: the **supplementary expression
file** (the counts or TPM matrix) and the **series matrix**, which carries
per-sample clinical characteristics. The series matrix is what makes the
expression usable — without it a sample is an anonymous column.

**1,085 samples.** The exact filename taken from each study is recorded in
`06_PROVENANCE/DATA_SOURCES.md`.

---

## Stage 2 — Expression parsing
`05_CODE/pipeline/01_parse_expression.py`

Every study's expression file is converted into one long-format table:
`dataset_id, sample_key, gene_id_raw, gene_id_type, value, unit`.

**Why.** The eight files share no layout. One is a `.tar` of per-sample
files, one a `.gct`, the rest variously delimited matrices with different
header conventions, identifier types and units. Converting once means every
later stage reads one shape.

**Measured zeros are retained.** A gene reading zero in a sample is a
measurement, not a missing value, and treating it as missing would discard
the switching-on that carries progression signal: IL6 is detected in 10% of
stage-1 patients and 64% of stage-4 patients.

| Study | Genes | Samples | Identifier | Unit |
|---|---|---|---|---|
| GSE126848 | 19,786 | 57 | Ensembl | raw count |
| GSE130970 | 19,585 | 78 | Entrez | TPM |
| GSE135251 | 64,258 | 216 | Ensembl | raw count |
| GSE162694 | 31,683 | 143 | Ensembl | raw count |
| GSE167523 | 26,364 | 98 | symbol | raw count |
| GSE193066 | 17,231 | 164 | symbol | unspecified |
| GSE240729 | 42,364 | 67 | Ensembl | raw count |
| GSE269412 | 43,285 | 262 | Ensembl | raw count |

GSE193066's unit is not stated by the depositor. It does not affect any
result, because every analysis uses `value_z`, which is standardised within
study and cancels the unit.

---

## Stage 3 — Gene identifier harmonisation
`05_CODE/pipeline/02_map_gene_ids.py`

Every identifier is translated to one canonical Ensembl gene ID, version
stripped, using the HGNC complete set.

**Why.** Three studies label genes by symbol, one by Entrez ID, four by
Ensembl. Gene symbols are the worst case: they are reused and renamed over
time, so the same symbol can mean different genes in files from different
years. Without one namespace the same gene appears as several.

**How.** Unique identifiers per dataset are mapped and then joined, rather
than mapping 40 million rows. Nothing is silently dropped — anything that
fails to map is written to a report.

| Study | Type | Unique | Mapped | % |
|---|---|---|---|---|
| GSE126848 | Ensembl | 17,843 | 17,843 | 100.0 |
| GSE130970 | Entrez | 19,226 | 18,985 | 98.7 |
| GSE135251 | Ensembl | 41,894 | 41,894 | 100.0 |
| GSE162694 | Ensembl | 31,683 | 31,683 | 100.0 |
| GSE167523 | symbol | 22,781 | 21,256 | 93.3 |
| GSE193066 | symbol | 17,231 | 17,190 | 99.8 |
| GSE240729 | Ensembl | 41,930 | 41,930 | 100.0 |
| GSE269412 | Ensembl | 33,175 | 33,175 | 100.0 |

Losses fall exactly on the symbol-based studies, which is why the mapping is
done. All 1,807 unmapped identifiers are listed in
`04_DATA/harmonisation/unmapped_genes.csv`.

**Two correctness rules.** `_PAR_Y` rows (duplicated X/Y chromosome-tip
genes) are dropped. Where two raw identifiers collapse onto one Ensembl ID
their values are **summed** rather than one overwriting the other — a real
condition in this data, where studies from different years use a gene's old
and current symbol (`05_CODE/validation/check_gene_mapping.py` detects it).

---

## Stage 4 — Sample crosswalk
`05_CODE/pipeline/03_build_crosswalk.py`

A bridge from each expression file's column name to the GEO accession, which
is what the clinical data is keyed on. Without it the expression and clinical
halves cannot be joined.

Each dataset gets its own rule, and the script does not trust them: it
applies each rule, checks the result against the sample keys actually present
in the expression files, and reports a match rate per dataset. A rule that
works for four samples and fails on the fifth shows up as a match rate below
100% rather than silently producing a half-connected graph.

---

## Stage 5 — Clinical label harmonisation
`05_CODE/pipeline/04_normalize_clinical.py`

Four clean fields are **added** beside the originals: `fibrosis_stage`
(integer 0–4), `disease_group`, `patient_id` and `biopsy_number`. The `*_raw`
columns are never modified, so every translation stays auditable.

**Why.** Each study records severity on its own ruler — `"0".."4"` in four
studies, `"F0".."F4"` in GSE240729, and `"normal liver histology"` as a
stage-0 synonym in GSE162694. A query against the raw field returns 29 of the
35 cirrhosis samples and reports no error. **Always use the harmonised
field.**

**`patient_id` is not cosmetic.** GSE193066's 164 samples are 106 patients,
58 biopsied twice. Counting them as independent is pseudo-replication.

**Labels are assigned only where the evidence supports them:**

- **GSE162694** — GEO records tissue, age, sex, fibrosis stage and NAS score,
  and no diagnosis. Samples with normal liver histology are labelled
  `control`; the remaining 112 are labelled **NAFLD**, which is what the
  source publication calls them and is true of all of them. NAFLD does not
  place a patient on the control → NAFL → NASH ladder, because it does not
  say which rung, so this study contributes its fibrosis staging in full and
  does not contribute to the disease ladder.
- **GSE135251** — the same situation: 206 patients labelled NAFLD, subtype
  unstated.
- **GSE130970** — no stated diagnosis, but GEO carries its full Kleiner panel
  (steatosis, ballooning, lobular inflammation), which is what a diagnosis is
  scored from. The standard NASH-CRN definition is applied and the result
  flagged `derived_from_histology`, so it can be excluded with one filter.
- **GSE269412, GSE240729, GSE193066** — left blank. A blank field is a known
  unknown; a guessed label is an unknown unknown that contaminates every
  comparison built on it.

---

## Stage 6 — Standardisation within study (`value_z`)

Expression is standardised per gene within each study to mean 0, SD 1. This
is the quantity every later analysis uses.

**Why.** The studies differ in units, depth, platform and centre. Raw values
are not comparable between them. Standardising per gene within study removes
the study-level offset and scale, leaving each sample's position relative to
that study's own distribution.

A positive `value_z` means above average for that gene in that study. It does
not mean highly expressed.

**Why not a fitted batch correction.** Per-study standardisation cannot leak
information between cohorts the way a fitted correction can, and it keeps
each study's contribution auditable. Where a stage comparison needed more,
`study` is included as a model term instead (stage 10).

---

## Stage 7 — Measurement layer
`05_CODE/pipeline/05_build_graph_all.py`

Node and edge tables for the measurement half of the graph: every mapped
gene, every sample, every measurement.

**The full union is kept** — 53,993 genes, 32.5 million measurement edges —
rather than a filtered panel, so filtering happens at query time where it can
be revisited rather than at load time where it forecloses questions.

**The consequence is made visible.** Every gene carries `n_datasets` (1–8):
how many studies measured it. **39,199 genes are missing from at least one
study and 10,621 appear in exactly one.** A gene backed by one cohort is not
evidence of the same weight as one backed by eight. **Never average across
genes without checking it.**

---

## Stage 8 — Knowledge layer
`05_CODE/pipeline/06_build_optimuskg_layer.py`

Curated biology attached to the same gene identifiers: diseases, drugs,
pathways, biological processes, phenotypes, and the relationships between
them, from OptimusKG.

**Why this resource.** It identifies genes by Ensembl ID, the namespace stage
3 standardises on, so 50,725 of 53,993 genes join directly (94%). Its
drug–gene edges carry a **mode of action** — INHIBITOR, AGONIST, BLOCKER and
20 more — which matters for any therapeutic reading: to lower a rising gene
you need a drug that inhibits it. And it records drugs treating the diseases
of interest: **74 for NASH, 95 for NAFLD, 71 for cirrhosis**, including
Resmetirom and Belapectin.

**The evidence threshold.** OptimusKG ships 9.7 million gene–disease links
because it includes every Open Targets association however weak; the median
score is 0.026, and at that level 5,568 genes "link" to NAFLD — a third of
the genome. **Links are kept at score ≥ 0.1, and the score is stored on every
edge** so a query can tighten further without a reload. At that cut NAFLD
keeps 274 genes and cirrhosis 234, and PNPLA3, TM6SF2 and PPARG all survive.

**Deliberately excluded**, so the exclusion is a choice rather than an
oversight: drug–drug interactions (safety, not mechanism), anatomy–gene edges
("gene occurs in tissue"), and the environmental-exposure slice.

---

## Stage 9 — Progression genes
`05_CODE/pipeline/07_find_progression_genes.py`

The genes whose expression tracks position on each ladder. This is the stage
that answers the project's aim; everything after it analyses its output.

**How.** For each gene, **within each study separately**, `value_z` is
correlated against ladder position by Spearman correlation. Per-study rho
values are combined by their **median**, per-study p-values by **Fisher's
method**, then corrected by Benjamini–Hochberg. A gene is kept only when
**every study that tested it agrees on the direction**.

**Why Spearman.** The stages are ordered ranks whose spacing is not
meaningful — the biological distance F0→F1 is not assumed equal to F3→F4.

**Why per study, then combined.** Studies differ in cohort, depth and centre.
A gene that climbs in one study and does nothing in the other four is a quirk
of that cohort, and pooling would let the largest study drive a result alone.
Requiring agreement across independent studies is the validation principle of
the whole project.

**Two guards.** Each patient contributes one row — for the 58 twice-biopsied
patients the first biopsy is used, so the expression is paired with the stage
recorded at that same biopsy. And only genes measured in **all eight
studies** are tested — **14,794** of them — so every study contributes to
every gene.

**That 14,794 is also the enrichment background** used in stages 12 and 13.

**Result: 5,884 progression genes** — 3,681 on the fibrosis ladder, 4,018 on
the disease ladder.

---

## Stage 10 — Progression groups (Task 1)
`05_CODE/analysis/task1_groups.py`

| Group | Genes | % | Increasing | Decreasing |
|---|---|---|---|---|
| Fibrosis only | 1,866 | 31.7 | 1,212 | 654 |
| Inflammation only | 2,203 | 37.4 | 1,782 | 421 |
| Shared | 1,815 | 30.8 | 1,472 | 330 |

Among the shared genes, 13 are discordant — rising on one ladder and falling
on the other.

Agreement between the ladders among shared genes, Spearman of fibrosis rho
against inflammation rho: **0.657** overall.

**The 3,681 fibrosis-associated genes** (fibrosis-only + shared) are the
starting set for stages 11, 12 and 14.

---

## Stage 11 — Trajectory clustering (Task 2)
`05_CODE/analysis/task2_trajectories.py`

The 3,681 fibrosis genes grouped by the **shape** of their stage curve.

Each gene's five stage means are z-scored *across stages*, so genes group by
shape rather than magnitude. K-means, 50 random starts, k tested from 3 to 8,
assessed on silhouette score plus two stability measures: 50 reclusterings of
random 80% gene subsets, and 50 patient bootstraps.

**k = 5 is reported.** See `04_LIMITATIONS.md` for the basis of that choice
and what must be stated in the Methods.

| | Pattern | Genes | Confidently assigned |
|---|---|---|---|
| C1 | Early increase (F0→F1), then continued | 948 | 3 |
| C2 | Late increase (largest at F3→F4) | 1,528 | 772 |
| C3 | Early rise, then plateau | 209 | 1 |
| C4 | Mid decrease (largest at F1→F2) | 313 | 130 |
| C5 | Late decrease (largest at F3→F4) | 683 | 510 |

Clusters were named **after** clustering, from their average curves. No gene
was assigned to a pattern by hand.

**What is solid.** The five shapes are reproducible — recovered at median
correlation 0.96–0.996 across 100 patient bootstraps — and are not created by
study mix (ARI 0.82 after study adjustment, median per-gene curve correlation
0.998).

**What is not.** Individual gene membership is much weaker for C1 and C3.
`membership_confidence` is reported per gene, together with
`confidence_n_bootstraps`, the number of bootstraps in which that gene's
cluster was soundly matched and the gene could therefore be assessed.

---

## Stage 12 — Stage transitions (Task 3)
`05_CODE/analysis/task3_transitions.py`

For each gene and each adjacent stage pair: does it change, by how much, and
where is the change largest?

Tested at **patient level**, not from stage means. A linear model
`value_z ~ stage + study` is fitted on the patients of the two stages only —
including `study` means stages are compared **within** each study, so a
difference in stage mix between studies cannot manufacture a false change.
t-test on the stage coefficient, BH correction **within each transition**.
"Substantially changing" is q < 0.05 **and** |beta| ≥ 0.2 SD.

**Power-matched check.** F4 has 34 usable patients, so every transition is
refitted 50 times on the *same* study-balanced design of 30 patients per
stage, giving all four equal statistical power.

| | F0→F1 | F1→F2 | F2→F3 | F3→F4 |
|---|---|---|---|---|
| Substantially changing genes | 1,197 | 1,145 | 1,127 | 934 |
| Median \|beta\| | 0.189 | 0.185 | 0.221 | **0.375** |
| **Power-matched median** | **0** | **0** | **2** | **287** |

**The power-matched row is the result.** On the full data the first three
transitions each show ~1,100–1,200 changing genes and F3→F4 shows fewer — but
F3→F4 rests on 34 patients against 109–166. Once power is equalised, F3→F4
dominates, with effect sizes about twice as large. Earlier transitions show
**many small consistent changes that need large samples to detect**; the
transition into cirrhosis shows **fewer but much larger changes**.

Direction has a clear ordering too: F0→F1 is almost entirely increases
(1,164 up against 33 down); decreases begin at F1→F2 (506 down).

---

## Stage 13 — Pathway enrichment (Task 4)
`05_CODE/analysis/task4_enrichment.py`

One-sided hypergeometric test, BH correction **within each group × database**,
significant at FDR < 0.05. Four databases from MSigDB v2024.1: GO Biological
Process, KEGG legacy, Reactome, Hallmark.

**Each group is tested separately** — six ladder groups, five clusters, and
the clusters again using only confidently assigned members — never all genes
together, which would average away the distinctions the grouping exists to
make.

**The background is the methodological core of this stage.** The **14,794**
genes eligible for cross-study analysis, not all ~20,000 human genes. Every
gene set is first restricted to those genes and kept only if 10–500 remain.
Using the whole genome would overstate enrichment for any term whose members
are preferentially well measured.

**The biology.**

- **Fibrosis-only increasing** — immune cell activation (myeloid, T cell),
  IL6–JAK–STAT3, allograft rejection, inflammatory response.
- **Fibrosis-only decreasing** — fatty-acid, xenobiotic and bile-acid
  metabolism: the loss of normal liver metabolism.
- **Shared increasing** — the core fibrogenic programme: extracellular matrix
  and collagen formation, epithelial–mesenchymal transition, TNFα–NFκB,
  apoptosis, p53.
- **Shared decreasing** — amino-acid and organic-acid catabolism, xenobiotic
  and bile-acid metabolism, coagulation.
- **C1 early increase** — adaptive immunity, T-cell activation,
  interferon-gamma. **Immune activation is established early.**
- **C2 late increase** — EMT, matrix organisation, cell migration, hypoxia,
  TNFα–NFκB. **Scarring accelerates late.**
- **C3 early rise** — cell cycle: E2F targets, G2/M checkpoint, chromosome
  segregation.
- **C4 mid decrease** — xenobiotic metabolism, metal-ion response. Few terms.
- **C5 late decrease** — bile-acid, fatty-acid and xenobiotic metabolism,
  peroxisome: metabolic failure as cirrhosis develops.

---

## Stage 14 — Gene prioritisation and mechanism network (Task 5)
`05_CODE/prioritisation/hc0`–`hc4`

The 3,681 fibrosis genes ranked by **how many independent kinds of evidence
agree**, rather than by p-value — every gene in the set already satisfies a
false-discovery threshold, so re-reading the same number adds nothing.

**Five scores, each reading a different property of the data.** All cutoffs
were fixed as named constants before any ranked list was inspected.

| | Score | 2 points | 1 point |
|---|---|---|---|
| **P** | Progression strength | \|rho\| ≥ 0.40 | ≥ 0.30 |
| **T** | Trajectory | \|F4 − F0\| ≥ 1.0 SD | ≥ 0.5 SD (0 if direction conflicts) |
| **X** | Transition | largest jump substantial in the full fit **and** reproducible in ≥ 50% of 50 equal-power draws | one of the two |
| **F** | Fibrosis specificity | — | fibrosis-only (shared scores 0) |
| **B** | Biological support | enriched terms in ≥ 2 of four databases | in 1 |

Total out of 9. **Tier 1 = 7–9 (525 genes)**, Tier 2 = 5–6 (1,464), Tier 3 =
below 5 (1,692).

Specificity is deliberately worth one point, so it acts as a tie-breaker
rather than a filter that would purge the shared genes.

**Sensitivity is measured and reported, never used to pick the cutoffs.**
Lowering the Tier 1 bar to 6 widens it while retaining all 525; raising it to
8 narrows it sharply. Dropping each score in turn leaves Spearman
correlations of 0.83–0.95 against the full ranking.

**X scores reproducibility, not significance.** At 30 patients per stage with
correction across 3,681 genes, the number of genes significant in ≥ 50% of
draws is 0, 0, 0 and 292 across the four transitions. Scoring on significance
would award every point to F3→F4 and exclude the three earlier transitions.
The strict counts are carried in the table as
`Matched_frac_significant_NOT_scored`, scoring nothing.

**The shortlist: top five Tier 1 genes per cluster**, ties broken by |rho|.
Five is the Tier 1 membership of the smallest cluster, so it is the largest
number at which all five clusters contribute equally. Result: **25 genes** —
15 increasing, 10 decreasing, 14 shared, 11 fibrosis-only, all five shapes,
and all four transitions represented as the site of largest change.

**Leave-one-study-out validation.** Each Tier 1 gene refitted five times, once
with each fibrosis-staging study withheld. Reported per gene: direction
retained, still significant, median |rho| still ≥ 0.30, and the largest
percentage loss in correlation across the five refits.

**The mechanism network (Figure 9).** Enrichment establishes which processes
are over-represented; it cannot say which gene connects to which mechanism,
or where several genes meet on the same one. Each graph node was tested the
way stage 13 tested its gene sets — hypergeometric against the same
14,794-gene background, BH across nodes — and kept if it holds 10–500
background genes, reaches at least 10 Tier 1 genes, and passes FDR 0.05;
ranked by q-value, near-duplicates collapsed, top twelve retained.

Ranking by q rather than gene count matters: count alone promotes terms that
appear in almost any gene list and are enriched here only 2–3×, against
3.4–9.6× for the twelve retained.

In this schema pathways and biological processes both attach to genes and not
to one another, so a gene's pathway and process memberships are two separate
connections rather than a chain. Convergence reads in the ordinary way, as
two genes meeting at one node.
