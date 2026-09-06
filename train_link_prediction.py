"""
train_link_prediction.py
------------------------
Trains a knowledge-graph embedding model on the triples and predicts the one
link that does not exist for any drug: which drug treats liver disease.

THE IDEA
The model gives every entity a position in a vector space, adjusted until
connected things sit near each other. Two entities that end up close without
an edge between them are the prediction: the graph's structure implies a
connection nobody has recorded.

That is why our TRACKS_FIBROSIS / TRACKS_INFLAMMATION edges matter here.
Without them NAFLD is connected only to what the literature already says, and
sits far from most drugs. Our 6,384 patient-derived edges pull it towards the
genes our own cohort implicates, so drugs acting on those genes land nearby.

WHY ComplEx
The graph is directional and multi-relational: ACTS_ON, ASSOCIATED_WITH and
TREATS behave differently, and A-treats-B does not imply B-treats-A. TransE
models relations as translation and handles one-to-many badly -- and
INDICATION is heavily one-to-many, since one drug treats many diseases.
ComplEx uses complex-valued embeddings, so it represents asymmetric and
one-to-many relations without that failure, at similar cost on CPU.

HONEST EVALUATION
Scores mean nothing on their own, so the run is judged two ways:

  1. Held-out test set (10% never seen in training). Hits@10 says how often
     the true answer lands in the model's top ten.
  2. A liver-specific check: hide nothing, but ask where the 95 drugs already
     known to treat NAFLD rank among all 12,025. If known drugs do not float
     to the top, the novel predictions are noise and must be discarded.

Only if both hold do the new candidates mean anything -- and even then they
are hypotheses for a lab to test, not findings.

Usage:
    python train_link_prediction.py [--epochs 40] [--dim 128]
"""

import argparse
import os

import pandas as pd
import torch
from pykeen.models import ComplEx
from pykeen.pipeline import pipeline
from pykeen.predict import predict_target
from pykeen.triples import TriplesFactory

TRIPLES = "data/kg_triples"
OUT = "data/prediction"

# the liver diseases we care about, as they appear in the triples
LIVER = {
    "dis:EFO_0003095": "non-alcoholic fatty liver disease",
    "dis:EFO_1001249": "non-alcoholic steatohepatitis",
    "dis:EFO_0001422": "cirrhosis of liver",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--batch", type=int, default=8192)
    # Ranking every test triple against all 65k entities runs at ~100
    # triples/s on CPU, so the full 129k test set costs ~20 minutes -- longer
    # than a short training run. A random sample gives the same metrics to
    # within a fraction of a percent at a twentieth of the cost.
    ap.add_argument("--eval-sample", type=int, default=0,
                    help="evaluate on N random test triples (0 = all)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    torch.set_num_threads(os.cpu_count() or 8)

    train = TriplesFactory.from_path(f"{TRIPLES}/train.tsv")
    valid = TriplesFactory.from_path(f"{TRIPLES}/valid.tsv",
                                     entity_to_id=train.entity_to_id,
                                     relation_to_id=train.relation_to_id)
    test = TriplesFactory.from_path(f"{TRIPLES}/test.tsv",
                                    entity_to_id=train.entity_to_id,
                                    relation_to_id=train.relation_to_id)
    if args.eval_sample and args.eval_sample < test.num_triples:
        import numpy as np
        rng = np.random.default_rng(42)
        pick = rng.choice(test.num_triples, args.eval_sample, replace=False)
        test = test.clone_and_exchange_triples(test.mapped_triples[pick])
        vpick = rng.choice(valid.num_triples,
                           min(args.eval_sample, valid.num_triples),
                           replace=False)
        valid = valid.clone_and_exchange_triples(valid.mapped_triples[vpick])

    print(f"train {train.num_triples:,}  valid {valid.num_triples:,}  "
          f"test {test.num_triples:,}")
    print(f"entities {train.num_entities:,}  relations {train.num_relations}")

    result = pipeline(
        training=train, validation=valid, testing=test,
        model=ComplEx,
        model_kwargs=dict(embedding_dim=args.dim),
        training_kwargs=dict(num_epochs=args.epochs,
                             batch_size=args.batch,
                             use_tqdm_batch=False),
        negative_sampler_kwargs=dict(num_negs_per_pos=8),
        random_seed=42,
        device="cpu",
    )

    m = result.metric_results.to_dict()
    print("\n=== HELD-OUT TEST PERFORMANCE ===")
    for k in ("hits_at_1", "hits_at_3", "hits_at_10",
              "inverse_harmonic_mean_rank"):
        try:
            print(f"  {k:28s} {result.get_metric(k):.4f}")
        except Exception:
            pass

    result.save_to_directory(f"{OUT}/model")

    # ---- predict TREATS for each liver disease ---------------------------
    all_tf = TriplesFactory.from_path(f"{TRIPLES}/all.tsv",
                                      entity_to_id=train.entity_to_id,
                                      relation_to_id=train.relation_to_id)
    for did, name in LIVER.items():
        if did not in train.entity_to_id:
            print(f"\n[skip] {name}: not in training graph")
            continue
        pred = predict_target(model=result.model, relation="INDICATION",
                              tail=did, triples_factory=train)
        df = pred.df
        # keep drugs only; the head of INDICATION is always a drug
        df = df[df["head_label"].str.startswith("drug:")].copy()
        df = df.add_prefix("").rename(columns={"head_label": "drug",
                                               "score": "score"})
        known = set(
            all_tf.triples[(all_tf.triples[:, 1] == "INDICATION") &
                           (all_tf.triples[:, 2] == did)][:, 0])
        df["already_known"] = df["drug"].isin(known)
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1
        df.to_csv(f"{OUT}/predicted_{did.replace(':', '_')}.csv", index=False)

        k = df[df.already_known]
        print(f"\n=== {name} ===")
        print(f"  drugs scored          : {len(df):,}")
        print(f"  already known to treat: {len(k)}")
        if len(k):
            print(f"  median rank of known  : {int(k['rank'].median()):,} "
                  f"of {len(df):,}")
            print(f"  known in top 100      : {int((k['rank'] <= 100).sum())}"
                  f" of {len(k)}")
        top = df[~df.already_known].head(10)
        print("  top NEW candidates:")
        for r in top.itertuples():
            print(f"    {r.rank:>5}  {r.drug.replace('drug:', ''):28s} "
                  f"{r.score:.3f}")


if __name__ == "__main__":
    main()
