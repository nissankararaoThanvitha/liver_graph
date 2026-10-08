TASK 3 -- Where does the major fibrosis-stage change occur?
===========================================================

Genes: the 3,645 fibrosis-associated genes (fibrosis-only + shared).
Data:  patient-level value_z, 5 staged studies (GSE130970, GSE135251,
       GSE162694, GSE193066, GSE240729).

METHOD
  For every gene and each transition F0->F1, F1->F2, F2->F3, F3->F4:
  1. delta_mean   = mean(stage b) - mean(stage a), from the stage table.
  2. beta_adjusted: linear model  value_z ~ stage + study, fitted on the
     patients of the two stages only. Including study means stages are
     compared WITHIN each study, so differences in stage mix between
     studies cannot create false changes. Studies lacking either stage
     are left out of that transition.
     Patients counted once: repeat biopsies at the same stage averaged
     (28 patients); a patient biopsied on both sides of a transition
     keeps one sample, chosen at random with a fixed seed (24 patients).
  3. t-test on beta, Benjamini-Hochberg FDR within each transition.
  4. "Substantially changing" = q < 0.05 AND |beta| >= 0.2 SD.
  5. Power-matched check: F4 has only 34 patients, so every transition was
     refitted 50 times on the SAME study-balanced design (30 patients per
     stage: GSE130970 2, GSE135251 14, GSE162694 8, GSE240729 6), so that
     all four transitions have equal statistical power.

RESULT -- the largest change is at F3 -> F4
                         F0->F1  F1->F2  F2->F3  F3->F4
  patients (a / b)      152/166 160/165 165/109 118/34
  substantial genes        1165    1175    1117     936
     up                    1135     647     906     865
     down                    30     528     211      71
  median |beta|           0.188   0.189   0.221   0.378
  genes with |beta|>=0.2   1699    1693    2043    2710
  power-matched, median       0       0       2     311

  With all patients, the first three transitions each have ~1,100-1,200
  substantially changing genes and F3->F4 has 936, even though F3->F4 rests
  on only 34 F4 patients. Once power is equalised, F3->F4 dominates
  (median 311 genes vs 0-2), and its typical effect size is about twice
  that of any earlier transition. Earlier transitions show many small,
  consistent changes that need large samples to detect; the transition
  into cirrhosis shows fewer-but-larger changes.

  Direction: F0->F1 is almost entirely increases (1,135 up vs 30 down).
  Decreases begin mainly at F1->F2 (528 down).

LIMITATIONS
  * Circularity: these genes were selected because they correlate with
    fibrosis stage in this same data, so absolute counts of significant
    genes are inflated. The COMPARISON between transitions (the question
    asked) is still fair: all four use the same genes.
  * |beta| >= 0.2 SD is a conventional, not a unique, cutoff for
    "substantial". The effect-size panel does not depend on it.
  * F3->F4 rests on 34 F4 patients; the power-matched check addresses
    power, but estimates for that transition are the least precise.

PER-CLUSTER CHECK (links to Task 2)
  C3 (originally "Rise to F3, then reverse", now "Early rise, then
  plateau"): at F3->F4 median beta = -0.04 and
  0 of 197 genes change significantly. The apparent drop at F4 in the
  stage means is NOT supported at patient level; C3 is better described
  as an early rise that then plateaus.

FILES
  task3_transition_summary.csv        the table above, with all columns
  task3_all_genes_all_transitions.csv every gene x transition: delta_mean,
                                      beta_adjusted, se, p, q, n_patients,
                                      substantial, Task 2 cluster
  task3_top_genes_per_transition.csv  top 20 increasing / decreasing genes
                                      per transition (q < 0.05, ranked by beta)
  task3_cluster_by_transition.csv     per Task 2 cluster: median beta and
                                      number of significant genes per transition
  task3_delta_distributions.png       distribution of delta per transition
                                      (stage means and patient-level)
  task3_transition_comparison.png     all four transitions: gene counts,
                                      power-matched counts, effect sizes
