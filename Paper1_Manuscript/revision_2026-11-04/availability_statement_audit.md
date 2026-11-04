# Availability statement audit

Scope: new Overleaf project 6aeadb061fca29e951a67537, read-only review. No manuscript changes.

- Confirmed: Overleaf statement lists the eight study accessions and repository URL.
- Confirmed online: repository is public; code and result-package directories are visible.
- Confirmed online: DOI 10.7910/DVN/IYNGEV identifies OptimusKG. This does not establish which version was originally downloaded.
- Missing: the Zenodo DOI remains a placeholder, so the archive claim is unsupported.
- Overstated: availability of graph exports is not established. Local repository .gitignore excludes data/graph_full, data/graph_okg, data/graph_all and the analysis core; the local origin/main tree does not track those bulk outputs. Scripts and rebuild instructions are distinct from a downloadable final graph. Current public API enumeration failed with HTTP 403, so no claim of a full remote audit is made.
- Incomplete provenance: the statement omits MSigDB 2024.1 (KEGG legacy/Hallmark) and CTD inputs added in the Methods. Original licensing and acquisition sources should be identified without implying unrestricted redistribution.
- Missing precision: no immutable commit/tag or final graph export location is identified. Updated integration code was previously reported on paper2-results; the release should document the exact code used.

Local origin/main snapshot: 565863549d7f2cde147d022b51f0dc65495b4ea3
Accessions in manuscript: GSE126848, GSE130970, GSE135251, GSE162694, GSE167523, GSE193066, GSE240729, GSE269412
