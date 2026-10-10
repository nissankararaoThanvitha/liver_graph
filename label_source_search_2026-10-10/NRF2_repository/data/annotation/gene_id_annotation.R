library(biomaRt)
library(tidyverse)

# download gene annotations across the species homo sapiens and mus musculus for
# various gene identifiers (e.g. symbol, ensembl, ...)

# listEnsemblArchives()
# used version/host = "http://jan2020.archive.ensembl.org" 

mouse_ensembl = useMart("ensembl",dataset="mmusculus_gene_ensembl")
human_ensembl = useMart("ensembl", dataset = "hsapiens_gene_ensembl")

common_attributes = c("ensembl_gene_id", "ensembl_gene_id_version", 
                      "entrezgene_id")
biomart_output = getLDS(
  attributes = c("mgi_symbol", common_attributes), mart = mouse_ensembl,
  attributesL = c("hgnc_symbol", common_attributes), 
  martL = human_ensembl)

tidy_biomart_output = biomart_output %>%
  as_tibble() %>%
  rename(symbol_mgi = MGI.symbol, 
         ensembl_mgi = Gene.stable.ID,
         ensembl_v_mgi = Gene.stable.ID.version,
         entrez_mgi = NCBI.gene.ID,
         symbol_hgnc = HGNC.symbol, 
         ensembl_hgnc = Gene.stable.ID.1,
         ensembl_v_hgnc = Gene.stable.ID.version.1,
         entrez_hgnc = NCBI.gene.ID.1) %>%
  mutate_if(is.integer, as.character) %>%
  na_if("")

saveRDS(tidy_biomart_output,
        "data/annotation/gene_id/gene_id_annotation.rds")
