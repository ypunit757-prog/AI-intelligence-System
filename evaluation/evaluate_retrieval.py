"""
Computes Recall@K, Precision@K, MRR, and Hit Rate against
evaluation/dataset.json.

NOT VERIFIED: run this yourself against a populated index — it has not
been executed in this environment.

Usage:
  python evaluate_retrieval.py --dataset dataset.json --top-k 5
"""
import argparse
import asyncio
import json
from pathlib import Path

from app.ai.embeddings.sentence_transformer_embeddings import get_embedding_model
from app.ai.retrieval.factory import get_vector_store


async def evaluate(dataset_path: str, top_k: int) -> dict:
    data = json.loads(Path(dataset_path).read_text())
    embedder = get_embedding_model()
    store = get_vector_store()

    hits, reciprocal_ranks, precisions, recalls = [], [], [], []

    for case in data["cases"]:
        query_embedding = embedder.embed_query(case["query"])
        results = await store.similarity_search(query_embedding, top_k=top_k, user_id=None)
        keywords = case.get("expected_keywords", [])

        relevant_ranks = [
            i + 1 for i, r in enumerate(results) if any(k.lower() in r["content"].lower() for k in keywords)
        ]
        hit = 1 if relevant_ranks else 0
        hits.append(hit)
        reciprocal_ranks.append(1 / relevant_ranks[0] if relevant_ranks else 0)
        precisions.append(len(relevant_ranks) / max(len(results), 1))
        recalls.append(1 if relevant_ranks else 0)  # single-relevant-doc approximation

    n = max(len(data["cases"]), 1)
    return {
        "hit_rate": sum(hits) / n,
        "mrr": sum(reciprocal_ranks) / n,
        "precision_at_k": sum(precisions) / n,
        "recall_at_k": sum(recalls) / n,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="dataset.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    metrics = asyncio.run(evaluate(args.dataset, args.top_k))
    print(json.dumps(metrics, indent=2))

    Path("results").mkdir(exist_ok=True)
    Path("results/retrieval_latest.json").write_text(json.dumps(metrics, indent=2))
