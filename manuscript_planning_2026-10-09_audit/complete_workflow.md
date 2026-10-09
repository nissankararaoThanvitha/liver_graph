> **Follow-up, 10 October 2026:** This is the preserved first-stage audit of the earlier results. The researcher clarified that the final goal is drug repurposing to stop progression at different stages; a patient-stage classifier is not the intended endpoint. Biopsy handling and affected analyses have since been corrected. Use `biopsy_correction_2026-10-10/CORRECTION_REPORT.md` for current counts, validation and graph status; historical findings below remain for traceability.

# Complete reconstructed workflow

Audit date: 9 October 2026. This reconstructs the completed project from its documentation, implementation, output files and dated development history. It is a planning record, not a new analysis run. Original files and graph data were preserved.

Paths are relative to /home/nikitha07/Projects/liver_graph. Package script paths below start at Paper1_Package/05_CODE/. See research_inventory.md for full dataset/schema inventories and results_evidence_map.md for publication mapping. Stored results can be confirmed without certifying that their scientific interpretation or validation is complete.

## Development chronology

Git dates establish implementation milestones, not acquisition dates or exact computation times. Claude transcripts are dated snapshots that also recount earlier events.

| Date | Commit | Completed milestone |
|---|---|---|
| 21 August 2026 | ec546c4 | Initial liver pipeline and curated pilot |
| 25 August | b8cadd4, 3878234, 61e7210 | Clinical harmonisation, GSE130970 derived labels and patient identity |
| 30 August | 585d0ff | Scale to the 53,993-gene union and integrate PrimeKG |
| 1 September | fed83be | Initial per-study progression analysis |
| 6 September | 3eb9671 | Replace PrimeKG with OptimusKG and add progression edges |
| 6 September | f1f513a | Retain measured zeros; historical union becomes 4,692 genes |
| 7 September | 07901cd | Link-prediction pipeline; first model fails its documented validation |
| 8 September | 747788e | Mentor’s stage/age/sex gene exports, following 7 September meeting |
| 6 October | 4011761 | Tasks 1–4 on earlier inputs |
| 6–7 October | 69705e7 through ffafe5d | Handover/setup, repository overview and separate Paper 2 scaffold |
| 8 October | ffafe5d, 26386ac | Prioritisation of earlier 3,645-gene fibrosis set; package assembly |
| 8 October | 3b361a6, 35a825a, 417238b | Repair mechanism network to actual OptimusKG layer; check live membership |
| 8 October | 7efea5d, 5e763b1 | Name superseded PrimeKG path and document untrimmed graph |
| 9 October | dfb1922 | Pair discovery expression with first-biopsy stage; reconcile graph/CSVs |
| 9 October | d2d7c69 | Rebuild Tasks 1–4 after corrected labels and repeat policy |
| 9 October | 5545955 | Remove superseded result folders; move analysis code into scripts/ |
| 9 October | ff01293 | Rebuild package using current results |
| 9 October | d8db10c, 5af209d | Add regenerable progression-edge script and complete knowledge loader |
| 9 October, this audit | read-only | Verify updated liver_kg and prepare the manuscript-planning records |

Sources: git log in chronological order; CLAUDE.md/Pipeline and Session history; handover/sessions/01–04. The package predates some final edge/loader updates, so freshness is checked per artifact.

## 1. Establish the study aim and separate the clinical axes

**Objective and rationale:** identify genes and biological programmes associated with liver-disease severity, as a foundation for eventual stage prediction and therapeutic prioritisation. The researcher’s datasets use inconsistent identifiers and clinical vocabularies, while curated graphs do not encode these patient-level measurements.

**Inputs and decisions:** mentor discussions and briefs referenced in the handover. Session 02/The problem and session 04’s stage-prediction exchanges preserve the aim “predict the stages.” Session 03 references “Immediate work for Paper 1.docx”; the original brief is absent. Later prioritisation scripts refer to another brief not available here.

**Completed scope:** Paper 1 examines stage-associated genes, expression shapes, adjacent-stage differences, enrichment and prioritisation. Fibrosis F0–F4 is separate from control→NAFL→NASH. “Inflammation” is the project’s shorthand for the disease-group axis, not a directly measured inflammation score. No patient-stage classifier was completed. Drug-link prediction became separate work.

**Sources/limitations:** CLAUDE.md/The aim and Known limits; package 01_OVERVIEW/The aim. Exact original mentor wording beyond the exported conversations cannot be independently verified.

## 2. Collect eight expression studies and clinical metadata

**Objective:** assemble independent public human liver cohorts with complementary severity information.

**Inputs:** eight GEO accessions and supplementary filenames in research_inventory.md and package 06_PROVENANCE/DATA_SOURCES.md; series matrices for per-sample characteristics; HGNC complete set for identifiers.

**Documented procedure/output:** download expression matrices and series metadata, producing raw assets and samples_metadata.csv. Combined cohort: 1,085 sample records from 1,027 patient IDs; GSE193066 includes 58 repeated biopsies.

**Limitations:** raw files, original series matrices, HGNC reference, acquisition script/logs, download dates/checksums, study screening strategy and complete primary-paper bibliography are absent. The current expression parser does not reconstruct every upstream metadata retrieval step. GEO/PMID references are documented leads, not independently verified source records for all studies.

## 3. Parse heterogeneous expression formats

**Script/input:** pipeline/01_parse_expression.py; eight supplementary files.

**Methods:** DATASETS selects matrix, GCT or tar archive. CSV/TSV is a delimiter choice, not a fourth algorithm. GCT skips two headers and removes Description. Archive members are decompressed and merged using GSM identifiers. Numeric columns are selected; identical raw gene rows keep the first; values are melted to long format and non-numeric/missing entries removed. Identifier inference inspects the first 500 IDs, requiring more than 80% Ensembl or numeric IDs.

**Parameters/output:** measured zeros retained by default; --drop-zeros reproduces the older branch. Output columns: dataset_id, sample_key, gene_id_raw, gene_id_type, value, unit. Eight compressed long tables and _parse_summary.csv were produced; only the summary is shipped locally.

**Rationale/change:** deleting measured zeros created stage-dependent missingness. Historical IL6 detection at F1 versus F4 motivated retention. The old zero-dropped analysis was superseded; individual detection claims cannot be recalculated without bulk data.

**Issues:** summary n_genes precedes raw-row deduplication; duplicate/missing rows are not comprehensively reported. This is processing deposited matrices, not alignment or primary RNA-seq quantification.

## 4. Harmonise gene identifiers

**Script/input:** pipeline/02_map_gene_ids.py; long tables and HGNC approved entries.

**Methods/parameters:** map unique identifiers per study, then join to measurements; strip Ensembl version suffixes. Resolve Entrez, current symbol, unambiguous previous symbol and unambiguous alias in priority order. Exclude withdrawn dictionary entries. Retain Ensembl IDs absent from HGNC, with blank annotation. Stream chunks of 500,000 rows.

**Outputs/results:** gene_id_map.csv, unmapped_genes.csv and _mapping_summary.csv; union 53,993 genes, all-study common set 14,794. Unmapped total 1,807 = 241 Entrez IDs, 1,525 GSE167523 symbols and 41 GSE193066 symbols. Historical date-corrupted symbols are reported, not automatically repaired.

**Rationale/limits:** one namespace prevents duplicated gene identities; ambiguous aliases could merge different genes. Ensembl “100% mapped” reflects identifier retention, not independent annotation validation. HGNC archive version/date and checksum are missing. Sources: build_lookups/resolve and validation/check_gene_mapping.py.

## 5. Connect expression column names to GSM accessions

**Script/input:** pipeline/03_build_crosswalk.py; metadata and observed expression sample keys.

**Method:** per-study rules use descriptions, titles, GSM accessions, final title tokens, zero-padded sample numbers or an added “s” prefix. RULES records which applies to each study. The script checks generated keys against actual columns and reports unmatched keys/titles.

**Output/rationale:** sample_crosswalk.csv with 1,085 rows connects expression and clinical metadata. Rules were derived by inspection, then tested; they are not a universal automatic metadata matcher.

**Limit:** crosswalk is available, but original long matrices/series metadata and match-rate logs are absent, preventing independent verification of every original join.

## 6. Harmonise severity labels and identify repeated patients

**Script/input:** pipeline/04_normalize_clinical.py; raw characteristics, descriptions and processed metadata.

**Methods:** fibrosis values “0”–“4,” “F0”–“F4” and normal histology are mapped to integers; add disease_group, disease_provenance, patient_id and biopsy_number beside preserved *_raw fields. GSE193066 patient IDs identify 164 samples from 106 people.

**Decisions/results:** GSE135251 severity bands become NAFLD of unspecified subtype. GSE162694 normal histology becomes control, while fibrosis suffixes become NAFLD unspecified. Earlier assignment of all 112 fibrosis-coded samples to NASH was unsupported and corrected on 9 October. GSE193066 filename-derived diagnosis was rejected; three studies remain disease-unlabelled. GSE130970 uses steatosis 0→control; otherwise ballooning≥1→NASH, else NAFL, flagged derived_from_histology.

**Output/consequence:** nodes_sample_clinical.csv, 1,085 samples and 668 staged samples. Disease axis has three varying studies and 221 patients. Broad NAFLD cannot be placed on the NAFL/NASH ladder. Historical four-study/364-patient disease counts are superseded.

**Unresolved:** GSE130970’s rule omits explicit lobular inflammation; calling it a validated NASH-CRN diagnosis needs clinical review. Sources: norm_disease and full script docstring; package Methods Stage 5; Paper1_Results/README/Why there is a v2.

## 7. Transform expression and build the union measurement layer

**Script/input:** pipeline/05_build_graph_all.py; long expression, maps, crosswalk, metadata and optional pilot categories.

**Methods:** calculate library totals over parsed genes before mapping/filtering; remove _PAR_Y duplicates; omit unmapped endpoints; sum distinct raw IDs onto canonical sample/gene pairs. TPM uses log2(TPM+1). All other units, including unknown GSE193066 units, use log2(value/library total×10^6+1). Then standardise within gene/study by sample SD (ddof=1); undefined/zero SD gives 0.

**Outputs/results:** nodes_gene.csv (53,993), nodes_dataset.csv (8), eight expression-edge CSVs (32,471,042 total) carrying value_raw/value_log/value_z; n_datasets records measurement coverage. Category is inherited from the 290-gene pilot, blank for 53,703 genes, not a complete HGNC biotype.

**Historical decisions:** pilot target of about 300 genes yielded 290 shared genes and 311,322 measurements. Expanded union graph initially omitted zeros, with 23,340,664 edges; retention raised this to 32,471,042, a difference of 9,130,378. A loader comment’s 17,218,924 is a conflicting historical quantity.

**Limits:** unknown units may matter because sample-wise rescaling precedes gene-wise z-scoring. Bulk expression edges are absent. Knowledge-builder still names the absent data/graph_all node file, while the corrected workflow builds data/graph_full.

## 8. Integrate curated knowledge and load Neo4j

**Scripts/inputs:** pipeline/06_build_optimuskg_layer.py, cypher/01–03; OptimusKG parquet and measured gene union.

**Resource decision:** replace PrimeKG with OptimusKG for Ensembl joins, liver drug associations and action annotations. Direct join of 50,725/53,993 genes (94%) is documented, not recomputed from absent source parquet.

**Methods:** gene–disease evidence_score≥0.1; orient endpoints by gene membership; retain measured genes; deduplicate symmetric interactions as unordered pairs and other edges by endpoint/source relation. Retain reached knowledge nodes. Exclude anatomy, exposures and drug–drug slices intentionally. Translate INDICATION/CONTRAINDICATION/OFF_LABEL_USE into TREATS/CONTRAINDICATED_IN/OFF_LABEL_FOR. ACTS_ON retains mode of action.

**Outputs:** shipped knowledge CSVs; eight node types and fourteen relationship types in the inventory. Unique-ID constraints precede load; knowledge loader MERGEs nodes/edges and MATCHes existing genes. Expression loader CREATEs after deletion; it is not independently idempotent per load statement. Of 44,215 hierarchy rows, 142 lack disease endpoints and cannot load.

**History/limits:** disease trimming was attempted, then restoration requested. Nodes and associations were restored but some disease-touching edge types remained short. Current updated graph resolves checked shortfalls and retains all 36,044 diseases. It is an untrimmed biomedical graph applied to liver analysis. This audit did not reload or delete anything.

## 9. Identify severity-associated genes

**Script/input:** pipeline/07_find_progression_genes.py; full value_z, harmonised labels and 14,794 genes measured in all eight studies.

**Method/parameters:** per-study Spearman against fibrosis 0–4 or disease 0/1/2; exclude obese and unspecified NAFLD. Skip constant labels and studies below the labeled-row threshold of 25; require at least three testable studies. Fisher combines p-values clipped at 10^-300; median summarises rho; BH across retained tests per axis. Selection requires q<0.05 and all testable studies agreeing in direction. No minimum discovery rho cutoff.

**Repeat correction:** use first biopsy only. Earlier averaging paired measurements from two stages to one label for 30 of 58 repeated patients. Corrected discovery uses 610 staged patients, with first-biopsy cells 152/160/152/112/34.

**Outputs/results:** 14,794 fibrosis and 14,784 disease tests; selected 3,681/4,018; union 5,884, intersection 1,815. progression_both.csv has 5,755 rows selected by a different rule (q significant on both, same sign, no unanimity filter). It is neither the union nor definitive shared set.

**Limits:** primary per-study rhos/p-values are not saved; study independence/patient overlap and low-expression testability require further verification. Code docstrings retain some old “most agree”/PrimeKG statements despite current filters.

## 10. Export stage/demographic summaries and progression edges

**Scripts/inputs:** pipeline/08_export_gene_tables.py and 09_build_progression_edges.py; individually filtered progression tables, full expression and metadata.

**Methods/output:** stage, disease, stage×sex and stage×age means over sample records, plus sample_demographics.csv. Gene tables have 5,884 rows; demographic stage summaries use 385 samples. Exported rho is rounded to three decimals, later consumed by scoring. No demographic-adjusted inferential model is implemented.

**Researcher rationale:** mentor requested stage-wise progression genes and age/sex, without pathways in that export; subsequently requested pathway analyses are separate. Means retain repeat biopsies, unlike discovery.

**Graph-edge change:** regeneration script added 9 October because interactive older edges went stale. q<0.05 plus unanimity creates TRACKS_FIBROSIS→EFO_0003095 and TRACKS_INFLAMMATION→EFO_1001249, with rho/q/study count/direction. Current graph_nodes copy has 7,699 edges; knowledge_layer duplicate has stale 5,576 rows. Use explicit current source, not whichever duplicate is convenient.

## 11. Task 1: groups and cross-axis agreement

**Script/input:** analysis/task1_groups.py; exported stage gene table.

**Method/output:** partition ladder values, then split directions; write summary, top 20 per direction, Venn-style overlap and shared-rho scatter. Figures 2–3 and Table 2 derive here.

**Results:** fibrosis-only 1,866; disease-only 2,203; shared 1,815, including 13 discordant. Overall shared correlation .657; audit recomputation within concordant directions .380 and .219.

**Boundary:** labels express passing separate tests of unequal power/stringency, not exclusive biology. Cohorts overlap minimally; the overall scatter partly separates positive and negative clouds. “Shared” is not a paired-patient mechanism.

## 12. Task 2: stage-shape clustering

**Script/input:** analysis/task2_trajectories.py; 3,681 selected genes, five stage means and patient-level expression for robustness.

**Method/parameters:** row-z-score stage means (ddof=0); K-means 50 starts/seed42. Try k3–8; 50 gene subsets of 80% and 50 within-study patient bootstraps with 10-start refits. Automatic largest-k rule at mean gene-subset ARI≥.95 gives 6. Reported 5 is an override chosen for stronger silhouette/stability/confident membership. Explicit positional 5 is needed to reproduce that choice.

**Output/results:** clusters 948/1,528/209/313/683; named after fitting and ordered by centroid endpoint change. C3’s apparent reversal was renamed plateau after transition testing; comments still cite older 197 rather than current 209 genes. Outputs include assignments, sizes, representatives, k diagnostics, robustness/crosstab and five images.

**Robustness:** 100 further patient bootstraps; Hungarian centroid matching; a gene’s confidence is assessed only when its matched cluster has r≥.5. Confidence≥.8 counts 3/772/1/130/510; medians of shape recovery .976/.996/.970/.960/.994. Study-adjusted profile ARI .870, median curve correlation .998.

**Limits:** same-patient/same-stage repeats averaged; multiple stage rows retained and resampled as patient blocks. Study-adjusted OLS does not model patient correlation. Conditional confidence differs from unconditional stability, and some matched shapes fail badly. Specific gene claims require individual confidence, not a cluster-wide blanket assertion.

## 13. Task 3: adjacent-stage contrasts and matched sampling

**Script/input:** analysis/task3_transitions.py; selected genes, cluster IDs, full measurements and clinical data.

**Methods:** for each adjacent pair, exclude studies lacking either stage; average same-stage repeats; randomly retain one side for patients spanning the pair. OLS uses a binary higher-stage coefficient plus study indicators, conventional SE and t test. BH per transition across 3,681 genes. Substantial means q<.05 and |beta|≥.2 SD; seed42.

**Outputs/results:** 14,724 gene×transition records; four summaries, top genes, twenty cluster×transition records and two figures. Substantial counts 1,197/1,145/1,127/934; up 1,164/639/909/869, down 33/506/218/65; median |beta| .1886/.1846/.2211/.3753. Patient cells 152/166,160/165,165/109,118/34.

**Matched design:** per-study cell size is the minimum across stages/transitions, leaving four studies and 30 patients per stage. Fifty draws give median substantial counts 0/0/2/287; late-transition SD412.4.

**Interpretation/limits:** larger late effects under this design, among preselected genes. No longitudinal patient progression or precise 287-gene estimate. Common selection does not prove that selection bias cancels equally across comparisons; covariate and cell-composition sensitivity is not completed.

## 14. Task 4: enrichment by group and cluster

**Script/input:** analysis/task4_enrichment.py; gene groups, cluster confidence, MSigDB 2024.1.Hs GMTs and 14,794 unique background symbols.

**Methods:** six direction groups, five clusters and five cores. Restrict gene sets to background; retain sizes10–500; skip groups below5. Local gseapy one-sided hypergeometric with BH per group/database, q<.05. Code verifies one p-value with SciPy. Collections: GO BP, KEGG legacy, Reactome and Hallmark.

**Outputs/results:** current aggregate 3,706 significant group/database/term rows, counts, top terms, all-versus-core comparisons, heatmaps and dot plots. Immune annotations enrich rising fibrosis-only genes; ECM/adhesion annotations enrich shared and late-rising genes; metabolic annotations enrich falling genes. These are interpretations of memberships, not validated mechanisms.

**Important conflict:** current C1/C3 cores of3/1 are untestable; C4 core130 is tested with zero terms. Older individual C1/C3 core CSVs and dot plots persist because skipped runs do not delete files. C4’s old PNG also remains after zero findings. Current aggregate/current confidence takes priority; stale panels are excluded from current manuscript evidence.

## 15. Task 5: scoring and shortlist

**Run order:** hc0→hc1→hc2→hc3→hc2 again→hc4. The second score run merges LOSO columns; order is documented, not rerun here.

**Methods/inputs:** hc0 writes the full 5,884 union despite filename 00_all_4692. hc2 joins 3,681 fibrosis genes, clusters, transitions and annotations with one-to-one assertions. P: |rho|≥.4/.3. T: |F4−F0|≥1/.5 SD, zero if direction conflicts. X: largest |beta| substantial in full fit and/or retains direction and |beta|≥.2 in≥50% draws. F: fibrosis-only bonus1. B: enriched membership through own group/cluster in≥2 or1 database. Scores sum to9.

**Outputs/results:** Tier1≥7 gives525; Tier2≥5 gives1,464; Tier3 gives1,692. Cutoffs6/7/8 give1,127/525/148. Dropping one feature yields rank correlations .839–.953; removing P retains52/148 top-band genes. Option A selects five per cluster, ties by |rho|:25 genes,15 increasing/10 decreasing. Option B’s53 genes were computed but not selected.

**Decisions/limits:** equal quota preserves reported shapes, not equal assignment reliability. Only10/25 shortlisted genes meet cluster confidence≥.8; no shortlisted C4 gene does. Related features are not five independent experiments. Prospective freezing is claimed in comments but not independently evidenced. Export rounding affects thresholds. FST and SLC5A10 have endpoint direction flags; the latter has rounded zero endpoint difference. No validated diagnostic panel or clinical prediction accuracy.

## 16. Leave-one-study-out robustness

**Script/input:** hc3_leave_one_study_out.py; 525 Tier1 genes, clinical data and full expression.

**Method/output:** recompute per-study Spearman, omit one of five staged studies, combine p, BH per run, record direction/significance/|medianrho|≥.3. There are2,625 run rows and525 summaries. Stored significance 5/5 for521, effect threshold5/5 for263 and0/5 for76; all directions5/5.

**Unresolved implementation:** averages repeat expression across stages with the first stage label, unlike corrected discovery. BH covers selected 525 rather than discovery’s eligible universe. Selection/prioritisation is not refitted in each held-out fold. Current numbers are confirmed stored outputs, but validation claims are provisional until policy/testing family is resolved and rerun with restored expression data.

**Interpretive boundary:** internal robustness, not external replication or predictive validation. The direction-only arithmetic guarantee assumes identical discovery per-study statistics; different aggregation breaks the exact equivalence of that rationale to this code.

## 17. Mechanism subgraph from OptimusKG

**Script/input:** hc4_mechanism_subgraph.py; 525 Tier1 genes,25 shortlist, pathway/process CSVs and Ensembl universe14,794.

**Development decision:** earlier PrimeKG source was wrong and repaired. Name matching to MSigDB was rejected because vocabulary/membership differed; direct graph-node enrichment was used. Actual schema is BioProcess←Gene→Pathway, not Gene→Pathway→BioProcess.

**Methods/results:** hypergeometric/BH across4,330 Tier1-reached nodes; background size10–500,≥10 Tier1 andq<.05 leave85. Rank byq, greedy Jaccard>.5 redundancy rule, top12. No duplicate candidate is actually collapsed before reaching12 in this output. Draw genes linked to≥3 selected nodes plus any shortlisted gene linked to one:47 genes,165 edges,59 totalnodes;6 of25 shortlist represented. Fold enrichment3.38–9.61, selectedq6.29e-12–4.88e-9.

**Outputs/limits:** mechanism image and7-sheet workbook. Sheet2/notes retain507,Figure12 anddegree 2 wording despite actual525/currentFigure9/degree 3. Figure title says most-connected despite q ranking. Pancreatic ductal development label needs driver-gene/literature review. No causal mechanism validation. Current audit confirmed all gene memberships of these12 nodes against live graph.

## 18. Package/manuscript assembly and current audit

**Package method:** builder copies outputs, makes cohort table/captions/numbering and checksums. It deletes/recreates the package if run, so it was not executed. Copying whole folders does not guarantee output freshness. Packaged scripts retain repository-root assumptions, missing paths and incomplete dependencies; fully self-contained rebuilding is not currently demonstrated.

**Existing manuscript:** Word draft covers Tasks1–4 using older4,692/3,645/1,692 counts and311 matched median. It contains old diagnosis errors and REF/author/Discussion/Conclusion placeholders. These historical drafting instructions were not treated as current requests. No manuscript prose was written.

**Current audit:** all264 package files and214 additional existing files read/indexed, tables parsed, workbooks fully extracted and designated figures reviewed. Updated liver_kg authenticated, schema/counts and progression-link identities checked, twelve mechanism memberships matched. Byte checksum differences are exactly explained by LF/CRLF conversion. Missing assets remain explicit. Four planning documents and audit records were created in a separate directory.

## Uncompleted or failed branches

- ComplEx code and a historical smoke test exist; first model failed documented known-drug ranking. Model files, metrics, splits and logs are absent. Default40epochs/dim128 are options, not proof of a successful run.
- Historical111 rule-derived drug candidates and3,147/3,839 gene-gap counts are transcript query reports, not current traceable candidate tables or therapeutic validation.
- Meta-paths are descriptive walks through existing relationships, not validated causal paths or missing-link predictions.
- Liver-only trimming was proposed, attempted and restored; current graph remains untrimmed.
- Stage classifier, RAG/chatbot, author contact, new clinical metadata and independent validation are future work without completed outputs here.
