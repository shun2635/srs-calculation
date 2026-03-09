"""In-memory coalition game model independent of CSV or DataFrame concerns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CoalitionGame:
    """Immutable cooperative game backed by coalition bitmasks."""

    player_count: int
    scores_by_mask: dict[int, float]
    base_ranks_by_mask: dict[int, int] | None = None

    def __post_init__(self) -> None:
        if self.player_count < 0:
            raise ValueError("player_count must be non-negative")

        max_mask = 1 << self.player_count
        normalized: dict[int, float] = {}
        for raw_mask, raw_score in self.scores_by_mask.items():
            mask = int(raw_mask)
            if mask < 0 or mask >= max_mask:
                raise ValueError(f"coalition mask out of range for {self.player_count} players: {mask}")
            normalized[mask] = float(raw_score)

        normalized_ranks = self._normalize_base_ranks_by_mask(
            player_count=self.player_count,
            scores_by_mask=normalized,
            base_ranks_by_mask=self.base_ranks_by_mask,
        )

        object.__setattr__(self, "scores_by_mask", normalized)
        object.__setattr__(self, "base_ranks_by_mask", normalized_ranks)

    @classmethod
    def from_scores_by_mask(
        cls,
        player_count: int,
        scores_by_mask: Mapping[int, float],
        base_ranks_by_mask: Mapping[int, int] | None = None,
    ) -> "CoalitionGame":
        """Build a game from an arbitrary mapping."""

        return cls(
            player_count=player_count,
            scores_by_mask=dict(scores_by_mask),
            base_ranks_by_mask=None if base_ranks_by_mask is None else dict(base_ranks_by_mask),
        )

    @staticmethod
    def _dense_base_ranks(scores_by_mask: Mapping[int, float]) -> dict[int, int]:
        ordered_masks = sorted(scores_by_mask, key=lambda mask: (-float(scores_by_mask[int(mask)]), int(mask)))
        ranks: dict[int, int] = {}
        current_rank = 0
        last_score: float | None = None
        for mask in ordered_masks:
            score = float(scores_by_mask[int(mask)])
            if last_score is None or score != last_score:
                current_rank += 1
                last_score = score
            ranks[int(mask)] = current_rank
        return ranks

    @classmethod
    def _normalize_base_ranks_by_mask(
        cls,
        *,
        player_count: int,
        scores_by_mask: Mapping[int, float],
        base_ranks_by_mask: Mapping[int, int] | None,
    ) -> dict[int, int]:
        max_mask = 1 << int(player_count)
        if base_ranks_by_mask is None:
            return cls._dense_base_ranks(scores_by_mask)

        normalized: dict[int, int] = {}
        for raw_mask, raw_rank in base_ranks_by_mask.items():
            mask = int(raw_mask)
            rank = int(raw_rank)
            if mask < 0 or mask >= max_mask:
                raise ValueError(f"coalition rank mask out of range for {player_count} players: {mask}")
            if mask not in scores_by_mask:
                raise ValueError(f"coalition rank mask missing from score table: {mask}")
            if rank <= 0:
                raise ValueError(f"coalition base rank must be positive: mask={mask} rank={rank}")
            normalized[mask] = rank

        missing = [mask for mask in scores_by_mask if mask not in normalized]
        if missing:
            raise ValueError(
                "base_ranks_by_mask must cover the same coalition masks as scores_by_mask; "
                f"missing {len(missing)} mask(s), e.g. {missing[:5]}"
            )
        return normalized

    @property
    def coalition_count(self) -> int:
        """Return the number of coalitions in a complete game."""

        return 1 << self.player_count

    def coalition_masks(self) -> Iterable[int]:
        """Iterate over present coalition masks in ascending bitmask order."""

        return iter(sorted(self.scores_by_mask))

    def coalition_value(self, mask: int) -> float:
        """Return the coalition value and fail if the coalition is absent."""

        return self.scores_by_mask[int(mask)]

    def coalition_value_or(self, mask: int, default: float = 0.0) -> float:
        """Return the coalition value or a default for incomplete inputs."""

        return float(self.scores_by_mask.get(int(mask), default))

    def coalition_rank(self, mask: int) -> int:
        """Return the serialized base rank / level for a coalition mask."""

        assert self.base_ranks_by_mask is not None
        return int(self.base_ranks_by_mask[int(mask)])

    def coalition_rank_or(self, mask: int, default: int = 0) -> int:
        """Return the serialized base rank or a default for incomplete inputs."""

        assert self.base_ranks_by_mask is not None
        return int(self.base_ranks_by_mask.get(int(mask), int(default)))

    def coalition_members(self, mask: int) -> tuple[int, ...]:
        """Return the players that belong to a coalition mask."""

        normalized_mask = int(mask)
        return tuple(
            player for player in range(self.player_count) if (normalized_mask >> player) & 1
        )

    def missing_masks(self) -> list[int]:
        """Return missing coalition masks if the game is incomplete."""

        return [mask for mask in range(self.coalition_count) if mask not in self.scores_by_mask]

    def is_complete(self) -> bool:
        """Return whether every coalition mask is present."""

        return not self.missing_masks()

    def require_complete(self) -> None:
        """Validate that every coalition is present."""

        missing = self.missing_masks()
        if missing:
            raise ValueError(
                "complete coalition game required; "
                f"missing {len(missing)} coalition(s), e.g. {missing[:5]}"
            )

    def coalition_levels(self) -> dict[int, int]:
        """Return a copy of the serialized base ranks / levels."""

        assert self.base_ranks_by_mask is not None
        return {int(mask): int(rank) for mask, rank in self.base_ranks_by_mask.items()}
