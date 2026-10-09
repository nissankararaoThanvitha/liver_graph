"""
build_optimuskg_layer.py
------------------------
Builds the knowledge layer from OptimusKG and writes Neo4j-ready CSVs that
attach to the existing expression graph.

WHY OPTIMUSKG AND NOT PRIMEKG
PrimeKG's own project page states it has been superseded by OptimusKG. We
replaced it after checking the one thing that actually mattered:

  drugs recorded as treating liver disease
      PrimeKG    NASH 0    NAFLD 0    cirrhosis 0
      OptimusKG  NASH 74   NAFLD 95   cirrhosis 71

Link prediction learns from examples. With zero known drug-disease links for
liver disease there was nothing to learn from, and the whole step was blocked.
OptimusKG carries Resmetirom (first approved NASH drug, March 2024, after
PrimeKG was built) and Belapectin, which targets galectin-3 -- LGALS3, one of
the top genes our own progression analysis found independently.

Two further gains:
  * OptimusKG identifies genes by ENSEMBL ID, the same identifier this
    pipeline standardised on in step 3. The join is direct, with no Entrez
    translation: 50,725 of our 53,993 genes match (94%), against 26,223 (49%)
    for PrimeKG.
  * drug-gene edges carry the mode of action -- INHIBITOR, AGONIST, BLOCKER
    and 20 more -- where PrimeKG had a single untyped "acts on". For
    repurposing this matters: to stop a rising gene you need a drug that
    inhibits it, not one that activates it.

THE EVIDENCE THRESHOLD
OptimusKG ships 9,734,774 gene-disease links because it includes every Open
Targets association, however weak. Median score is 0.026 -- a score of 0.0015
means one paper mentioned the pair once. Taken whole, 5,568 genes "link" to
NAFLD, which is a third of the genome; a graph where everything connects to
everything cannot support prediction.

We keep score >= 0.1 and store the score on every edge, so queries can
tighten further without a reload. At that cut NAFLD keeps 274 genes and
cirrhosis 234 -- comparable to PrimeKG's 139 and 104, but each properly
evidenced, and PNPLA3 (1,900 studies), TM6SF2 and PPARG all survive.

DELIBERATELY EXCLUDED
  drug_drug            interaction safety, not disease mechanism
  anatomy_gene         "gene occurs in tissue", mostly noise here
  exposure_*           environmental toxins; CTD's exposure slice
Any of these can be added later.

Output (data/graph_okg/): node and edge CSVs, one file per type.

Usage:
    python build_optimuskg_layer.py
"""

import os

import pandas as pd

OKG = "data/optimuskg"
GENES = "data/graph_full/nodes_gene.csv"
OUT = "data/graph_okg"
MIN_SCORE = 0.1

# node parquet -> (label, output basename)
NODES = {
    "disease": "Disease",
    "drug": "Drug",
    "pathway": "Pathway",
    "biological_process": "BioProcess",
    "phenotype": "Phenotype",
}

# edge parquet -> (our relationship, left node type, right node type)
# 'gene' means the endpoint is one of our Gene nodes, keyed by ensembl_id.
EDGES = {
    "disease_gene":            ("ASSOCIATED_WITH", "gene", "disease"),
    "gene_gene":               ("INTERACTS_WITH", "gene", "gene"),
    "biological_process_gene": ("INVOLVED_IN", "gene", "biological_process"),
    "pathway_gene":            ("IN_PATHWAY", "gene", "pathway"),
    "disease_phenotype":       ("HAS_PHENOTYPE", "disease", "phenotype"),
    "disease_disease":         ("PARENT_OF", "disease", "disease"),
    "drug_gene":               ("ACTS_ON", "drug", "gene"),
    "drug_disease":            ("DRUG_DISEASE", "drug", "disease"),
}


def name_of(props):
    """OptimusKG stores the display name inside the properties struct."""
    if props is None:
        return ""
    return props.get("name") or props.get("symbol") or ""


def main():
    os.makedirs(OUT, exist_ok=True)

    genes = pd.read_csv(GENES, dtype=str).fillna("")
    mine = set(genes["ensembl_id"])
    print(f"our genes: {len(mine):,}")

    # ---- nodes ------------------------------------------------------------
    # Only keep knowledge nodes that an imported edge actually reaches; the
    # full disease list is 36,345 and most never touch our genes.
    kept_ids = {t: set() for t in NODES}
    edge_frames = {}

    print("\nEDGES")
    for fname, (rel, ltype, rtype) in EDGES.items():
        cols = ["from", "to", "relation", "properties"]
        e = pd.read_parquet(f"{OKG}/{fname}.parquet", columns=cols)

        if fname == "disease_gene":
            score = pd.to_numeric(
                e["properties"].apply(lambda p: p.get("evidence_score")),
                errors="coerce")
            before = len(e)
            e = e[score >= MIN_SCORE].copy()
            e["score"] = score[score >= MIN_SCORE].round(4)
            print(f"  {rel:16s} evidence filter >= {MIN_SCORE}: "
                  f"{before:,} -> {len(e):,}")
        else:
            e = e.copy()
            e["score"] = ""

        # OptimusKG does not guarantee which side is which, so orient by
        # checking membership rather than trusting column order.
        if ltype == "gene" and rtype != "gene":
            gene_on_left = e["from"].isin(mine)
            left = e["from"].where(gene_on_left, e["to"])
            right = e["to"].where(gene_on_left, e["from"])
        elif rtype == "gene" and ltype != "gene":
            gene_on_right = e["to"].isin(mine)
            right = e["to"].where(gene_on_right, e["from"])
            left = e["from"].where(gene_on_right, e["to"])
        else:
            left, right = e["from"], e["to"]

        out = pd.DataFrame({"from_id": left, "to_id": right,
                            "rel_type": e["relation"], "score": e["score"]})

        # keep only edges whose gene endpoints we actually measured
        if ltype == "gene":
            out = out[out["from_id"].isin(mine)]
        if rtype == "gene":
            out = out[out["to_id"].isin(mine)]
        if ltype == "gene" and rtype == "gene":
            # symmetric: one row per unordered pair
            pair = out.apply(lambda r: tuple(sorted((r.from_id, r.to_id))),
                             axis=1)
            out = out[~pair.duplicated()]

        out = out.drop_duplicates(subset=["from_id", "to_id", "rel_type"])

        if ltype in kept_ids:
            kept_ids[ltype].update(out["from_id"])
        if rtype in kept_ids:
            kept_ids[rtype].update(out["to_id"])

        edge_frames[fname] = (rel, out)
        print(f"  {rel:16s} {len(out):>9,}  ({fname})")

    # ---- write node files -------------------------------------------------
    print("\nNODES")
    for parq, label in NODES.items():
        n = pd.read_parquet(f"{OKG}/{parq}.parquet", columns=["id", "properties"])
        n = n[n["id"].isin(kept_ids[parq])]
        pd.DataFrame({"node_id": n["id"],
                      "name": n["properties"].apply(name_of)}).to_csv(
            f"{OUT}/nodes_{label.lower()}.csv", index=False)
        print(f"  {label:12s} {len(n):>7,}")

    # ---- write edge files -------------------------------------------------
    for fname, (rel, out) in edge_frames.items():
        out.to_csv(f"{OUT}/edges_{fname}.csv", index=False)

    total = sum(len(o) for _, o in edge_frames.values())
    print(f"\ntotal knowledge edges {total:,}")
    print(f"written to {OUT}/")


if __name__ == "__main__":
    main()
