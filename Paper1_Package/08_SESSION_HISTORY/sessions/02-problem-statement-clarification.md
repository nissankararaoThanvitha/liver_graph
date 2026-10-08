# Problem statement clarification

*Claude Code session — last active 2026-10-02*


---

## once i want to rewind everything from start....once will u tell me the problem statement i

once i want to rewind everything from start....once will u tell me the problem statement in simple words clearly


<sub>ran — Bash: List project files, history, and README · Bash: Read script headers and recent commit messages</sub>

Here's the whole project from the beginning, in plain words.

## The problem

Fatty liver disease (NAFLD) gets worse in steps:

- **Disease ladder:** healthy → fat in the liver (NAFL) → fat plus inflammation (NASH)
- **Fibrosis ladder:** scarring stage 0 → 1 → 2 → 3 → 4 (stage 4 is cirrhosis)

Doctors can only find out the stage with a **liver biopsy**, which means cutting out a piece of the liver. Early stages can still be reversed. Later scarring mostly can't. Inflammation without scarring yet (NASH with fibrosis 0) is the stage where treatment helps most.

**The question:** *As the liver gets sicker, stage by stage, which genes go up or down?*

Those genes could lead to:
1. Predicting a patient's stage from gene activity, which is your mentor's main aim ("our aim is to predict the stages")
2. Explaining the biology of what changes at each step
3. Drug ideas, by finding drugs that act on those genes

## Why it's hard

There isn't one big dataset. The data is spread across **8 separate public studies (GEO)**, and each one recorded things differently:
- One writes fibrosis as `"4"`, another as `"F4"`. Sex is written 6 different ways.
- Some patients were biopsied twice. That's 1,085 samples from 1,027 people, and counting them as different people would skew the statistics.
- Gene IDs and measurement scales also differ from study to study.

So a big part of the work was cleaning things up so all 8 studies use the same labels.

## What you've built so far

1. **Cleaned the data:** one set of stage and disease labels, patient IDs, all 53,993 genes mapped to the same IDs, and values standardised (z-scores) so the studies can be compared.
2. **Built a knowledge graph in Neo4j:** patients, samples, genes and measurements, plus published biology from OptimusKG (which replaced PrimeKG): gene–disease links, drugs, pathways.
3. **Found the progression genes:** 4,692 genes that rise or fall with stage, and only counted when most studies agree. Examples: STMN2 rises about 36× from stage 0 to 4, and TREM2 also showed up.
4. **Tried missing-link prediction** to guess new drugs for NAFLD. The first model failed its own check, so you threw those predictions out. Your mentor has since said this is a side project, not the main paper.
5. **Sent your mentor the stage-wise CSVs:** gene levels by stage, by disease group, by sex and by age.

## Where things stand

- **Main paper:** the progression genes, aimed at *Scientific Reports*.
- **Still to do from the last meeting:** trim the diseases in the graph to liver-related ones only. It still holds all 36,044.
- **Later and smaller:** missing-link prediction, maybe for a conference.

**In one sentence:** combine 8 messy liver gene-expression studies into one clean knowledge graph, so you can find which genes change as fatty liver disease progresses, with the goal of predicting a patient's stage.


---

## once tell me what is the problem statemnet clearly in simple words

once tell me what is the problem statemnet clearly in simple words

**Problem statement, in simple words:**

Fatty liver disease gets worse step by step. It starts with fat in the liver, then the liver gets inflamed, then it scars, and finally it can turn into cirrhosis. Today the only way to know what stage a patient is at is a liver biopsy, which means cutting out a piece of the liver. That is painful and risky.

**We want to find which genes change as the disease moves from one stage to the next.** Those genes could then be used to **predict a patient's stage**, and they could also point to new treatments.

**The challenge:** no single study has enough patients. So we combine 8 different studies, but each one records its data in a different format. We first have to clean and join them into one knowledge graph, and only then can we look for the genes that track the disease's progression.

**One line:** *Use gene data from 8 liver studies to find the genes that change as fatty liver disease gets worse, so we can predict a patient's stage without a biopsy.*


---

## now step by step tell me what we did clearly in simple words...after each step i will say 

now step by step tell me what we did clearly in simple words...after each step i will say ok..then u have to say next step

**Step 1: Collect the data**

We downloaded 8 liver studies from **GEO**, a free public website where scientists upload their data.

Each study has two kinds of information:
- **Gene data:** for every liver sample, how active each gene is (a number per gene).
- **Patient info:** for every sample, details such as the disease stage, fibrosis score, age and sex.

All 8 studies together give us **1,085 liver samples**.

We read all these files into Python so the computer could work with them (`parse_expression.py`).

**In short:** we gathered liver gene data and patient details from 8 public studies.

Say **ok** when you're ready for Step 2.


---

## ok

ok

**Step 2: Make the gene names the same everywhere**

Different studies name the same gene in different ways. For example:
- One study uses a code like `ENSG00000141510`
- Another uses the name `TP53`

The computer would treat these as two different genes, even though they are the same one.

So we **gave every gene one standard ID** across all 8 studies (`map_gene_ids.py`). In the end we had **53,993 genes**, all with the same naming in every study.

**In short:** we made sure each gene has one name, so we can compare it across studies.

Say **ok** for Step 3.


---

## ok

ok

**Step 3: Make the patient labels the same everywhere**

The genes were fixed, but the patient information was still messy. Each study wrote things its own way:

- **Fibrosis stage 4:** one study wrote `"4"`, another wrote `"F4"`
- **Disease:** one said `healthy`, another `control`, another `normal liver histology`
- **Sex:** written 6 different ways (`Female`, `female`, `F`, `Male`, `male`, `M`)

If we searched for "stage 4", we found only **29 of the 35** real cirrhosis samples. Nothing warned us that 6 were missing. That's dangerous.

So we created **clean labels** for every sample (`normalize_clinical.py`):
- **Fibrosis stage:** always a number from 0 to 4
- **Disease group:** always one of control / obese / NAFL / NASH / NAFLD

We kept the original values too, so anyone can check the translation.

We also **recovered missing labels**. For example, one study had hidden the diagnosis inside the sample name (like `nash12_F3`), and another had only a scoring panel from which we worked out the diagnosis.

**In short:** we made every study describe patients the same way.

Say **ok** for Step 4.


---

## ok

ok

**Step 4: Find out which samples came from the same person**

We first thought **1,085 samples meant 1,085 patients**. That turned out to be wrong.

In one study (GSE193066), **58 patients had a liver biopsy twice**. So its 164 samples came from only 106 people.

Why this matters: if we counted the same person twice, that person would get double weight in the statistics. Our results would look stronger than they really are. This mistake is called **pseudo-replication**.

So we gave every sample:
- a **patient ID**, saying which person it came from
- a **biopsy number** (1st or 2nd)

**Final count:** 1,085 samples from **1,027 real patients**.

**In short:** we made sure each person is counted only once.

Say **ok** for Step 5.


---

## ok

ok

**Step 5: Make the numbers comparable, then build the graph**

**Part A: Fix the scale problem**

Each study measured gene activity differently, with different machines and different depth. A value of "50" in one study is not the same as "50" in another.

So for each gene we converted its values into a **z-score** inside each study. A z-score just says:
- **0** = normal level for that study
- **+2** = much higher than usual
- **−2** = much lower than usual

Now all 8 studies are on the same scale and can be compared.

We also **kept the genes measured as zero**. At first, zeros were thrown away. But "this gene is switched off" is real information. Keeping them added **9.1 million measurements**, and **514 more progression genes** showed up as a result, including **TREM2**.

**Part B: Build the knowledge graph**

We loaded everything into **Neo4j**, a graph database. Think of it as a map of dots connected by lines:

- **Dots:** Patients, Samples, Genes, Studies
- **Lines:** Patient → gave → Sample, and Sample → expresses → Gene (with its value)

Now one query can answer a question like *"show me gene X in every stage-4 patient across all studies."*

**In short:** we put all the data on the same scale and connected it in one big graph.

Say **ok** for Step 6.


---

## ok

ok

**Step 6: Add existing medical knowledge to the graph**

Our graph so far only had **our own patient data**. We also wanted to include what science **already knows** about these genes.

So we added a **knowledge layer** from a big public biomedical database:
- **Gene → disease:** which genes are known to be linked to which diseases
- **Drug → gene:** which drugs act on which genes
- **Drug → disease:** which drugs treat which diseases
- **Pathways and phenotypes:** what biological processes the genes take part in

**First we used PrimeKG.** Later we **replaced it with OptimusKG**, which is newer and better. Your mentor agreed, saying PrimeKG was "just a reference".

Now the graph connects **our patients → their genes → known diseases, drugs and pathways**.

⚠️ **Still pending:** the graph includes **all 36,044 diseases**, including heart and brain diseases. Your mentor asked to **keep only liver-related diseases**. This hasn't been done yet.

**In short:** we linked our patient data with known medical knowledge (drugs, diseases, pathways).

Say **ok** for Step 7.


---

## ok

ok

**Step 7: Find the progression genes (the main result)**

This is the core of the project. We asked: **which genes steadily go up or down as the disease gets worse?**

We checked this along **two ladders**, because they measure different things:
- **Fibrosis ladder:** scarring stage 0 → 1 → 2 → 3 → 4
- **Disease ladder:** control → NAFL → NASH (inflammation)

Why use both? **40 NASH patients have no scarring yet** (fibrosis 0). They are inflamed but not scarred, which is the **best time to treat**. With only the fibrosis ladder, we would miss them.

**How we did it** (`find_progression_genes.py`):
1. For each gene, **inside each study separately**, we checked whether its value rises or falls with the stage. (The test is called Spearman correlation.)
2. We kept a gene **only if most studies agreed** on the direction. A gene that changes in just one study is probably a quirk of that study, not real biology.
3. We counted each patient only once (from Step 4).
4. We tested only genes measured in **all 8 studies**.

**Result:** **4,692 progression genes**.

One example is **STMN2**. Its raw level rises about **36 times** from stage 0 to stage 4.

We then added these findings back into the graph as new links:
- Gene → **TRACKS_FIBROSIS** → disease
- Gene → **TRACKS_INFLAMMATION** → disease

**In short:** we found the 4,692 genes that change as liver disease gets worse, and only kept the ones that several studies agree on.

Say **ok** for Step 8.


---

## ok

ok

**Step 8: Try to predict new drugs (missing links), which failed**

**The idea:** the graph already knows some drugs that treat liver disease. Could the computer **guess new drugs** that might also work?

**How:** we trained a model called **ComplEx** (`train_link_prediction.py`).
- It turns every dot in the graph (gene, drug, disease) into a position in space, so connected things sit close together.
- If a drug ends up **close to liver disease** without a link between them, that's a possible new treatment.

We gave it about **1.3 million facts** from the graph. We left out the raw gene measurements, because they are data rather than knowledge.

**We tested it honestly in two ways:**
1. **Hidden-answer test:** we hid 10% of the facts and checked whether the model could find them again.
2. **Liver check:** **95 drugs are already known** to treat NAFLD. If the model works, those should rank near the top out of about 12,000 drugs.

**Result: it failed.** The known drugs did not come out near the top. So any "new" drugs it suggested would just be noise, and **we threw the predictions away** instead of reporting them.

Your mentor then said missing-link prediction is a **small side project**, maybe for a conference later. **The main paper is the progression genes.**

**In short:** we tried to predict new drugs, the model didn't pass its own test, and this is now low priority.

Say **ok** for Step 9.


---

## ok

ok

**Step 9: Send the stage-wise genes to the mentor**

At the **7 September 2026 meeting**, your mentor asked:
> "send me those genes, stage wise… I will do analysis"

They also said:
- Don't send all 54,000 genes, only the progression genes
- Don't send pathway or phenotype information

So we made **CSV files for the 4,692 progression genes** (`export_for_mentor.py`):

| File | What it shows |
|---|---|
| `genes_by_fibrosis_stage.csv` | Average gene level at stage 0, 1, 2, 3, 4 |
| `genes_by_disease_group.csv` | control / obese / NAFL / NAFLD / NASH |
| `genes_by_stage_and_sex.csv` | Stage × male/female |
| `genes_by_stage_and_age.csv` | Stage × age group |
| `sample_demographics.csv` | One row per sample |
| `README.txt` | Explains everything |

Before this, we had to **clean up sex labels** (the 6 different spellings), or else every group would have split in two.

**Limits we told the mentor about:**
- The stage file uses **668 staged samples**.
- The age and sex files use only **385 samples**, because only 3 studies recorded age, sex and stage together. Some groups are very small, and a few are empty (no cirrhosis patients under 40).

**In short:** we gave the mentor clean, stage-by-stage gene tables to analyse.

Say **ok** for Step 10, which covers where we are now and what's next.


---

## ok

ok

**Step 10: Where we are now and what's next**

**Done ✅**
1. Collected 8 liver studies (1,085 samples)
2. Gave every gene one standard name (53,993 genes)
3. Made patient labels the same across studies
4. Counted each person once (1,027 patients)
5. Put the numbers on one scale and built the graph in Neo4j
6. Added medical knowledge from OptimusKG
7. **Found 4,692 progression genes** (the main result)
8. Tried drug prediction, which failed and is now low priority
9. Sent the stage-wise CSVs to the mentor

**Still to do ⏳**
1. **Trim the diseases.** The graph still has all 36,044. Keep only liver-related ones, as the mentor asked.
2. **Wait for the mentor's analysis** of the CSVs, and act on their feedback.
3. **Build the stage-prediction model.** This is the mentor's main aim ("predict the stages"), and **we haven't built it yet**. So far we've found *which genes* change. The next step is a model that uses those genes to tell a patient's stage from their gene data.
4. **Write the paper** on the progression genes, targeting **Scientific Reports**.
5. **Later, optional:** return to drug prediction for a smaller conference paper.

**The whole journey in one line:**
*Messy data from 8 studies → cleaned and joined → one knowledge graph → 4,692 genes that track liver disease getting worse → next: use them to predict a patient's stage, and publish.*

That's everything from the start. If you want, I can now explain any step in more detail, or start on one of the to-do items.


---

## ok now will u tell me what is the part of optimum kg that we added....like whhat nodes wha

ok now will u tell me what is the part of optimum kg that we added....like whhat nodes what relations.....what is the meaning of those nodes and relations


<sub>ran — Bash: Read the OptimusKG layer build script · ToolSearch: select:mcp__neo4j-liver-kg__read_neo4j_cypher · Bash: Count rows in each OptimusKG output file · Bash: Show relation subtypes and progression edge format</sub>

Here is exactly what we took from OptimusKG and added to our graph. I counted everything from the files in `data/graph_okg/`.

## First, a reminder: what we already had

Our graph started with **our own patient data**:

- **Patient**, **Sample** and **Study** nodes
- **Gene** nodes (53,993)
- A **Sample → EXPRESSES → Gene** relation, which stores how active that gene was in that sample

On top of that, OptimusKG adds **what science already knows**.

## The 5 new node types (the dots)

| Node | How many | What it means, simply |
|---|---|---|
| **Disease** | 36,044 | Any illness, for example NAFLD, NASH, cirrhosis, diabetes |
| **Drug** | 12,025 | A medicine or chemical, for example Resmetirom |
| **Pathway** | 2,220 | A chain of steps genes follow to do a job, for example "fat breakdown" |
| **BioProcess** | 12,203 | A general job in the body that genes help with, for example "inflammation response" or "cell death" |
| **Phenotype** | 8,666 | A visible sign or symptom, for example "enlarged liver" or "jaundice" |

We did **not** add new Gene nodes. OptimusKG uses the same gene IDs as we do (Ensembl), so its facts attach straight onto **our existing genes**. 94% of our genes matched.

## The 8 new relation types (the lines)

| Relation | Connects | Meaning | How many |
|---|---|---|---|
| **ASSOCIATED_WITH** | Gene → Disease | Research has linked this gene to this disease | 1,832,441 |
| **INTERACTS_WITH** | Gene ↔ Gene | These two genes' proteins work together | 324,116 |
| **INVOLVED_IN** | Gene → BioProcess | This gene helps with this body job | 157,081 |
| **IN_PATHWAY** | Gene → Pathway | This gene is one step in this pathway | 46,751 |
| **ACTS_ON** | Drug → Gene | This drug affects this gene's protein | 20,674 |
| **DRUG_DISEASE** | Drug → Disease | How this drug relates to this disease | 70,380 |
| **HAS_PHENOTYPE** | Disease → Phenotype | This disease shows this symptom | 157,144 |
| **PARENT_OF** | Disease → Disease | Disease family tree, for example "liver disease" → "NAFLD" → "NASH" | 44,215 |

**Some relations have extra detail:**

- **DRUG_DISEASE** comes in 3 kinds:
  - **INDICATION** (57,601): the drug is approved to treat this disease
  - **CONTRAINDICATION** (11,718): the drug should not be used with this disease
  - **OFF_LABEL_USE** (1,061): doctors use the drug for this disease, but it isn't officially approved for it
- **ACTS_ON** says *how* the drug acts: INHIBITOR (blocks the gene), AGONIST (activates it), TARGET, ENZYME and others. This matters because if a gene **rises** in disease, you want a drug that **blocks** it, not one that activates it.
- **ASSOCIATED_WITH** stores an **evidence score**. We kept only links with **score ≥ 0.1**. Weaker links (sometimes just one paper mentioning the gene once) were dropped. Before that filter, 5,568 genes were linked to NAFLD, which is meaningless. After it, **274** remain, including well-known ones like PNPLA3 and TM6SF2.

## What we left out on purpose

- **Drug–drug interactions:** about safety, not about how the disease works
- **Anatomy–gene:** "this gene is found in this tissue", which was mostly noise
- **Environmental exposures:** toxins and similar

## Our own relations, added on top

We also added **5,576** links from our own analysis in Step 7:

- **Gene → TRACKS_FIBROSIS → Disease:** this gene rises or falls as scarring gets worse
- **Gene → TRACKS_INFLAMMATION → Disease:** this gene rises or falls from control → NAFL → NASH

Each link stores the direction (rises/falls), how strongly the gene follows the stage (`rho`), how significant the result is (`q`), and how many studies agreed.

## Why we switched to OptimusKG

1. **Liver drugs:** PrimeKG had **0** drugs recorded for NASH, NAFLD or cirrhosis. OptimusKG has **74, 95 and 71**, including **Resmetirom**, the first approved NASH drug (2024).
2. **Gene match:** 94% of our genes matched, compared with 49% for PrimeKG.
3. **Drug action:** OptimusKG says *how* a drug acts on a gene. PrimeKG only said that it does.

## The whole graph as one picture

```
Patient → Sample → EXPRESSES → Gene ──ASSOCIATED_WITH──→ Disease ──HAS_PHENOTYPE──→ Phenotype
                                 │ ↑                       ↑   ↑
                    TRACKS_* (ours)│ ACTS_ON           DRUG_DISEASE   PARENT_OF (disease tree)
                                 │ │                       │
                                 │ Drug ───────────────────┘
                                 ├── IN_PATHWAY → Pathway
                                 ├── INVOLVED_IN → BioProcess
                                 └── INTERACTS_WITH → Gene
```

**Pending reminder:** all 36,044 diseases are still in the graph. Your mentor asked to keep only liver-related ones. The `PARENT_OF` disease tree is the natural way to do that: keep everything under "liver disease" plus close relatives like diabetes and obesity.


---

## i want to check these in the graph visually....fo each relation give me query .. i will se

i want to check these in the graph visually....fo each relation give me query .. i will see


<sub>ran — mcp__neo4j-liver-kg__read_neo4j_cypher: CALL db.schema.visualization() YIELD nodes, relationships RETURN [n IN nodes | labels(n)] AS labels, [r IN rel · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (d:Disease) WHERE toLower(d.name) IN ['non-alcoholic fatty liver disease','nonalcoholic steatohepatitis' · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene {symbol:'PNPLA3'}) OPTIONAL MATCH (s:Sample) WITH g, s LIMIT 1 OPTIONAL MATCH (d:Disease) WHERE  · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene)-[r:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->(d:Disease) RETURN type(r) AS t, d.name AS disease, co · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (s:Sample)-[r:EXPRESSES]->(g:Gene) WITH r, s LIMIT 1 MATCH (dr:Drug)-[a:ACTS_ON]->(:Gene) WITH r, s, a L · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene {symbol:'PNPLA3'})-[r:ASSOCIATED_WITH]->(d:Disease {name:'non-alcoholic fatty liver disease'}) W · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene {symbol:'LGALS3'}) RETURN COUNT { (g)-[:IN_PATHWAY]->() } AS pw, COUNT { (g)-[:INVOLVED_IN]->()  · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (d:Disease {name:'non-alcoholic fatty liver disease'}) RETURN COUNT { (d)-[:HAS_PHENOTYPE]->() } AS ph,  · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (d:Disease {name:'cirrhosis of liver'}) RETURN COUNT { (:Drug)-[:CONTRAINDICATED_IN]->(d) } AS contra, C · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (dr:Drug)-[:OFF_LABEL_FOR]->(d:Disease) WHERE toLower(d.name) CONTAINS 'liver' OR toLower(d.name) CONTAI</sub>

I checked every query below against your live Neo4j database. Two corrections to what I told you before:

1. **There is no Patient node.** The patient ID is stored as a `patient_id` property on each **Sample**. Samples link to studies through `IN_DATASET → Dataset`.
2. **"DRUG_DISEASE" is not one relation in Neo4j.** It is split into three: **TREATS**, **CONTRAINDICATED_IN** and **OFF_LABEL_FOR**. Also, the graph holds **6,384** TRACKS links (3,645 fibrosis + 2,739 inflammation), not the 5,576 I quoted from a CSV.

**How to view:** open **Neo4j Browser** (usually http://localhost:7474), paste one query, press **Ctrl+Enter**, and look at the **Graph** tab. Click a node or line to see its properties. Every query has a `LIMIT` so the picture stays readable.

---

### 1. ASSOCIATED_WITH (Gene → Disease): genes linked to NAFLD
```cypher
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease {name:'non-alcoholic fatty liver disease'})
RETURN g, r, d ORDER BY r.score DESC LIMIT 25
```
*You'll see the 25 genes with the strongest research evidence for NAFLD (PNPLA3 should be there). Click a line to see its `score`.*

### 2. INTERACTS_WITH (Gene ↔ Gene): partners of a gene
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:INTERACTS_WITH]-(p:Gene)
RETURN g, r, p LIMIT 30
```
*LGALS3 is one of our top progression genes. It has 156 partners in total; this shows 30.*

### 3. INVOLVED_IN (Gene → BioProcess): what jobs a gene does
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:INVOLVED_IN]->(b:BioProcess)
RETURN g, r, b
```
*Shows its 27 processes.*

### 4. IN_PATHWAY (Gene → Pathway)
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:IN_PATHWAY]->(p:Pathway)
RETURN g, r, p
```
*Shows its 4 pathways.*

### 5. ACTS_ON (Drug → Gene): drugs hitting a gene
```cypher
MATCH (dr:Drug)-[r:ACTS_ON]->(g:Gene {symbol:'PPARG'})
RETURN dr, r, g LIMIT 25
```
*PPARG is a known NAFLD gene with 60 drugs acting on it. Click a line to see `action` (AGONIST, INHIBITOR and so on).*

### 6. TREATS (Drug → Disease): approved drugs for NAFLD
```cypher
MATCH (dr:Drug)-[r:TREATS]->(d:Disease {name:'non-alcoholic fatty liver disease'})
RETURN dr, r, d LIMIT 30
```
*There are 95 in total. Look for **RESMETIROM**.*

### 7. CONTRAINDICATED_IN (Drug → Disease): drugs to avoid in cirrhosis
```cypher
MATCH (dr:Drug)-[r:CONTRAINDICATED_IN]->(d:Disease {name:'cirrhosis of liver'})
RETURN dr, r, d LIMIT 30
```
*There are 60 in total. NAFLD itself has none, which is why this one uses cirrhosis.*

### 8. OFF_LABEL_FOR (Drug → Disease): unofficial use in liver diseases
```cypher
MATCH (dr:Drug)-[r:OFF_LABEL_FOR]->(d:Disease)
WHERE toLower(d.name) CONTAINS 'hepat' OR toLower(d.name) CONTAINS 'liver'
RETURN dr, r, d
```
*Only a few exist for liver diseases (chronic hepatitis, liver cancer, alcoholic hepatitis).*

### 9. HAS_PHENOTYPE (Disease → Phenotype): symptoms
```cypher
MATCH (d:Disease {name:'cirrhosis of liver'})-[r:HAS_PHENOTYPE]->(p:Phenotype)
RETURN d, r, p
```
*Shows cirrhosis's 16 symptoms. NAFLD has only 2.*

### 10. PARENT_OF (Disease → Disease): the disease family tree
```cypher
MATCH path = (a:Disease)-[:PARENT_OF*1..2]->(d:Disease {name:'non-alcoholic fatty liver disease'})-[:PARENT_OF*0..2]->(c:Disease)
RETURN path
```
*Shows NAFLD's parents above it and its sub-types below it.*

---

### Our own relations

### 11. TRACKS_FIBROSIS (Gene → NAFLD): genes that change with scarring
```cypher
MATCH (g:Gene)-[r:TRACKS_FIBROSIS]->(d:Disease)
RETURN g, r, d ORDER BY abs(r.rho) DESC LIMIT 25
```
*The 25 strongest of 3,645. Click a line to see `rho`, `direction` (rises/falls) and `n_studies`.*

### 12. TRACKS_INFLAMMATION (Gene → NASH): genes that change with inflammation
```cypher
MATCH (g:Gene)-[r:TRACKS_INFLAMMATION]->(d:Disease)
RETURN g, r, d ORDER BY abs(r.rho) DESC LIMIT 25
```
*The 25 strongest of 2,739.*

### 13. EXPRESSES + IN_DATASET (Sample → Gene, Sample → Dataset): our patient data
```cypher
MATCH (s:Sample)-[r:EXPRESSES]->(g:Gene {symbol:'STMN2'})
MATCH (s)-[i:IN_DATASET]->(ds:Dataset)
RETURN s, r, g, i, ds LIMIT 30
```
*Click a Sample to see `patient_id`, `disease_group` and `sex`. Click an EXPRESSES line to see `value_raw` and `value_z`.*

---

### Bonus: everything in one picture
```cypher
MATCH (g:Gene {symbol:'PPARG'})-[t:TRACKS_FIBROSIS|TRACKS_INFLAMMATION|ASSOCIATED_WITH]->(d:Disease)
WHERE d.name IN ['non-alcoholic fatty liver disease','non-alcoholic steatohepatitis']
OPTIONAL MATCH (dr:Drug)-[a:ACTS_ON]->(g)
WITH g, t, d, collect(DISTINCT [dr, a])[0..8] AS drugs
OPTIONAL MATCH (g)-[p:IN_PATHWAY]->(pw:Pathway)
WITH g, t, d, drugs, collect(DISTINCT [p, pw])[0..5] AS pws
RETURN g, t, d, drugs, pws
```
*This shows one gene with our findings, the literature link, some drugs that act on it, and some of its pathways, all connected. If a link doesn't appear, PPARG may not be one of our progression genes. Swap in another gene from query 11.*

**Tip:** if the Graph view shows only nodes and no lines, open Browser settings (gear icon) and turn on **"Connect result nodes"**.


---

## not only just queries...also explain each query in simple words

not only just queries...also explain each query in simple words

Each query below has the same three parts: **the question it asks**, **what each line means**, and **what you'll see**.

## First: how to read any query (1 minute)

Cypher draws pictures with text:

| Symbol | Meaning | Example |
|---|---|---|
| `( )` | a **node** (a dot) | `(g:Gene)` = "a Gene, which I'll call **g**" |
| `[ ]` | a **relation** (a line) | `[r:TREATS]` = "a TREATS line, which I'll call **r**" |
| `-->` | the direction of the line | `(a)-->(b)` = from a to b |
| `{ }` | a filter | `{symbol:'PPARG'}` = "only the gene named PPARG" |
| `MATCH` | "find this pattern" | |
| `WHERE` | "but only if…" | |
| `RETURN` | "show me these" | |
| `ORDER BY … DESC` | sort, biggest first | |
| `LIMIT 25` | show only 25 | |

The letters `g`, `r`, `d` are just nicknames, so you can refer to things later in the query.

---

## Part A: Relations from OptimusKG (existing knowledge)

### 1. ASSOCIATED_WITH: which genes are known to be linked to NAFLD?
```cypher
MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease {name:'non-alcoholic fatty liver disease'})
RETURN g, r, d ORDER BY r.score DESC LIMIT 25
```
**Line by line:**
- `MATCH (g:Gene)` → find any gene, call it **g**
- `-[r:ASSOCIATED_WITH]->` → that has an "associated with" line, call it **r**
- `(d:Disease {name:'non-alcoholic fatty liver disease'})` → pointing to the disease NAFLD
- `ORDER BY r.score DESC` → sort by evidence score, strongest first
- `LIMIT 25` → show only the top 25

**What you'll see:** NAFLD in the middle, with 25 genes around it. These are the genes research most strongly links to NAFLD (PNPLA3 should be there). Click a line to see its `score`. Higher means more evidence.

---

### 2. INTERACTS_WITH: which genes work together with LGALS3?
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:INTERACTS_WITH]-(p:Gene)
RETURN g, r, p LIMIT 30
```
**Line by line:**
- `(g:Gene {symbol:'LGALS3'})` → start from the gene LGALS3, one of our top progression genes
- `-[r:INTERACTS_WITH]-` → follow its "interacts with" lines. **There is no arrow here**, because an interaction goes both ways.
- `(p:Gene)` → to another gene, called **p** (partner)
- `LIMIT 30` → show 30 of its 156 partners

**What you'll see:** LGALS3 at the centre, with partner genes around it. Their proteins physically work together in the body.

---

### 3. INVOLVED_IN: what body jobs does LGALS3 help with?
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:INVOLVED_IN]->(b:BioProcess)
RETURN g, r, b
```
**Line by line:**
- Start at LGALS3
- Follow its "involved in" lines
- To BioProcess nodes, called **b**
- No LIMIT, because it has only 27

**What you'll see:** LGALS3 linked to processes such as "inflammatory response" or "cell adhesion". This tells you *what the gene does*.

---

### 4. IN_PATHWAY: which pathways is LGALS3 part of?
```cypher
MATCH (g:Gene {symbol:'LGALS3'})-[r:IN_PATHWAY]->(p:Pathway)
RETURN g, r, p
```
**Line by line:** same shape as query 3, but going to Pathway nodes.

**What you'll see:** LGALS3 with its 4 pathways. A pathway is a step-by-step chain of genes doing one job, like an assembly line. A BioProcess is a broader category.

---

### 5. ACTS_ON: which drugs affect the gene PPARG?
```cypher
MATCH (dr:Drug)-[r:ACTS_ON]->(g:Gene {symbol:'PPARG'})
RETURN dr, r, g LIMIT 25
```
**Line by line:**
- `(dr:Drug)` → any drug, called **dr**
- `-[r:ACTS_ON]->` → that acts on
- `(g:Gene {symbol:'PPARG'})` → the gene PPARG, a well-known fat-control gene in NAFLD
- `LIMIT 25` → 25 of its 60 drugs

**What you'll see:** PPARG at the centre, with drugs around it. **Click a line** to see `action`:
- **AGONIST** = switches the gene's protein **on**
- **INHIBITOR / ANTAGONIST** = switches it **off**

This is important: if a gene goes **up** in disease, you want a drug that turns it **off**.

---

### 6. TREATS: which drugs are approved for NAFLD?
```cypher
MATCH (dr:Drug)-[r:TREATS]->(d:Disease {name:'non-alcoholic fatty liver disease'})
RETURN dr, r, d LIMIT 30
```
**Line by line:**
- Any drug
- With a "treats" line
- To NAFLD
- Show 30 of 95

**What you'll see:** NAFLD surrounded by drugs used to treat it. Look for **RESMETIROM**, the first drug approved for NASH (2024). PrimeKG had **zero** of these, and that is why we switched to OptimusKG.

---

### 7. CONTRAINDICATED_IN: which drugs are dangerous for cirrhosis patients?
```cypher
MATCH (dr:Drug)-[r:CONTRAINDICATED_IN]->(d:Disease {name:'cirrhosis of liver'})
RETURN dr, r, d LIMIT 30
```
**Line by line:** same shape as query 6, but the line means **"don't give this drug"**, and the disease is cirrhosis.

**What you'll see:** cirrhosis with drugs that should be **avoided** in it (60 in total). A scarred liver can't break down some medicines safely. We used cirrhosis because NAFLD has no contraindications recorded.

---

### 8. OFF_LABEL_FOR: drugs used unofficially for liver diseases
```cypher
MATCH (dr:Drug)-[r:OFF_LABEL_FOR]->(d:Disease)
WHERE toLower(d.name) CONTAINS 'hepat' OR toLower(d.name) CONTAINS 'liver'
RETURN dr, r, d
```
**Line by line:**
- Any drug with an "off-label" line to any disease
- `WHERE … CONTAINS 'hepat' OR … 'liver'` → but only diseases whose name includes "hepat" (as in hepatitis) or "liver"
- `toLower` → ignore capital letters, so "Liver" and "liver" both match

**What you'll see:** a small picture, only about 7 links (chronic hepatitis, liver cancer, alcoholic hepatitis). Off-label means doctors use the drug for this disease even though it isn't officially approved for it.

---

### 9. HAS_PHENOTYPE: what symptoms does cirrhosis have?
```cypher
MATCH (d:Disease {name:'cirrhosis of liver'})-[r:HAS_PHENOTYPE]->(p:Phenotype)
RETURN d, r, p
```
**Line by line:** start at cirrhosis, follow "has phenotype" lines, to Phenotype nodes.

**What you'll see:** cirrhosis with its 16 signs and symptoms, for example jaundice or an enlarged spleen. NAFLD has only 2 recorded, because it is often silent with no symptoms.

---

### 10. PARENT_OF: where does NAFLD sit in the disease family tree?
```cypher
MATCH path = (a:Disease)-[:PARENT_OF*1..2]->(d:Disease {name:'non-alcoholic fatty liver disease'})-[:PARENT_OF*0..2]->(c:Disease)
RETURN path
```
**Line by line:**
- `path =` → save the whole chain as one thing called **path**
- `(a:Disease)-[:PARENT_OF*1..2]->` → go **up** 1 to 2 levels to find NAFLD's parents and grandparents
- `(d:Disease {name:'…NAFLD…'})` → NAFLD in the middle
- `-[:PARENT_OF*0..2]->(c:Disease)` → go **down** 0 to 2 levels to find its children
- `*1..2` means "follow this line 1 or 2 times in a row"

**What you'll see:** a small tree, for example *fatty liver disease → NAFLD → NASH*. **We'll use this tree later to trim the graph to liver diseases only.**

---

## Part B: Our own relations (from our patient data)

### 11. TRACKS_FIBROSIS: which genes change most as scarring gets worse?
```cypher
MATCH (g:Gene)-[r:TRACKS_FIBROSIS]->(d:Disease)
RETURN g, r, d ORDER BY abs(r.rho) DESC LIMIT 25
```
**Line by line:**
- Any gene with a TRACKS_FIBROSIS line to a disease (always NAFLD)
- `abs(r.rho)` → `rho` measures how closely the gene follows the stage, from −1 to +1. `abs` removes the minus sign, so strong **rises** and strong **falls** both count.
- `DESC LIMIT 25` → the 25 strongest of 3,645

**What you'll see:** NAFLD with 25 genes. **Click a line** to see:
- `direction`: **rises** or **falls** from stage 0 to 4
- `rho`: how strongly the gene follows the stage
- `q`: how sure we are. Smaller is surer.
- `n_studies`: how many studies agreed

**This is our main finding, not something copied from a database.**

---

### 12. TRACKS_INFLAMMATION: which genes change most from healthy to NASH?
```cypher
MATCH (g:Gene)-[r:TRACKS_INFLAMMATION]->(d:Disease)
RETURN g, r, d ORDER BY abs(r.rho) DESC LIMIT 25
```
**Line by line:** same as query 11, but for the inflammation ladder (control → NAFL → NASH). These lines point to **NASH**.

**What you'll see:** NASH with its 25 strongest genes (2,739 in total). Some genes appear in both query 11 and query 12. Others appear in only one, which means they track inflammation but not scarring, or the other way round.

---

### 13. EXPRESSES + IN_DATASET: the raw patient data behind it all
```cypher
MATCH (s:Sample)-[r:EXPRESSES]->(g:Gene {symbol:'STMN2'})
MATCH (s)-[i:IN_DATASET]->(ds:Dataset)
RETURN s, r, g, i, ds LIMIT 30
```
**Line by line:**
- First MATCH → find liver samples that have a measurement for gene STMN2
- Second MATCH → for those **same** samples (`s` again), find which study they came from
- Show 30

**What you'll see:** STMN2 in the middle, linked to 30 samples, each linked to its study.
- **Click a Sample:** `patient_id`, `disease_group`, `sex`, `biopsy_number`
- **Click an EXPRESSES line:** `value_raw` (the original number), `value_z` (the comparable score), `value_log`

STMN2 is the gene that rises about 36× from stage 0 to stage 4.

---

## Bonus: one gene, everything connected
```cypher
MATCH (g:Gene {symbol:'PPARG'})-[t:TRACKS_FIBROSIS|TRACKS_INFLAMMATION|ASSOCIATED_WITH]->(d:Disease)
WHERE d.name IN ['non-alcoholic fatty liver disease','non-alcoholic steatohepatitis']
OPTIONAL MATCH (dr:Drug)-[a:ACTS_ON]->(g)
WITH g, t, d, collect(DISTINCT [dr, a])[0..8] AS drugs
OPTIONAL MATCH (g)-[p:IN_PATHWAY]->(pw:Pathway)
WITH g, t, d, drugs, collect(DISTINCT [p, pw])[0..5] AS pws
RETURN g, t, d, drugs, pws
```
**Line by line:**
- Line 1 → PPARG's links to diseases. The `|` means "any of these three relation types".
- Line 2 → keep only NAFLD and NASH
- `OPTIONAL MATCH` → "also try to find this, but don't fail if there's none". Here: drugs acting on PPARG.
- `collect(...)[0..8]` → gather them into a list and keep the first 8
- Same again for pathways, keeping 5
- Show everything

**What you'll see:** the whole story of one gene in one picture:
**our finding** (TRACKS) + **literature** (ASSOCIATED_WITH) + **drugs** (ACTS_ON) + **biology** (IN_PATHWAY).

If no TRACKS line appears, PPARG may not be one of our progression genes. Replace `'PPARG'` with any gene name from query 11's result.

---

**Tip:** if you see dots but no lines between them, click the **gear icon** in Neo4j Browser and turn on **"Connect result nodes"**.


---

## i think from optimum kg we have gene associated with disease and also if the same gene is 

i think from optimum kg we have gene associated with disease and also if the same gene is in our progression genes then we added the same relation again?


<sub>ran — mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene)-[t:TRACKS_FIBROSIS|TRACKS_INFLAMMATION]->(d:Disease) · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene)-[t:TRACKS_FIBROSIS]->(d:Disease)<-[a:ASSOCIATED_WITH]-(g) RETURN g.symbol, t.direction, round(t</sub>

No, we didn't add the same relation twice. When a gene is both known from research and one of our progression genes, it gets **two different lines** to the disease, and each line means something different.

## The two lines

| | **ASSOCIATED_WITH** | **TRACKS_FIBROSIS / TRACKS_INFLAMMATION** |
|---|---|---|
| **Where it comes from** | OptimusKG (published research) | **Our own 8 studies, our own analysis** |
| **What it says** | "Some papers have linked this gene to NAFLD" | "In our patients, this gene **rises or falls** as the disease gets worse" |
| **What's stored on it** | `score` (how much evidence) | `rho`, `direction`, `q`, `n_studies` |
| **Does it say up or down?** | ❌ No | ✅ Yes |
| **Does it say which stage?** | ❌ No | ✅ Yes, it follows stage 0 → 4 |

So when a gene has **both** lines, the second one isn't a copy. It means **our data confirms what the literature says, and adds detail it didn't have** (the direction, and that the change follows the stage).

## How much they overlap (checked in your graph just now)

| Our relation | Our genes | Also in literature (ASSOCIATED_WITH) | **New, only from our data** |
|---|---|---|---|
| TRACKS_FIBROSIS → NAFLD | 3,645 | 73 | **3,572** |
| TRACKS_INFLAMMATION → NASH | 2,739 | 20 | **2,719** |

**About 98% of our progression genes are NOT linked to NAFLD/NASH in OptimusKG.** These are new findings, not something we copied.

## Examples of genes with both lines

| Gene | Our finding | Literature score |
|---|---|---|
| CDH6 | rises, rho 0.47 | 0.29 |
| **TREM2** | rises, rho 0.47 | 0.10 |
| COBLL1 | falls, rho −0.45 | 0.33 |
| CDKN1A | rises, rho 0.45 | 0.11 |
| THBS1 | rises, rho 0.43 | 0.11 |

These 73 + 20 genes act as a **sanity check**. Our method rediscovered genes that research already knew about, which gives us confidence in the other 3,572 + 2,719.

## See it yourself
```cypher
MATCH (g:Gene)-[t:TRACKS_FIBROSIS]->(d:Disease)<-[a:ASSOCIATED_WITH]-(g)
RETURN g, t, a, d LIMIT 10
```
**In simple words:** "find genes that have **both** our TRACKS line **and** the literature line to the same disease." Each of the 10 genes will show **two separate lines** going to NAFLD. Click each line and you'll see different properties on them.

**One-line answer:** ASSOCIATED_WITH says *"papers link this gene to the disease."* TRACKS says *"in our patients, this gene goes up or down as the disease gets worse."* They are two separate facts, and only 93 genes have both.


<sub>ran — mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene {symbol:'PPARG'})-[t]->(d:Disease) · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease) WITH g, d, count(r) AS c WHERE c > 1 RETURN count(*) AS duplic</sub>

Those two ASSOCIATED_WITH lines aren't a duplicate. They go to **two different diseases**. I checked in your graph:

| Line | From | To | Score |
|---|---|---|---|
| ASSOCIATED_WITH #1 | PPARG | **non-alcoholic fatty liver disease** (NAFLD) | 0.407 |
| ASSOCIATED_WITH #2 | PPARG | **non-alcoholic steatohepatitis** (NASH) | 0.324 |

## Why you see both

My query asked for both diseases on purpose:
```cypher
WHERE d.name IN ['non-alcoholic fatty liver disease','non-alcoholic steatohepatitis']
```
In simple words: "show PPARG's links to NAFLD **or** NASH." Research links PPARG to **each** of them separately, so you get one line to each disease. They are two separate disease nodes in the graph.

To confirm, click the **two disease dots** at the ends of the lines. They have different names and different IDs (`EFO_0003095` for NAFLD and `EFO_1001249` for NASH).

I also checked the **whole graph**: **no gene has two ASSOCIATED_WITH lines to the same disease.** There are no duplicates anywhere.

## Something else this picture tells you

You see **only ASSOCIATED_WITH lines and no TRACKS lines** for PPARG. That means:
- ✅ Research says PPARG is linked to NAFLD and NASH
- ❌ But in **our** patients, PPARG did **not** steadily rise or fall with the stage, so it is **not** one of our progression genes

So PPARG was a poor pick for the bonus example, and I'm sorry about that. To see **both kinds of line on one gene**, use **TREM2**, which has both:

```cypher
MATCH (g:Gene {symbol:'TREM2'})-[t:TRACKS_FIBROSIS|TRACKS_INFLAMMATION|ASSOCIATED_WITH]->(d:Disease)
WHERE d.name IN ['non-alcoholic fatty liver disease','non-alcoholic steatohepatitis']
RETURN g, t, d
```
**In simple words:** "show TREM2's lines to NAFLD and NASH, both from research and from our data." You'll see TREM2 → NAFLD with **both** an ASSOCIATED_WITH line (from research) **and** a TRACKS_FIBROSIS line (ours). Click each one and you'll see different properties: `score` on the first, `rho` and `direction` on the second.


---

## ok just like this give a query for a progression gene

ok just like this give a query for a progression gene


<sub>ran — mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene)-[f:TRACKS_FIBROSIS]->(:Disease), (g)-[:TRACKS_INFLAMMATION]->(:Disease) · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (g:Gene {symbol:'TNF'})-[t]->(d:Disease) WHERE type(t) IN ['TRACKS_FIBROSIS','TRACKS_INFLAMMATION','ASSO</sub>

I picked **TNF**, a well-known inflammation gene. In your graph it is one of our progression genes on **both** ladders, research links it to **both** diseases, and **21 drugs** act on it. So the picture shows every kind of line.

## The query
```cypher
MATCH (g:Gene {symbol:'TNF'})-[t:TRACKS_FIBROSIS|TRACKS_INFLAMMATION|ASSOCIATED_WITH]->(d:Disease)
WHERE d.name IN ['non-alcoholic fatty liver disease','non-alcoholic steatohepatitis']
OPTIONAL MATCH (dr:Drug)-[a:ACTS_ON]->(g)
WITH g, t, d, collect(DISTINCT [dr, a])[0..8] AS drugs
OPTIONAL MATCH (g)-[p:IN_PATHWAY]->(pw:Pathway)
WITH g, t, d, drugs, collect(DISTINCT [p, pw])[0..5] AS pws
RETURN g, t, d, drugs, pws
```

## What it means, line by line
1. **Line 1:** start at gene **TNF** and follow any of 3 kinds of line to a disease: our 2 TRACKS lines, and the research line ASSOCIATED_WITH.
2. **Line 2:** keep only NAFLD and NASH.
3. **Line 3:** also find drugs that act on TNF. `OPTIONAL` means "don't fail if there are none".
4. **Line 4:** gather those drugs into a list and keep 8, so the picture isn't crowded.
5. **Line 5:** also find pathways TNF belongs to.
6. **Line 6:** keep 5 of them.
7. **Line 7:** show everything.

## What you'll see: 4 lines to diseases (I checked these)

| Line | To | Comes from | Click it to see |
|---|---|---|---|
| **TRACKS_FIBROSIS** | NAFLD | **Our data** | rises, rho 0.25, 5 studies agree |
| **TRACKS_INFLAMMATION** | NASH | **Our data** | rises, rho 0.28, 4 studies agree |
| ASSOCIATED_WITH | NAFLD | Research | score 0.12 |
| ASSOCIATED_WITH | NASH | Research | score 0.11 |

**Plus:**
- **8 drug dots** → ACTS_ON → TNF (for example Ethyl pyruvate, Andrographolide, Dilmapimod)
- TNF → IN_PATHWAY → **5 pathway dots**

## How to read the picture

- **Two lines from TNF to NAFLD:** one from research ("linked"), one from our patients ("rises with scarring"). As we discussed, these are two different facts, not a duplicate.
- **Two lines from TNF to NASH:** the same idea, for inflammation.
- **The story:** TNF goes **up** as the disease gets worse in our patients, research agrees it is involved, and drugs that act on it already exist. That makes it an interesting gene to target.

⚠️ For TNF, all 21 drug lines say `action = TARGET`, which only means "this drug acts on TNF". It doesn't say whether the drug blocks it or activates it, so you would need to check that separately.

## Other genes you can try
Replace `'TNF'` with any of these. They all have both TRACKS lines, the research link, and drugs:

| Gene | What it does | Our finding |
|---|---|---|
| **MMP9** | breaks down tissue (scarring) | rises, rho 0.36 |
| **CASP1** | inflammation and cell death | rises, rho 0.28 |
| **CCR5** | immune cell signalling | rises, rho 0.30 |
| **RBP4** | vitamin A transport | **falls**, rho −0.24 |
| **PPARD** | fat burning | rises, rho 0.20 |


---

## phenotypes for other diseases query

phenotypes for other diseases query


<sub>ran — mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (d:Disease)-[:HAS_PHENOTYPE]->(p:Phenotype) · mcp__neo4j-liver-kg__read_neo4j_cypher: MATCH (d:Disease {name:'non-alcoholic fatty liver disease'})-[:HAS_PHENOTYPE]->(p) RETURN p.name UNION MATCH ( · mcp__neo4j-liver-kg__read_neo4j_cypher: UNWIND ['obesity','type 2 diabetes mellitus','hepatocellular carcinoma','cirrhosis of liver','metabolic syndro</sub>

Here are phenotype queries for other diseases, each with a plain explanation. I checked the counts in your graph.

## Query 1: phenotypes of any one disease (template)
```cypher
MATCH (d:Disease {name:'metabolic syndrome'})-[r:HAS_PHENOTYPE]->(p:Phenotype)
RETURN d, r, p
```
**In simple words:** "Start at one disease, follow its HAS_PHENOTYPE lines, and show the symptoms at the end."

**What you'll see:** that disease in the middle, with its symptoms around it.

**Swap in other diseases by changing the name.** These exist in your graph:

| Disease name to type | Phenotypes | Why it matters to us |
|---|---|---|
| `'cirrhosis of liver'` | 16 | Fibrosis stage 4 |
| `'metabolic syndrome'` | 14 | Strongly tied to fatty liver |
| `'obesity'` | 6 | A main risk factor (one of our disease groups) |
| `'type 2 diabetes mellitus'` | 5 | A main risk factor |
| `'hepatocellular carcinoma'` | 4 | Liver cancer, which can follow cirrhosis |
| `'Wilson disease'` | 74 | A genetic liver disease (copper build-up) |
| `'non-alcoholic fatty liver disease'` | 2 | Hepatic steatosis, non-Mendelian inheritance |
| `'non-alcoholic steatohepatitis'` | 2 | The same 2 |

⚠️ The name must match **exactly**, including capital letters. If you see nothing, the name is spelled differently. Use Query 2 to find the right spelling.

---

## Query 2: find a disease when you don't know its exact name
```cypher
MATCH (d:Disease)-[r:HAS_PHENOTYPE]->(p:Phenotype)
WHERE toLower(d.name) CONTAINS 'diabetes'
RETURN d, r, p LIMIT 50
```
**In simple words:** "Find every disease whose name **contains** 'diabetes' (ignoring capitals) and show their symptoms."
- `toLower` → ignore capital letters
- `CONTAINS 'diabetes'` → the name only has to include this word somewhere

**What you'll see:** several diabetes-type diseases, each with its symptoms. Replace `'diabetes'` with `'hepat'`, `'cirrho'`, `'obes'` and so on.

---

## Query 3: several key diseases side by side
```cypher
MATCH (d:Disease)-[r:HAS_PHENOTYPE]->(p:Phenotype)
WHERE d.name IN ['non-alcoholic fatty liver disease','cirrhosis of liver',
                 'obesity','type 2 diabetes mellitus','metabolic syndrome',
                 'hepatocellular carcinoma']
RETURN d, r, p
```
**In simple words:** "Show the symptoms of all 6 of these diseases in one picture."
- `IN [ ... ]` → the disease must be one in this list

**What you'll see:** 6 disease dots with their symptoms. **Look for symptom dots connected to more than one disease.** Those are shared symptoms, and they show how these diseases are related to each other.

---

## Query 4: only the symptoms that are shared
```cypher
MATCH (d1:Disease)-[r1:HAS_PHENOTYPE]->(p:Phenotype)<-[r2:HAS_PHENOTYPE]-(d2:Disease)
WHERE d1.name = 'non-alcoholic fatty liver disease'
RETURN d1, r1, p, r2, d2 LIMIT 40
```
**In simple words:** "Find symptoms that NAFLD **shares** with other diseases, and show those other diseases."
- `(d1)->(p)<-(d2)` → two diseases pointing to the **same** symptom. Notice the arrows meet in the middle.
- `d1` = NAFLD, `d2` = any other disease

**What you'll see:** NAFLD → "Hepatic steatosis" ← many other diseases that also cause fatty liver. This shows which diseases look similar to NAFLD.

---

## Query 5: a list instead of a picture (which liver diseases have the most symptoms?)
```cypher
MATCH (d:Disease)-[:HAS_PHENOTYPE]->(p:Phenotype)
WHERE toLower(d.name) CONTAINS 'liver' OR toLower(d.name) CONTAINS 'hepat'
   OR toLower(d.name) CONTAINS 'cirrho' OR toLower(d.name) CONTAINS 'steato'
RETURN d.name AS disease, count(p) AS phenotypes
ORDER BY phenotypes DESC LIMIT 25
```
**In simple words:** "For every liver-related disease, count its symptoms and list the top 25."
- `count(p)` → count the symptoms for each disease
- We return **names and numbers**, not dots, so you get a **table** instead of a graph

**What you'll see:** a table. The top entries are mostly **rare genetic conditions** (like mitochondrial DNA depletion syndrome, with 190 symptoms), because those are described in great detail.

---

## Important point for the paper

Common diseases like NAFLD (2 phenotypes) and obesity (6) have **very few symptoms recorded**, while rare genetic diseases have dozens. So **phenotypes add little to our NAFLD story**. That matches what your mentor said: *"these phenotypes are not very useful."* They're fine to look at, but don't build on them.
