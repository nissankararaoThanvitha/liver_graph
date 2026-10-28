# Paper 2 — Task 4: drug coverage and repurposing candidates

**Gene set note:** the plan refers to 4,692 genes (pre-correction). This uses the corrected Paper 1 union of **6,222 genes**.
**Scope:** knowledge graph only (project scope decision: repurposing, not reversal). Main analysis uses **pharmacological-target links** (ENZYME/TRANSPORTER/CARRIER removed, Task 3); any-link gene counts are in `n_progression_genes_any_link`.
Script: `Paper2_Results_Idea1/code/task4_drug_coverage.py`.

**This is candidate generation only.** Coverage is not a therapeutic score. Broad, heavily annotated drugs (e.g. multi-kinase inhibitors) touch many genes, so `progression_target_fraction` (progression targets / all pharmacological targets in the graph) is reported alongside coverage. No drug here is "the best candidate".

**Idea 1 rerun:** only drugs already used for a fibrosis-type liver disease are excluded. Fibrosis-type = liver diseases whose name matches *fatty liver, steatohepatitis, cirrhosis, fibrosis, portal hypertension, liver failure* (the Task 5 fibrosis-spectrum definition; 21 of 161 liver diseases, flagged in `liver_disease_set.csv`). Drugs used only for liver cancer, viral hepatitis, bile-duct cancer or other liver diseases are now **kept**: using them for fibrosis is still repurposing. Diagrams are not drawn in this rerun.

## From drugs to repurposing candidates

| Step | Drugs |
|---|---|
| Drugs with ≥1 pharmacological link to a progression gene | 2407 |
| …with max_phase ≥ 2 | 1392 |
| …and not withdrawn | 1333 |
| …and no existing FIBROSIS-TYPE liver-disease TREATS/OFF_LABEL_FOR use (Idea 1) → **repurposing candidates** | 1269 |
| …of which mechanism-annotated (≥1 link with known action or mechanism text) → **main list** | 666 |

- Liver disease = `EFO_0001421` "liver disease" + all `PARENT_OF` descendants, **minus 70 non-hepatic-tissue entries** that EFO files under it (malaria, gallbladder / ampulla / extrahepatic bile-duct tumours, erythropoietic porphyrias) = **161 liver diseases**. Both kept and removed entries are listed in `liver_disease_set.csv`. Without this step, antimalarials such as those for *Plasmodium* malaria would be wrongly treated as existing liver drugs.
- 227 drugs hitting progression genes have some liver-disease TREATS/OFF_LABEL_FOR use; only the **65** with a fibrosis-type use are excluded now (reference set in `drug_coverage.csv`).
- Old rule (any liver use) removed 224 phase ≥ 2, non-withdrawn drugs; **160 of them are brought back** by Idea 1 (`brought_back_by_idea1`).
- 181 candidates are **contraindicated** in a liver disease. They are kept and flagged (`liver_contraindicated`), as requested.
- 107 candidates hit at least one gene in the Paper 1 23-gene shortlist.

## Brought back by Idea 1 (top 20 by fibrosis-gene coverage)

| candidate_order | Drug | phase | n_fibrosis_genes | n_progression_genes | mechanism_annotated | liver_indications |
|---|---|---|---|---|---|---|
| 6 | CANNABIDIOL | 4 | 17 | 26 | False | Autoimmune Hepatitis |
| 7 | NABIXIMOLS | 3 | 16 | 26 | False | liver disease |
| 12 | ASPIRIN | 4 | 11 | 17 | True | alcoholic liver disease; hepatocellular carcinoma |
| 14 | DASATINIB | 4 | 10 | 13 | True | cholangiocarcinoma; hepatocellular carcinoma |
| 24 | MINOCYCLINE | 4 | 8 | 14 | False | sclerosing cholangitis |
| 25 | REGORAFENIB | 4 | 8 | 10 | True | bile duct carcinoma; biliary tract cancer; cholangiocarcinoma; hepatocellular carcinoma; intrahepatic cholangiocarcinoma |
| 32 | CHLORPROMAZINE | 4 | 8 | 9 | True | acute intermittent porphyria |
| 34 | PAROXETINE | 4 | 8 | 9 | False | chronic hepatitis C virus infection |
| 51 | CYSTEINE | 4 | 6 | 8 | False | liver disease |
| 53 | NINTEDANIB | 4 | 6 | 7 | True | hepatocellular carcinoma |
| 60 | TRETINOIN | 4 | 6 | 7 | True | sclerosing cholangitis |
| 64 | TOPIRAMATE | 4 | 6 | 9 | True | liver disease |
| 72 | ERDAFITINIB | 4 | 5 | 7 | True | hepatocellular carcinoma; liver disease |
| 73 | AMLODIPINE | 4 | 5 | 5 | True | liver disease |
| 77 | ACETAZOLAMIDE | 4 | 5 | 5 | True | hepatocellular carcinoma |
| 79 | PAZOPANIB | 4 | 5 | 6 | True | hepatocellular carcinoma |
| 81 | ILOPERIDONE | 4 | 5 | 6 | True | liver disease |
| 89 | TAMOXIFEN | 4 | 5 | 7 | True | chronic hepatitis C virus infection; liver cancer |
| 98 | ESCITALOPRAM | 4 | 5 | 5 | False | hepatitis C virus infection |
| 114 | LENVATINIB | 4 | 4 | 7 | True | biliary tract cancer; biliary tract neoplasm; cholangiocarcinoma; hepatocellular carcinoma; intrahepatic cholangiocarcinoma; liver and intrahepatic bile duct neoplasm; liver disease |

## Main list: top 20 mechanism-annotated repurposing candidates

Ordered by fibrosis-gene coverage, then progression-target fraction. "Mechanism-annotated" means the graph says *how* the drug acts on at least one of its progression-gene targets (inhibitor, agonist, … or a mechanism-of-action text). These are the interpretable candidates.

| mechanism_order | Drug | phase | n_fibrosis_genes | n_progression_genes | pharm_targets_graph | frac | n_down_actions | n_up_actions | shortlist_targets | liver CI | now used for |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FOSTAMATINIB | 4 | 82 | 131 | 302 | 0.43 | 1 | 0 | EPHA3;PDGFRA;PLK3 |  | Anemia, Hemolytic, Autoimmune; COVID-19; IGA glomerulonephritis |
| 2 | PSEUDOEPHEDRINE | 4 | 11 | 12 | 19 | 0.63 | 0 | 0 |  | ⚠️ yes | Rhinitis, Allergic, Perennial; allergic conjunctivitis; allergic disease |
| 3 | ASPIRIN | 4 | 11 | 17 | 28 | 0.61 | 2 | 0 |  |  | Barrett's esophagus; COVID-19; Disorder of lipid metabolism |
| 4 | ZONISAMIDE | 4 | 11 | 13 | 31 | 0.42 | 2 | 0 |  |  | Lewy body dementia; Parkinson disease; alcohol abuse |
| 5 | DASATINIB | 4 | 10 | 13 | 23 | 0.56 | 8 | 0 |  |  | Alzheimer disease; Blast Phase Chronic Myelogenous Leukemia, BCR-ABL1 Positive; Burkitts lymphoma |
| 6 | AMOXAPINE | 4 | 10 | 12 | 44 | 0.27 | 3 | 0 | HTR7 |  | depressive disorder; major depressive disorder |
| 7 | ENFLURANE | 4 | 10 | 12 | 52 | 0.23 | 0 | 2 | CACNA1C |  |  |
| 8 | DEXTROMETHORPHAN | 4 | 9 | 10 | 21 | 0.48 | 0 | 1 |  | ⚠️ yes | Alzheimer disease; Crohn's disease; HIV infection |
| 9 | ARIPIPRAZOLE | 4 | 9 | 12 | 44 | 0.27 | 1 | 0 | HTR7 |  | Asperger syndrome; Tourette syndrome; aggressive behavior |
| 10 | LAMOTRIGINE | 4 | 9 | 10 | 41 | 0.24 | 3 | 0 |  |  | Fish-eye disease; HIV infection; Lennox-Gastaut syndrome |
| 11 | REGORAFENIB | 4 | 8 | 10 | 18 | 0.56 | 10 | 0 | PDGFRA |  | Malignant Bone Neoplasm; acute myeloid leukemia; adenoid cystic carcinoma |
| 12 | DONEPEZIL | 4 | 8 | 8 | 15 | 0.53 | 1 | 0 |  |  | Alzheimer disease; Central Nervous System Neoplasm; Classical progressive supranuclear palsy |
| 13 | MARIMASTAT | 3 | 8 | 10 | 23 | 0.43 | 3 | 0 |  |  | breast cancer; lung cancer |
| 14 | IMIPRAMINE | 4 | 8 | 9 | 25 | 0.36 | 1 | 0 | HTR7 |  | actinic keratosis; anxiety; breast cancer |
| 15 | CHLORPROMAZINE | 4 | 8 | 9 | 26 | 0.35 | 2 | 0 | HTR7 |  | COVID-19; acute intermittent porphyria; conduct disorder |
| 16 | HALOTHANE | 4 | 8 | 9 | 34 | 0.27 | 0 | 3 |  |  |  |
| 17 | ZANUBRUTINIB | 4 | 7 | 10 | 15 | 0.67 | 1 | 0 |  |  | Anemia, Hemolytic, Autoimmune; COVID-19; Castleman disease |
| 18 | ASENAPINE MALEATE | 4 | 7 | 9 | 20 | 0.45 | 1 | 0 | HTR7 | ⚠️ yes | bipolar I disorder; bipolar disorder; psychosis |
| 19 | BROMOCRIPTINE | 4 | 7 | 8 | 18 | 0.44 | 0 | 1 | HTR7 |  | Adenomyosis; Alzheimer disease; Parkinson disease |
| 20 | HALOPERIDOL | 4 | 7 | 7 | 18 | 0.39 | 1 | 0 | HTR7 |  | Alzheimer disease; Huntington disease; Tourette syndrome |

Full list: `repurposing_candidates_mechanism_annotated.csv` (666 drugs).

## All candidates, including drugs with no mechanism annotation

The all-candidate ordering is dominated by **nutrients, metal ions and cofactors** (zinc salts, glutamic acid, pyridoxal phosphate, ATP, glycine, calcium salts). DrugBank lists many enzymes that *bind* them as "TARGET", with no action or mechanism. They are kept for completeness but are not meaningful repurposing hypotheses without mechanism evidence.

| candidate_order | Drug | phase | n_fibrosis_genes | fib_only_pos | fib_only_neg | shared_pos | shared_neg | n_progression_genes | pharm_targets_graph | frac | n_down_actions | n_up_actions | shortlist_targets | liver CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FOSTAMATINIB | 4 | 82 | 30 | 17 | 30 | 5 | 131 | 302 | 0.43 | 1 | 0 | EPHA3;PDGFRA;PLK3 |  |
| 2 | ZINC ACETATE ANHYDROUS | 4 | 39 | 2 | 23 | 6 | 7 | 49 | 124 | 0.40 | 0 | 0 | F2;KNG1 |  |
| 3 | ZINC CHLORIDE | 4 | 31 | 2 | 18 | 5 | 5 | 41 | 97 | 0.42 | 0 | 0 | KNG1 |  |
| 4 | GLUTAMIC ACID | 3 | 22 | 2 | 10 | 4 | 6 | 33 | 61 | 0.54 | 0 | 0 |  |  |
| 5 | PYRIDOXAL PHOSPHATE ANHYDROUS | 3 | 20 | 1 | 9 | 2 | 8 | 23 | 49 | 0.47 | 0 | 0 | OAT |  |
| 6 | CANNABIDIOL | 4 | 17 | 5 | 4 | 4 | 4 | 26 | 41 | 0.63 | 0 | 0 |  |  |
| 7 | NABIXIMOLS | 3 | 16 | 5 | 4 | 3 | 4 | 26 | 41 | 0.63 | 0 | 0 |  |  |
| 8 | ADENOSINE TRIPHOSPHATE | 2 | 16 | 5 | 6 | 3 | 2 | 21 | 42 | 0.50 | 0 | 0 |  |  |
| 9 | GLYCINE | 4 | 12 | 1 | 4 | 0 | 7 | 14 | 24 | 0.58 | 0 | 0 |  |  |
| 10 | PSEUDOEPHEDRINE | 4 | 11 | 2 | 2 | 7 | 0 | 12 | 19 | 0.63 | 0 | 0 |  | ⚠️ yes |
| 11 | PROCAINE | 4 | 11 | 2 | 4 | 2 | 3 | 12 | 19 | 0.63 | 0 | 0 |  |  |
| 12 | ASPIRIN | 4 | 11 | 3 | 0 | 6 | 2 | 17 | 28 | 0.61 | 2 | 0 |  |  |
| 13 | ZONISAMIDE | 4 | 11 | 3 | 4 | 1 | 3 | 13 | 31 | 0.42 | 2 | 0 |  |  |
| 14 | DASATINIB | 4 | 10 | 4 | 1 | 4 | 1 | 13 | 23 | 0.56 | 8 | 0 |  |  |
| 15 | GLUTATHIONE | 3 | 10 | 1 | 4 | 5 | 0 | 13 | 37 | 0.35 | 0 | 0 |  |  |
| 16 | AMOXAPINE | 4 | 10 | 1 | 2 | 6 | 1 | 12 | 44 | 0.27 | 3 | 0 | HTR7 |  |
| 17 | ENFLURANE | 4 | 10 | 4 | 2 | 4 | 0 | 12 | 52 | 0.23 | 0 | 2 | CACNA1C |  |
| 18 | DEXTROMETHORPHAN | 4 | 9 | 4 | 4 | 1 | 0 | 10 | 21 | 0.48 | 0 | 1 |  | ⚠️ yes |
| 19 | CALCIUM CITRATE | 4 | 9 | 4 | 2 | 2 | 1 | 15 | 32 | 0.47 | 0 | 0 |  |  |
| 20 | CALCIUM PHOSPHATE, TRIBASIC | 2 | 9 | 4 | 2 | 2 | 1 | 15 | 32 | 0.47 | 0 | 0 |  |  |

Full list: `repurposing_candidates.csv` (1,269 drugs, with current indications, target genes, cluster counts and action counts).

## Top 15 drugs by raw progression-gene coverage (all drugs, incl. existing liver drugs)

| Drug | max_phase | n_progression_genes | n_fibrosis_genes | inflammation_only_targets | pharm_targets_graph | frac | liver use |
|---|---|---|---|---|---|---|---|
| FOSTAMATINIB | 4.0 | 131 | 82 | 49 | 302 | 0.43 |  |
| CHEMBL1201279 |  | 50 | 40 | 10 | 125 | 0.40 |  |
| ZINC ACETATE ANHYDROUS | 4.0 | 49 | 39 | 10 | 124 | 0.40 |  |
| ZINC CHLORIDE | 4.0 | 41 | 31 | 10 | 97 | 0.42 |  |
| GLUTAMIC ACID | 3.0 | 33 | 22 | 11 | 61 | 0.54 |  |
| CANNABIDIOL | 4.0 | 26 | 17 | 9 | 41 | 0.63 | yes |
| NABIXIMOLS | 3.0 | 26 | 16 | 10 | 41 | 0.63 | yes |
| PHENETHYLISOTHIOCYANATE |  | 26 | 14 | 12 | 44 | 0.59 |  |
| PYRIDOXAL PHOSPHATE ANHYDROUS | 3.0 | 23 | 20 | 3 | 49 | 0.47 |  |
| ADENOSINE TRIPHOSPHATE | 2.0 | 21 | 16 | 5 | 42 | 0.50 |  |
| CHEMBL384759 |  | 21 | 5 | 16 | 36 | 0.58 |  |
| SODIUM beta-NICOTINAMIDE ADENINE DINUCLEOTIDE PHOSPHATE |  | 19 | 12 | 7 | 30 | 0.63 |  |
| FLAVIN ADENIN DINUCLEOTIDE | -1.0 | 18 | 11 | 7 | 25 | 0.72 |  |
| ASPIRIN | 4.0 | 17 | 11 | 6 | 28 | 0.61 | yes |
| CALCIUM CITRATE | 4.0 | 15 | 9 | 6 | 32 | 0.47 |  |

Full top 50: `top50_by_coverage.csv`.

## Drugs that already have a fibrosis-type liver use (reference, not candidates)

| Drug | max_phase | n_fibrosis_genes | n_progression_genes | fibrosis_type_liver_uses |
|---|---|---|---|---|
| CAFFEINE | 4.0 | 11 | 13 | non-alcoholic steatohepatitis |
| SPIRONOLACTONE | 4.0 | 10 | 14 | cirrhosis of liver; non-alcoholic steatohepatitis |
| RESVERATROL | 3.0 | 9 | 11 | non-alcoholic fatty liver disease |
| ALCOHOL | 4.0 | 9 | 10 | cirrhosis of liver |
| ERGOCALCIFEROL | 4.0 | 7 | 9 | non-alcoholic fatty liver disease |
| ICOSAPENT | 3.0 | 5 | 7 | non-alcoholic fatty liver disease |
| CYCLOBENZAPRINE | 4.0 | 5 | 5 | cirrhosis of liver |
| ORNITHINE | 3.0 | 5 | 5 | cirrhosis of liver |
| ADEMETIONINE | 4.0 | 4 | 4 | alcoholic liver cirrhosis; non-alcoholic fatty liver disease; primary biliary cirrhosis |
| CARVEDILOL | 4.0 | 4 | 4 | portal hypertension |

## Network
`network_nodes.csv` / `network_edges.csv` (Cytoscape-ready): top 30 candidates → their progression-gene targets (236 genes, 410 links). Gene attributes: class, direction, trajectory cluster, main Paper 1 pathway (Hallmark > Reactome > KEGG > GO, most significant), shortlist flag. Drug attribute: is_approved. Edge attribute: action direction.

(Network picture not drawn in this rerun.)

## Caveats
- Coverage counts known drug–target annotations, which favour well-studied drugs and genes.
- Most links have unknown push direction (Task 2). Whether a candidate's action opposes the fibrosis direction is checked in Task 7.
- "No fibrosis-type liver use in the graph" means none is recorded in OptimusKG, not necessarily none in practice.
- Candidates are **repurposing hypotheses**, not treatments.
