"""
build_primekg_layer.py
----------------------
Extracts the knowledge layer from PrimeKG and writes Neo4j-ready CSVs that
attach to the existing expression graph.

WHY
The expression graph holds measurements only: Patient -> Gene, 23.3M of them.
It contains no biology, so it can answer "which genes are high in cirrhosis"
but not "why is this patient progressing" or "what drug might stop it".
Those need chains that run through pathways, diseases and drugs:

    Patient -> Gene -> Pathway -> Drug
    Patient -> Gene -> Disease -> Drug

PrimeKG (Chandak, Huang & Zitnik, Scientific Data 2023) already assembles
that biology from 20 curated resources, including three of the four the
project asked for -- Reactome, DrugBank and CTD. KEGG is absent from PrimeKG
because bulk KEGG access requires a paid licence; Reactome covers much of the
same pathway biology and is open.

THE JOIN
PrimeKG identifies genes by NCBI/Entrez ID. map_gene_ids.py stored entrez_id
alongside ensembl_id for every gene back in step 3, so the two graphs join
directly on that column. 26,223 of our 53,993 genes are known to PrimeKG,
including 14,789 of the 14,794 genes found in all eight studies (100%).
The genes that do not join are overwhelmingly unnamed novel transcripts --
nothing in science describes them, so there is nothing to attach.

WHAT IS DELIBERATELY EXCLUDED
  anatomy_protein_present/absent (3.0M)  "protein X occurs in tissue Y".
                                         Mostly noise for this question.
  drug_drug (2.7M)                       drug-drug interaction safety data,
                                         not disease mechanism.
Both can be added later; they would triple the graph for little gain here.

PrimeKG stores every edge twice (once per direction). We keep one direction
and let Cypher traverse undirected where that is the right reading.

Output (data/graph_primekg_superseded/):
    nodes_disease.csv  nodes_drug.csv  nodes_pathway.csv
    nodes_bioprocess.csv  nodes_phenotype.csv
    edges_<relation>.csv  -- one file per relation type

Usage:
    python build_primekg_layer.py
"""

import csv
import os
from collections import defaultdict

import pandas as pd

PRIMEKG = "data/primekg/kg.csv"
GENES = "data/graph_all/nodes_gene.csv"
OUT = "data/graph_primekg_superseded"

# PrimeKG node type -> our label and output file
NODE_LABEL = {
    "disease": "Disease",
    "drug": "Drug",
    "pathway": "Pathway",
    "biological_process": "BioProcess",
    "effect/phenotype": "Phenotype",
}

# relation -> (our relationship type, left type, right type)
# Only relations that either touch a gene or connect two knowledge nodes.
RELATIONS = {
    "disease_protein":            ("ASSOCIATED_WITH",   "gene/protein", "disease"),
    "pathway_protein":            ("IN_PATHWAY",        "gene/protein", "pathway"),
    "drug_protein":               ("TARGETS",           "drug",         "gene/protein"),
    "protein_protein":            ("INTERACTS_WITH",    "gene/protein", "gene/protein"),
    "bioprocess_protein":         ("INVOLVED_IN",       "gene/protein", "biological_process"),
    "disease_disease":            ("RELATED_DISEASE",   "disease",      "disease"),
    "indication":                 ("TREATS",            "drug",         "disease"),
    "contraindication":           ("CONTRAINDICATED_IN", "drug",        "disease"),
    "off-label use":              ("OFF_LABEL_FOR",     "drug",         "disease"),
    "disease_phenotype_positive": ("HAS_PHENOTYPE",     "disease",      "effect/phenotype"),
    "pathway_pathway":            ("RELATED_PATHWAY",   "pathway",      "pathway"),
}


def main():
    os.makedirs(OUT, exist_ok=True)

    genes = pd.read_csv(GENES, dtype=str).fillna("")
    # entrez -> our canonical ensembl id, the key the graph already uses
    ent2ens = (genes[genes["entrez_id"] != ""]
               .drop_duplicates(subset="entrez_id")
               .set_index("entrez_id")["ensembl_id"].to_dict())
    print(f"our genes with an Entrez ID: {len(ent2ens):,}")

    nodes = {t: {} for t in NODE_LABEL}          # type -> {id: name}
    edges = defaultdict(list)                    # our_rel -> rows
    seen = defaultdict(set)                      # our_rel -> dedup keys
    kept_genes = set()

    with open(PRIMEKG, newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            spec = RELATIONS.get(row["relation"])
            if spec is None:
                continue
            our_rel, ltype, rtype = spec

            # PrimeKG writes each edge in both directions; orient it so the
            # left side is the type this relation expects.
            if row["x_type"] == ltype and row["y_type"] == rtype:
                lx, ly = "x", "y"
            elif row["y_type"] == ltype and row["x_type"] == rtype:
                lx, ly = "y", "x"
            else:
                continue

            lid, lname = row[lx + "_id"], row[lx + "_name"]
            rid, rname = row[ly + "_id"], row[ly + "_name"]

            # Map gene endpoints onto our Ensembl ids; drop edges whose gene
            # we never measured -- they have nothing to attach to.
            if ltype == "gene/protein":
                lid = ent2ens.get(lid)
                if lid is None:
                    continue
                kept_genes.add(lid)
            if rtype == "gene/protein":
                rid = ent2ens.get(rid)
                if rid is None:
                    continue
                kept_genes.add(rid)

            # protein_protein is symmetric: keep one copy per unordered pair.
            key = tuple(sorted((lid, rid))) if ltype == rtype else (lid, rid)
            if key in seen[our_rel]:
                continue
            seen[our_rel].add(key)

            if ltype in NODE_LABEL:
                nodes[ltype].setdefault(lid, lname)
            if rtype in NODE_LABEL:
                nodes[rtype].setdefault(rid, rname)

            edges[our_rel].append((lid, rid))

    # ---- write node files -------------------------------------------------
    print("\nNODES")
    for t, label in NODE_LABEL.items():
        d = nodes[t]
        fn = f"{OUT}/nodes_{label.lower()}.csv"
        pd.DataFrame({"node_id": list(d), "name": list(d.values())}).to_csv(
            fn, index=False)
        print(f"  {label:12s} {len(d):>7,}  -> {os.path.basename(fn)}")

    # ---- write edge files -------------------------------------------------
    print("\nEDGES")
    total = 0
    for our_rel, rows in sorted(edges.items(), key=lambda x: -len(x[1])):
        fn = f"{OUT}/edges_{our_rel.lower()}.csv"
        pd.DataFrame(rows, columns=["from_id", "to_id"]).to_csv(fn, index=False)
        print(f"  {our_rel:20s} {len(rows):>8,}  -> {os.path.basename(fn)}")
        total += len(rows)

    print(f"\ntotal edges     {total:,}")
    print(f"genes connected {len(kept_genes):,}")


if __name__ == "__main__":
    main()
