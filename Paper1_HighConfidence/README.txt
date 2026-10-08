HIGH-CONFIDENCE FIBROSIS GENE PRIORITISATION
============================================

Starting set: the 3,645 fibrosis-associated genes (1,953 fibrosis-only +
1,692 shared with inflammation) carried by the TRACKS_FIBROSIS edges.

The aim is to re-rank them by how many INDEPENDENT kinds of evidence agree,
not by p-value. Every gene in the starting set already passes fibrosis
FDR < 0.05 -- that is how it entered -- so ranking by q-value again only
re-reads the same number.

    P  progression strength   |rho| >= 0.40 -> 2,  >= 0.30 -> 1
    T  trajectory             |F4 - F0| >= 1.0 SD -> 2, >= 0.5 -> 1,
                              wrong direction -> 0
    X  transition             largest of the four stage jumps: real in the
                              full fit AND reproducible in >= 50% of 50
                              equal-power draws -> 2, one of the two -> 1
    F  fibrosis specificity   fibrosis-only -> 1, shared -> 0
    B  biological support     in enriched processes in >= 2 of GO BP, KEGG,
                              Reactome, Hallmark -> 2, in 1 -> 1

    Total = P + T + X + F + B, max 9
    Tier 1: 7-9  (507 genes)   Tier 2: 5-6  (1,483)   Tier 3: <5  (1,655)

All scoring rules were frozen as named constants before any ranked list was
inspected. Sensitivity to each cutoff is reported rather than used to choose
it (03_, 04_, 08_).


FINAL OUTPUT
------------
  11_FINAL_shortlist_25_genes.csv   the shortlist: top 5 Tier 1 genes per
                                    trajectory cluster
  11_final_tier1_507_genes.csv      all Tier 1 genes, same columns
  11_final_all_3645_genes.csv       every scored gene, nothing hidden
                                    behind the selection
  12_mechanistic_subgraph.png       the focused knowledge-graph figure
  12_KG_supplementary.xlsx          7 sheets, for supplementary material

Supporting:
  01_master_table.csv               all 3,645 genes with every intermediate
  05_powermatched_per_gene.csv      per-gene matched results, 4 transitions
  09a_tier1_genes.csv               the 507 before selection
  09a_tier1_pathway_dominance.csv   which processes Tier 1 sits in
  09b_option_A / _B / _comparison   the two selection rules considered
  10_loso_summary.csv               leave-one-study-out, per gene
  10_loso_runs.csv                  all 2,535 individual LOSO runs

Scripts, in order:
  powermatched_transitions.py       -> 05_   (reads data/graph_full, slow)
  high_confidence_genes.py          -> 01_, 03_, 04_, 08_, 09_, 11_
  loso_validation.py                -> 10_   (reads data/graph_full, slow)
  kg_subgraph.py                    -> 12_
  Run powermatched first, then high_confidence_genes, then loso_validation,
  then high_confidence_genes again so step 11 picks up the LOSO columns,
  then kg_subgraph.


HOW THE SHORTLIST WAS CHOSEN
----------------------------
Not the top 25 by score. Tier 1 is very uneven: C2 alone holds 333 of the
507 genes and all six perfect scores, so sorting by score gives a list that
is 87% increasing genes with 75% of their largest change at F3->F4. The
early and decreasing programmes would disappear.

Top 5 per cluster, ties broken by |rho|. Five is not a chosen number: C4 has
exactly 5 Tier 1 genes, so k=5 is the largest k at which all five clusters
still contribute equally. Beyond it only C1, C2 and C5 can grow, so a larger
set is a less balanced one -- the alternative rule (each cluster's own top
score) gives 43 genes of which C1 takes 29, with C3 and C4 contributing one
gene each.

The Tier 1 bar never moves. Only the sampling changes.

Result: 15 increasing / 10 decreasing, 12 fibrosis-only / 13 shared, largest
jumps spread 5 / 4 / 9 / 7 across the four transitions, and no enriched
process covering more than 12% of the list.


THE KNOWLEDGE-GRAPH SUBGRAPH
----------------------------
The graph is NOT rebuilt. kg_subgraph.py reads the same CSVs that were
loaded into Neo4j (data/graph_kg) and filters them, so it needs no running
database.

What it adds over Task 4: enrichment said WHICH processes are
over-represented among fibrosis genes. It could not say which gene connects
to which mechanism, or where several genes meet on the same one. That wiring
is what the graph holds.

Structure, which is not the chain the brief describes. Pathways (Reactome)
and BioProcesses (GO) are both attached to genes and not to each other:

    BioProcess  <-INVOLVED_IN-  Gene  -IN_PATHWAY->  Pathway

So "Gene -> Pathway -> Biological Process" is two separate connections per
gene, not a path. Nothing is missing; convergence still reads normally as
Gene A -> node <- Gene B.

Choosing the 12 mechanisms. Each graph node was tested the way Task 4 tested
its gene sets: a hypergeometric test of the Tier 1 genes against the same
14,794-gene background, BH-FDR across nodes. Kept if it has 10-500 member
genes in the background, at least 10 Tier 1 genes, and q < 0.05; ranked by
q-value; near-duplicates collapsed; top 12.

Ranked by q and not by gene count. Count alone returned "positive regulation
of gene expression", "negative regulation of apoptotic process" and
"positive/negative regulation of cell population proliferation" in the top
twelve -- terms that appear in almost any gene list. They are significant
here too, but only 2.3-3.0x enriched against 4-13x for the twelve shown, and
q weighs size and fold together, so they fall away without a hand-picked
fold cutoff.

Tested on the nodes themselves rather than by matching their names to Task
4's term names. Name matching was tried first and is brittle: MSigDB 2024.1
has no GOBP_EXTRACELLULAR_MATRIX_ORGANIZATION because GO renamed that term
to "external encapsulating structure organization", so the most connected
mechanism in the graph -- 56 Tier 1 genes, 7.5x enriched, q = 8e-30 -- was
marked "not enriched" and dropped from the figure over a vocabulary change.
Matching on gene membership was no better: that node's best Jaccard against
any significant term is 0.45.

The twelve: extracellular matrix organization, cell adhesion, inflammatory
response, cytokine-mediated signalling, positive regulation of the ERK1/ERK2
cascade, integrin cell surface interactions, ECM proteoglycans,
angiogenesis, integrin-mediated signalling, signalling by PDGF, collagen
fibril organization, positive regulation of collagen biosynthetic process.

Which genes are drawn: those reaching 3 or more of the twelve, plus every
one of the final 25 that reaches any, so no shortlisted gene is cut by that
rule. 46 genes, 169 edges.


LIMITATIONS -- state these, do not paper over them
--------------------------------------------------

1. LEAVE-ONE-STUDY-OUT IS 5 RUNS, NOT 8.
   Only five of the eight studies stage fibrosis: GSE130970, GSE135251,
   GSE162694, GSE193066, GSE240729. The other three carry no F0-F4 labels,
   so there is nothing to leave out. R is reported as n/5.

2. THE BRIEF'S LOSO TEST CANNOT FAIL, AND IS LABELLED AS SUCH.
   Every Tier 1 gene already has all five studies agreeing on direction, so
   dropping one leaves four that still agree and the median keeps its sign
   by arithmetic. All 507 genes score 5/5 on direction without anything
   being tested. Two measures that can fail are reported beside it:
   significance recomputed on the remaining four studies, and whether
   median |rho| stays at or above 0.30. All 25 shortlisted genes keep
   direction and significance in every run; 19 of 25 also stay above 0.30,
   and the six that dip land at 0.280-0.292 -- grazing the line, not
   collapsing.
   The column LOSO_max_pct_drop_in_rho is the one that discriminates:
   MYC 2.6%, TREM2 2.7% against TPM4 27.6%, CACNA1C 37.3%. The direction
   test scores all four identically at 5/5.

3. THE POWER-MATCHED ANALYSIS CANNOT CARRY SIGNIFICANCE.
   The matched design cuts every stage to 30 patients so each transition is
   judged on equal evidence, then corrects across 3,645 genes. Measured,
   not assumed: genes significant in >= 50% of the 50 draws number 0, 0, 0
   and 297 across F0->F1, F1->F2, F2->F3, F3->F4. Scoring X on that would
   have handed every available point to F3->F4 and excluded the three
   earlier transitions outright.
   X therefore scores REPRODUCIBILITY -- did the jump stay large and keep
   its direction across 50 equal-power redraws (1,522 / 1,856 / 1,713 /
   2,790 genes) -- which answers the same question at this sample size,
   since a fluke depends on which patients were drawn. The strict counts
   are carried in the table as Matched_frac_significant_NOT_scored.
   The matched design also uses 4 studies, not 5: GSE193066 lacks patients
   at some stage and cannot contribute an equal cell to every transition.

4. T STRUCTURALLY FAVOURS LATE-CHANGING GENES.
   T reads F4 - F0 and ignores F1-F3, so a gene that rises sharply at
   F0->F1 and then plateaus has a real early trajectory but a small
   endpoint delta. C3 (early rise, then plateau) has 1 gene at T=2 out of
   197; C4 (mid decrease) has 9 of 309. X is the corrective -- it finds the
   largest jump wherever it falls, and 1,133 genes earn X=2 from a jump
   before F3->F4 -- but T itself was left as defined rather than tuned.

5. C4 IS WEAK ON TWO SCORES AT ONCE.
   C4 also has the thinnest enrichment of any cluster: 10 significant terms
   in total across all four databases, against 542 for C2. 61% of C4 genes
   score B=0. Being weak on both T and B, only 5 of 309 C4 genes reached
   Tier 1 (1.6%, against 22% for C2). The shortlist includes all five. They
   are there to represent mid-decreasing biology, not because that cluster
   is as well supported as the others.

6. THE CANONICAL COLLAGENS ARE IN TIER 1 BUT NOT IN THE 25.
   Nine collagens reached Tier 1 -- COL16A1, COL5A1, COL1A1, COL1A2,
   COL3A1, COL4A1, COL4A2, COL4A4, COL8A2, scores 7-8 -- confirming the
   method recovers established fibrosis biology. None are in the shortlist:
   they sit just below the top five of C1 and C2 on |rho| (COL1A1 0.448
   against UNC5B 0.490). This is the cluster cap, not a judgement on them.
   No pathway dominates either way; the largest enriched process covers 12%
   of the shortlist.

7. AT THE TOP OF THE RANKING, P DOES MOST OF THE WORK.
   Dropping each score in turn and re-ranking: every Spearman correlation
   against the full ranking is >= 0.83, so no single score drives the
   ranking overall. But in the top band (score 8-9, 135 genes), removing P
   retains only 49 of them (Jaccard 0.21). The elite end of this list is
   more effect-size-driven than "five evidence types agree" suggests.

8. USE 'INCREASING / DECREASING WITH FIBROSIS STAGE', NOT
   'UPREGULATED / DOWNREGULATED'.
   The latter denotes a differential-expression comparison between two
   groups. This is a correlation along an ordered stage ladder. The
   Direction column carries the wording the manuscript should use.

9. THE FINAL 25 BARELY CONVERGE, AND THE FIGURE MUST NOT BE READ AS IF THEY
   DO. Among the 25, only 2 pathways connect to two or more of them and
   none to three or more; of the twelve mechanisms in the figure, 8 of the
   25 reach at least one and NOT ONE reaches three. This follows directly
   from the shortlist rule, which selected genes to be as unlike each other
   as possible. The convergence visible in the figure comes from the other
   Tier 1 genes: 168 of the 507 reach at least one of the twelve, and 24
   reach three or more. The hubs doing that connecting are COL1A1, COL1A2,
   COL3A1, COL4A1/2/4, COL16A1, ITGAX, ITGB2, ITGB8 and TGFB1 -- Tier 1
   genes the cluster cap kept out of the shortlist. That is the strongest
   form of limitation 6: the genes structurally central to this mechanism
   network are precisely the ones the shortlist excludes.


DIRECTION, AND WHY ITS CROSS-CHECKS MATTER
------------------------------------------
Direction is the sign of fibrosis_rho, fitted across all 668 staged samples
within study. Delta_F0_F4 agrees for 3,641 of 3,645 genes (99.9%) and the
cluster shape for 3,643. The four disagreements -- DNPH1, FST, SLC5A10,
FUNDC2 -- all have both a weak rho (|rho| <= 0.18) and a near-zero delta, so
both signals are noise rather than two strong signals in conflict. They are
flagged in the table and were not relabelled.
