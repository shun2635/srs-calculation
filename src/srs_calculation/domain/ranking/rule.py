"""Common interfaces and helpers for ranking rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from ..games.coalition_game import CoalitionGame
from .result import RankingResult


class RankingRule(ABC):
    """Abstract ranking rule interface."""

    rule_id: str

    @abstractmethod
    def evaluate(self, game: CoalitionGame) -> RankingResult:
        """Evaluate the rule on an in-memory coalition game."""


def dense_rank_desc(values: Sequence[float | int]) -> dict[int, int]:
    """Assign dense ranks in descending score order."""

    order = sorted(range(len(values)), key=lambda index: (-float(values[index]), index))
    ranks: dict[int, int] = {}
    last_value: float | int | None = None
    current_rank = 0
    for index in order:
        value = values[index]
        if last_value is None or value != last_value:
            current_rank += 1
            last_value = value
        ranks[index] = current_rank
    return ranks


def dense_rank_lex_desc(vectors: Sequence[Iterable[int]]) -> dict[int, int]:
    """Assign dense ranks by lexicographic descending comparison."""

    normalized = [tuple(vector) for vector in vectors]
    order = sorted(range(len(normalized)), key=lambda index: tuple([-v for v in normalized[index]] + [index]))
    ranks: dict[int, int] = {}
    last_vector: tuple[int, ...] | None = None
    current_rank = 0
    for index in order:
        vector = normalized[index]
        if last_vector is None or vector != last_vector:
            current_rank += 1
            last_vector = vector
        ranks[index] = current_rank
    return ranks


def popcount(mask: int) -> int:
    """Return the number of set bits with Python 3.9 compatibility."""

    return bin(int(mask)).count("1")
