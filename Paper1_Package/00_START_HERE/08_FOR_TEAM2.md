# 8. For Team 2 — the drug-repurposing handover

Paper 1 hands Team 2 a gene list. This file is everything else they need: what
the gene list actually is, how the knowledge graph is built, and the six traps
in it that will otherwise produce confident, publishable-looking garbage.

Every number here was measured against the loaded Neo4j graph and the committed
Paper 1 outputs. None is an estimate. Section 9 says how to re-check each one.

---

## 1. What Paper 1 hands over

| File | Rows | What it carries |
|---|---|---|
| `Paper1_HighConfidence/00_all_4692_progression_genes.csv` | 4,692 | `ladder` (the progression class), fibrosis and inflammation `rho`/`q`/`direction`/`n_studies`, F0–F4 stage means |
| `Paper1_HighConfidence/11_final_all_3645_genes.csv` | 3,645 | clusters, cluster patterns, largest transition + beta + q, GO/KEGG/Reactome/Hallmark, tier, LOSO stability |
| `Paper1_HighConfidence/11_FINAL_shortlist_25_genes.csv` | 25 | the high-confidence prioritisation layer |

**Paper 2 is not blocked on Paper 1.** All trajectory, transition and pathway
results exist and are committed. A master progression-gene table is a column
rename of the first file, not an analysis.

The three progression classes, which must not be collapsed into a single
"progression" category:

| class | genes |
|---|---|
| fibrosis-only | 1,953 |
| shared (both ladders) | 1,692 |
| inflammation-only | 1,047 |

---

## 2. The knowledge graph is deliberately untrimmed. Do not trim it.

Every gene carries all of its OptimusKG biology, including biology with nothing
to do with liver. This is a settled decision, not an oversight.

Trimming to liver-only diseases would delete the answer. Of the **2,889** drugs
that act on a progression gene, **164** already treat a liver disease; the other
**2,725** are the repurposing space, and they exist only because nothing was
trimmed. It is also how LGALS3 reached belapectin, and why TREM2 — known from
Alzheimer's microglia — is interesting at all.

The rule is therefore:

> **The graph stays wide. The queries stay narrow.**

Filtering happens at read time, per edge type, with tunable thresholds. Nothing
is deleted from the store. This matches how the gene-disease evidence cut was
already handled at build time: `build_optimuskg_layer.py` applies `score >= 0.1`
*and stores the score on every edge*, so a query can tighten further without a
reload.

Two consequences to accept. Pruning a node because it is highly connected is
pruning by degree, the exact bias the Paper 2 plan warns against in three
separate places. And these annotations are the same ones Paper 1's enrichment
ran against the **14,794-gene** eligible background, so deleting terms now would
silently invalidate committed work.

---

## 3. Filter per edge type — the five axes do not behave alike

Measured on the 4,692 progression genes:

| Edge | Edges | Median/gene | Max | Genes covered | Verdict |
|---|---|---|---|---|---|
| `ACTS_ON` drug->gene | 8,715 | — | — | 846 | usable; split by `action` (§4, §5) |
| `IN_PATHWAY` Reactome | 12,252 | 1 | 192 | 3,010 (64%) | **usable as-is — prefer this bridge** |
| `INVOLVED_IN` GO BP | 47,653 | 6 | 199 | 4,341 (93%) | **cap term size or it is useless** |
| `ASSOCIATED_WITH` gene->disease | 540,911 | 78 | 1,141 | — | exclude hub terms, raise `score` |
| `INTERACTS_WITH` gene-gene | — | 18 | 5,189 | 4,531 | cap degree if used at all |

299 progression genes have neither a pathway nor a biological process.

### Reactome is the clean axis

Its top terms on our genes are specific and on-topic: Neutrophil degranulation
(190 genes), RAC1/RHOA/CDC42 GTPase cycles (68/60/60), Integrin cell surface
interactions (54), Interleukin-4 and Interleukin-13 signalling (53). That is
fibrosis and inflammation biology.

### GO biological process is not

Its top terms are housekeeping: `signal transduction` (539 genes),
`lipid metabolic process` (293), and five near-duplicate transcription-regulation
terms (304 + 294 + 274 + 256 + 208) that count largely the same genes over and
over.

### Why this matters more than the disease breadth

A metapath of the form `Drug -> Gene -> <bridge> <- Progression Gene` is a join,
so a hub bridge multiplies. Pairs manufactured by a **single** bridge node:

| Bridge | Progression genes | Drugs | Pairs |
|---|---|---|---|
| GO: signal transduction | 539 | 1,683 | **907,137** |
| GO: lipid metabolic process | 293 | 1,702 | 498,686 |
| GO: positive regulation of transcription by RNA Pol II | 304 | 962 | 292,448 |
| Reactome: Neutrophil degranulation | 190 | 617 | 117,230 |
| Reactome: Platelet degranulation | 68 | 499 | 33,932 |
| Reactome: RAC1 GTPase cycle | 68 | 34 | 2,312 |

The six largest GO terms alone manufacture over 2.1 million drug-gene pairs.
Reactome's worst case is one eighth of GO's and decays fast — by fourth place it
is down to 2,312. Treating `Drug -> Gene -> Pathway` and
`Drug -> Gene -> Biological Process` as interchangeable is a mistake.

**Do:** cap GO term size to the usual enrichment convention (5–200, or 10–500
genes) and collapse the redundant transcription family by parent-child
reduction. Use Reactome as the primary bridge.

### The disease axis

Hub "diseases" are generic EFO upper-level terms, not diseases:
`measurement` (reached by 4,422 of the 4,692 genes), `cancer or benign tumor`
(3,574), `neoplasm` (3,549), `nervous system disease` (3,533),
`protein measurement` (3,445).

Consequence: an unfiltered `Drug -> Gene -> Disease <- Drug` walk from just
**500** progression genes reaches **8,394 of the 12,025** drugs in the graph.
That is 70% of the drug vocabulary — a dictionary, not a shortlist.

`PARENT_OF` (28,919 edges) is the disease ontology, and is the correct way to
roll specific liver diagnoses up to `liver disease` instead of hand-listing EFO
IDs. It appears in no metapath so far and is a free improvement.

Liver disease anchors, with gene and drug counts:

| EFO / MONDO | Disease | Genes | Drugs |
|---|---|---|---|
| `EFO_0003095` | non-alcoholic fatty liver disease | 274 | 95 |
| `EFO_1001249` | non-alcoholic steatohepatitis | 66 | 74 |
| `EFO_0001422` | cirrhosis of liver | 234 | 71 |
| `EFO_0006890` | fibrosis | 472 | 17 |
| `EFO_0008573` | alcoholic liver disease | 42 | 5 |
| `EFO_0001421` | liver disease (parent term) | 3,722 | 251 |

---

## 4. Half of the drug-gene edges are pharmacokinetic, not therapeutic

`ENZYME` + `TRANSPORTER` + `CARRIER` account for **4,444 of the 8,715 (51%)**
drug-gene edges on progression genes. These mean the gene product *metabolises
or transports the drug* — not that the drug targets it.

Because this is a liver study, that is a systematic bias and not noise. Liver is
where the cytochromes live, their expression genuinely changes as the liver
fails, so they legitimately appear among progression genes while telling you
nothing therapeutic. Drugs reached per gene through a pharmacokinetic role alone:

`CYP3A4` **893** · `ALB` 361 · `CYP1A2` 291 · `CYP2C19` 281 · `CYP3A5` 271 ·
`CYP2C8` 257 · `ABCG2` 183 · `SLCO1B1` 153 · `CYP2E1` 133 · `SLCO1B3` 102

**Do:** classify `ACTS_ON.action` into therapeutic (`TARGET` plus the directional
actions in §5) versus pharmacokinetic (`ENZYME`, `TRANSPORTER`, `CARRIER`,
`SUBSTRATE`) during extraction; run every downstream analysis on the therapeutic
subset; report the pharmacokinetic subset separately. A druggability percentage
or a drug-coverage ranking computed over both is measuring liver drug
metabolism, not therapeutic opportunity.

---

## 5. Mode of action exists on about a tenth of the edges

`ACTS_ON` does carry an `action` property, so direction-aware analysis is
possible. It is just far smaller than it looks. On progression genes:

| Group | Edges |
|---|---|
| decreasing: `INHIBITOR` 408, `ANTAGONIST` 151, `BLOCKER` 58, `ALLOSTERIC_ANTAGONIST` 2, `NEGATIVE_ALLOSTERIC_MODULATOR` 2, `INVERSE_AGONIST` 2, `NEGATIVE_MODULATOR` 1, `DEGRADER` 1 | 625 |
| increasing: `AGONIST` 171, `POSITIVE_ALLOSTERIC_MODULATOR` 68, `STABILISER` 14, `POSITIVE_MODULATOR` 12, `PARTIAL_AGONIST` 5, `RELEASING_AGENT` 4, `ACTIVATOR` 3, `OPENER` 1 | 278 |
| **directional total** | **903 (10.4%)** |
| non-directional: `TARGET` 3,356, `ENZYME` 2,845, `TRANSPORTER` 1,132, `CARRIER` 467, `MODULATOR` 7, `SUBSTRATE` 3, `BINDING_AGENT` 2 | 7,812 |

Any reversal-consistency analysis — drug action against the Paper 1 progression
direction — is computable for a few hundred drug-gene pairs, not thousands. It is
still worth doing. It is not a basis for a ranked candidate list on its own, and
the "unknown" bucket must be reported as the majority it is.

---

## 6. The drug vocabulary contains things that are not therapeutics

Top drugs by raw progression-gene coverage, as the graph returns them today:

| Drug | Genes | of which pharmacokinetic |
|---|---|---|
| FOSTAMATINIB | 104 | 2 |
| ZINC CHLORIDE | 44 | 9 |
| CHEMBL1201279 | 43 | 0 |
| ZINC ACETATE ANHYDROUS | 43 | 1 |
| CANNABIDIOL | 26 | 7 |
| NABIXIMOLS | 25 | 6 |
| CALCIUM PHOSPHATE, TRIBASIC | 22 | 9 |
| GLUTAMIC ACID | 22 | 2 |
| TAMOXIFEN | 20 | 14 |
| CALCIUM CITRATE | 20 | 7 |
| ALCOHOL | 19 | 12 |
| AMITRIPTYLINE | 18 | 7 |

One promiscuous kinase inhibitor, a run of mineral salts, and ethanol. In a
liver-disease paper, `ALCOHOL` on a candidate list is not a cosmetic problem.

A specificity measure of the form *progression targets / all known targets* does
not fix this — it makes it worse, because a mineral salt has few annotated
targets and therefore scores *high*. **Do:** filter on molecule type and clinical
phase, and exclude elements, salts, excipients and nutrients, before any coverage
ranking is computed.

---

## 7. Two results are already known, so do not build a narrative on them

**Druggability does not differ across the progression classes.** Computed now:

| Class | Genes | Drug-connected | % | Directional only |
|---|---|---|---|---|
| fibrosis-only | 1,953 | 360 | 18.4% | 3.5% |
| shared | 1,692 | 314 | 18.6% | 3.8% |
| inflammation-only | 1,047 | 172 | 16.4% | 3.6% |

A two-point spread at these n will not survive any test, least of all a
degree-aware null. Report it honestly as a null result; do not let the paper's
structure depend on a difference appearing.

**The 1,047 inflammation-only genes have no trajectory, pathway or tier
evidence.** Paper 1's cluster, transition, enrichment and tier work covers the
3,645 fibrosis-associated genes, and 4,692 − 3,645 = 1,047 is exactly the
inflammation-only set. F0–F4 stage means do exist for all 4,692.

So any composite target score with a trajectory or pathway component ranks those
1,047 genes last for **missing data, not biology** — while the analysis plan
simultaneously requires the three classes be preserved as distinct. This needs an
explicit rule before any score is computed: normalise within class, or score the
classes separately. It cannot be left to a generic missing-value policy.

---

## 8. Two things named in the Paper 2 plan do not exist here

- **CausalKG.** There is no CausalKG in this project. The knowledge layer is
  OptimusKG (`data/graph_okg`). PrimeKG is superseded and retained only as
  `data/graph_primekg_superseded` for the comparison that justified the switch;
  it records 0 drugs treating NASH, NAFLD or cirrhosis.
- **A transcriptomic drug-reversal resource** (LINCS / CMap or equivalent). Not
  in the graph and not held by this project. It is an external dependency needing
  sourcing and licensing, and it sits on the critical path to the stated final
  evidence chain. Raise it now, not at the end.

One further constraint carries over: the mentor's instruction of 2026-09-07 is
**no pathway information** in deliverables, reflected in `export_for_mentor.py`.
Pathways are fine inside Paper 2's own analysis; they must not re-enter anything
shared back through that channel.

---

## 9. How to re-check every number here

Drug nodes carry `node_id` (ChEMBL) and `name`; `ACTS_ON` carries `action`; Gene
nodes carry `ensembl_id`, `symbol`, `entrez_id`, `n_datasets`. Progression genes
are those with a `TRACKS_FIBROSIS` or `TRACKS_INFLAMMATION` edge (6,384 edges
over 4,692 genes) — patient-derived, and this project's own contribution to the
graph.

```cypher
// the progression gene set, and its three classes
MATCH (g:Gene) WHERE (g)-[:TRACKS_FIBROSIS]->() OR (g)-[:TRACKS_INFLAMMATION]->()
WITH g, exists((g)-[:TRACKS_FIBROSIS]->())     AS isFib,
        exists((g)-[:TRACKS_INFLAMMATION]->()) AS isInf
RETURN CASE WHEN isFib AND isInf THEN 'shared'
            WHEN isFib THEN 'fibrosis-only'
            ELSE 'inflammation-only' END AS class, count(g) AS genes;

// sections 4 and 5: the action breakdown that splits therapeutic from PK
MATCH (g:Gene)-[:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->() WITH DISTINCT g
MATCH (dr:Drug)-[a:ACTS_ON]->(g)
RETURN a.action AS action, count(*) AS edges,
       count(DISTINCT dr) AS drugs, count(DISTINCT g) AS genes
ORDER BY edges DESC;

// section 3: how many pairs one bridge node manufactures
MATCH (g:Gene)-[:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->() WITH DISTINCT g
MATCH (g)-[:INVOLVED_IN]->(b:BioProcess)
WITH b, count(DISTINCT g) AS prog_genes ORDER BY prog_genes DESC LIMIT 6
MATCH (dr:Drug)-[:ACTS_ON]->(:Gene)-[:INVOLVED_IN]->(b)
RETURN b.name AS bridge, prog_genes, count(DISTINCT dr) AS drugs,
       prog_genes * count(DISTINCT dr) AS pairs
ORDER BY pairs DESC;
```

The server runs a 1 GB heap and a 512 MB page cache against a 2.5 GB store.
Counting all relationships by type in one query times out; count per type
instead, which hits the count store and returns instantly.

---

## 10. Summary — the six things to carry away

1. Do not trim the graph. Filter in the query, per edge type.
2. Walk `ACTS_ON` directly. Do not reach drugs through disease.
3. Split therapeutic from pharmacokinetic actions before anything is counted.
4. Prefer Reactome over GO biological process as a bridge; cap GO term size.
5. Filter non-therapeutic entities out of the drug vocabulary first.
6. Rank on Paper 1's own evidence — `rho`, `q`, `n_studies`, tier — never on
   degree or raw path counts. Link prediction in this project failed its own
   validation once already, and degree-based ranking is the likeliest reason.
