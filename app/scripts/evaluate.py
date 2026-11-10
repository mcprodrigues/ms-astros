"""
Evaluate search quality on the golden set against the running index.

Usage: uv run python -m app.scripts.evaluate [--k 5] [--golden tests/eval/golden.jsonl]

Reports Recall@k, nDCG@k and MRR on positive queries, plus a min_score sweep
(micro precision/recall of what the API would return) to calibrate
MIN_SCORE_THRESHOLD. Requires Weaviate up and the index loaded.
"""

import argparse
import logging
from pathlib import Path
from statistics import mean

from app.evaluation.golden import GoldenQuery, load_golden_set
from app.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank, sweep_thresholds
from app.providers.pipelines.interfaces import ISearchPipeline

POOL = 20  # candidates fetched per query; >= any k used below


def run_queries(
    pipeline: ISearchPipeline, golden: list[GoldenQuery]
) -> list[list[tuple[str, float]]]:
    return [[(doc.id, doc.score) for doc in pipeline.search(q.query, top_k=POOL)] for q in golden]


def report(golden: list[GoldenQuery], results: list[list[tuple[str, float]]], k: int) -> str:
    positives = [(q, r) for q, r in zip(golden, results, strict=True) if not q.is_negative]
    lines = [f"## Ranking quality ({len(positives)} positive queries, k={k})", ""]
    rows = []
    for q, ranked in positives:
        ids = [doc for doc, _ in ranked]
        rows.append(
            (
                q.query,
                recall_at_k(ids, q.relevant_ids, k),
                ndcg_at_k(ids, q.relevant_ids, k),
                reciprocal_rank(ids, q.relevant_ids),
            )
        )
    lines += [
        f"| Metric | Value |\n|---|---|\n| Recall@{k} | {mean(r[1] for r in rows):.3f} |",
        f"| nDCG@{k} | {mean(r[2] for r in rows):.3f} |",
        f"| MRR | {mean(r[3] for r in rows):.3f} |",
        "",
        f"| Query | Recall@{k} | nDCG@{k} | RR |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| {r[0]} | {r[1]:.2f} | {r[2]:.2f} | {r[3]:.2f} |"
        for r in sorted(rows, key=lambda r: r[2])
    ]

    thresholds = [round(0.30 + 0.02 * i, 2) for i in range(16)]
    sweep = sweep_thresholds(
        [(ranked, set(q.relevant_ids)) for q, ranked in zip(golden, results, strict=True)],
        thresholds,
        k,
    )
    negatives = sum(q.is_negative for q in golden)
    best = max(sweep, key=lambda p: p.f1)
    lines += [
        "",
        f"## min_score sweep (top {k}, {negatives} negative queries)",
        "",
        "| min_score | Precision | Recall | F1 | Negatives with results |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {p.threshold:.2f}{' ← best F1' if p is best else ''} | {p.precision:.3f} | "
        f"{p.recall:.3f} | {p.f1:.3f} | {p.false_positive_negatives}/{negatives} |"
        for p in sweep
    ]
    return "\n".join(lines)


def main() -> None:
    from app.dependencies import build_container
    from app.settings import Settings

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--golden", type=Path, default=Path("tests/eval/golden.jsonl"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    golden = load_golden_set(args.golden)
    container = build_container(Settings())
    try:
        print(report(golden, run_queries(container.search_pipeline, golden), args.k))
    finally:
        container.close()


if __name__ == "__main__":
    main()
