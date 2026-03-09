"""Structured ranking outputs for the new domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class RuleScoreSet:
    """Score output of a ranking rule."""

    scope: str
    values_by_entity: dict[int, float]

    @classmethod
    def from_player_mapping(cls, values_by_player: Mapping[int, float]) -> "RuleScoreSet":
        return cls(
            scope="player",
            values_by_entity={int(player): float(value) for player, value in values_by_player.items()},
        )

    @classmethod
    def from_coalition_mapping(cls, values_by_coalition: Mapping[int, float]) -> "RuleScoreSet":
        return cls(
            scope="coalition",
            values_by_entity={int(mask): float(value) for mask, value in values_by_coalition.items()},
        )

    @classmethod
    def from_mapping(cls, values_by_player: Mapping[int, float]) -> "RuleScoreSet":
        """Backward-compatible alias for player-scoped score sets."""

        return cls.from_player_mapping(values_by_player)

    @property
    def values_by_player(self) -> dict[int, float]:
        if self.scope != "player":
            raise ValueError("score set is not player-scoped")
        return dict(self.values_by_entity)

    @property
    def values_by_coalition(self) -> dict[int, float]:
        if self.scope != "coalition":
            raise ValueError("score set is not coalition-scoped")
        return dict(self.values_by_entity)


@dataclass(frozen=True)
class RuleRankSet:
    """Rank output of a ranking rule."""

    scope: str
    ranks_by_entity: dict[int, int]

    @classmethod
    def from_player_mapping(cls, ranks_by_player: Mapping[int, int]) -> "RuleRankSet":
        return cls(
            scope="player",
            ranks_by_entity={int(player): int(rank) for player, rank in ranks_by_player.items()},
        )

    @classmethod
    def from_coalition_mapping(cls, ranks_by_coalition: Mapping[int, int]) -> "RuleRankSet":
        return cls(
            scope="coalition",
            ranks_by_entity={int(mask): int(rank) for mask, rank in ranks_by_coalition.items()},
        )

    @classmethod
    def from_mapping(cls, ranks_by_player: Mapping[int, int]) -> "RuleRankSet":
        """Backward-compatible alias for player-scoped rank sets."""

        return cls.from_player_mapping(ranks_by_player)

    @property
    def ranks_by_player(self) -> dict[int, int]:
        if self.scope != "player":
            raise ValueError("rank set is not player-scoped")
        return dict(self.ranks_by_entity)

    @property
    def ranks_by_coalition(self) -> dict[int, int]:
        if self.scope != "coalition":
            raise ValueError("rank set is not coalition-scoped")
        return dict(self.ranks_by_entity)


@dataclass(frozen=True)
class RankingResult:
    """Rule evaluation result detached from table mutation concerns."""

    rule_id: str
    score_set: RuleScoreSet | None = None
    rank_set: RuleRankSet | None = None
    auxiliary_score_sets: dict[str, RuleScoreSet] = field(default_factory=dict)

    def has_scores(self) -> bool:
        return self.score_set is not None

    def has_ranks(self) -> bool:
        return self.rank_set is not None
