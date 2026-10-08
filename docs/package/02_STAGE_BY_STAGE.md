# 2. What we did, stage by stage

Fourteen stages, in the order they were run. Each one states what it does,
why it exists, how it does it, what it reads, what it writes, the numbers it
produced, and — where there was one — the trap it avoids. There is also one
strand that did not work, documented at the end rather than hidden.

The script for each stage is named in its heading and is in `05_CODE/`.
Commands are in `06_PROVENANCE/REBUILD.md`.

---

## Stage 1 — Collecting the datasets

**What.** Eight human liver transcriptome studies downloaded from GEO, chosen
because each has bulk RNA-seq of human liver biopsies with some form of
clinical severity information.

**How.** For each study, two things were retrieved: the **supplementary
expression file** (the counts or TPM matrix) and the **series matrix** (the
per-sample clinical characteristics). The series matrix is what makes the
expression usable — without it a sample is an anonymous column.

**What it produced.** 1,085 samples, 104 MB of compressed downloads. The
exact filename taken from each study is recorded in
`06_PROVENANCE/DATA_SOURCES.md`.

**Not shipped in this package.** The raw downloads are regenerable from GEO
and are not needed to check any result. Their provenance is recorded instead.

---

## Stage 2 — Parsing expression into one long format
`05_CODE/pipeline/01_parse_expression.py`

**What.** Every study's expression file converted into one common long-format
table: `dataset_id, sample_key, gene_id_raw, gene_id_type, value, unit`.

**Why.** The eight files share no layout. One is a `.tar` of per-sample
files, one is a `.gct`, the rest are variously delimited matrices with
different header conventions, different identifier types and different units.
Any analysis written against eight layouts is eight analyses. Converting once
to a long format means every later stage reads one shape.

**What it produced.** 40,654,247 measurements across eight files.

| Study | Genes | Samples | Identifier type | Unit |
|---|---|---|---|---|
| GSE126848 | 19,786 | 57 | Ensembl | raw count |
| GSE130970 | 19,585 | 78 | Entrez | TPM |
| GSE135251 | 64,258 | 216 | Ensembl | raw count |
| GSE162694 | 31,683 | 143 | Ensembl | raw count |
| GSE167523 | 26,364 | 98 | symbol | raw count |
| GSE193066 | 17,231 | 164 | symbol | unknown |
| GSE240729 | 42,364 | 67 | Ensembl | raw count |
| GSE269412 | 43,285 | 262 | Ensembl | raw count |

`04_DATA/harmonisation/_parse_summary.csv` is this table as produced by the
script.

**The decision that matters here.** The parser can drop measured zeros
(`--drop-zeros`) and the project deliberately **does not**. See
`04_DECISIONS.md` — this is the single most consequential choice in the
pipeline.

---

## Stage 3 — Harmonising gene identifiers
`05_CODE/pipeline/02_map_gene_ids.py`

**What.** Every gene identifier translated into one canonical identifier —
Ensembl gene ID, version stripped — using the HGNC complete set as the
dictionary.

**Why.** Three studies label genes by symbol, one by Entrez ID, four by
Ensembl ID. Gene symbols are the worst case: they are reused and renamed over
time, so the same symbol can mean different genes in files from different
years. Without one namespace, the same gene appears as several genes and no
cross-study comparison is valid.

**How, and why that way.** The script maps the **unique identifiers per
dataset** (roughly 17,000–42,000 of them) and then joins, rather than mapping
40 million rows one at a time. Nothing is silently dropped: anything that
fails to map is written to a report for inspection.

**What it produced.**

| Study | Type | Unique IDs | Mapped | % | Unmapped |
|---|---|---|---|---|---|
| GSE126848 | Ensembl | 17,843 | 17,843 | 100.0 | 0 |
| GSE130970 | Entrez | 19,226 | 18,985 | 98.7 | 241 |
| GSE135251 | Ensembl | 41,894 | 41,894 | 100.0 | 0 |
| GSE162694 | Ensembl | 31,683 | 31,683 | 100.0 | 0 |
| GSE167523 | symbol | 22,781 | 21,256 | 93.3 | 1,525 |
| GSE193066 | symbol | 17,231 | 17,190 | 99.8 | 41 |
| GSE240729 | Ensembl | 41,930 | 41,930 | 100.0 | 0 |
| GSE269412 | Ensembl | 33,175 | 33,175 | 100.0 | 0 |

The two symbol-based studies are exactly where the losses fall, which is the
expected result and the reason the mapping was done at all. Every unmapped
identifier is listed in `04_DATA/harmonisation/unmapped_genes.csv` — 1,807
rows, inspectable rather than assumed.

**Two correctness fixes carried forward.** `_PAR_Y` rows (duplicated
X/Y-chromosome tip genes) are dropped, and where two raw identifiers collapse
onto one Ensembl ID their values are **summed** rather than one silently
overwriting the other.

**Outputs.** `04_DATA/harmonisation/gene_id_map.csv`,
`_mapping_summary.csv`, `unmapped_genes.csv`.

---

## Stage 4 — Connecting expression columns to GEO samples
`05_CODE/pipeline/03_build_crosswalk.py`

**What.** A bridge from each expression file's column name (`sample_key`) to
the GEO accession (`GSM...`), which is what the clinical data is keyed on.

**Why.** Each study names its expression columns differently, and none of
them uses the GSM accession. Without this bridge the expression half and the
clinical half of the data cannot be joined at all.

**How, and the safeguard.** Each dataset gets its own small rule. The script
does not trust the rules: it applies each one, checks the result against the
sample keys actually present in the expression files, and reports the match
rate per dataset. A rule that works for the first four samples and fails on
the fifth shows up here as a match rate below 100%, rather than silently
producing a half-connected graph.

**Output.** `04_DATA/harmonisation/sample_crosswalk.csv`, 1,085 rows.

---

## Stage 5 — Harmonising the clinical labels
`05_CODE/pipeline/04_normalize_clinical.py`

**What.** The patient side harmonised the way stage 3 harmonised the gene
side. Four clean fields are **added**: `fibrosis_stage` (integer 0–4, blank
where the study never staged), `disease_group` (one of control, obese, NAFL,
NASH, NAFLD), `patient_id`, and `biopsy_number`.

**Why — this is the bug that justifies the whole stage.** Each study recorded
severity on its own ruler:

- fibrosis: `"0".."4"` in four studies, `"F0".."F4"` in GSE240729, and
  `"normal liver histology"` as a stage-0 synonym in GSE162694;
- disease: healthy/obese/NAFLD/NASH in one study, control/early/moderate in
  another, NAFL/NASH in a third.

A query for `fibrosis_stage_raw = '4'` therefore returns **29 of the 35 real
cirrhosis samples and reports no error**. A silent 17% undercount with no
warning is far more dangerous than a crash. The harmonised field removes it.

**Raw fields are never modified.** The `*_raw` originals sit beside the clean
ones, so every translation remains auditable. Always use the harmonised
field.

**`patient_id` is not cosmetic.** GSE193066's 164 samples are 106 patients,
58 biopsied twice (confirmed against the study's own GEO characteristics and
its paper, PMID 35731891). Counting them as 164 independent people is
pseudo-replication and inflates significance in any test run across that
study. No other dataset repeats a patient.

**One label set was recovered.** GSE162694 encodes diagnosis in its sample
titles (`nash12_F3` → NASH, `nash100_N` → control). The suffix was
cross-checked against `fibrosis_stage_raw` for all 143 samples and agreed on
every one, so it was trusted.

**One label set was recovered and then rejected.** GSE193066's
`sample_description` looks like a diagnosis (`NAFLD.HUn106.gct` / `NASH.*`),
but reading it that way produced a group that was *more* fibrotic (mean stage
2.16 against 1.78) and yet had *lower* COL1A1 than its NAFL group — backwards
for collagen, and contradicting that study's own staging. Every other study
runs the correct direction. The string also splits 106/58, which matches the
processed-file batches rather than the 116/48 split of the sample titles. It
encodes a file batch, not a diagnosis, so the study is **left unlabelled**.

**One label set was derived, and marked as derived.** GSE130970 states no
diagnosis but GEO carries its full Kleiner panel — steatosis, ballooning,
lobular inflammation — which is what a pathologist scores a diagnosis *from*.
The standard NASH-CRN definition was applied (steatosis 0 → control;
ballooning ≥ 1 → NASH; steatosis ≥ 1 with ballooning 0 → NAFL) and the result
flagged `derived_from_histology`, so it can be excluded with one filter.

**Four studies are deliberately left blank**: GSE269412 (GEO stores only
`{"tissue": "Liver"}`, titles are anonymised codes, no join key exists),
GSE240729 (fibrosis score only), GSE167523 and GSE126848 (diagnosed but never
staged), GSE193066 (see above). **A blank field is a known unknown; a guessed
label is an unknown unknown** that would quietly contaminate every group
comparison built on it.

**Output.** The harmonised clinical table, shipped here as
`04_DATA/gene_tables/sample_demographics.csv` and summarised as
`02_TABLES/main/Table1_cohort.csv`.

---

## Stage 6 — Standardising expression within study (`value_z`)

**What.** Expression standardised per gene *within each study* to mean 0 and
standard deviation 1. This is the quantity called `value_z`, and it is what
every later analysis uses.

**Why.** The eight studies differ in units (raw counts, TPM, one unknown),
sequencing depth, platform and centre. Raw values are simply not comparable
between them. Standardising per gene within study removes the study-level
offset and scale, leaving each sample's position relative to that study's own
distribution for that gene — which *is* comparable.

**What it means when reading any table here.** A positive `value_z` means
above average for that gene in that study. It does not mean highly expressed.
Values from different genes are on the same scale; values of the same gene
from different studies are each relative to their own study.

---

## Stage 7 — Building the expression graph
`05_CODE/pipeline/05_build_graph_all.py`

**What.** Neo4j-ready node and edge CSVs for the measurement layer: every
mapped gene, every sample, every measurement as an `EXPRESSES` edge.

**Why the full union and not a filtered panel.** An earlier pilot kept only
genes that were both in a curated panel and present in all eight studies —
290 genes and 311,322 edges. That forecloses every question not anticipated
when the panel was written. This stage drops both filters and keeps the
union: **53,993 genes**, 32.5 M measurement edges. Filtering moves from load
time to query time, where it can be revisited.

**The consequence is made visible rather than hidden.** Every Gene node
carries `n_datasets` (1–8): how many studies measured that gene. **39,199 of
the 53,993 genes are missing from at least one study and 10,621 appear in
exactly one.** Those are real measurements, but a gene backed by one cohort
is not evidence of the same weight as one backed by eight. `n_datasets` is
what lets a query say so instead of silently averaging across them. **Never
average across genes without checking it.**

**Output.** Node and per-study edge CSVs (2.1 GB, regenerable, not shipped).
The gene and dataset node tables *are* shipped, in
`04_DATA/graph_nodes/`, because `n_datasets` is needed to interpret any gene
list.

---

## Stage 8 — Adding the knowledge layer
`05_CODE/pipeline/06_build_optimuskg_layer.py`

**What.** Curated biology attached to the same gene identifiers: diseases,
drugs, pathways, biological processes, phenotypes, and the relationships
between them.

**Why OptimusKG and not PrimeKG.** PrimeKG was used first and replaced, after
checking the one thing that actually mattered — drugs recorded as treating
liver disease:

| | NASH | NAFLD | Cirrhosis |
|---|---|---|---|
| PrimeKG | 0 | 0 | 0 |
| OptimusKG | 74 | 95 | 71 |

With zero known drug–disease links there is nothing for a link-prediction
model to learn from, and the whole downstream step was blocked. OptimusKG
also carries Resmetirom (the first approved NASH drug, March 2024, after
PrimeKG was built) and Belapectin, which targets galectin-3 — LGALS3, a gene
this project's own progression analysis found independently.

Two further gains: OptimusKG identifies genes by **Ensembl ID**, the same
namespace stage 3 standardised on, so the join is direct — 50,725 of 53,993
genes match (94%) against 26,223 (49%) for PrimeKG; and its drug–gene edges
carry a **mode of action** (INHIBITOR, AGONIST, BLOCKER and 20 more) where
PrimeKG had one untyped "acts on". For repurposing that distinction is the
whole point: to lower a rising gene you need a drug that inhibits it.

**The evidence threshold, and why there is one.** OptimusKG ships 9,734,774
gene–disease links because it includes every Open Targets association however
weak. The median score is 0.026; a score of 0.0015 means one paper mentioned
the pair once. Taken whole, 5,568 genes "link" to NAFLD — a third of the
genome — and a graph where everything connects to everything cannot support
prediction. **Links are kept at score ≥ 0.1, and the score is stored on every
edge** so a query can tighten further without a reload. At that cut NAFLD
keeps 274 genes and cirrhosis 234, comparable to PrimeKG's 139 and 104 but
each properly evidenced, and PNPLA3 (1,900 studies), TM6SF2 and PPARG all
survive.

**Deliberately excluded**, and listed so the exclusion is a choice rather than
an oversight: drug–drug interactions (safety, not disease mechanism),
anatomy–gene edges ("gene occurs in tissue", mostly noise here), and the
environmental-exposure slice. Any of them can be added later.

**Output.** `04_DATA/knowledge_layer_optimuskg/` — the node and edge CSVs,
shipped in full (132 MB). Its counts match the graph described in
`01_OVERVIEW.md` exactly (BioProcess 12,203, Pathway 2,220, INVOLVED_IN
157,081, IN_PATHWAY 46,751), which is how we know this is the layer that was
loaded.

**The superseded PrimeKG layer also ships**, as
`04_DATA/knowledge_layer_primekg_superseded/`, because the stage 14 mechanism
subgraph reads it rather than the OptimusKG layer. That is a real
inconsistency and it is documented in `05_LIMITATIONS.md` section 14 — read
it before writing about Figure 9's provenance.

---

## Stage 9 — Finding the progression genes
`05_CODE/pipeline/07_find_progression_genes.py`

**What.** The genes whose expression tracks position on each ladder. This is
the stage that answers the project's aim, and everything after it is analysis
of its output.

**How.** For each gene, **within each study separately**, correlate `value_z`
against ladder position by Spearman correlation. Per-study rho values are
combined by their **median**, and the per-study p-values by **Fisher's
method**, then corrected by Benjamini–Hochberg. A gene is kept only when most
studies agree on the direction of change.

**Why Spearman.** The stages are ordered ranks whose spacing is not
meaningful — the biological distance from F0 to F1 is not assumed equal to F3
to F4. A rank correlation is the right tool; Pearson would impose linear
spacing the data does not support.

**Why per study and then combined, never pooled.** Studies differ in cohort,
sequencing depth and centre. A gene that climbs beautifully in one study and
does nothing in the other four is a quirk of that cohort, not biology.
Pooling patients would let one large study drive a result on its own.
Requiring **agreement across independent studies** is the same rule that
validated the recovered GSE162694 labels and caught the bad GSE193066 ones,
and it is the project's central validation principle.

**Two guards.** Samples are collapsed to one row per `patient_id` per study
before any statistic (the GSE193066 repeat-biopsy problem of stage 5). And
only genes measured in **all eight studies** are tested — 14,794 of them — so
that every study contributes to every gene.

**That 14,794 is also the enrichment background** used in stages 13 and 14.
Using all ~20,000 human genes instead would overstate enrichment for any term
whose members are preferentially well measured, and it materially changes
which terms reach significance.

**What it produced.** **4,692 progression-associated genes**: 1,953 fibrosis
only, 1,047 inflammation only, 1,692 both. Full statistics for all 14,794
tested genes, significant or not, are in
`04_DATA/progression_statistics/`.

---

## Stage 10 — Splitting the genes into groups (Task 1)
`05_CODE/analysis/task1_groups.py` → `03_RESULTS/Task1_gene_groups/`

**What.** The 4,692 genes partitioned by which ladder they track and in which
direction.

**Results.**

| Group | Genes | % | Increasing | Decreasing |
|---|---|---|---|---|
| Fibrosis only | 1,953 | 41.6 | 1,301 | 652 |
| Inflammation only | 1,047 | 22.3 | 597 | 450 |
| Shared | 1,692 | 36.1 | 1,335 (both up) | 356 (both down) |

Among the 1,692 shared genes **exactly one is discordant** — GPD1, rising on
one ladder and falling on the other.

**Agreement between the ladders** among shared genes, Spearman of fibrosis
rho against inflammation rho: **0.725 overall** (p = 2.9 × 10⁻²⁷⁶), but 0.453
within rising genes (n = 1,335) and 0.354 within falling genes (n = 356). The
overall figure is partly an artefact of two separate clouds; **quote the
within-direction values**, which are the conservative estimate. Figure 3.

**The 3,645 fibrosis-associated genes** (1,953 fibrosis-only + 1,692 shared)
are the starting set for stages 11, 12 and 14.

---

## Stage 11 — Clustering the F0→F4 trajectories (Task 2)
`05_CODE/analysis/task2_trajectories.py` → `03_RESULTS/Task2_trajectories/`

**What.** The 3,645 fibrosis genes grouped by the **shape** of their stage
curve.

**How.** Each gene's five stage means were z-scored *across stages*, so that
genes group by shape rather than by magnitude. K-means (50 random starts),
k tested from 3 to 8, k chosen from silhouette score plus two stability
measures: 50 reclusterings of random 80% gene subsets, and 50 patient
bootstraps (resampled within study, stage means recomputed, reclustered),
each scored by adjusted Rand index against the full-data clustering.

| k | Silhouette | Gene-subsample ARI | Patient-bootstrap ARI |
|---|---|---|---|
| 3 | 0.560 | 0.981 | 0.754 |
| 4 | 0.461 | 0.968 | 0.564 |
| **5** | **0.338** | **0.957** | **0.526** |
| 6 | 0.291 | 0.932 | 0.464 |
| 7 | 0.280 | 0.795 | 0.423 |
| 8 | 0.258 | 0.757 | 0.367 |

**Rule: the largest k with gene-subsample ARI ≥ 0.95 → k = 5.** Stated
honestly: silhouette alone favours k = 3, and this rule was set *after*
inspecting the k = 3–6 curves, because k = 3 and 4 visibly merge different
shapes (the two decreasing ones) and k = 6 splits the late-increase cluster
into two near-identical halves. Clusters were named **after** clustering from
their average curves; no gene was assigned to a pattern by hand.

**The five clusters.**

| | Pattern | Genes | High-confidence members |
|---|---|---|---|
| C1 | Early increase (F0→F1), then continued | 927 | 47 |
| C2 | Late increase (largest at F3→F4) | 1,514 | 841 |
| C3 | Early rise, then plateau | 197 | 36 |
| C4 | Mid decrease (largest at F1→F2) | 309 | 78 |
| C5 | Late decrease (largest at F3→F4) | 698 | 423 |

C3 was first named "rise to F3, then reverse" from its stage means. Stage
12's patient-level test found **no significant F3→F4 drop at all** (0 of 197
genes), so it was renamed. Its core genes are cell-cycle genes (ANLN, ASPM,
KIF20A, RRM2, TTK, TOP2A).

**What is solid and what is not — read this before writing about clusters.**

- **The five shapes are reproducible.** Across 100 patient bootstraps each
  shape was recovered with median correlation 0.97–0.997 to the original.
- **The study mix does not create them.** Stage profiles re-estimated as
  `value_z ~ stage + study` correlate 0.998 (median per gene) with the plain
  stage means, and reclustering those gives ARI 0.84 with the main clusters.
- **Individual gene membership is much less certain.** Under patient
  bootstrap many genes move between neighbouring clusters, mostly among the
  three increasing ones, which differ only in timing.
  `membership_confidence` — the fraction of 100 bootstraps in which a gene
  keeps its cluster — is given per gene. C2 and C5 have large stable cores;
  C1, C3 and C4 are dominated by borderline genes.

**Report the shapes with confidence. For any claim about a specific gene in a
cluster, use the high-confidence members** (`membership_confidence ≥ 0.8`).

---

## Stage 12 — Comparing the four stage transitions (Task 3)
`05_CODE/analysis/task3_transitions.py` → `03_RESULTS/Task3_transitions/`

**What.** For each of the 3,645 genes and each transition F0→F1, F1→F2,
F2→F3, F3→F4: does the gene change, by how much, and where is the change
largest?

**How.** Tested at **patient level**, not from stage means:

1. `delta_mean` — the plain difference of stage means.
2. `beta_adjusted` — a linear model `value_z ~ stage + study` fitted on the
   patients of the two stages only. Including `study` means stages are
   compared **within** each study, so a difference in stage mix between
   studies cannot manufacture a false change. Studies lacking either stage
   are left out of that transition.
3. t-test on beta, Benjamini–Hochberg **within each transition**.
4. "Substantially changing" = q < 0.05 **and** |beta| ≥ 0.2 SD.
5. **Power-matched check.** F4 has only 34 usable patients, so every
   transition was refitted 50 times on the *same* study-balanced design of
   30 patients per stage (GSE130970 2, GSE135251 14, GSE162694 8, GSE240729
   6), giving all four transitions equal statistical power.

Patients are counted once: repeat biopsies at the same stage are averaged (28
patients), and a patient biopsied on both sides of a transition keeps one
sample, chosen at random under a fixed seed (24 patients).

**Results.**

| | F0→F1 | F1→F2 | F2→F3 | F3→F4 |
|---|---|---|---|---|
| Patients (a / b) | 152/166 | 160/165 | 165/109 | 118/34 |
| Substantially changing genes | 1,165 | 1,175 | 1,117 | 936 |
| — increasing | 1,135 | 647 | 906 | 865 |
| — decreasing | 30 | 528 | 211 | 71 |
| Median \|beta\| | 0.188 | 0.189 | 0.221 | **0.378** |
| Genes with \|beta\| ≥ 0.2 | 1,699 | 1,693 | 2,043 | 2,710 |
| **Power-matched, median genes** | **0** | **0** | **2** | **311** |

**The result, and why the power-matched row is the one that matters.** On the
full data the first three transitions each show ~1,100–1,200 changing genes
and F3→F4 shows 936 — fewer, which looks like the opposite of the real
answer. But F3→F4 rests on 34 patients against 109–166 for the others. Once
power is equalised, F3→F4 dominates completely: a median of **311** genes
against 0–2, with typical effect sizes about twice as large. Earlier
transitions show **many small consistent changes that need large samples to
detect**; the transition into cirrhosis shows **fewer but much larger
changes**.

**Direction has a clear ordering too.** F0→F1 is almost entirely increases
(1,135 up against 30 down). Decreases begin mainly at F1→F2 (528 down).

**Per-cluster check that fed back into stage 11.** For C3 at F3→F4 the median
beta is −0.04 and **0 of 197 genes change significantly**, so the apparent
drop at F4 in its stage means is not supported at patient level — which is
why that cluster was renamed.

---

## Stage 13 — Pathway enrichment per group (Task 4)
`05_CODE/analysis/task4_enrichment.py` → `03_RESULTS/Task4_enrichment/`

**What.** Which biological processes are over-represented in each gene group
and each trajectory cluster.

**How.** One-sided hypergeometric test (`gseapy.enrich`, run locally),
Benjamini–Hochberg **within each group × database**, significant at FDR <
0.05. Four databases, MSigDB v2024.1 human symbols: GO Biological Process,
KEGG legacy, Reactome, Hallmark.

**Each group is tested separately and never all 4,692 genes together**, which
would average away exactly the distinctions the grouping exists to make.

**The background is the methodological core of this stage.** The 14,794 genes
eligible for cross-study analysis — those measured in all eight studies — not
all ~20,000 human genes. Every gene set was first restricted to those 14,794
genes and then kept only if 10–500 of them remained (GO BP 4,853 sets, KEGG
183, Reactome 1,279, Hallmark 50). **Using the whole genome as background
invalidates this stage**, because it overstates enrichment for any term whose
members are preferentially well measured. One p-value was recomputed directly
from SciPy's hypergeometric distribution and matched gseapy exactly.

**Significant terms (FDR < 0.05).**

| Group | Genes | GO BP | KEGG | Reactome | Hallmark |
|---|---|---|---|---|---|
| Fibrosis only, rising | 1,301 | 234 | 35 | 18 | 7 |
| Fibrosis only, falling | 652 | 106 | 26 | 33 | 8 |
| Inflammation only, rising | 597 | 2 | 1 | 30 | 2 |
| Inflammation only, falling | 450 | **0** | **0** | **0** | **0** |
| Shared, rising | 1,335 | 446 | 27 | 71 | 30 |
| Shared, falling | 356 | 62 | 22 | 19 | 5 |
| C1 early increase | 927 | 348 | 47 | 50 | 15 |
| C2 late increase | 1,514 | 542 | 20 | 48 | 21 |
| C3 early rise, plateau | 197 | 85 | 3 | 29 | 3 |
| C4 mid decrease | 309 | 5 | 1 | 2 | 2 |
| C5 late decrease | 698 | 159 | 35 | 38 | 7 |

**The biology.**

- **Fibrosis-only rising** — immune cell activation (myeloid, T cell),
  IL6–JAK–STAT3, allograft rejection, inflammatory response.
- **Fibrosis-only falling** — xenobiotic, fatty-acid and bile-acid
  metabolism, peroxisome: the loss of normal liver metabolism.
- **Inflammation-only** — weak. Interferon-alpha response and G2/M among
  rising genes; **nothing at all** among falling genes. Most interpretable
  inflammatory biology in these data is shared with the fibrosis ladder
  rather than specific to inflammation.
- **Shared rising** — the strongest signal of any group, and the core
  fibrogenic programme: extracellular matrix and collagen formation,
  epithelial–mesenchymal transition, TNFα–NFκB, apoptosis, p53, angiogenesis.
- **Shared falling** — amino-acid and organic-acid catabolism, xenobiotic and
  bile-acid metabolism, coagulation.
- **C1 early increase** — adaptive immunity, T-cell activation,
  interferon-gamma, allograft rejection. **Immune activation starts early.**
- **C2 late increase** — EMT, matrix organisation, cell migration,
  TNFα–NFκB, hypoxia, TGF-beta. **Scarring accelerates late.**
- **C3 early rise** — cell cycle: E2F targets, G2/M checkpoint, chromosome
  segregation, mitotic spindle.
- **C4 mid decrease** — few terms, no clear theme.
- **C5 late decrease** — bile-acid, fatty-acid and xenobiotic metabolism,
  peroxisome: metabolic failure as cirrhosis develops.

**The robustness check, which narrows two of these claims.** Every cluster
analysis was repeated using only high-confidence cluster members. C2, C3 and
C5 hold up (most top-10 terms stay significant). **C1 only partly** — 8 of
its top 10 GO BP immune terms survive, but with just 47 core genes its
Hallmark, KEGG and Reactome terms do not. **C4 is too weak to judge.** So:
state C2, C3 and C5 biology with confidence; state C1 at the level of "immune
activation" only; claim no theme for C4.

---

## Stage 14 — Prioritising high-confidence genes, and the mechanism subgraph
`05_CODE/analysis/hc1`–`hc4` → `03_RESULTS/Task5_high_confidence_genes/`

**What.** The 3,645 fibrosis genes re-ranked by **how many independent kinds
of evidence agree**, down to 507 high-confidence genes and a prioritised 25,
then placed on the knowledge graph to see where they converge.

**Why not just rank by q-value.** Every gene in the starting set already
passes fibrosis FDR < 0.05 — that is how it got in. Ranking by q again only
re-reads the same number. Agreement between *different* kinds of evidence is
new information; a smaller p-value is not.

**The five scores, each reading a different property of the data.** All
cutoffs were frozen as named constants **before any ranked list was
inspected.**

| | Score | 2 points | 1 point |
|---|---|---|---|
| **P** | Progression strength | \|rho\| ≥ 0.40 | ≥ 0.30 |
| **T** | Trajectory | \|F4 − F0\| ≥ 1.0 SD | ≥ 0.5 SD (0 if the wrong direction) |
| **X** | Transition | largest stage jump real in the full fit **and** reproducible in ≥ 50% of 50 equal-power draws | one of the two |
| **F** | Fibrosis specificity | — | fibrosis-only (shared scores 0) |
| **B** | Biological support | in enriched terms in ≥ 2 of the four databases | in 1 |

Total out of 9. **Tier 1 = 7–9 (507 genes)**, Tier 2 = 5–6 (1,483), Tier 3 =
below 5 (1,655).

Specificity is deliberately worth only one point, so that it acts as a
tie-breaker rather than a filter that would purge the shared genes.

**Sensitivity is measured and reported, never used to pick the cutoffs.**
Lowering the Tier 1 bar to 6 widens it to 1,111 genes while retaining all
507; raising it to 8 narrows it to 135 (26.6% of the frozen set). Dropping
each score in turn and re-ranking leaves Spearman correlations of 0.83–0.95
against the full ranking.

**Tier 1 composition.** 275 shared / 232 fibrosis-only — so the shared genes
were *not* squeezed out. No enriched process covers more than 10.8% of it. By
cluster, though, it is very uneven: C2 alone has 333 of the 507, against C1
103, C5 60, C3 6 and C4 5. Consequently Tier 1 is 87% increasing genes (442
against 65) and 379 of 507 make their largest change at F3→F4.

**The shortlist, and why it is not the top 25 by score.** Ranking by score
alone would have produced a list that was almost entirely C2 — late-rising,
increasing, well-annotated genes — and the early and decreasing programmes
would have vanished. Instead: **the top five Tier 1 genes per cluster, ties
broken by |rho|.** Five is not chosen for neatness — C4 has exactly five Tier
1 genes, so five is the largest number at which all five clusters contribute
equally. The Tier 1 bar never moves; only the sampling within it does.

**Result: 25 genes** — 15 increasing / 10 decreasing, 12 fibrosis-only / 13
shared, all five shapes, largest change spread 5 / 4 / 9 / 7 across the four
transitions, |rho| 0.307–0.533, scores 7–9, and no enriched process covering
more than 12% of the list. The alternative rule (each cluster's own top
score) gives 43 genes of which 29 come from C1 and two clusters contribute
one gene each. Both are reported:
`02_TABLES/supplementary/TableS16_shortlist_rule_comparison.csv`.

The 25: IL32, UNC5B, NFASC, ADAMTSL2, PLPP4, PDGFRA, MYC, CACNA1C, TPM4,
TAX1BP3, TREM2, CDC45, HTR7, FABP5, TYMS, CYP2C19, OAT, NAAA, CLPX, F2,
DGAT2, SLC38A4, NCAM2, CYP4F3, ACADSB.

**Leave-one-study-out validation.** Only five of the eight studies stage
fibrosis, so robustness is reported out of five, not eight. All 25 keep both
direction and significance in all five refits; 19 of 25 also keep median
|rho| ≥ 0.30, and the six that dip land at 0.280–0.292 — grazing the line,
not collapsing. The discriminating column is the largest percentage loss in
rho: MYC 2.6% and TREM2 2.7% against TPM4 27.6% and CACNA1C 37.3%.

**A sanity check the method passed without being told to.** Nine collagens
reach Tier 1 — COL1A1, COL1A2, COL3A1, COL4A1, COL4A2, COL4A4, COL5A1,
COL8A2, COL16A1, scores 7–8 — confirming the scheme recovers established
fibrosis biology. None are in the 25: they sit just below the top five of
their clusters on |rho| (COL1A1 0.448 against UNC5B 0.490). That is the
cluster cap, not a verdict on them.

**The mechanism subgraph (Figure 9).** Enrichment said *which* processes are
over-represented. It could not say which gene connects to which mechanism, or
where several genes meet on the same one. That wiring is what the graph holds.

- **The graph is not rebuilt.** The subgraph is filtered from the same
  knowledge-layer CSVs that were loaded into Neo4j, so it needs no running
  database.
- **The schema is not the chain it may appear to be.** Pathways (Reactome)
  and biological processes (GO) both attach to genes and not to each other:
  `BioProcess ←INVOLVED_IN— Gene —IN_PATHWAY→ Pathway`. So "gene → pathway →
  process" is two separate connections per gene, not a path. Nothing is
  missing; convergence reads normally as gene A → node ← gene B.
- **How the twelve mechanisms were chosen.** Each graph node was tested the
  way stage 13 tested its gene sets — hypergeometric test of the Tier 1 genes
  against the same 14,794-gene background, BH-FDR across nodes — and kept if
  it holds 10–500 background genes, reaches ≥ 10 Tier 1 genes and q < 0.05;
  ranked by q, near-duplicates collapsed above Jaccard 0.5, top twelve.
- **Ranked by q and not by gene count**, deliberately. Count alone returns
  "positive regulation of gene expression" and the like — terms in almost any
  gene list, enriched here only 2.3–3.0× against 3.9–13.3× for the twelve
  kept.
- **Tested on the nodes themselves, not by matching their names to stage 13's
  term names.** Name matching was tried first and is brittle: MSigDB 2024.1
  has no `GOBP_EXTRACELLULAR_MATRIX_ORGANIZATION` because GO renamed that
  term, so the most connected mechanism in the graph — 56 Tier 1 genes, 7.5×
  enriched, q = 8 × 10⁻³⁰ — was marked "not enriched" and dropped from the
  figure over a change of vocabulary.

The twelve: extracellular matrix organization, cell adhesion, inflammatory
response, cytokine-mediated signalling, positive regulation of the ERK1/ERK2
cascade, integrin cell surface interactions, ECM proteoglycans, angiogenesis,
integrin-mediated signalling, signalling by PDGF, collagen fibril
organization, positive regulation of collagen biosynthetic process.

The figure draws the genes reaching three or more of the twelve plus every one
of the 25 reaching any: **46 genes, 12 mechanisms, 169 edges.** Across all 507
Tier 1 genes the graph is densely convergent (328 pathways connect two or more
Tier 1 genes, 163 connect three or more). **The 25 themselves barely converge
— see `05_LIMITATIONS.md`, which is essential before interpreting Figure 9.**

---

## The strand that did not work — link prediction
`05_CODE/unresolved/`

**What was attempted.** Using the graph to predict drug–disease links that do
not yet exist in it — drug repurposing. The pipeline is built
(`export_triples.py` exports the graph as triples, `train_link_prediction.py`
trains a ComplEx embedding model with PyKEEN).

**Status: unresolved.** The first model **failed its own validation.** Any
drug-repurposing output from it is unverified and is not a result of this
paper.

It is shipped here, in a folder named `unresolved`, because it is part of the
honest record of what was tried. **Do not cite it, and do not include its
output in the manuscript.** If the paper mentions this direction at all, it
belongs in future work.
