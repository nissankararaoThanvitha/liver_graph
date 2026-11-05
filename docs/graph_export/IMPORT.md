# Rebuild the graph in Neo4j from this export

Graph version 2026-11-05, exported from Neo4j 2026.10.1. The export leaves out the KEGG pathways (see DATA_TERMS.md), so it is not the complete graph. VERIFICATION.json gives the counts.

| | Live graph | This export |
|---|---|---|
| Nodes | 126,480 | 126,294 (186 KEGG Pathway nodes left out) |
| Relationships | 35,152,951 | 35,140,166 (12,724 KEGG `IN_PATHWAY` and 61 KEGG `IMPLICATED_IN` left out) |
| Entity types | 8 | 8 |
| Relationship types | 15 | 15 |

## Quickest route: the dump file

`liver_kg_2026-11-05.dump` (a separate release asset) is a Neo4j 5.26.0 database built from these CSV files, with the same content. It needs Neo4j 5.26 or newer. Rename it to the database name you want, put it in an empty folder, and load it:

```bash
mv liver_kg_2026-11-05.dump liverkg.dump
neo4j-admin database load liverkg --from-path=<that folder>
```

Then run `constraints.cypher` (step 3 below). The rest of this page covers the CSV route.

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

## 2. Import

Use neo4j-admin from Neo4j 5.x or later (Community or Enterprise). Unzip into an empty folder, open a terminal there, and import into a database that does not exist yet (here `liverkg`). Each file carries its own header, so each one is passed separately:

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

On Community edition, import into the default database `neo4j` (stop the server first, and add `--overwrite-destination` if it already exists). On Enterprise, start the server and run `CREATE DATABASE liverkg`.

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

With your own copy of the MSigDB 2024.1 file `c2.cp.kegg_legacy.v2024.1.Hs.symbols.gmt` in `data/genesets/` of the code repository, these commands rebuild the left-out parts. You also need the CTD download for the second one.

```bash
python scripts/add_msigdb_pathways.py --apply
python scripts/build_pathway_nafld_links.py --load
```

The first command loads KEGG and Hallmark; the Hallmark rows already exist, and it merges onto them. The second rebuilds all 89 `IMPLICATED_IN` links, including the 61 KEGG ones. Both read `NEO4J_PASSWORD` and connect to `bolt://localhost:7687` by default.

## Re-running the expression analyses

The release CSVs are import files, not the per-study analysis CSV format. See
[the repository rebuild guide](https://github.com/nissankararaoThanvitha/liver_graph/blob/main/docs/provenance/REBUILD.md)
for `scripts/prepare_analysis_core.py`, including the original annotation-layer recovery.
