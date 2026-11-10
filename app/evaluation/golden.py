"""Golden set: queries with human relevance judgments, keyed by (title, year)."""

import json
from dataclasses import dataclass
from pathlib import Path

from app.domain.movie import make_movie_id


@dataclass(frozen=True)
class GoldenQuery:
    query: str
    relevant_ids: frozenset[str]
    relevant_titles: tuple[str, ...]
    basis: str

    @property
    def is_negative(self) -> bool:
        return not self.relevant_ids


def load_golden_set(path: Path) -> list[GoldenQuery]:
    queries = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            relevant = [(title, year) for title, year in item["relevant"]]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            raise ValueError(f"{path}:{line_number}: invalid golden entry ({e})") from e
        queries.append(
            GoldenQuery(
                query=item["query"],
                relevant_ids=frozenset(make_movie_id(t, y) for t, y in relevant),
                relevant_titles=tuple(t for t, _ in relevant),
                basis=item.get("basis", ""),
            )
        )
    return queries
