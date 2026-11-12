# GSE225740 versus the eight discovery cohorts: independence assessment

Date: 7 November 2026. Scope: published recruitment provenance and deposited identifier overlap; no association tests or expression fingerprint comparisons.

## Conclusion

**The available evidence supports treating GSE225740 as a separately recruited, held-out cohort. No patient/sample overlap with the eight discovery cohorts was identified. Complete individual-level non-overlap is not proven.** Recruitment information, clinical setting and separate deposition support this interpretation; they are not an identity linkage service. This is adequate evidence to proceed with a transparently qualified external-cohort replication analysis, rather than a claim of guaranteed zero overlap.

## Validation-cohort provenance (confirmed)

Powell et al., *Nature Communications* 14,1474 (2023), DOI 10.1038/s41467-023-37209-1, PMID 36927865: [full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10020163/), Methods—Patient selection, RNA-seq data processing and Statistical analysis; Data availability. The study describes clinical percutaneous biopsies from 93 NAFLD patients, Indiana University IRB protocols 1506218127 and 1011003025R008, and submitter aggregation of technical assays to one measurement per patient. The deposited count matrix contains 93 matching patient columns. The exact recruitment calendar interval was not established from the inspected public material; do not infer it from an IRB number.

The paper also performs a literature-based meta-analysis using other public studies. Those additional cohorts are separate from the 93-patient deposited expression matrix being used here; this screen is not importing the paper's meta-analysis results as new patient data.

## Comparison with every original accession

| Discovery dataset | Recruitment provenance checked | Assessment relative to Indiana validation cohort | Evidence location |
|---|---|---|---|
| GSE126848 | Danish recruitment: NAFLD patients at Aarhus; control recruitment at Gentofte/Copenhagen | Different documented recruitment source; no shared GSM | [Suppli et al.](https://journals.physiology.org/doi/abs/10.1152/ajpgi.00358.2018), study population; [author-hosted original paper](https://www.gubra.dk/wp-content/uploads/2023/11/Suppli_2019_AJP-Gastrointest-Liver-Physiol_human-NASH-transcriptome.pdf); downloaded GEO SOFT |
| GSE130970 | Virginia Commonwealth University/HemoShear study of 78 liver biopsies | No Indiana recruitment identified; no shared GSM. Author affiliations alone are not proof of collection site, so the exact clinical provenance is less fully documented here than for some rows | [Hoang et al., PMID 31467298](https://pubmed.ncbi.nlm.nih.gov/31467298/); [original paper PDF](https://www.nature.com/articles/s41598-019-48746-5.pdf); downloaded GEO SOFT |
| GSE135251 | European multicentre EPoS/European NAFLD Registry biopsy cohort | Distinct recruitment described; no Indiana cohort contribution identified in inspected sources; no shared GSM | [Govaere et al., PMID 33268509](https://pubmed.ncbi.nlm.nih.gov/33268509/); [Vacca et al., Methods—Human next-generation sequencing datasets](https://pmc.ncbi.nlm.nih.gov/articles/PMC11199145/); downloaded GEO SOFT |
| GSE162694 | MGH NAFLD Cohort: MGH Fatty Liver Clinic/Weight Center in Boston and Bon Secours in Richmond | These named recruitment centres differ from Indiana; no shared GSM | [Pantano et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8433177/), Methods—Human subjects |
| GSE167523 | Transcriptome subset: 98 biopsies at Sendai Kousei Hospital, Japan, 2016–2018; separate serum cohorts in the same paper must not be confused with this subset | Different country and documented recruitment; no shared GSM | [Kozumi et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8596693/), Materials and Methods—Study Patients |
| GSE193066 | 106 HCC-naive patients with first/follow-up biopsies; source paper's tissue validation set 1, Japanese clinical cohort | No Indiana cohort identified for this deposited subset; no shared GSM. The source paper includes several other cohorts; only the deposited subset is relevant | [Fujiwara et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC9236162/), tissue validation set 1; downloaded GEO SOFT (164 biopsies/106 patients) |
| GSE240729 | Archived biopsies from Erasmus MC and Utrecht MC, Netherlands; 67 of 74 selected specimens passed sequencing QC | Different documented clinical sources; no shared GSM | [Verschuren et al., original paper](https://www.nature.com/articles/s41467-024-48956-0.pdf), Methods—Selection of translation cohort; downloaded GEO overall design |
| GSE269412 | Vanderbilt bariatric-surgery cohort; study approved under Vanderbilt protocols 090657 and 171845 | Different recruitment institution, clinical collection setting and IRB protocols; no shared GSM | [Steinhauser et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11981625/), Methods and Study approval; downloaded GEO SOFT |

These observations support a distinct cohort; neither a different institution, different author list nor different accession is by itself an absolute guarantee against cross-institutional recruitment or re-deposition.

## Deposited identifier audit

The downloaded metadata records and their hashes are retained in `../candidate_screening_2026-11-07/`, including `original_cohort_metadata/`. `cohort_overlap_checks.tsv` records all eight pairwise comparisons.

- All 93 validation GSM identifiers differ from all 1,085 discovery GSM identifiers.
- GSE225740 provides **zero BioSample and zero SRX/ERX/DRX experiment identifiers** in its downloaded SOFT. These overlap comparisons are **not assessable**, not confirmed negatives. The screening inventory has been corrected accordingly.
- The 93 patient labels are local integers. Matching generic numbers across studies would not constitute an identity match. No universal patient crosswalk is public.
- Raw validation sequencing reads are withheld for participant privacy. Genotype-based donor matching cannot be performed with the retrieved resources. No transcriptomic fingerprint or cross-cohort duplicate-profile analysis was performed.
- No author confirmation was obtained and no one was contacted. A definitive statement that not even one person was enrolled in both studies would need additional non-identifying linkage confirmation from the study custodians.

## Interpretation for subsequent work

Proceed using the fixed shortlist and predeclared tests as a held-out public-cohort replication, while reporting that no overlap was identified from public provenance and available identifiers. Do not describe patients as identity-verified or guarantee zero overlap. Keep study-derived gene selections fixed regardless of future validation outcomes. No validation claim exists until the tests are performed and their complete results are reported.

## Separate observation: discovery-cohort overlap must not be assumed absent

[Vacca et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11199145/), Methods—Human next-generation sequencing datasets, explicitly removed 38 EPoS/GSE135251 patients overlapping a pooled UCAM–VCU resource, which combined E-MTAB-9815 and GSE130970. This does **not** establish that those 38 are specifically in the GSE130970 portion used here; they may be in the other component. It does demonstrate why different accessions cannot guarantee patient independence. Resolving the original discovery cohorts' deduplication is a separate provenance task. This observation does not identify overlap with GSE225740 and no discovery results have been changed.
