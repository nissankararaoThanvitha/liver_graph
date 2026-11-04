# Reference-file checksum manifest

The repository-root `source_checksums.txt` preserves the historical SHA-256 manifest supplied with the manuscript. It covers one HGNC complete-set file and 14 OptimusKG parquet files. The record states it was generated on 21 October 2026 after analysis; filesystem dates are not official release identifiers.

The raw inputs are not bundled with this manifest. Original input paths were unavailable during the 4 November packaging check, so that check validated the record format rather than freshly recomputing the original-file hashes. Do not substitute the separate six-column HGNC dictionary or later OptimusKG downloads simply because their filenames match.

This manifest does not cover later MSigDB/CTD/ChEMBL additions; their provenance and checksums require separate documentation. The same 15 checksums are reproduced under Supplementary Methods.
