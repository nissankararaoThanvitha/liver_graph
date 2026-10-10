# Current data dictionary

value_z is within-study/gene standardised expression after the deposited-value log transformation. Stage means average independent patients under the shared biopsy rule; they are not fold changes.

- progression_genes/progression_fibrosis.csv:14,794 tested genes; progression_disease.csv:14,784. Fields median_rho,n_studies,n_agree,combined_p,q_value,min_rho,max_rho,symbol. Selection q<.05 plus all-direction agreement.
- diagnostic_both_q_significant.csv: diagnostic overlap with q on both and median-sign match, not selected shared/union.
- gene_tables stage/disease/age/sex summaries:6222 selected-union genes; staged patients610,demographic staged patients327. sample_demographics.csv has all1,085 raw sample records and biopsy_number; analyse after selection/aggregation.
- harmonisation: original metadata, additive clinical labels/diagnosis provenance, crosswalk, mapping summary/unmapped IDs, parse summary. Raw clinical fields preserved.
- graph_nodes/nodes_gene.csv:53,993 union genes; n_datasets records study coverage. category is a pilot annotation, not comprehensive biotype.
- graph_nodes/edges_my_progression.csv and knowledge_layer/edges_my_progression.csv: identical final8,044 links with Ensembl gene,disease ID,relationship,rho,q,study count,direction.
- gene_progression_scores.csv:6222 selected-union genes; fib_rho/fib_q and dis_rho/dis_q blank where not selected on that axis.
- knowledge layer: Gene-associated curated Disease,Drug,Pathway,BioProcess,Phenotype nodes/relations. ASSOCIATED_WITH scores≥.1; ACTS_ON mode-of-action annotations retained. No Pathway→BioProcess relationship.

All file counts/columns are recorded in the inventory and manifest; dataset sample counts are raw-resource counts, not every test's patient n.

