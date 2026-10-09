> **Follow-up, 10 October 2026:** This is the preserved first-stage audit of the earlier results. The researcher clarified that the final goal is drug repurposing to stop progression at different stages; a patient-stage classifier is not the intended endpoint. Biopsy handling and affected analyses have since been corrected. Use `biopsy_correction_2026-10-10/CORRECTION_REPORT.md` for current counts, validation and graph status; historical findings below remain for traceability.

# Missing information, discrepancies and additional work

9 October 2026. Original files were preserved. These are audit findings and proposed follow-up work, not new completed analyses. Priority A affects scientific claims; B identifies concrete source conflicts. Publication-display issues are mapped in results_evidence_map.md.

## Priority A: scientific evidence and decisions

| ID | Issue and source | Consequence and resolution |
|---|---|---|
| A01 | Original aim is stage prediction; CLAUDE.md and package04_LIMITATIONS §13 say no classifier was built | Mentor should confirm association/resource scope versus required stage model. No predictor accuracy or non-invasive staging claim is supported. |
| A02 | hc3_leave_one_study_out.py lines103–123 averages repeat biopsies and takes first stage; discovery07 uses biopsy1 | LOSO is not an exact refit of corrected discovery. Restore expression, harmonise patient policy and rerun. Stored521/263/76 counts remain provisional validation claims. |
| A03 | hc3 lines96–98 restricts analysis to525 selected genes; lines137–147 applies BH to that set | Discovery uses a larger universe; selection/prioritisation is not refitted per omitted study. Define robustness versus predictive validation and the appropriate BH family. |
| A04 | Exported stage means use all sample rows; Task2 uses patient-stage rows; Task3 has transition-specific repeat handling | Universal first-biopsy/one-row-per-patient wording is false. Report each policy and assess dependence/sensitivity where required. |
| A05 | GSE130970 diagnosis derivation uses steatosis and ballooning, not explicit lobular inflammation;78 derived labels constitute35.3% of disease-axis patients | Clinical review of rule and source histology is required. Consider exclusion or alternative-rule sensitivity after definition is agreed. Do not call it validated clinical diagnosis. |
| A06 | GSE193066 units are unknown; graph builder applies the non-TPM CPM-like branch before log/z | Gene z-scoring does not guarantee sample-wise rescaling is harmless. Retrieve original units/assay documentation and assess sensitivity if needed. |
| A07 | Discovery selection and downstream testing use the same data; documentation says all contrasts remain fair | Common selection does not prove equal bias. Describe contrasts within the selected set; stronger inference needs selection-aware or held-out checks. |
| A08 | P/T/X/F/B share patient data and overlapping annotation libraries | They are complementary features, not five independent validation experiments. Prospective cutoff freezing is documented in comments but not independently proven. |
| A09 | Table6 shortlist joins show only10/25 confidence≥.8; no shortlisted C4 gene passes that threshold | Add confidence and denominator. Mentor can retain exploratory balanced candidates with uncertain timing disclosed or revise selection later. |
| A10 | k rule returns6; reported5 is an override; Figure6 and rebuild command misstate selection | Disclose departure, rationale and explicit positional5 command; preserve k6 sensitivity if needed. |
| A11 | F4 has35 samples/34 patients; matched late count median287 but SD412.4 | Show uncertainty and avoid a precise gene-number or longitudinal claim. Draw-level counts are not retained beyond summaries. |
| A12 | Disease3 studies/221 patients versus fibrosis5 studies/610 discovery patients; minimal cohort overlap | “Only/shared” is test membership, not exclusive biology. Verify study independence, overlap and derived-label sensitivity. |
| A13 | Graph enrichment BH covers4,330 Tier1-reached nodes; annotation families overlap | State actual correction family and zero-overlap handling. Statistical review may require a broader eligible-node family. |
| A14 | Pancreatic ductal developmental pathway is among12 selected mechanisms | Inspect driver genes and source pathway definition/literature; retain or revise transparently after biological review. Unexpected label alone is not grounds for deletion. |
| A15 | Original labels are NAFLD/NASH; modern MASLD/MASH criteria were not reconstructed | Check metabolic/alcohol/exclusion metadata. Do not silently reclassify every patient. |
| A16 | No demographic, BMI, treatment or cell-composition adjustment in discovery;385 staged samples have demographic coverage | State confounding. Age/sex mean tables are descriptive, not adjusted analysis. |

For A05, the [NIDDK histology protocol](https://repository.niddk.nih.gov/media/studies/nafld-pediatric-database-2/Pediatric_DB2_SOPs.pdf) includes steatosis, lobular inflammation and ballooning in its NASH definition. This audit identifies a rule mismatch, not a new patient diagnosis.

## Priority B: concrete source discrepancies

| ID | Conflict | Interpretation to retain |
|---|---|---|
| B01 | Overview progression edges3,645/2,739 versus current3,681/4,018 | Current graph_nodes file and live graph agree; overview paragraph is stale. |
| B02 | knowledge_layer progression duplicate has5,576 rows; graph_nodes has7,699 | Different content, not line endings; prefer explicitly current source and preserve discrepancy. |
| B03 | Dictionary calls progression_both5,755 a union-like set; executable rule selects q on both plus matching sign without unanimity | File is neither union5,884 nor definitive shared1,815. Individually filtered axis tables define memberships. |
| B04 | Documentation study-adjusted ARI.82 versus current output.870 | Current task2_robustness.csv is authoritative for stored result. |
| B05 | Current C1/C3 cores3/1 are untested; per-run CSVs still show old47/36 | Eight residual core database files are historical, not current evidence. |
| B06 | S13 shows47; S17 shows36; S19 shows78 and one term; current cores3/1/130 | Exclude stale panels from current manuscript; distinguish untested C1/C3 from tested-null C4. |
| B07 | Limitation forbids naming C1/C3 genes; shortlist includes ten, with TREM2 confidence.85 | Judge specific genes individually. Most early timing assignments are uncertain, not every one. |
| B08 | “Four genes” heading versus “two” prose; master flags FST/SLC5A10 | Actual flags are two; SLC5A10 has a rounded-zero endpoint, not a strong opposite effect. |
| B09 | F0 prose counts sum139; clinical table has152 | Include omitted13 NAFL samples. F0 is not a healthy control group. |
| B10 | Identifier prose says3 symbol/1 Entrez/4 Ensembl; actual2/1/5 | Use actual parser/summary configuration. |
| B11 | Dictionary says category from HGNC; code inherits pilot labels | Category annotates290 pilot genes and53,703 blanks, not all-gene biotype. |
| B12 | Workbook says507, Figure12 and degree≥2; actual525, packageFigure9 and degree≥3 | Use actual memberships/edges; fix notes later. Duplicate-collapse sheet has zero records. |
| B13 | Network title says most-connected; selection is q-ranked; only6/25 shortlist shown | Caption an enriched Tier1 subset, not shortlist convergence or raw-degree ranking. |
| B14 | Results README says old folder untouched/tasks pending; current tasks exist and old versions removed | Dated text is superseded by current files/history. Claimed per-task README.txt files are absent. |
| B15 | Word draft uses4,692/3,645/1,692/311 and old diagnosis/core claims | Historical scaffold only; current tables use5,884/3,681/1,815/287. Embedded figures also show the older results. |
| B16 | Earlier graph total35,091,066 and40,247 missing links; current total35,132,486 | Current counts and progression identities verified;142 missing hierarchy endpoints explain the remaining CSV/live difference. |
| B17 | “Eight independent studies” phrasing versus actual5/3 axis tests | Eight-study measured universe does not mean eight studies validate each axis. |
| B18 | Loader comment reports17,218,924 recovered edges; final totals differ by9,130,378 | Raw parse and mapped edge quantities may differ; use explicit totals and identify the quantity. |
| B19 | Stale comments say most agree, PrimeKG or old gene/tier counts | Executable unanimity filters/current rows supersede comments for method/result; retain historical rationale separately. |
| B20 | Discovery rho precision differs from three-decimal exported values consumed by score thresholds | State rounding and assess boundary sensitivity if needed; do not mistake a cutoff artifact for biological change. |

## Missing or inaccessible inputs and documents

| Item | Availability | Reference and impact |
|---|---|---|
| Raw expression downloads, series matrices and HGNC complete set | Absent under data/raw | DATA_SOURCES/REBUILD; original metadata, units and mapping reference cannot be fully verified |
| Parsed long matrices | data/interim_full absent | Cannot independently check every original expression column join |
| Full expression graph CSVs | data/graph_full absent | Required to rerun discovery, Tasks 2–3, matched analysis and LOSO |
| Knowledge graph source directory | data/graph_okg absent | Built knowledge copies are available in package04_DATA/knowledge_layer; existing scripts do not automatically redirect to these copies |
| OptimusKG original parquet | data/optimuskg absent | Source version/checksums unavailable; Dataverse DOI documented |
| MSigDB GMTs | data/genesets absent | Version 2024.1.Hs filenames documented; intentionally excluded with KEGG redistribution caveat |
| Earlier union graph directory | data/graph_all absent | Knowledge-builder still expects this node file while current workflow creates graph_full |
| Mentor’s original Word briefs | Not found locally | Session03 references Immediate work for Paper1.docx; prioritisation code cites a further brief |
| Original session ZIP/JSONL exports | Not found locally; historical Windows paths | Collapsed Markdown does not retain complete historical tool outputs |
| Acquisition/metadata retrieval chain and logs | Incomplete | samples_metadata is supplied, but full acquisition commands and checks are unavailable |
| Per-study discovery rho/p table | Not saved by discovery script | LOSO recomputes statistics; full expression is needed to audit heterogeneity |
| Prediction model, splits, logs, metrics and candidate tables | Absent | data/prediction and data/kg_triples excluded; historical candidate counts cannot be certified |
| Older result folders and k6 run | Removed or absent | Dated history documents differences; complete old membership requires version recovery or rerun |
| Verified bibliography and source papers | Not supplied; draft REF placeholders | PMIDs, PMC IDs and DOIs are literature leads, not a completed bibliography |
| Vector/PDF publication figures | Absent | PNG assets available; no PDFs found in audited project scope |
| Authors, affiliations, funding, contributions, conflicts and final ethics wording | Incomplete/placeholders | Author confirmation required |
| Versioned data/code release and graph download | No release DOI supplied | Repository clone URL documented; public availability/version/licence not independently verified |

Relocated sources are not automatically missing. Packaged renamed scripts often map to root scripts or scripts/ and docs/package. The candidate reference ledger contains 204 unresolved-or-relocated textual references, **not 204 proven missing files**. Historical Windows paths, Claude artifact links and placeholders are classified separately. DATA_SOURCES refers to nonexistent 05_LIMITATIONS.md/02_STAGE_BY_STAGE.md; current equivalents are 00_START_HERE/04_LIMITATIONS.md/02_METHODS.md. The verification guide refers to absent per-task README.txt files.

## Rebuild and software issues

1. Packaged copies retain repository-relative assumptions. hc0–hc4 set ROOT=HERE.parent, which resolves to 05_CODE inside the package. The packaged builder sets ROOT to its own 05_CODE directory. Direct package execution cannot find the original project data/results without adapting paths or restoring the intended layout.
2. build_optimuskg_layer.py reads data/graph_all/nodes_gene.csv while the prescribed current workflow creates data/graph_full. Equivalent historical node unions do not make a missing path executable.
3. Task2’s REBUILD command omits the positional 5 override. Current code’s rule selects 6. The selected-run command/log is not retained.
4. REBUILD omits build_progression_edges.py, which CLAUDE.md includes. Sample/gene node loading and complete clinical property population are not fully automated by the supplied constraint/expression loaders; constraints alone create no nodes.
5. requirements pins core packages but omits openpyxl, networkx, the Neo4j driver and a parquet engine used by scripts. Original environment lock/installed-version records are absent. Python3.13.7 and pinned package versions are documented historical provenance, not independently verified installed versions for every run.
6. Knowledge MERGE reruns do not delete obsolete edges after an input set shrinks. Expression CREATE can duplicate an already loaded file. Later updates need explicit migration and count/membership checks; this audit performed no reload.
7. Enrichment skip/empty-output paths leave old files. Copying whole result directories into the package does not establish freshness. Add run IDs, input hashes and output manifests in a later repair.
8. Manifest differences are entirely explained: 71 byte-identical plus 192 exact after LF/CRLF conversion, with zero unexplained discrepancies. Record this transfer condition rather than interpret it as changed scientific content.

## Proposed work and completion conditions

Before making stronger scientific claims, confirm Paper1 scope, review the diagnosis rule and GSE193066 units, resolve LOSO patient policy/testing family, restore expression inputs and rerun affected checks. Add confidence to the shortlist; distinguish residual outputs from current results; freeze the exact k5 override and release version. Existing confirmed association results can be described cautiously while affected validation claims remain provisional.

Before biological interpretation, verify the primary cohort papers and modern terminology, inspect driver genes behind enriched terms and the pancreatic developmental annotation, and review confounding/cell composition. Graph annotation or absence of an association is not proof of mechanism or novelty.

Before submission, update the Word draft, verify references, correct Figures1/6/9 and S13/17/19, proof all figures at final size, and prepare data/code availability, versioned archives, author and ethics statements. [Scientific Reports guidance](https://www.nature.com/srep/author-instructions/submission-guidelines) supports Data Availability and figure-legibility requirements; detailed current limits still need verification because the full page was blocked by its identity redirect during this audit.

## Questions for researcher or mentor

1. Is Paper1 an exploratory stage-resolved resource, or must it include a validated patient-stage model?
2. Can the original mentor briefs, original metadata/unit documentation and missing raw/full-expression assets be restored?
3. Which patient policy and BH family should define LOSO, and should gene selection also be refitted per omitted study?
4. How should the 78 histology-derived diagnoses be validated, and should excluding them be a primary sensitivity check?
5. Should the balanced 25-gene list remain exploratory with timing confidence disclosed, or should selection be revised?
6. What is the approved public release, licence and archive DOI, and who supplies authorship, ethics and funding statements?

These questions are saved for review; no messages were sent to the mentor.
