TASK 1 -- Master progression-gene table
=======================================

Plan: "Create the Paper-2 master progression-gene table. Start with all
progression-associated genes... Do not remove genes simply because they are not
already known drug targets."

Nothing is filtered. All 6,222 progression genes are carried through.

Built by: scripts/paper2_task1_master_table.py
Source:   Paper1_HighConfidence/00_all_progression_genes.csv


VERIFICATION -- gene by gene, not count by count
  scripts/paper2_task1_verify_against_neo4j.py

Run 12 October 2026 against instance LiverDiseaseDB
(dbms-1c965ecc-01bb-470f-86fa-237c81d9d40d), database `neo4j`. Note this is a
different Neo4j instance from the one used before 12 October; the earlier
instance no longer exists.

Matching totals prove nothing on their own -- two sets of 6,222 genes can agree
on size and disagree on membership -- so the audit compares the sets themselves
and then every value:

  gene SET identical                6,222, symmetric difference empty
  progression_class vs TRACKS edges 6,222 agree
  fibrosis_rho                      3,845 compared, max diff 5.0e-05
  fibrosis_q_FDR                    3,845 compared, max diff 3.4e-21
  fibrosis_n_studies                3,845 exact
  fibrosis_direction                3,845 exact
  inflammation_rho                  4,199 compared, max diff 5.0e-05
  inflammation_q_FDR                4,199 compared, max diff 3.4e-21
  inflammation_n_studies            4,199 exact
  inflammation_direction            4,199 exact
  gene symbols                      6,222 exact

The residual rho difference of 5e-05 is CSV rounding to four decimal places,
not disagreement. Direction is spelled rises/falls in the graph and
increasing/decreasing in Paper 1's CSVs; that vocabulary difference is mapped,
and once mapped the two agree on every row.

RESULT: PASS. The table reproduces the live graph exactly.


FILES
  Paper2_progression_genes.csv        6,222 rows -- the master table
  task1_class_summary.csv             counts per progression class
  task1_discordant_shared_genes.csv   30 rows -- see FINDING below


THE GENE COUNT DIFFERS FROM THE PLAN
The plan says 4,692 genes. That figure predates the biopsy-pairing correction
of 9-10 October 2026 (BIOPSY_CORRECTION.md), after which repeat biopsies are
averaged only when the fibrosis stage matches, and biopsy 1 is retained
otherwise. The current corrected set is 6,222. The plan's intent is "all
progression-associated genes", so the current set is used.

  fibrosis-associated (fibrosis-only + both)   3,845
  disease-associated (inflammation-only + both) 4,199
  shared (both ladders)                        1,822
  union                                        6,222

These match CLAUDE.md, final_combined_2026-10-10/FINAL_SELECTION.md, and a
direct count of TRACKS_FIBROSIS / TRACKS_INFLAMMATION edges in Neo4j. The
script asserts all of them and fails rather than writing a table that
disagrees.


CLASS SUMMARY (the short summary the plan asks for)
  class               genes   % of union   increasing   decreasing
  fibrosis-only        2,023      32.5        1,040         983
  inflammation-only    2,377      38.2        2,042         335
  both                 1,822      29.3        1,438         414
  UNION                6,222     100.0

For the "both" class, increasing + decreasing = 1,852, which exceeds 1,822.
That is not an error: a gene is counted under a direction if EITHER ladder has
it, and the 30 discordant genes below therefore appear in both columns.

The inflammation ladder is strongly skewed towards increases (2,042 up vs 335
down); the fibrosis ladder is close to balanced (1,040 vs 983).


FINDING -- 30 discordant shared genes, up from 1
Paper 1 Task 1 reported exactly ONE shared gene whose two ladders point in
opposite directions (GPD1). On the corrected data there are THIRTY, and all 30
point the same way: DECREASING with fibrosis, INCREASING with inflammation.
GPD1 is still among them.

  PEX3 GDI2 DARS1 SCP2 ABCD3 ALDH8A1 RAD23B ALDH1A2 SERPINF1 FST PNPLA8
  PPM1B USO1 ABHD2 AHSG ZYG11B AZI2 LMBRD2 TMEM135 GPD1 DHX36 NRIP1 SRPRA
  GBP7 (and 6 more -- see the CSV)

Not treated as an error here. The direction of change is the single most
important input to Task 7's reversal-consistency classification, and a gene
that falls on one ladder while rising on the other cannot be given one
direction. Task 7 must handle these explicitly rather than averaging them.

Both rho values are weak for most of them (|fibrosis_rho| mostly 0.08-0.38),
so this may reflect genuinely different biology on the two axes rather than a
defect. Worth a sentence in the manuscript either way.


WHY THE BLANK CELLS ARE NOT MISSING DATA
2,377 rows have no fibrosis_rho and 2,023 have no inflammation_rho. That is
what the class labels mean: an inflammation-only gene was never significant on
the fibrosis ladder, so it has no fibrosis statistics. These are structural
blanks. They must NOT be imputed, and they must not be read as measurement
failure. F0-F4 stage means are present for all 6,222 genes.


CARRIED WARNING FOR TASK 6
Paper 1's trajectory, transition, pathway and tier work covers only the 3,845
fibrosis-associated genes. The 2,377 inflammation-only genes have none of it.

A TargetScore with a trajectory (T) or pathway (B) component will therefore
rank those 2,377 genes last for MISSING DATA, not for biology -- while the plan
simultaneously requires the three classes be preserved as distinct. The rule
must be decided before Task 6 computes anything: normalise within class, or
score the classes separately. It cannot be left to a default missing-value
policy.

Every row carries `in_fibrosis_starting_set` (True for 3,845, False for 2,377)
so the affected genes stay identifiable at every later step.


COLUMNS
  Gene                        HGNC symbol
  Ensembl_ID                  canonical Ensembl gene ID (unique, 6,222)
  progression_class           fibrosis-only | inflammation-only | both
  fibrosis_rho                median per-study Spearman rho vs fibrosis stage
  fibrosis_q_FDR              Benjamini-Hochberg q
  fibrosis_direction          increasing | decreasing
  fibrosis_n_studies          studies the gene was tested in
  inflammation_rho            median per-study Spearman rho vs disease group
  inflammation_q_FDR          Benjamini-Hochberg q
  inflammation_direction      increasing | decreasing
  inflammation_n_studies      studies the gene was tested in
  F0..F4                      mean value_z at each fibrosis stage (all 6,222)
  in_fibrosis_starting_set    True if the gene has Paper 1 trajectory/tier work


NOT DONE HERE, ON PURPOSE
Trajectory cluster, stage-transition results and tier are NOT merged into this
table. The plan stages them as later refinement, and merging now would make the
2,377 inflammation-only genes look as though they failed a test they were never
eligible for. They are available in
Paper1_HighConfidence/11_final_all_3845_genes.csv and can be joined on
Ensembl_ID when Tasks 4, 6 and 7 need them.
