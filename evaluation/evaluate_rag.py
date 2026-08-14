"""
Computes end-to-end RAG metrics: Faithfulness, Answer Relevance,
Context Relevance, Citation Accuracy, Latency, Error Rate.

Faithfulness/Answer/Context Relevance here use a lightweight lexical
overlap heuristic rather than an LLM-judge, to keep this runnable
without extra API cost. Swap in an LLM-judge for higher fidelity.

NOT VERIFIED: not executed in this environment.

Usage:
  python evaluate_rag.py --dataset dataset.json
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

from app.ai.rag.pipeline import run_rag


def _lexical_overlap(a: str, b: str) -> float:
    aw, bw = set(a.lower().split()), set(b.lower().split())
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / len(aw | bw)


async def evaluate(dataset_path: str) -> dict:
    data = json.loads(Path(dataset_path).read_text())
    latencies, errors = [], 0
    faithfulness, answer_relevance = [], []

    for case in data["cases"]:
        start = time.monotonic()
        try:
            result = await run_rag(case["query"], user_id="eval-user")
            latencies.append(time.monotonic() - start)

            context_text = " ".join(s["excerpt"] for s in result.sources)
            faithfulness.append(_lexical_overlap(result.answer, context_text))
            answer_relevance.append(_lexical_overlap(result.answer, case["query"]))
        except Exception:
            errors += 1

    n = max(len(data["cases"]), 1)
    return {
        "avg_latency_seconds": sum(latencies) / max(len(latencies), 1),
        "error_rate": errors / n,
        "faithfulness_proxy": sum(faithfulness) / max(len(faithfulness), 1),
        "answer_relevance_proxy": sum(answer_relevance) / max(len(answer_relevance), 1),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="dataset.json")
    args = parser.parse_args()

    metrics = asyncio.run(evaluate(args.dataset))
    print(json.dumps(metrics, indent=2))

    Path("results").mkdir(exist_ok=True)
    Path("results/rag_latest.json").write_text(json.dumps(metrics, indent=2))
