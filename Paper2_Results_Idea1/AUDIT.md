# Paper 2 audit (Tasks 1–8)

Independent re-computation from source files and a fresh read-only Neo4j query. Script: `Paper2_Results_Idea1/code/audit_tasks.py`.

**93 / 93 checks passed.**

| Task | Check | Result | Detail |
|---|---|---|---|
| T1 | 6,222 rows, unique Ensembl IDs | ✅ | 6222 rows |
| T1 | same gene set as Paper 1 union | ✅ |  |
| T1 | rho, q and F0–F4 copied exactly from source | ✅ |  |
| T1 | progression class matches Paper 1 ladder | ✅ |  |
| T1 | fibrosis direction matches source | ✅ |  |
| T1 | fibrosis direction agrees with sign of rho | ✅ |  |
| T1 | cluster sizes match Paper 1 Task 2 | ✅ | C1=857, C2=1367, C3=226, C4=397, C5=998 |
| T1 | 23 shortlist genes flagged | ✅ |  |
| T1 | class totals match Paper 1 Task 1 | ✅ |  |
| T1 | annotations only on 3,845 fibrosis genes | ✅ |  |
| Graph | TRACKS_FIBROSIS edges = the 3,845 Task 1 fibrosis genes, same rho and direction | ✅ |  |
| Graph | no script reads the stale Gene.fibrosis_rho node property | ✅ | note: node property missing for 391 fibrosis genes (pre-correction values); edges are current |
| T2 | edge count equals fresh Neo4j query | ✅ | 8948 vs 8948 |
| T2 | identical drug–gene–action triples vs Neo4j | ✅ |  |
| T2 | identical to knowledge-layer CSV | ✅ |  |
| T2 | every edge gene is a progression gene | ✅ |  |
| T2 | action → direction mapping consistent | ✅ | 0 inconsistent |
| T2 | known-direction count = 1,001 | ✅ |  |
| T2 | gene annotations agree with Task 1 | ✅ |  |
| T3 | background = 14,794 genes, contains all 6,222 | ✅ |  |
| T3 | background % any link (indep.) = 14.5% | ✅ | 14.52% |
| T3 | background % pharmacological (indep.) = 13.0% | ✅ | 12.98% |
| T3 | fibrosis-associated count & Fisher p reproduce independently | ✅ | 639/3845, p=2.86e-14 |
| T3 | fibrosis_only_negative count reproduces | ✅ | 190/983 |
| T3 | shared_negative count reproduces | ✅ | 87/384 |
| T3 | inflammation_only count reproduces | ✅ | 319/2377 |
| T3 | permutation p-values within [1/1001, 1] | ✅ |  |
| T4 | per-drug progression-gene counts reproduce | ✅ |  |
| T4 | drugs with only enzyme/transporter links have 0 pharm genes | ✅ |  |
| T4 | pharm targets in graph ≥ progression targets | ✅ |  |
| T4 | progression_target_fraction in [0, 1] | ✅ |  |
| T4 | malaria/gallbladder/ampulla/erythropoietic removed from liver set | ✅ | 161 kept, 70 removed |
| T4 | core liver diseases kept (NAFLD, NASH, cirrhosis, HCC) | ✅ |  |
| T4 | hepatoerythropoietic porphyria kept (hepatic) | ✅ |  |
| T4 | Idea 1: fibrosis-type set = Task 5 fibrosis-spectrum names, none non-hepatic | ✅ | 21 of 161 |
| T4 | no candidate has a fibrosis-type liver TREATS/OFF_LABEL use (fresh query) | ✅ | 0 violations |
| T4 | Idea 1: brought-back drugs have a liver use, but none fibrosis-type | ✅ | 160 brought back |
| T4 | all candidates phase ≥ 2, not withdrawn, ≥1 progression gene | ✅ |  |
| T4 | candidate count reproduces from coverage table | ✅ | 1269 |
| T4 | mechanism-annotated list reproduces | ✅ | 666 |
| T4 | candidates sorted by fibrosis coverage then fraction | ✅ |  |
| T4 | network: 30 drugs, every edge endpoint is a node | ✅ |  |
| T4 | network uses no enzyme/transporter/carrier links | ✅ |  |
| T5p | proxies satisfy Jaccard ≥ 0.5 and ≥ 5 shared genes | ✅ | 82 proxies |
| T5p | name matches use the right node type (GO→BioProcess, Reactome→Pathway) | ✅ |  |
| T5p | name matches are exact after normalisation | ✅ |  |
| T5p | no fuzzy matches remain | ✅ |  |
| T5p | all 1,903 Paper 1 terms present | ✅ |  |
| T5 | Python path counts = Neo4j counts (M1–M4, M6) | ✅ | 8 checks |
| T5 | M1 reproduces with a fresh query (no drug filter needed) | ✅ | 24,497 paths, 1,921 drugs |
| T5 | M6 per-transition paths reproduce from Task 2 edges | ✅ |  |
| T5 | M5 cluster paths sum to M4 paths minus non-cluster end genes | ✅ |  |
| T5 | drug scores cover all 2,407 pharmacological drugs, DNS ≥ 0 | ✅ |  |
| T5 | 3 example subgraphs saved (CSV; pictures not drawn in Idea 1 rerun) | ✅ |  |
| T5 | Example 3 drugs = all candidates acting on PDGFRA | ✅ |  |
| T5 | Cypher file is read-only (no CREATE/MERGE/SET/DELETE) | ✅ |  |
| T6 | prototype scores all 6,222 genes, every component in [0, 1] | ✅ |  |
| T6 | every design-test row points to the final ranking | ✅ |  |
| T6 | inflammation-only genes: T = 0 and B = 0 (structural zeros) | ✅ |  |
| T6 | framework document numbers match prototype outputs | ✅ | all match |
| T6 | framework covers definitions, normalisation, missing values, ablation, Dirichlet | ✅ |  |
| T6 | freezing rule recorded and applied | ✅ |  |
| T7 | all requested columns present, one row per Task 2 link | ✅ | 8,948 rows |
| T7 | consistency labels reproduce with independent code | ✅ |  |
| T7 | 88.5% unknown direction stated and correct | ✅ |  |
| T7 | candidates with ≥1 consistent link reproduce | ✅ | 382 |
| T7 | candidate patterns add up to 1,109 | ✅ |  |
| T7 | summary states consistency is a hypothesis, not proof | ✅ |  |
| Final | pre-registration written with frozen rules | ✅ |  |
| Final | target scores = equal-weight mean of components (biology P,F,T,B; actionable +K) | ✅ |  |
| Final | both target lists cover all 6,222 genes | ✅ |  |
| Final | drug lists = 559 main-list and 1,109 candidates | ✅ |  |
| Final | DrugScore = equal-weight mean of D1–D4, all in [0, 1] | ✅ |  |
| Final | D1 reproduces independently | ✅ |  |
| Final | D2 reproduces independently | ✅ |  |
| Final | no ranked drug already has a fibrosis-type liver use | ✅ |  |
| Final | summary says repurposing hypotheses, not treatments | ✅ |  |
| Rev | Task 5 revised: MP1–MP3 path counts = Neo4j | ✅ |  |
| Rev | Task 5 revised: no BioProcess MetaPath | ✅ |  |
| Rev | Task 5 revised pharmacological MP1 = original Task 5 MP1 | ✅ | 24,497 |
| Rev | Task 5 revised: no 'NEW' pair is a known use (fresh query) | ✅ |  |
| Rev | Task 7 revised: pathway directions follow the stated rule | ✅ |  |
| Rev | Task 7 revised: route consistency labels reproduce | ✅ |  |
| T8 | report states KG-only repurposing scope and out-of-scope items | ✅ |  |
| T8 | report has the 6,222 vs 4,692 note | ✅ |  |
| T8 | report lists the 4 required limitations | ✅ |  |
| T8 | shortlist-supported vs broad counts correct | ✅ | 107 vs 1,162 |
| T8 | known-direction share correct (1,001 / 8,948 = 11.2%) | ✅ |  |
| T8 | 'treatment' only used in negation | ✅ |  |
| Rules | no anti-fibrotic claim in summaries | ✅ |  |
| Rules | no old 'reversal' wording in summaries | ✅ |  |
| Rules | no best-candidate claim in summaries | ✅ |  |
| Rules | every task summary mentions 6,222 vs 4,692 | ✅ |  |
