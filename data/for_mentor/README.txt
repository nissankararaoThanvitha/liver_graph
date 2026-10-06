PROGRESSION GENES -- for analysis
=================================

4,692 genes whose expression tracks liver disease progression,
from 1,027 patients across 8 GEO studies. Only genes measured in
ALL 8 studies were tested, and a gene is included only where every
study agreed on the direction (Spearman per study, combined by
Fisher's method, Benjamini-Hochberg q < 0.05).

VALUES
  All numbers are value_z: expression standardised per gene within
  each study (mean 0, sd 1). This is what makes 8 cohorts
  comparable. Positive = above average for that gene.

COLUMNS
  fibrosis_rho       correlation with fibrosis stage 0-4 (-1..+1)
  inflammation_rho   correlation with control->NAFL->NASH
  n_studies          how many studies the gene was tested in
  ladder             fibrosis_only / inflammation_only / both
  blank rho          gene not significant on that ladder

FILES
  genes_by_fibrosis_stage.csv   mean per stage 0,1,2,3,4
  genes_by_disease_group.csv    mean per control/NAFL/NASH etc
  genes_by_stage_and_sex.csv    stage x M/F
  genes_by_stage_and_age.csv    stage x age band
  sample_demographics.csv       one row per sample

COVERAGE LIMIT -- important
  Age and sex are recorded by 5 of the 8 studies, and only 3 of
  those also stage fibrosis. The stage x age and stage x sex files
  therefore rest on 385 samples (GSE130970, GSE162694, GSE193066),
  not all 1,085. The per-stage file uses all 668 staged samples.
  Sex was written six ways across studies (Female/female/F/Male/
  male/M) and has been harmonised to M/F.

  GSE193066 contributes 164 samples from 106 patients -- 58 were
  biopsied twice. Group by patient_id, not sample_id, for stats.
