"""Structured ranking outputs for the new domain layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RuleScoreSet:
    """Per-player score output of a ranking rule."""

    column_name: str
    values_by_player: dict[int, float]

    @classmethod
    def from_mapping(cls, column_name: str, values_by_player: Mapping[int, float]) -> "RuleScoreSet":
        return cls(
            column_name=column_name,
            values_by_player={int(player): float(value) for player, value in values_by_player.items()},
        )


@dataclass(frozen=True)
class RuleRankSet:
    """Per-player rank output of a ranking rule."""

    column_name: str
    ranks_by_player: dict[int, int]

    @classmethod
    def from_mapping(cls, column_name: str, ranks_by_player: Mapping[int, int]) -> "RuleRankSet":
        return cls(
            column_name=column_name,
            ranks_by_player={int(player): int(rank) for player, rank in ranks_by_player.items()},
        )


@dataclass(frozen=True)
class RankingResult:
    """Rule evaluation result detached from table mutation concerns."""

    rule_id: str
    score_set: RuleScoreSet | None = None
    rank_set: RuleRankSet | None = None

    def has_scores(self) -> bool:
        return self.score_set is not None

    def has_ranks(self) -> bool:
        return self.rank_set is not None
