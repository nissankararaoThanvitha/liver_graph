# Current repository versus manuscript review

Reviewed 4 November 2026. Repository main commit: `7b71ea80fbd02c29740e757e9af8eb11abfd5604`. Paper: https://www.overleaf.com/project/6aeadb061fca29e951a67537 . Fresh main and supplementary source snapshots are saved beside this report. Untracked local history was not treated as published repository evidence. No code, result tables, graph or manuscript were edited.

## Outcome

The main numerical findings are supported by the published result tables. All P/T/X/F/B components were independently reconstructed from the retained inputs for all 3,845 fibrosis genes, with zero differences from the final table and 447 reconstructed Tier 1 genes. Remaining fixes concern the graph rebuild/verification workflow, stale documentation and manuscript interpretation/consistency. This is not a complete raw-data reproduction or a new live-database audit.

## Repository fixes

### R1. Supply the missing final drug-schema conversion (high priority)

Evidence: `scripts/write_new_links_to_graph.py:45` still sets `REL, XLAB = "EXTERNAL_ACTS_ON", "ExternalDrug"`. Its header explicitly says it recreates an older layer. `docs/provenance/REBUILD.md:56` and `data/graph_drug_layer/README.md` acknowledge that the conversion to the final ACTS_ON relationship type is not saved as a script.

Impact: following the documented rebuild does not produce the paper's final single-Drug, single-ACTS_ON schema. The `--as-drug` option adds Drug but does not remove ExternalDrug. The committed final graph count record and downloadable graph can be correct despite this rebuild gap.

Required fix: add an explicit, repeatable migration (or a final-schema writer) preserving endpoints and all action/source/evidence properties; remove the auxiliary label only after verifying that every such node has Drug; retain counts and identity/property checks, then include the command in the rebuild guide. Treat existing unified relationships as already migrated, rather than deleting/recreating them on every run. No graph mutation was attempted in this review.

### R2. Repair the subgraph verification script (high priority)

Evidence: `scripts/verify_against_neo4j.py:74` reads `HERE / "12_KG_supplementary.xlsx"`, where HERE is scripts/. The actual tracked workbook is Paper1_HighConfidence/12_KG_supplementary.xlsx. The expected scripts/ workbook does not exist.

It also compares original Reactome-only CSV totals with whole-current-graph Pathway/IN_PATHWAY totals at lines 81–106. The added 236 pathways and 20,031 memberships make that comparison fail even when original annotation membership is unchanged.

Required fix: accept an explicit workbook/results path with the correct default; compare the original annotation universe to the matching subset in the live graph, and use verify_extended_graph_counts.py separately for whole-graph totals. Keep endpoint-level checks for the selected 12 annotations. Do not silently add the new pathways to the manuscript's original annotation-testing family.

### R3. Make fresh-clone rebuilding actionable (high priority for reproducibility)

Evidence: REBUILD.md:7 says the checkout has a recovered expression core, but neither data/expression_analysis_core nor data/graph_full is tracked. The first command at line 16 requires that missing core. The guide starts with derived expression inputs and does not give a complete fresh-download-to-analysis sequence. DATA_SOURCES.md acknowledges that metadata acquisition is not fully scripted.

Required fix: clearly distinguish reading result tables, importing the downloadable graph, and reproducing the analyses. Provide exact preparation/extraction commands for the expected analysis input format, or the complete raw-download, metadata, parsing, mapping and graph-building sequence. Raw source files need not be committed. In particular, unpacking the graph ZIP does not by itself produce the per-study edges_GSE*.csv format expected by the analysis scripts.

### R4. Correct stale documentation and the dry-run statement (medium priority)

- REBUILD.md:42 says every graph addition defaults to dry run, but `scripts/add_msigdb_pathways.py` defaults to loading Neo4j; only --dry-run avoids graph writes. Correct the guide or standardise the command defaults.
- REBUILD.md:9 points to a separate optional requirements file that is no longer tracked.
- DATA_SOURCES.md names 02_map_gene_ids.py and task4_enrichment.py; current names are map_gene_ids.py and paper1_task4_enrichment.py. It also points to the removed biopsy_correction runtime file; the retained final_combined runtime record is available.
- The general methods documentation and script headers still contain stale counts such as 507 Tier 1 genes, 25 shortlist genes, 3,645/3,681 fibrosis genes, and 668 staged patients where current analysis uses 610. These comments do not change the checked executable scoring logic, but can mislead readers. Preserve genuinely historical records with explicit dates; update active explanatory text.
- docs/paper1/02_METHODS.md describes 14 relationship types without clearly identifying it as the original layer; the current full resource has 15.

### R5. Retain current manuscript figure-generation sources (recommended)

docs/PAPER1_MAP.md explicitly says the final paper figures are not in the repository. This is disclosed, so it is not a false availability claim. However, scripts/make_fig1.py generates an older diagram with task labels and a downstream repurposing box; it is not the current manuscript figure. Publishing the final assembly/layout scripts or editable vector sources would improve figure reproducibility and prevent users from rebuilding obsolete layouts. This does not require distributing restricted gene-set source files.

### R6. Add lightweight automated release checks (recommended)

The five existing tests cover biopsy handling and pass. No tracked CI workflow exists. Add checks for selected-set/cluster ID agreement, 447 Tier 1 genes, the 23-row shortlist, score rules, and documented graph-composition arithmetic. A clean-environment smoke test would also catch moved workbook paths. Such checks supplement, rather than replace, scientific validation.

## Manuscript corrections still present in the freshly read source

### P1. Confidence comparison uses the wrong denominator

The Results comparison of Tier 1 versus "other fibrosis-associated genes" is still 71% versus 48%. Repository counts are 319/447 = 71.36% for Tier 1 and 1,519/3,398 = 44.70% for the remaining genes. Use 71% versus 45%. Alternatively explicitly compare Tier 1 with all selected genes, for which 1,838/3,845 = 47.80%.

### P2. Replace equal-power and causal-separation language

Results still says F3–F4 remained prominent "at equal power"; Discussion says matched refits "separated biological from power-driven differences". The implementation matches sample counts and study allocation, not all determinants of power, and does not isolate biological causation. Describe persistence under sample-size-matched refits. Keep the existing caveats about 34 F4 patients, draw overlap, and unmeasured confounding.

### P3. Soften the C3 plateau description

"Without further increase" is used repeatedly. The stored C3 pooled stage means are -0.2697, -0.0120, 0.1081, 0.2133 and 0.1360. This is an approximate early-rise/plateau shape, not literally no increase after F1 or evidence of equivalence between later stages. Use an approximate shape description consistently.

### P4. Restrict the research-gap claim

The Introduction still generalises that earlier studies summarised progression as categorical contrasts, despite its own table marking separate F0–F4 analysis for Hoang and Govaere. Frame the contribution around the particular combination of cross-study associations, stage-pattern clustering, adjacent-stage comparisons, prioritisation and graph interpretation. Avoid implying all prior studies lacked stage information.

### P5. Synchronise supplementary authors

Current main and README agree on five authors and Ashmita Dey corresponding. The live supplement still lists the original three authors and V. Lakshmi Nikitha corresponding. A corrected local supp_author_details_corrected.tex was prepared previously, but the online file remains unchanged because the session is view-only.

### P6. Align checksum coverage and pointers

The repository now has docs/provenance/SOURCE_CHECKSUMS.txt with the original 15 HGNC/OptimusKG entries plus four MSigDB hashes and an added recheck statement dated 4 November. The supplement reproduces only the earlier 15-entry manifest and expressly excludes MSigDB. That is not evidence that those 15 hashes are wrong; it means the two manifests have different coverage and dates. Identify the older record versus the extended record clearly, link to the canonical repository manifest, or update the supplement to include the four new entries. Do not infer official release dates from file modification dates. This review did not independently rehash unavailable original inputs.

### P7. Add the actual AI-assistance disclosure

Neither current source contains a Claude/Codex or other AI-assistance disclosure. Describe actual assistance and human verification, following the publisher's policy: https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation . Do not invent tool versions or author-review actions.

### P8. Availability timing is now aligned (resolved)

The freshly saved source already removes the proposed public-release priority from Conclusions and adds the existing graph release to Availability, explicitly excluding KEGG. The earlier finding does not apply to this snapshot; no availability correction is currently required on that basis.

The project is currently labelled/formatted for Human Genomics. Confirm that this is the intended journal before applying the older Scientific Reports formatting requirements.

## Items already fixed or confirmed — do not repeat earlier missing-item claims

- README now lists five authors, current resource counts, code MIT licence, graph links and separate source-data terms.
- The nesting script and result files now exist: 3,533/3,845 = 91.89%; C1 splits 311/546; rerun-k5 agreement is recorded as ARI 1.000.
- Source checksums now include MSigDB; they are no longer absent from main.
- Latest main paper now correctly reports 889 genes with unrounded |rho| >= .30 and 165 with >= .40. It also uses shared-gene p = 1.8e-270, consistent with recomputed 1.764592e-270.
- Latest abstract explicitly says 442 remained significant in every LOSO refit.
- Latest Results correctly identifies six maximum-score genes: PDGFRA, MYC, CACNA1C, TPM4, PLK3, TAX1BP3; five enter the representative shortlist.
- Committed tables reproduce selected sets 3,845/4,199, overlap 1,822, union 6,222; testing families 14,794/14,784; 14,794 unique symbol background; Tier counts 447/1,403/1,995; shortlist 23; Tier 1 cluster counts 93/262/7/3/82.
- The entire P/T/X/F/B score vector was independently reconstructed from stored stage, transition, matched-refit and enrichment inputs for all 3,845 genes: zero component mismatches; 447 genes score >= 7. No discovery or expression pipeline was rerun.
- Five biopsy-policy unit tests pass in the available pandas/scientific environment. The system Python initially lacked pandas; this is an environment issue, not a failed scientific test. All 35 tracked Python files parse without syntax errors.
- Invoking only the pure expected-count calculation from verify_extended_graph_counts.py reproduced 126,999 nodes, 35,160,254 relationships and 15 types; all six saved-write-log checks passed. The committed record also reports a matching live count on 4 November. No fresh database query or graph write was performed here, and the saved live record was not overwritten.
- Public release page, CSV ZIP and Neo4j dump links all returned HTTP 200 during this review. ZIP response length: 693,904,947 bytes; dump: 1,288,186,298 bytes. They were checked without downloading the bulk files. Their contents, hashes and test import were not independently verified in this review.
- No GMT source gene-set files are tracked. README explicitly separates full graph and KEGG-excluded release counts. Enrichment-result tables and pathway–NAFLD result tables remain present; this is not a legal assessment of all upstream redistribution terms. DATA_TERMS.md itself still marks some source permissions unconfirmed, which should be resolved before claiming permissions are fully cleared.

## Recommended order

1. Repair the graph migration and annotation verifier.
2. Complete and test fresh-clone input preparation; correct stale command/path/default documentation.
3. Apply remaining manuscript wording, author and manifest-alignment fixes.
4. Retain final figure-generation sources and add small automated consistency checks.
5. Pin the reviewed submission commit/release. The existing graph-export tag need not be repurposed as the manuscript's code-version identifier.

None of the confirmed reporting/documentation problems alone establishes that the gene shortlist must be rerun or that the completed scientific results are invalid.
