import json

import pytest

from app.domain.movie import make_movie_id
from app.evaluation.golden import load_golden_set
from app.evaluation.metrics import (
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
    sweep_thresholds,
)
from app.scripts.evaluate import report


def test_recall_caps_denominator_at_k():
    assert recall_at_k(["a", "x", "y"], {"a", "b", "c", "d"}, k=2) == 0.5
    assert recall_at_k(["a", "b"], {"a", "b", "c", "d"}, k=2) == 1.0


def test_ndcg_rewards_relevant_items_ranked_first():
    best = ndcg_at_k(["a", "x"], {"a"}, k=2)
    worse = ndcg_at_k(["x", "a"], {"a"}, k=2)

    assert best == pytest.approx(1.0)
    assert worse == pytest.approx(1 / 1.585, abs=1e-3)


def test_metrics_reject_negative_queries():
    with pytest.raises(ValueError):
        recall_at_k(["a"], set(), k=1)


def test_reciprocal_rank():
    assert reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["x"], {"a"}) == 0.0


def test_sweep_trades_recall_for_precision_and_counts_noisy_negatives():
    results = [
        ([("a", 0.6), ("x", 0.45)], {"a"}),  # positive query
        ([("y", 0.40)], set()),  # negative query
    ]

    low, high = sweep_thresholds(results, [0.35, 0.5], k=5)

    assert (low.precision, low.recall, low.false_positive_negatives) == (1 / 3, 1.0, 1)
    assert (high.precision, high.recall, high.false_positive_negatives) == (1.0, 1.0, 0)


def test_load_golden_set_resolves_ids_like_the_mapper(tmp_path):
    path = tmp_path / "golden.jsonl"
    path.write_text(
        json.dumps({"query": "q", "relevant": [["Lavra dor", 1968]], "basis": "b"})
        + "\n"
        + json.dumps({"query": "neg", "relevant": []})
        + "\n",
        encoding="utf-8",
    )

    positive, negative = load_golden_set(path)

    assert positive.relevant_ids == {make_movie_id("Lavra dor", 1968)}
    assert negative.is_negative


def test_load_golden_set_reports_bad_line(tmp_path):
    path = tmp_path / "golden.jsonl"
    path.write_text('{"query": "q"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="golden.jsonl:1"):
        load_golden_set(path)


def test_report_renders_metrics_and_sweep(tmp_path):
    path = tmp_path / "golden.jsonl"
    path.write_text(
        json.dumps({"query": "q", "relevant": [["A", 2000]]})
        + "\n"
        + json.dumps({"query": "neg", "relevant": []})
        + "\n",
        encoding="utf-8",
    )
    golden = load_golden_set(path)
    a = make_movie_id("A", 2000)

    text = report(golden, [[(a, 0.7)], [("z", 0.2)]], k=5)

    assert "| Recall@5 | 1.000 |" in text
    assert "← best F1" in text


def test_repository_golden_set_is_well_formed():
    from pathlib import Path

    golden = load_golden_set(Path("tests/eval/golden.jsonl"))

    assert len(golden) >= 20
    assert any(q.is_negative for q in golden)
    assert len({q.query for q in golden}) == len(golden)
