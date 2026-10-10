> Follow-up search: all six original supplements have now been retrieved and inspected through BioStudies. Supplemental Table1 reports6 normal controls,72 NAFLD patients and58 steatohepatitis cases, but contains no sample-ID diagnosis mapping. Some aggregate component scores disagree with GEO. See ../label_source_search_2026-10-10/SEARCH_RESULTS.md; earlier access limitations below are historical. Active labels remain unchanged.

# GSE130970 diagnosis-label audit

10 October 2026. This is a source and label audit; no clinical labels, analysis results or graph relationships were changed.

## Conclusion

The existing control/NAFL/NASH labels are derived proxies, not author-supplied diagnoses. The implementation does not fully reproduce the original study's diagnostic approach. Five samples require particular review, and exact source diagnoses for the full cohort remain unavailable in the inspected GEO metadata.

Do not repair this simply by adding an inflammation threshold and assume the original diagnoses have been recovered. The study combined borderline and definite steatohepatitis, which cannot necessarily be reconstructed exactly from component scores alone.

## Sources checked

1. Fresh GEO series matrix, downloaded from https://ftp.ncbi.nlm.nih.gov/geo/series/GSE130nnn/GSE130970/matrix/GSE130970_series_matrix.txt.gz . All78 sample IDs are present. Local steatosis, ballooning, lobular inflammation, NAS and fibrosis values match the fresh records exactly: zero discrepancies. These records do not contain a direct diagnosis field.
2. Hoang et al., Scientific Reports2019, DOI10.1038/s41598-019-48746-5, PMID31467298, PMC6715650. Full article XML was obtained from Europe PMC. Source sections: Methods/Study population and Assessment of liver histology. The authors used histologically normal controls and diagnosed steatohepatitis using steatosis, ballooning and lobular inflammation; borderline and definite cases were analysed together. [Source publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC6715650/).
3. Current normalize_clinical.py/norm_disease. Its GSE130970 branch uses steatosis and ballooning but not the parsed lobular-inflammation score.
4. Current data/processed/samples_metadata.csv and data/graph/nodes_sample_clinical.csv. Current derived groups:8 control,23 NAFL,47 NASH, all marked derived_from_histology.

The paper references Supplemental Table1 in a PDF and five supplementary spreadsheets. Publisher PDF retrieval failed due to unavailable host resolution; Europe PMC supplementary ZIP retrieval timed out; direct PMC supplement access was unavailable. These files were not inspected, so original sample-level diagnoses cannot be claimed recovered. Download URLs/failures and hashes of successfully retrieved sources are recorded in source_manifest.json.

## Actual implemented rule

- Steatosis grade0: control, irrespective of inflammation, ballooning or fibrosis.
- Steatosis above0 and ballooning above0: NASH, irrespective of lobular inflammation.
- Steatosis above0 and ballooning0: NAFL.

Steatosis grade0 is a histology component score, not proof of globally normal liver histology or a direct healthy-control diagnosis. Fibrosis scores remain source-provided; the diagnosis rule does not alter their values.

## Samples requiring particular review

| Sample | Current label | Steatosis | Ballooning | Lobular inflammation | Fibrosis | Reason |
|---|---|---:|---:|---:|---:|---|
| GSM3758028 | control |0|0|2|2| Current control derivation ignores recorded inflammation and F2 fibrosis |
| GSM3758039 | control |0|1|0|0| Current control derivation ignores recorded ballooning |
| GSM3758073 | control |0|0|1|0| Recorded inflammation despite control proxy |
| GSM3758074 | control |0|0|1|0| Recorded inflammation despite control proxy |
| GSM3758038 | NASH |2|1|0|1| Current NASH derivation does not require inflammation; borderline inclusion makes exact source diagnosis uncertain |

These are audit flags, not newly assigned diagnoses. The other four current controls have zero values for the inspected steatosis/ballooning/inflammation/fibrosis components; that makes them normal-feature candidates, but does not independently establish all source control eligibility criteria. Forty-six of47 current NASH proxies have all three positive component scores. Agreement with a component checklist does not independently recover the authors' full diagnostic judgments, including borderline cases.

## Consequences for this project

The supplied fibrosis stages and fibrosis-only discovery calculation are not changed by this audit. Disease-axis association depends on these labels; its overlap with fibrosis determines the specificity feature and influences prioritisation/shortlist/network. The impact on gene counts or rankings has not been recomputed here.

There are currently three varying studies in the disease axis. Removing GSE130970 entirely would leave only two, below the existing minimum-three-study criterion. Such an exclusion would require an explicitly different sensitivity design; it is not a drop-in correction under the current discovery rule.

## Recommended resolution

Retrieve the original per-sample pathologist diagnosis and control-group membership from the authors or an accessible source supplement, joined using GSM/internal sample IDs. Ask the mentor/pathologist to review the five flagged samples and the treatment of borderline steatohepatitis.

Until that is available, describe GSE130970 classifications as derived and unverified, not validated NASH-CRN diagnoses. A stricter three-component rule, selective abstention on ambiguous cases or cohort exclusion could be explored as separately labelled sensitivity analyses, but none should silently overwrite the current labels.

## Audit artifacts

- all_78_sample_label_audit.csv: every sample's component scores, current derived label/provenance and flags.
- samples_requiring_review.csv: the five flagged cases.
- fresh_GEO_characteristics.json and metadata_comparison.json: fresh metadata and exact local/source comparison.
- source_manifest.json: URLs, hashes and inaccessible supplementary sources.
- GSE130970_series_matrix.txt(.gz) and PMC6715650.xml: retrieved public primary records.

The live graph and active package still contain the preceding corrected-biopsy result set. This audit establishes a separate label-evidence issue, not a validated replacement classification.
