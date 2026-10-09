"""Generate current method/evidence documentation from the promoted outputs."""
from pathlib import Path
import json,pandas as pd
R=Path(__file__).resolve().parent.parent;P=R/'docs/package';P.mkdir(parents=True,exist_ok=True)
D=R/'biopsy_correction_2026-10-10';comparison=json.loads((D/'comparison_summary.json').read_text())
f=pd.read_csv(R/'data/progression_full/progression_fibrosis.csv');d=pd.read_csv(R/'data/progression_full/progression_disease.csv');fs=f[(f.q_value<.05)&(f.n_agree==f.n_studies)];ds=d[(d.q_value<.05)&(d.n_agree==d.n_studies)];union=set(fs.ensembl_id)|set(ds.ensembl_id);shared=set(fs.ensembl_id)&set(ds.ensembl_id)
tier=pd.read_csv(R/'Paper1_HighConfidence/11_final_tier1_genes.csv');short=pd.read_csv(R/'Paper1_HighConfidence/shortlist_with_membership_confidence.csv');clusters=pd.read_csv(R/'Paper1_Results/Task2/task2_cluster_sizes.csv');confidence=pd.read_csv(R/'Paper1_Results/Task2/task2_bootstrap_shape_stability.csv');ks=pd.read_csv(R/'Paper1_Results/Task2/task2_choosing_k.csv');transition=pd.read_csv(R/'Paper1_Results/Task3/task3_transition_summary.csv');enrich=pd.read_csv(R/'Paper1_Results/Task4/task4_significant_counts.csv');clinical=pd.read_csv(R/'data/graph/nodes_sample_clinical.csv');counts=json.loads((D/'final_graph_readonly_verification.json').read_text())['counts'];wb=pd.read_excel(R/'Paper1_HighConfidence/12_KG_supplementary.xlsx',sheet_name=None);edges=wb['4_figure_edges'];networkgenes=edges.Ensembl_ID.nunique();mechanisms=wb['3_all_mechanisms_ranked'];selected=mechanisms[mechanisms.selected_for_figure];sig5=int((tier.LOSO_still_significant_of_5==5).sum());strong5=int((tier['LOSO_still_strong_rho0.30_of_5']==5).sum())
def table(frame):
 cols=list(frame.columns);rows=['| '+' | '.join(str(c) for c in cols)+' |','| '+' | '.join('---' for c in cols)+' |']
 for row in frame.fillna('').itertuples(index=False,name=None):rows.append('| '+' | '.join(str(v).replace('|','/') for v in row)+' |')
 return '\n'.join(rows)
def put(name,body):(P/name).write_text(body+'\n')
summary=f'''Corrected active version: 10 October 2026. Eight human liver transcriptome studies contain1,085 samples from1,027 patient IDs. Fibrosis analysis uses610 independent staged patients; the disease-group axis uses221 patients from three studies. Repeat biopsies are averaged only if fibrosis stage matches; otherwise biopsy1 is retained before any stage filtering.

Selected genes: **{len(fs):,} fibrosis**, **{len(ds):,} disease**, **{len(shared):,} shared**, **{len(union):,} union**. Tier1 has **{len(tier)} genes**, with25 shortlisted. The network displays **{networkgenes} genes**, **{len(selected)} mechanisms**, **{len(edges)} connections**, with{edges.loc[edges.In_final_25,'Ensembl_ID'].nunique()} shortlisted genes shown.
'''
put('README.md',f'''# Current research package

{summary}
The final goal clarified by the researcher is drug repurposing to identify drugs that could interrupt disease progression at different stages. This paper supplies stage-associated genes and biological context; it does not demonstrate drug efficacy or a validated patient-stage predictor.

Read01_OVERVIEW,02_METHODS,03_STATISTICS and04_LIMITATIONS before drafting. Actual data/output files take priority over dated conversations. Current supporting audit: ../biopsy_correction_2026-10-10/CORRECTION_REPORT.md in the repository. The previous package/draft are archived under archives/previous_results_2026-10-10.tar.gz.

The package contains current derived data, figures, tables and source-code copies. Bulk expression is not shipped. Root data/expression_analysis_core contains a verified14,794-gene recovery subset, not the full expression-load export; do not reload all EXPRESSES links from that subset.
''')
put('01_OVERVIEW.md',f'''# Objective and completed outputs

{summary}
## Research objective

Build a stage-informed biomedical graph linking human liver expression to OptimusKG genes, diseases, drugs, pathways, biological processes and phenotypes, supporting the next team's stage-specific drug-repurposing analysis. Association, prioritisation and annotation are completed; therapeutic prediction/effectiveness remains downstream work.

## Clinical axes and sample units

Fibrosis is F0–F4. Disease-group ordering is control→NAFL→NASH. Broad NAFLD of unspecified subtype is excluded from that ordering. Five studies stage fibrosis; three provide varying disease labels. The full resource contains668 staged biopsies, but the corrected analysis gives each of610 staged patients one contribution. Stage-by-age/sex summaries use327 patients. Raw metadata and measurements remain intact.

## Current graph

Eight labels,126,244 nodes; {sum(counts.values()):,} relationships at final correction verification. Patient identity is a Sample property, not a Patient node. Curated gene/disease/drug/annotation relationships remain unchanged; only7,706 patient-derived progression links were replaced. The graph is not trimmed to liver diseases only.

## Outputs

Task1 groups genes by qualifying axis/direction; Task2 clusters five stage profiles; Task3 models four adjacent-stage contrasts; Task4 performs local over-representation; Task5 scores genes, checks internal LOSO robustness and maps gene–mechanism connections. Top25 and top12 selection rules were not changed by the correction. Their input gene profiles/scores changed.

'''+table(clusters))
methods='''# Completed methodology

## 1. Collection and deposited expression parsing

Eight GEO studies and exact downloaded filenames are listed in06_PROVENANCE/DATA_SOURCES.md. Deposited matrices are parsed by matrix/GCT/tar branches; missing/non-numeric values removed, duplicate raw gene rows keep first, measured zeros retained. This is reanalysis of deposited counts/TPM, not a new alignment/quantification pipeline. Raw source downloads and the full acquisition chain are not supplied here.

## 2. Identifiers and clinical metadata

HGNC approved symbols, Entrez IDs, unambiguous previous symbols/aliases map to canonical version-stripped Ensembl IDs; non-HGNC Ensembl IDs pass through without annotation. Mapping failures are reported. _PAR_Y rows removed; distinct raw IDs collapsing to a gene are summed. The graph holds53,993 union genes;14,794 are measured in all eight studies. Gene category records the pilot categories, not complete HGNC biotypes.

Study-specific expression keys map to GSM via checked title/description/prefix rules. Clinical fibrosis labels, diagnosis provenance, patient identity and biopsy order are added beside raw fields. GSE135251/GSE162694 broad NAFLD is not treated as NASH. GSE130970 diagnosis is derived from steatosis/ballooning and requires clinical-definition review; GSE193066 has no usable disease diagnoses.

## 3. Measurement transformation

Library sums are calculated before mapping/filtering. TPM uses log2(TPM+1); other units use log2(CPM+1), including the unresolved GSE193066 unit. Expression is then standardised by within-study/gene mean and sample SD (ddof1); undefined SD gives0. No DESeq2/limma/edgeR or fitted batch-correction algorithm is used. Effect values are within-study SD units, not fold changes.

## 4. Shared repeat-biopsy policy

biopsy_policy.py selects repeat measurements before filtering any stage contrast. Same-stage repeats are averaged; differing stages retain biopsy1 only. There are28 same-stage and30 different-stage repeated patients. Stage means, discovery, trajectory bootstraps, stage contrasts, matched refits and LOSO use one observation per patient. Raw sample-demographics files continue to contain every original biopsy plus biopsy_number.

## 5. Progression discovery and stage summaries

Spearman within study correlates value_z with each axis; median rho summarises effects; Fisher combines p-values (clipped at10^-300); BH applies separately to retained tests on each axis. Require q<.05, all testable studies agreeing in direction, at least three testable studies. The fibrosis table tests14,794 genes; disease14,784 after testability filtering. Discovery has no minimum rho cutoff. Exported stage means average patients and rho is rounded to three decimals in downstream summary/scoring inputs.

The file diagnostic_both_q_significant.csv is a separate historical-style diagnostic: q significance on both axes plus matching median sign, without the unanimity filter. It is neither the selected shared set nor union. Define selected sets from the two complete progression tables.

## 6. Groups and trajectories

Task1 partitions selected genes into fibrosis-only, disease-only and shared, with direction. Task2 row-z-scores five patient-weighted stage means (ddof0); K-means with50 starts,seed42. Try k3–8;50 gene subsets of80% and50 patient bootstraps,10-start refits. Largest k with mean gene-subset ARI≥.95 is5 in the corrected run. Historical run selected6 under the rule and reported5 as an override; do not transfer that historical selection claim to current results.

A further100 patient bootstraps match centroids by Hungarian assignment. Membership confidence uses only own-cluster matches with r≥.5 and publishes denominators. Study-adjusted profiles use categorical stage+study OLS, then compare cluster/profile agreement.

## 7. Adjacent-stage contrasts

Fit value_z on binary higher-stage indicator plus study dummies, restricting to studies with both stages. Use one patient observation under the shared policy; no random choice between different-stage biopsies remains. OLS t test, BH across the selected fibrosis set within each contrast; substantial means q<.05 and|beta|≥.2. Power-matched refits use four studies,30 patients/stage,50 draws,seed42. Counts are within a preselected set; sampling and selection bias limit inference.

## 8. Local enrichment

MSigDB2024.1.Hs GO BP,KEGG legacy,Reactome,Hallmark; eligible background14,794 unique symbols. Intersect sets with background and retain10–500 members; group minimum5 genes. One-sided hypergeometric via gseapy; BH within group/database,q<.05. Six direction groups,five clusters,five cores at confidence≥.8. Groups below5 are untested, not tested-null.

## 9. Scores, shortlist and LOSO

P:2/1 at|rho|≥.4/.3. T:2/1 at|F4−F0|≥1/.5SD,0 if direction conflicts. X:2 if largest|beta| is substantial in full fit and reproducible with same sign/|beta|≥.2 in≥50% draws,1 for one condition. F:1 for fibrosis-only. B:2/1 for enriched membership in≥2/1 annotation databases via own group/cluster. Sum maximum9; Tier1≥7,Tier2≥5. These features share data and are not five independent validations.

Top25 remains five Tier1 genes per cluster, ranking total score then absolute rho. Alternative cluster-top-score list remains an unselected comparison. LOSO refits per-study correlations on the same biopsy rule, removes one of five staged studies and applies BH to all14,794 eligible genes before reporting Tier1. Selection is not repeated within a held-out clinical prediction design; this is internal robustness.

## 10. OptimusKG and mechanism subgraph

Gene–disease score≥.1; matched measured genes; symmetric interactions deduplicated; source drug indications/actions preserved. Eight node types/fourteen relationship types. Knowledge-loader MERGE does not remove obsolete edges automatically. Raw measurement CREATE loaders need full source exports; the core recovery is not suitable for reloading all measurements.

Pathway and BioProcess each attach directly to Gene. Test Tier1 enrichment against Ensembl background14,794 with BH over Tier1-reached mechanism nodes. Eligible mechanism size10–500,at least10 Tier1 members,q<.05. Rank byq; check Jaccard>.5 redundancy; select12. Draw genes reaching≥3 selected nodes plus shortlisted genes reaching any. No top25/top12 selection rule changed. Annotation connectivity is not causal validation.
'''
put('02_METHODS.md',methods)
put('03_STATISTICS.md',f'''# Current statistics and test families

{summary}
## Trajectory sizes and confidence

'''+table(confidence)+f'''

## k diagnostics

'''+table(ks)+'''

## Stage contrasts

'''+table(transition)+'''

## Enrichment counts

'''+table(enrich)+f'''

C3 core has one gene and is untested. Zero entries for that core do not mean a null test. Other current core findings must be read from this table rather than earlier captions.

## LOSO

BH family14,794 eligible genes per omitted-study run. Tier1 reports{len(tier)*5:,} gene/run records: {sig5}/{len(tier)} significant in all five refits; {strong5}/{len(tier)} retain median|rho|≥.30 in all five. Direction retention follows discovery consistency and is not an independent validation test.

## Selected graph mechanisms

'''+table(selected[['Mechanism_ID','mechanism','n_tier1_genes','fold_enrichment','q_value']])+f'''

Displayed network{networkgenes} genes+12 mechanisms,{len(edges)} edges. Five of25 shortlisted genes appear; ITGA2 reaches6 selected mechanisms and PDGFRA4; ADAMTSL2,NFASC,TREM2 reach one each.

Software: core dependency versions are those pinned in requirements; corrected run Python3.12.14. Baseline discovery reproduced the historical results under this runtime before correction. See the archived correction audit's runtime_requirements.txt for the exact installed environment.
''')
limits='''# Evidence boundaries and outstanding questions

- Final goal is drug repurposing; no suitable drug has been predicted or shown to stop progression by this correction.
- Cross-sectional stage associations do not establish individual progression, causality or a validated stage predictor.
- F4 has34 independent patients; late matched counts are highly variable. Counts are inside a preselected gene set; equal selection does not prove unbiased contrast comparisons.
- Disease axis uses221 patients/three studies versus fibrosis610/five; shared is independently selected association, not necessarily the same patients or specificity.
- GSE130970's78 diagnoses are derived from a simplified histology rule and need clinical-definition/source review. GSE193066 units remain unresolved.
- Modern MASLD/MASH eligibility was not reconstructed from complete metabolic/alcohol criteria. Preserve original labels transparently.
- Demographic stage summaries use327 independent patients. BMI, treatment and cell composition are not comprehensively adjusted.
- Bootstrap shape medians can conceal failed centroid matches; membership confidence is conditional on sound matches. C3 core1 is untestable. A high score does not guarantee stable cluster timing; Table6 includes individual confidence.
- Score features and annotation databases overlap. Cutoff and top-band sensitivity are material; no prospectively registered protocol establishes pre-specification.
- LOSO now uses consistent patient handling/full-universe BH, but remains selected-set internal robustness, not external validation or fully nested prediction.
- Only five shortlisted genes reach the selected twelve mechanisms. The network shows a Tier1 subset, not universal shortlist convergence.
- A pancreatic developmental annotation remains among selected mechanisms; inspect driver genes and source biology before interpreting it as a liver process. Gene annotation alone does not establish mechanism or therapeutic direction.
- Original acquisition assets, HGNC/source release dates, source-paper verification and independent cohort overlap/metadata review are incomplete.
- Expression recovery covers only the14,794-gene analysis core; do not replace all32.5million EXPRESSES links from it.

Biopsy consistency, whole-universe LOSO correction, corrected reruns and graph-link replacement are completed. Other independent evidence checks remain outstanding. Historical conflicts and original outputs are in the recovery archive, not the active package.
'''
put('04_LIMITATIONS.md',limits)
put('05_HOW_TO_VERIFY.md','''# Verify the current package

1. Recompute SHA-256 against00_START_HERE/06_FILE_MANIFEST.csv; all current files should match bytes exactly. The manifest excludes itself.
2. Filter progression_fibrosis/disease by q<.05 AND n_agree=n_studies. Compute intersections/unions rather than infer counts from filenames.
3. Check cluster-assignment IDs match the fibrosis selected set. Read confidence and confidence_n_bootstraps for individual genes.
4. Read Table6 and the mechanism workbook; the latter contains per-gene annotations, ranked mechanisms and displayed nodes/edges.
5. The correction audit under biopsy_correction_2026-10-10 records baseline reproduction, changed memberships, numerical tests, graph backup and post-update matching. Those are historical run records; active outputs now use the standard root directories.
6. Run pytest/unittest policy checks through tests/test_biopsy_policy.py from repository root. Rebuild commands are in06_PROVENANCE/REBUILD.md.

Full primary reprocessing cannot be done from this package alone: raw downloads, HGNC, original OptimusKG parquet and full expression-export assets are omitted. Packaged source copies retain repository-relative path assumptions; use the root scripts from the root checkout, or adapt paths explicitly. No database is needed to read the shipped analysis tables/network.
''')
put('DATA_DICTIONARY.md',f'''# Current data dictionary

value_z is within-study/gene standardised expression after the deposited-value log transformation. Stage means average independent patients under the shared biopsy rule; they are not fold changes.

- progression_genes/progression_fibrosis.csv:14,794 tested genes; progression_disease.csv:14,784. Fields median_rho,n_studies,n_agree,combined_p,q_value,min_rho,max_rho,symbol. Selection q<.05 plus all-direction agreement.
- diagnostic_both_q_significant.csv: diagnostic overlap with q on both and median-sign match, not selected shared/union.
- gene_tables stage/disease/age/sex summaries:{len(union)} selected-union genes; staged patients610,demographic staged patients327. sample_demographics.csv has all1,085 raw sample records and biopsy_number; analyse after selection/aggregation.
- harmonisation: original metadata, additive clinical labels/diagnosis provenance, crosswalk, mapping summary/unmapped IDs, parse summary. Raw clinical fields preserved.
- graph_nodes/nodes_gene.csv:53,993 union genes; n_datasets records study coverage. category is a pilot annotation, not comprehensive biotype.
- graph_nodes/edges_my_progression.csv and knowledge_layer/edges_my_progression.csv: identical corrected7,706 links with Ensembl gene,disease ID,relationship,rho,q,study count,direction.
- gene_progression_scores.csv:{len(union)} selected-union genes; fib_rho/fib_q and dis_rho/dis_q blank where not selected on that axis.
- knowledge layer: Gene-associated curated Disease,Drug,Pathway,BioProcess,Phenotype nodes/relations. ASSOCIATED_WITH scores≥.1; ACTS_ON mode-of-action annotations retained. No Pathway→BioProcess relationship.

All file counts/columns are recorded in the inventory and manifest; dataset sample counts are raw-resource counts, not every test's patient n.
''')
put('CODE_MAP.md','''# Current code map

Use root scripts from the repository root; source copies in05_CODE are for reproducibility review and retain path assumptions.

- pipeline01–06: expression parsing, ID mapping, crosswalk, clinical labels, union measurement build and OptimusKG integration.
- biopsy_policy.py: shared equal-stage mean/otherwise biopsy1 policy; locates explicitly named expression analysis core when present.
- pipeline07: Spearman/Fisher/BH discovery. Default same_stage_mean; first/average options retained only for historical comparison.
- pipeline08: independent-patient group summaries, retaining raw sample metadata with biopsy order.
- pipeline09: progression-edge generation from corrected selections.
- analysis: Task1groups; Task2profiles/k/bootstrap; Task3contrasts/matched refits; Task4local MSigDB enrichment; Figure1design.
- prioritisation: hc0union→hc1matched→hc2scores→hc3LOSO→hc2final→hc4network. Top25/top12 rules unchanged.
- validation: mapping/parse inspection, membership matching diagnosis, graph counts, exact mechanism memberships and version comparison. Historical recorded counts in the old verifier must not be treated as current live results; use--live.
- cypher: unique constraints; full-expression replacement (do not use the recovered core to reload); curated knowledge and patient-derived links.

The recovered14,794-gene expression subset is data/expression_analysis_core, distinct from a full expression-load export. All association/robustness scripts use that directory when available. Missing source assets are declared in provenance. Link prediction remains separate, previously failed work.
''')
# Current result README and root entrypoints derive from current statistics.
(R/'Paper1_Results/README.md').write_text('# Current Paper1 results\n\n'+summary+'\nUse Task1–4 and00_progression_genes. These replace the earlier biopsy-inconsistent results. Correction records remain in biopsy_correction_2026-10-10; previous results are only in the recovery archive.\n')
(R/'Paper1_HighConfidence/README.md').write_text('# Current prioritisation\n\n'+summary+'\nUse11_final_tier1_genes.csv and11_FINAL_shortlist_25_genes.csv for exact scores. Table6 uses shortlist_with_membership_confidence.csv. The original numerical filenames are descriptive run artifacts, not evidence of their row count.\n')
(R/'README.md').write_text('# Stage-informed liver knowledge graph\n\n'+summary+'\nThe final objective is to support the next team’s drug repurposing for interrupting disease progression at different stages. Curated biology from OptimusKG connects stage-associated genes to drugs, diseases, pathways and processes. No therapeutic efficacy or validated clinical stage predictor is established.\n\n## Active files\n\n- Paper1_Package: current data, methods, figures, tables and evidence boundaries.\n- Paper1_Results: corrected Tasks1–4.\n- Paper1_HighConfidence: corrected scores, shortlist, LOSO and network.\n- data/progression_full and data/for_mentor: corrected association/group summaries.\n- data/graph_full and data/graph_okg: current node/knowledge/progression CSVs.\n- data/expression_analysis_core: core-only recovery for analysis; never use to replace all graph expression measurements.\n- manuscript_planning: current inventory/workflow/evidence map/missing information.\n- biopsy_correction_2026-10-10: verified correction audit, comparison and graph rollback snapshot.\n- archives: checksum-verified recovery copy of superseded results/draft; excluded from Git by default.\n\n## Rebuild and checks\n\nRead docs/provenance/REBUILD.md. Run scripts from repository root with explicit outputs. Requirements cover Paper1; requirements-link-prediction.txt is optional and unrelated to the verified Paper1 results. Patient-policy tests are in tests/.\n\nHistorical Claude sessions under handover/ preserve rationale and rejected branches; their counts/method descriptions are not current results.\n')
(R/'CLAUDE.md').write_text('# Current project context\n\n'+summary+'\nFinal purpose, clarified by the researcher: a graph for stage-informed drug repurposing to interrupt progression. Use the active root directories and Paper1_Package, not archived historical numbers.\n\nSame-stage repeat biopsies are averaged; differing stages retain biopsy1 before all contrasts. Stage summaries and LOSO use the same independent-patient policy; LOSO BH uses14,794 eligible genes. Top25: five Tier1 genes per cluster, score then|rho|. Top12: enrichment-ranked mechanisms with existing eligibility/redundancy rules. Those selection rules are unchanged.\n\nRaw expression/sample nodes and curated knowledge were preserved; current patient-derived links match corrected CSVs. The recovered analysis core is not a full measurement-load export. All missing metadata/unit/clinical-definition/causality questions remain explicit in04_LIMITATIONS.md.\n\nExecute source scripts from root. Prioritisation order hc0→hc1→hc2→hc3→hc2→hc4. Never mix old intermediate files with a corrected run.\n')
print('Current docs generated from active outputs.')
