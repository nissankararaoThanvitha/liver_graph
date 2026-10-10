# Search for original GSE130970 sample-level diagnoses

10 October 2026. No active labels, analysis outputs or graph data were changed.

## Result

All six original paper supplements were recovered from BioStudies record S-EPMC6715650 and inspected. They establish original aggregate clinical groups, but **do not provide a GSM/internal-sample-ID-to-control/NAFL/steatohepatitis mapping**. The original labels for all78 samples have not been recovered.

The original PDF's Supplemental Table1 (pages6–7) reports6 histologically normal controls and72 NAFLD patients, of whom58 have steatohepatitis. Our current derived classifications are8 controls,23 NAFL and47 NASH. The paper combined borderline and definite steatohepatitis. These counts cannot be reconciled by guessing identities or relabelling samples solely to reach a target count.

Source: original41598_2019_48746_MOESM1_ESM.pdf,Supplemental Table1; article Methods/Assessment of liver histology; [BioStudies original-paper record](https://www.ebi.ac.uk/biostudies/studies/S-EPMC6715650).

## Original supplementary files inspected

Files were downloaded from https://www.ebi.ac.uk/biostudies/files/S-EPMC6715650/ and their byte sizes matched the record. SHA-256 hashes and URLs are in original_supplements_manifest.json. Workbooks were inspected across all sheets/cells, with worksheet dimensions reset because several stored dimensions incorrectly reportedA1 only. No source files were edited.

| Supplement | Contents inspected | Sample-level diagnosis table? |
|---|---|---|
| MOESM1 PDF |7 pages; supplementary figures and aggregate population/histology table | No |
| MOESM2 XLSX | NAS and fibrosis ordinal-regression sheets;16,010 gene records per sheet | No |
| MOESM3 XLSX |18 gene-community pathway-enrichment sheets;100 records per sheet | No |
| MOESM4 XLSX |18 fibrosis-community pathway-enrichment sheets;100 records per sheet | No |
| MOESM5 XLSX | NAS/fibrosis network centrality;2,139/1,224 gene records | No |
| MOESM6 XLSX | NAS/fibrosis pathway regression;1,679 records per sheet | No |

Page6 was rendered and visually checked to establish table-column alignment; page7 text was inspected for the continuation. None of the original supplements supplies the required sample diagnosis mapping. The worksheet profiles and full extracted PDF text are saved locally.

## Published table versus GEO: additional source discrepancy

Fresh GEO metadata match the project's local component scores exactly, as shown by the previous audit. But aggregate totals differ from the original paper:

| Field | Published Supplemental Table1, all78 | Fresh GEO, all78 |
|---|---:|---:|
| Steatosis grade0 |8|8|
| Ballooning grade0 |20|30|
| Ballooning grade1 |28|23|
| Ballooning grade2 |30|25|
| Inflammation grade0 |11|9|
| Inflammation grade1 |55|57|
| Inflammation grade2 |12|12|
| NAS0 |6|4|

Fibrosis-stage totals agree:25/28/9/14/2. This supports retaining the supplied fibrosis scores while treating the categorical diagnosis reconstruction as unresolved. It does not establish which publication or metadata entry is wrong, nor which samples should have different diagnoses. Differences may reflect reporting, scoring or data-release issues that require author clarification; no cause is assumed here.

## Other public sources checked

- [NRF2-activity-in-CLD research repository](https://github.com/saezlab/NRF2-activity-in-CLD): repository archive downloaded and scripts inspected. Adult cohort metadata are read directly from GEO and contain component scores/NAS; no independent original diagnostic labels. The data directory asks users to download the adult expression matrix from GEO.
- [NN1177_liver_RNAseq](https://github.com/novonordisk-research/NN1177_liver_RNAseq): public repository has only a README saying code will be added/contact authors; no sample diagnosis table.
- [BioStudies S-BSST1361](https://www.ebi.ac.uk/biostudies/studies/S-BSST1361), associated with the2024 mouse-model/cohort study: record lists mouse/rat metadata and aggregate human differential/enrichment results, not a GSE130970 sample diagnosis mapping. Its publication says additional human metadata are available from original authors.
- [MASLD Portal dataset table](https://www.masldportal.net/datasets/): reports later curated Control/MASL/MASH counts4/48/26 for this cohort. An aggregate secondary classification is not the original pathologist's diagnosis mapping and was not adopted.

Public search covered the original accession/publication/supplement filenames, relevant sample IDs, researcher repositories and data records. The search cannot prove no label file exists anywhere; it establishes that the inspected sources do not provide the required original mapping.

## Recommended next action

Ask the original study team for:

1. The original normal-control membership and NAFL/steatohepatitis diagnoses for all78 samples, with GSM or internal RNA-seq IDs.
2. The treatment of borderline steatohepatitis and whether per-sample borderline/definite calls can be shared.
3. Clarification of the ballooning/inflammation/NAS discrepancies between Supplemental Table1 and the GEO clinical fields.

Your mentor can make that request. No email or other message was sent by this search. Until labels are recovered/reviewed, current classifications remain explicitly derived and unverified. Do not infer which six are controls or which58 have steatohepatitis from aggregate totals.
