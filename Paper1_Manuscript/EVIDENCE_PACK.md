# Evidence pack for manuscript draft v1

Date: 10 October 2026. Final source: the researcher-selected combined analysis.
This handoff describes available evidence; it is not manuscript prose.

## Study question and architecture

Resource article with transcriptomic association and prioritisation analyses.
Question: how can public liver expression, fibrosis-stage associations and
curated biomedical relations be integrated into a traceable graph for future
stage-informed drug repurposing? No drug-efficacy or causal prediction claim.

## Cohorts and statistical units

All eight inputs are human liver expression studies, with matrices and clinical
metadata described in docs/provenance/DATA_SOURCES.md. Accession/sample counts:
GSE126848/57; GSE130970/78; GSE135251/216; GSE162694/143;
GSE167523/98; GSE193066/164; GSE240729/67; GSE269412/262.
Resource total1,085 samples and1,027 recorded patient IDs. Independence between
different accessions has not been fully verified. Fibrosis:610 patient units
across five studies. Ordered disease groups:216 across three studies.
GSE193066:106 patients,58 repeat pairs;28 equal-stage means and30 biopsy1-only.
GSE130970: five cases unclassified, remaining73 labels derived, not confirmed.

## Workflow and statistical design

Source: docs/package/02_METHODS.md; current root scripts; final_combined_2026-10-10
logs, analysis_run_status.json and graph_verification.json.

Ensembl harmonisation;14,794 all-eight-study genes. TPM log2+1; other count
inputs log2(CPM+1), except GSE193066 deposited linear RLE log2+1; study/gene
sample-SD standardisation. Spearman two-sided t approximation; Fisher p-value
combination; BH separately per axis; q<.05 and all testable studies agreeing,
minimum three studies. Disease test family14,784 after testability filtering.
Five-stage row-standardised K-means,k5,n_init50,seed42; resampling diagnostics.
Study-adjusted adjacent-stage OLS; substantial q<.05 and |beta|>=.2;
50 matched draws of30 patients per stage across four common studies.
GO BP/KEGG legacy/Reactome/Hallmark MSigDB2024.1.Hs hypergeometric tests,
BH per group/database, size10–500 and minimum5 group genes.
P/T/X/F/B scoring maximum9,Tier1>=7; up to five per cluster.
LOSO BH across14,794 genes; selected-set internal robustness.

## Claim–evidence–boundary map

| ID | Confirmed result | Source/locator | Strength and boundary |
|---|---|---|---|
| C1 | 126,244 nodes;35,132,831 relationships;8 node and14 relationship types | docs/package/01_OVERVIEW.md; final graph verification counts; graph node CSVs | Confirmed resource content; node count inherited from verified intake, nodes not changed in final sync |
| C2 | Fibrosis3,845;disease4,199;shared1,822;union6,222 | progression_fibrosis/disease.csv selection;Task1/task1_summary.csv | Confirmed association; overlapping cohorts not ruled out |
| C3 | Fibrosis-only2,023;disease-only2,377;shared concordant1,792 anddiscordant30 | Task1/task1_summary.csv | Confirmed; do not call fibrosis-only biologically specific |
| C4 | Five cluster sizes857/1367/226/397/998;1,838 genes confidence>=.8 | Task2 cluster sizes and bootstrap shape stability | Confirmed; conditional confidence, variable patient-bootstrap stability |
| C5 | Substantial adjacent-stage counts857/1048/1116/781 | Task3/task3_transition_summary.csv | Confirmed; selected gene set and unequal sample sizes |
| C6 | Tier1=447;shortlist23;Tier1 clusters93/262/7/3/82 | final Tier1 and shortlist CSVs | Confirmed administrative prioritisation; not validated targets |
| C7 |442/447 significant and247/447 absolute median rho>=.30 in all five LOSO refits | final Tier1 CSV LOSO columns | Confirmed internal robustness, not independent validation |
| C8 |12 selected mechanisms;42 displayed genes;154 edges;4 shortlist genes |12_KG_supplementary.xlsx sheets3–5 | Confirmed annotation view; pancreatic annotation needs interpretation |
| C9 |449 drug IDs across17 shortlisted genes;101 broad liver/biliary indications;11 NAFLD/NASH | drug_shortlist_audit_2026-10-10 CSVs andsummary.json | Confirmed export counts; includes metabolism links, indication does not mean approval |
| C10 |16 shortlisted genes shared by all four sensitivity runs | final_combined_2026-10-10 comparison report/candidate_stability.csv | Confirmed specified sensitivity; no causal or drug-target validation |

## Figure and table handoff

See FIGURE_TABLE_PLAN.md. Eight proposed main display items: five figures and
three tables. Existing components are available; proposed composites have not
yet been assembled. Draft numbering differs from the existing package.

## Software and provenance

Python3.12.14;pandas2.3.3;numpy2.2.4;scipy1.16.3;scikit-learn1.7.2;
matplotlib3.10.7;gseapy1.3.1;Neo4j Enterprise2026.09.0.
HGNC release and exact downloaded OptimusKG version remain missing.
MSigDB2024.1.Hs is the version actually used; a newer current release does not
change this project's provenance.

## Missing and unsupported claims

Original individual GSE130970 diagnoses, inter-study participant independence,
complete confounder adjustment, complete upstream downloads/releases, publicly
deposited code/graph URLs, author/funding/ethics declarations: missing.
Drug predictions, stopping progression at any stage, clinical prediction,
causal mechanisms and external validation: unsupported by this project.

## Writing handoff

Ready for resource-focused Introduction, Results, Discussion and documented
Methods. Report derived labels and sensitivity choice transparently. Keep
missing author declarations as explicit placeholders. Authoritative final
numbers take priority over historic Claude-session counts and removed variants.
