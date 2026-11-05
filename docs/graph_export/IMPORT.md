# Rebuild the graph in Neo4j from this export

Graph version 2026-11-05, exported from Neo4j 2026.10.1. The export leaves out the KEGG pathways (see DATA_TERMS.md), so it is not the complete graph. VERIFICATION.json gives the counts.

| | Live graph | This export |
|---|---|---|
| Nodes | 126,480 | 126,294 (186 KEGG Pathway nodes left out) |
| Relationships | 35,152,951 | 35,140,166 (12,724 KEGG `IN_PATHWAY` and 61 KEGG `IMPLICATED_IN` left out) |
| Entity types | 8 | 8 |
| Relationship types | 15 | 15 |

This repository copy clarifies the original release instructions. The published ZIP, dump and checksums are unchanged.

## Quickest route: the dump file

`liver_kg_2026-11-05.dump` (a separate release asset) is a Neo4j 5.26.0 database built from these CSV files, with the same content. It needs Neo4j 5.26 or newer. Copy it under the database name you want in an empty working folder, and load it:

```bash
cp liver_kg_2026-11-05.dump liverkg.dump
neo4j-admin database load liverkg --from-path=<that folder>
```

Stop the target instance before loading, use a new database in a separate instance, and retain the original downloaded dump. On Community edition use the default database name `neo4j` instead of `liverkg`. On Enterprise register the loaded database with `CREATE DATABASE liverkg` after starting the server. Then run `constraints.cypher` (step 3 below). The rest of this page covers the CSV route.

## Files

- `nodes/<Label>[__<source>].csv.gz`: one row per node, all properties. The first column is the node's ID (`node_id`; for Gene `ensembl_id`, for Sample `sample_id`, for Dataset `dataset_id`).
- `relationships/<TYPE>__<Start>__<End>[__<source>].csv.gz`: one row per relationship, all properties.
- Headers follow the neo4j-admin import format, for example `max_phase:double`, `unified_sources:string[]`, `:START_ID(Drug)`.
- Strings are always quoted. `""` is an empty string; an empty unquoted field means the property is absent. List values are separated by `;`.
- MANIFEST.csv lists every file with its row count and SHA-256 checksum.

## 1. Check the download

```bash
sha256sum -c SHA256SUMS.txt
```

This checks every asset listed in `SHA256SUMS.txt`; download all listed assets first, or check only the entry for the particular ZIP/dump you downloaded.

## 2. Import

Use neo4j-admin from Neo4j 5.26 or newer (Community or Enterprise). Unzip into an empty folder, open a terminal there, and import into a database that does not exist yet (here `liverkg`). Each file carries its own header, so each one is passed separately:

```bash
args=()
for f in nodes/*.csv.gz;         do args+=("--nodes=$f"); done
for f in relationships/*.csv.gz; do args+=("--relationships=$f"); done
HEAP_SIZE=2G neo4j-admin database import full liverkg \
  --id-type=string --array-delimiter=";" --multiline-fields=true \
  --ignore-empty-strings=false --bad-tolerance=0 --max-off-heap-memory=1G \
  "${args[@]}"
```

PowerShell:

```powershell
$a = @(Get-ChildItem nodes\*.csv.gz | ForEach-Object { "--nodes=$($_.FullName)" }) +
     @(Get-ChildItem relationships\*.csv.gz | ForEach-Object { "--relationships=$($_.FullName)" })
$env:HEAP_SIZE = "2G"
neo4j-admin database import full liverkg --id-type=string --array-delimiter=";" --multiline-fields=true --ignore-empty-strings=false --bad-tolerance=0 --max-off-heap-memory=1G @a
```

Stop the separate target server before import. On Community edition, replace `liverkg` with the default database name `neo4j`. Use an empty database; do not add an overwrite flag to an instance holding work you need to keep. On Enterprise, start the server after import and run `CREATE DATABASE liverkg`.

## 3. Constraints and indexes

Run `constraints.cypher` in the new database, for example with `cypher-shell -d liverkg -f constraints.cypher`. It creates the eight uniqueness constraints and the Gene symbol index of the original graph.

## 4. Check the counts

```cypher
MATCH (n) RETURN count(n);                     // 126,294
MATCH ()-[r]->() RETURN count(r);              // 35,140,166
CALL db.labels() YIELD label RETURN count(*);  // 8
CALL db.relationshipTypes() YIELD relationshipType RETURN count(*);  // 15
```

Per-file counts are in MANIFEST.csv.

## Adding the KEGG pathways back

These commands restore a **Paper 1 working copy only**. Run them from a checkout of the Paper 1 code repository, not from the extracted release folder. Before running either loader, prepare:

| Required input | Expected location in the Paper 1 checkout |
|---|---|
| Authorised MSigDB 2024.1 KEGG legacy GMT | `data/genesets/c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt` |
| MSigDB 2024.1 Hallmark GMT | `data/genesets/h.all.v2024.1.Hs.symbols.gmt` |
| CTD disease–pathway CSV gzip | `data/ctd/CTD_diseases_pathways.csv.gz` |
| Original OptimusKG pathway parquet | `data/optimuskg/pathway.parquet` |
| Original Reactome pathway-node CSV | `data/graph_okg/nodes_pathway.csv` |
| Retained Paper 1 enrichment results (committed) | `Paper1_Results/Task4/task4_all_significant.csv` |

Source links are in [the data-source guide](../provenance/DATA_SOURCES.md). The Reactome node CSV is produced by the original knowledge-layer builder, or recovered by `scripts/prepare_analysis_core.py --annotations-only` from the release ZIP. Recovery requires a new output directory; do not overwrite an existing `data/graph_okg` folder. The pathway–disease builder reads that exact default location.

Set `NEO4J_PASSWORD`, `NEO4J_URI` and `NEO4J_USERNAME` for the intended working instance. **These original loaders always use database `neo4j`; they do not read `NEO4J_DATABASE`.** Use a separate instance with that database name. With other writers stopped, run:

```bash
python scripts/add_msigdb_pathways.py --apply
python scripts/build_pathway_nafld_links.py --load
python scripts/verify_extended_graph_counts.py --live
```

The first command reads **two** GMT files (not the four used by expression enrichment). It loads KEGG and merges the Hallmark records already present, and writes local pathway CSVs required by the second command. The second rebuilds all 89 `IMPLICATED_IN` links, merging the 28 Reactome links already present and restoring the 61 KEGG links. The restored Paper 1 graph should contain 126,480 nodes and 35,152,951 relationships. KEGG inputs and generated KEGG CSVs remain outside version control.

**For Paper 2:** use [Paper 2’s self-contained rebuild guide](https://github.com/knarendrakumar187/Drug_Repurposing/blob/main/docs/REBUILD.md) instead. It restores only the omitted KEGG portion from a local KEGG GMT and CTD file, then adds the saved Paper 2 drug evidence in a separate database. Do not run Paper 2’s additions against the Paper 1 database.

## Re-running the expression analyses

The release CSVs are import files, not the per-study analysis CSV format. See
[the repository rebuild guide](https://github.com/nissankararaoThanvitha/liver_graph/blob/main/docs/provenance/REBUILD.md)
for `scripts/prepare_analysis_core.py`, including the original annotation-layer recovery.
