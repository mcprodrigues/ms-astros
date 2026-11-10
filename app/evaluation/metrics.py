"""Retrieval metrics with binary relevance. Pure functions over ranked IDs."""

import math
from collections.abc import Sequence
from dataclasses import dataclass


def recall_at_k(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    """Share of relevant items in the top k, out of min(k, |relevant|)."""
    if not relevant:
        raise ValueError("recall is undefined for queries without relevant items")
    hits = len(set(ranked[:k]) & relevant)
    return hits / min(k, len(relevant))


def ndcg_at_k(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    if not relevant:
        raise ValueError("nDCG is undefined for queries without relevant items")
    dcg = sum(1 / math.log2(i + 2) for i, doc in enumerate(ranked[:k]) if doc in relevant)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return dcg / ideal


def reciprocal_rank(ranked: Sequence[str], relevant: set[str]) -> float:
    return next((1 / (i + 1) for i, doc in enumerate(ranked) if doc in relevant), 0.0)


@dataclass(frozen=True)
class ThresholdPoint:
    threshold: float
    precision: float
    recall: float
    f1: float
    false_positive_negatives: int  # negative queries that still returned something


def sweep_thresholds(
    scored_results: Sequence[tuple[Sequence[tuple[str, float]], set[str]]],
    thresholds: Sequence[float],
    k: int,
) -> list[ThresholdPoint]:
    """
    Micro-averaged precision/recall of what the API would return (top k, score >= t).

    `scored_results` holds, per query, the ranked (id, score) list and the
    relevant set; an empty relevant set marks a negative (out-of-domain) query.
    """
    points = []
    for t in thresholds:
        tp = returned = expected = noisy_negatives = 0
        for ranked, relevant in scored_results:
            kept = [doc for doc, score in ranked[:k] if score >= t]
            returned += len(kept)
            tp += len(set(kept) & relevant)
            expected += min(k, len(relevant))
            noisy_negatives += int(not relevant and bool(kept))
        precision = tp / returned if returned else 1.0
        recall = tp / expected if expected else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        points.append(ThresholdPoint(t, precision, recall, f1, noisy_negatives))
    return points
