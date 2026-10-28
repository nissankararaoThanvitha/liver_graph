# Paper 2 — Task 7 (revised): drug direction judged through pathways

**Gene set:** corrected Paper 1 union of 6,222 progression genes (earlier plans cite 4,692, the pre-correction count).
**Scope:** knowledge graph only (live Neo4j, read-only). Direction-consistency is a **repurposing hypothesis, not proof**.
Script: `code/task7_revised_pathway_direction.py`.

## Why revise
The first Task 7 could only judge a drug when its target was itself a progression gene. Many drugs act on genes that are not progression genes but sit in the same pathways. Here each pathway gets a fibrosis direction from its Paper 1 genes, and the drug's push on its target is compared with the direction of the target's pathways.

## 1. Pathway direction (Reactome)
A pathway is **rising** (or **falling**) when at least 3 of its Paper 1 fibrosis genes are present and at least two thirds of them rise (or fall) with fibrosis; otherwise **mixed**, or **too few genes**.

| pathway_direction | pathways |
|---|---|
| rising | 659 |
| falling | 205 |
| mixed | 225 |
| too few genes | 686 |

Largest rising pathways:
| pathway_name | n_rising | n_falling | share_rising |
|---|---|---|---|
| Neutrophil degranulation | 121 | 34 | 0.781 |
| RAC1 GTPase cycle | 45 | 14 | 0.763 |
| G alpha (i) signalling events | 48 | 7 | 0.873 |
| CDC42 GTPase cycle | 36 | 17 | 0.679 |
| Platelet degranulation  | 39 | 12 | 0.765 |
| Integrin cell surface interactions | 44 | 4 | 0.917 |
| Interleukin-4 and Interleukin-13 signaling | 42 | 5 | 0.894 |
| Immunoregulatory interactions between a Lymphoid and a non-Lymphoid cell | 38 | 4 | 0.905 |

Largest falling pathways:
| pathway_name | n_rising | n_falling | share_rising |
|---|---|---|---|
| Peroxisomal protein import | 1 | 28 | 0.034 |
| Regulation of Complement cascade | 3 | 19 | 0.136 |
| MLL4 and MLL3 complexes regulate expression of PPARG target genes in adipogenesis and hepatic steatosis | 5 | 12 | 0.294 |
| Aspirin ADME | 1 | 15 | 0.062 |
| Mitochondrial protein degradation | 0 | 15 | 0.0 |
| Intrinsic Pathway of Fibrin Clot Formation | 3 | 10 | 0.231 |
| Transcriptional activation of mitochondrial biogenesis | 4 | 8 | 0.333 |
| Heme signaling | 2 | 10 | 0.167 |

## 2. Drug → target → pathway routes
All 94,872 routes (every ACTS_ON link, target in any Reactome pathway):

| pathway_consistency | routes |
|---|---|
| direction-consistent | 4,995 |
| direction-inconsistent | 2,353 |
| ambiguous | 5,193 |
| unknown | 82,331 |

**3,039** decided routes come from targets that are **not** progression genes. These drugs could not be judged at all in the first Task 7.

## 3. Gene level vs pathway level, per drug
| Drug set | gene-level call | call only through pathways | combined: consistent | combined: inconsistent |
|---|---|---|---|---|
| All drugs | 717 | 260 | 527 | 412 |
| Repurposing candidates | 641 | 101 | 397 | 317 |
| Main list | 641 | 0 | 332 | 282 |

Where both levels give a call, they **agree for 367 drugs and disagree for 192**. Combined call = gene level where it exists, otherwise the pathway majority.

### Repurposing candidates judged only through pathways, consistent (most pathways)
These candidates act on progression genes only through links of unknown direction, so the first Task 7 could not judge them. Their other targets have a known action, so they can be judged through pathways. The main list has none, because every main-list drug already has a gene-level call.
| drug_name | pathway_level_consistent | pathway_level_inconsistent | consistent_pathways |
|---|---|---|---|
| VX-702 | 12 | 1 | ADP signalling through P2Y purinoceptor 1; CD163 mediating an anti-inflammatory response; ERK/MAPK targets; NOD1/2 Signaling Pathway; Neutrophil degranulation |
| PONATINIB | 12 | 3 | CDC42 GTPase cycle; Cyclin D associated events in G1; FCGR3A-mediated phagocytosis; Factors involved in megakaryocyte development and platelet production; RAC1 GTPase cycle |
| TALMAPIMOD | 12 | 1 | ADP signalling through P2Y purinoceptor 1; CD163 mediating an anti-inflammatory response; ERK/MAPK targets; NOD1/2 Signaling Pathway; Neutrophil degranulation |
| DABRAFENIB | 9 | 0 | MAP2K and MAPK activation; Negative regulation of MAPK pathway; Paradoxical activation of RAF signaling by kinase inactive BRAF; RAF activation; Signaling by RAF1 mutants |
| ENCORAFENIB | 9 | 0 | MAP2K and MAPK activation; Negative regulation of MAPK pathway; Paradoxical activation of RAF signaling by kinase inactive BRAF; RAF activation; Signaling by RAF1 mutants |
| BINIMETINIB | 8 | 0 | MAP2K and MAPK activation; Paradoxical activation of RAF signaling by kinase inactive BRAF; RAF activation; Signal transduction by L1; Signaling by RAF1 mutants |
| NILOTINIB | 7 | 3 | Cyclin D associated events in G1; FCGR3A-mediated phagocytosis; Factors involved in megakaryocyte development and platelet production; RHO GTPases Activate WASPs and WAVEs; Regulation of actin dynamics for phagocytic cup formation |
| GILTERITINIB | 7 | 1 | Constitutive Signaling by Aberrant PI3K in Cancer; Negative regulation of FLT3; PI5P, PP2A and IER3 Regulate PI3K/AKT Signaling; PIP3 activates AKT signaling; RAF/MAP kinase cascade |
| TANDUTINIB | 6 | 1 | Constitutive Signaling by Aberrant PI3K in Cancer; Negative regulation of FLT3; PI5P, PP2A and IER3 Regulate PI3K/AKT Signaling; PIP3 activates AKT signaling; RAF/MAP kinase cascade |
| CHENODIOL | 5 | 0 | Endogenous sterols; Recycling of bile acids and salts; SUMOylation of intracellular receptors; Synthesis of bile acids and bile salts via 27-hydroxycholesterol; Synthesis of bile acids and bile salts via 7alpha-hydroxycholesterol |
| TELMISARTAN | 4 | 0 | Cargo recognition for clathrin-mediated endocytosis; Clathrin-mediated endocytosis; G alpha (q) signalling events; Peptide ligand-binding receptors |
| IRBESARTAN | 4 | 0 | Cargo recognition for clathrin-mediated endocytosis; Clathrin-mediated endocytosis; G alpha (q) signalling events; Peptide ligand-binding receptors |

## Files
`pathway_direction.csv`, `drug_target_pathway_direction.csv` (every route), `drug_direction_gene_vs_pathway.csv` (per drug).

## Caveats
- A pathway's direction is a vote of its measured genes. Pathways contain activators and inhibitors, so a pathway vote is a simplification.
- The action labels still decide everything: TARGET / ENZYME / TRANSPORTER / CARRIER links stay unknown at both levels.
