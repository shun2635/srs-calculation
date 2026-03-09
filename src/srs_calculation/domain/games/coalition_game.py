"""In-memory coalition game model independent of CSV or DataFrame concerns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CoalitionGame:
    """Immutable cooperative game backed by coalition bitmasks."""

    player_count: int
    scores_by_mask: dict[int, float]

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

        object.__setattr__(self, "scores_by_mask", normalized)

    @classmethod
    def from_scores_by_mask(
        cls,
        player_count: int,
        scores_by_mask: Mapping[int, float],
    ) -> "CoalitionGame":
        """Build a game from an arbitrary mapping."""

        return cls(player_count=player_count, scores_by_mask=dict(scores_by_mask))

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
