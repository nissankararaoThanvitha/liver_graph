"""
paper2_manifest.py
------------------
Regenerate Paper2_Results/00_FILE_MANIFEST.csv.

Mirrors Paper 1's 00_START_HERE/06_FILE_MANIFEST.csv: path, bytes, sha256 for
every file under the results tree, so a reviewer can tell whether the copy they
are holding is the one the numbers were computed from.

Run after each task.

Usage:
    python scripts/paper2_manifest.py
"""

import csv
import hashlib
import os

ROOT = "Paper2_Results"
OUT = f"{ROOT}/00_FILE_MANIFEST.csv"


# Regenerable intermediates, deliberately not shipped. Each is large and
# every number taken from it is delivered in a smaller table beside it:
#   task5_mp7_pairs.csv  ->  task5_mp7_reach_per_drug.csv, which is what
#                            the convergence permutation actually runs on
INTERMEDIATE = {"Task5/task5_mp7_pairs.csv"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rows = []
    for dirpath, _, filenames in os.walk(ROOT):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            if rel == os.path.basename(OUT):
                continue          # never hash the manifest into itself
            if rel in INTERMEDIATE:
                continue          # large, regenerable, nothing downstream reads it
            rows.append({"path": rel,
                         "bytes": os.path.getsize(full),
                         "sha256": sha256(full)})

    rows.sort(key=lambda r: r["path"])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256"])
        w.writeheader()
        w.writerows(rows)

    total = sum(r["bytes"] for r in rows)
    print(f"wrote {OUT}")
    print(f"{len(rows)} files, {total:,} bytes")
    for r in rows:
        print(f"  {r['bytes']:>9,}  {r['path']}")


if __name__ == "__main__":
    main()
