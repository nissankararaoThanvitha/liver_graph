# Setup — getting the project running from scratch

Written for someone who has been sent the Neo4j dump and nothing else.

Rough timings: Neo4j up in ~30 minutes, the repo in ~10, the data whenever it
arrives. Steps 1–4 are the graph, 5–6 are the code, 7 is what you still need
from Thanvitha.

---

## 1. Install Neo4j Desktop 2 — not Community Edition

Download Neo4j Desktop 2 from `neo4j.com/download`.

**This specific product matters.** The dump is in `block` store format, which
only Neo4j Enterprise can read. Desktop 2 bundles an Enterprise development
licence, so it works. If you install Neo4j Community Edition instead, the load
fails and the error message will not tell you why.

**The version must be 2026.07.0 or newer.** The dump was taken from 2026.07.0,
and Neo4j will not load a dump into an older version. Newer is fine — it
migrates on load.

## 2. Load the dump

Easiest route is the Desktop 2 interface: it can create a new instance directly
from a dump file. Look for the option to create an instance from a backup or
dump file when adding an instance — dragging the `.dump` onto the instance list
also works in recent builds. Point it at the file, give the instance a password,
and let it run. It takes a few minutes; the file is ~2.4 GB.

If you would rather use the command line, stop the instance first and run
`neo4j-admin` from the instance's `bin/` folder:

```bash
neo4j-admin database load neo4j --from-path=<folder-containing-the-dump> --overwrite-destination=true
```

`--from-path` wants the *folder*, not the file itself.

## 3. Give it enough memory before you start it

The store is ~2.5 GB. Neo4j's defaults are far smaller than that, and an
undersized instance does not fail — it just crawls, and large queries die with
a transaction timeout that looks like a bug in your Cypher.

In the instance's `conf/neo4j.conf`, on a 16 GB machine:

```
server.memory.heap.initial_size=4g
server.memory.heap.max_size=4g
server.memory.pagecache.size=4g
```

Scale down if you have less; leave at least 4 GB for the operating system.
Restart the instance after editing.

## 4. Check the load worked

Open Neo4j Browser for the instance and run:

```cypher
MATCH (n) RETURN count(n)
```

You should get **126,244**.

For relationships, count one type at a time. Counting all of them in a single
query reads 35M records and will time out — that is expected, not a problem
with your setup:

```cypher
MATCH ()-[r:EXPRESSES]->() RETURN count(r)          // 32,471,042
MATCH ()-[r:ASSOCIATED_WITH]->() RETURN count(r)    //  1,832,441
MATCH ()-[r:TRACKS_FIBROSIS]->() RETURN count(r)    //      3,645
```

A per-type count hits Neo4j's internal count store and returns instantly.
Full totals: 126,244 nodes, 35,091,066 relationships.

## 5. Get the code

```bash
git clone https://github.com/nissankararaoThanvitha/liver_graph.git
cd liver_graph
pip install -r requirements.txt
```

Everything is on `main`. Built on Python 3.13.7; the pins in
`requirements.txt` are the versions the committed Paper 1 results were actually
produced with, so install them rather than the latest.

`torch` and `pykeen` are a ~2 GB install and are only needed for
`train_link_prediction.py`. Skip both if you are not touching link prediction —
and read what `CLAUDE.md` says about that model before you trust its output.

## 6. Read these, in this order

1. **`CLAUDE.md`** — the whole project in five minutes: pipeline order, the
   decisions already settled and why, the limits that must not be papered over.
   If you open this repo in Claude Code it loads automatically.
2. **`handover/README.md`** — then the four session transcripts, which are the
   arguments behind those decisions.
3. **`Paper1_Results/Task*/README.txt`** — method and caveats per analysis.

Where a transcript and `CLAUDE.md` disagree, `CLAUDE.md` wins. Where `CLAUDE.md`
and the code disagree, the code wins.

## 7. What is still missing

`data/` is 5.5 GB and none of it is in git. The graph you just loaded already
contains the built result, so you only need these to *re-run* the pipeline:

| Folder | Size | How to get it |
|---|---|---|
| `data/raw` | 104 MB | From Thanvitha, or re-download from GEO |
| `data/optimuskg` | 161 MB | Dataverse DOI `10.7910/DVN/IYNGEV` |
| `data/genesets` | 5.7 MB | **Download yourself** from MSigDB v2024.1 — KEGG-derived sets may not be redistributed, so it cannot be sent to you |

Skip `data/primekg` entirely: 937 MB and superseded by OptimusKG.

Everything else under `data/` is derived — `.gitignore` lists the rebuild
command for each folder.

## 8. Know what you have

This is a **copy**, taken 2026-10-06. It is not linked to Thanvitha's database.
Anything you change stays on your machine and anything she changes never reaches
you. If you need to work on the same graph at the same time, that needs a shared
instance instead — not two dumps.
