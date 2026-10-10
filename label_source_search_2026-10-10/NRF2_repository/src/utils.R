
#' Tidy a matrix
#'
#' This utility function takes a matrix and converts it to a tidy format and
#' adds if available observations' meta data.
#'
#' @param mat A matrix with observations/features in rows and variables in
#' columns
#' @param feature Class name of observations/features, e.g.
#' transcription_factors
#' @param key Class name of variables, e.g. samples
#' @param value Class name of matrix values, e.g. activities
#' @param meta Data frame with meta data of the observations. To map the meta
#' data to the tidied table the observation/feature column name must be
#' identical.
#'
#' @return Tidy table.
#'
#' @export
tdy = function(mat, feature, key, value, meta = NULL) {
  res = mat %>%
    data.frame(check.names = F, stringsAsFactors = F) %>%
    rownames_to_column(feature) %>%
    as_tibble() %>%
    gather({{key}}, {{value}}, -{{feature}})
  
  if (!is.null(meta)) {
    res = res %>%
      left_join(meta, by=key)
  }
  
  return(res)
}

#' This function translates genes across different gene id classes from mouse 
#'   and human
#'
#' @param x Data frame that must store at least a column containing genes.
#' @param from string indicating the present gene id class. Must match to a 
#'   column in the annotation data frame (e.g. 
#'   \code{symbol_mgi, ensembl_mgi, entrez_hgnc, ...})
#' @param to string indicating the desired gene id class. Similar to 
#'   \code{from} parameter.
#'   
#' @param ref string indicating the column name of the genes. Mostly \code{gene}
#' @param na_rm gene id mapping can lead to NAs. This logical argument indicates
#'   whether rows with NA should be removed.
#'   
#' @return The input is returned with translated gene ids.
translate_gene_ids = function(x, from, to, ref = "gene", na_rm = F) {
  
  anno = readRDS(here("data/annotation/gene_id_annotation.rds"))
  
  if (!all(c(from, to) %in% colnames(anno))) {
    stop("'from' and 'to' must be one of: ", 
         str_c(colnames(anno), collapse = ", "))
  }
  
  annotation_df = anno %>%
    select({{from}}, {{to}}) %>%
    drop_na()
  
  mapped_x = x %>%
    rename({{from}} := {{ref}}) %>%
    left_join(annotation_df, by=from) %>%
    select({{ref}} := {{to}}, everything(), -{{from}})
  
  if (na_rm == T) {
    res = mapped_x %>%
      drop_na({{ref}})
  } else {
    res = mapped_x
  }
  return(res)
}

#' Wrapper for voom normalization 
#' 
#' @param count_matrix count matrix with genes in rows and samples in columns
#' 
#' @return normalized count matrix -> expression matrix
voom_normalization = function(count_matrix) {
  
  # filter low read counts, TMM normalization and logCPM transformation
  keep = filterByExpr(count_matrix)
  
  norm = count_matrix[keep,,keep.lib.sizes=F] %>%
    calcNormFactors() %>%
    voom() %>%
    pluck("E")
  
  message("Discarding ", sum(!keep), " genes \nKeeping ", sum(keep), " genes")
  
  return(norm)
}