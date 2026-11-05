# Data sources, terms and what is left out

This export is built from public resources, and each part stays under its source's terms. The largest part comes from OptimusKG, which is licensed CC BY-NC-SA 4.0. Use the export as a whole for non-commercial purposes only, credit the sources below, and share any derived data under the same terms. The licence in the code repository (MIT) covers code only, not this data.

These are the terms the source pages showed when checked on 4 Nov 2026. This is not legal advice. Before reusing a part, check its source's current terms, especially for the sources marked "not confirmed".

## Left out: KEGG

KEGG is not an openly licensed database, and its terms say non-academic use needs a commercial licence. The MSigDB terms for the KEGG legacy sets defer to KEGG's own policies. The export therefore leaves out:

| File (not included) | Rows |
|---|---|
| `nodes/Pathway__KEGG_legacy.csv.gz`: KEGG legacy pathways from MSigDB 2024.1 | 186 |
| `relationships/IN_PATHWAY__Gene__Pathway__KEGG_legacy.csv.gz`: their gene memberships | 12,724 |
| `relationships/IMPLICATED_IN__Pathway__Disease__KEGG.csv.gz`: Pathway -> NAFLD links whose pathway is KEGG | 61 |

That leaves 126,294 of 126,480 nodes and 35,140,166 of 35,152,951 relationships. IMPORT.md explains how to add them back from your own MSigDB download.

## Included parts and their sources

| Part of the export | Source | Terms (as checked) |
|---|---|---|
| Disease, Phenotype, BioProcess, Reactome Pathway nodes; Drug nodes `__OptimusKG`; `ASSOCIATED_WITH`, `INTERACTS_WITH`, `INVOLVED_IN`, `HAS_PHENOTYPE`, `PARENT_OF`, Reactome `IN_PATHWAY`; `ACTS_ON __OptimusKG`; `TREATS __OptimusKG`, `CONTRAINDICATED_IN`, `OFF_LABEL_FOR` | OptimusKG v3 (Harvard Dataverse, doi:10.7910/DVN/IYNGEV) | CC BY-NC-SA 4.0. OptimusKG states that each of its upstream resources keeps its own terms. |
| within those: `ACTS_ON __OptimusKG` (all 20,674 cite DrugBank) | DrugBank, via OptimusKG | DrugBank data: CC BY-NC 4.0. Its academic licence is limited to non-commercial academic work. |
| within those: gene–disease scores, indications | Open Targets Platform; DrugCentral, via OptimusKG | Open Targets: CC0. DrugCentral: not confirmed. |
| within those: phenotypes, GO processes, Reactome pathways | HPO, Gene Ontology, Reactome, via OptimusKG | HPO: not confirmed (listed as CC0 by Open Targets). Reactome: CC BY 4.0. |
| Hallmark Pathway nodes and `IN_PATHWAY __Hallmark` | MSigDB 2024.1 Hallmark | CC BY 4.0 (MSigDB terms) |
| `IMPLICATED_IN __Reactome` | This project's enrichment results, checked against CTD | CTD: not confirmed; cite CTD. |
| Sample, Dataset nodes; `EXPRESSES`, `IN_DATASET` | Eight NCBI GEO studies (GSE126848, GSE130970, GSE135251, GSE162694, GSE167523, GSE193066, GSE240729, GSE269412), processed by this project | GEO submitter data: not confirmed. Samples carry derived clinical labels only, no direct identifiers. |
| Gene nodes; `TRACKS_FIBROSIS`, `TRACKS_INFLAMMATION` | This project (gene IDs from HGNC/Ensembl) | Project results. HGNC: CC0. |

"Not confirmed" means the source's terms page could not be read when checked. These parts are included on the understanding that the sources are public research resources. Whoever publishes or reuses the export should confirm them.
