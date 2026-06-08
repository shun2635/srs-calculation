"""Reversal lens constraints for formation-value analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..games.coalition_game import CoalitionGame


@dataclass(frozen=True)
class ReversalConstraint:
    """One strict comparison required by the Reversal lens."""

    preferred_mask: int
    dispreferred_mask: int
    coalition_size: int


def _popcount(mask: int) -> int:
    return int(mask).bit_count()


def _masks_of_size(game: CoalitionGame, coalition_size: int) -> list[int]:
    return [
        int(mask)
        for mask in range(1, game.coalition_count)
        if _popcount(int(mask)) == int(coalition_size)
    ]


def _sorted_singleton_ranks(
    mask: int,
    base_rank_by_mask: dict[int, int],
    player_count: int,
) -> list[int]:
    ranks: list[int] = []
    for player in range(int(player_count)):
        singleton_mask = 1 << int(player)
        if int(mask) & singleton_mask:
            ranks.append(int(base_rank_by_mask[int(singleton_mask)]))
    ranks.sort()
    return ranks


def _weakly_dominates_with_singleton_strict(
    stronger_singleton_ranks: list[int],
    weaker_singleton_ranks: list[int],
) -> bool:
    """Return whether stronger ranks dominate weaker ranks with at least one strict gap."""

    if len(stronger_singleton_ranks) != len(weaker_singleton_ranks):
        return False

    has_strict = False
    for stronger, weaker in zip(stronger_singleton_ranks, weaker_singleton_ranks, strict=True):
        if int(stronger) > int(weaker):
            return False
        if int(stronger) < int(weaker):
            has_strict = True
    return has_strict


def generate_reversal_constraints(
    game: CoalitionGame,
    coalition_size: int,
) -> tuple[ReversalConstraint, ...]:
    """Generate Reversal constraints for one group size.

    For ordered groups (G, H), G must be weakly better than H at singleton level
    with at least one strict singleton comparison, and H must be *strictly*
    better than G at group level. The required output comparison is then H
    strictly above G. Pairs that tie at the group level are excluded, matching
    the paper's strict coalition ordering S > T. This strictness is a fixed spec
    (see application/paper_simulation/fixed_specs.py:
    REVERSAL_STRICT_GROUP_ORDERING) and must not be relaxed.
    """

    game.require_complete()
    k = int(coalition_size)
    if k < 2 or k > int(game.player_count):
        return ()

    masks = _masks_of_size(game, k)
    if len(masks) <= 1:
        return ()

    base_rank_by_mask = game.coalition_levels()
    singleton_rank_cache = {
        int(mask): _sorted_singleton_ranks(int(mask), base_rank_by_mask, int(game.player_count))
        for mask in masks
    }
    constraints: list[ReversalConstraint] = []

    for stronger_individual_mask in masks:
        stronger_singletons = singleton_rank_cache[int(stronger_individual_mask)]
        stronger_group_rank = int(base_rank_by_mask[int(stronger_individual_mask)])
        for weaker_individual_mask in masks:
            if int(weaker_individual_mask) == int(stronger_individual_mask):
                continue

            if not _weakly_dominates_with_singleton_strict(
                stronger_singletons,
                singleton_rank_cache[int(weaker_individual_mask)],
            ):
                continue

            weaker_group_rank = int(base_rank_by_mask[int(weaker_individual_mask)])
            # Strict coalition ordering S > T: tied group ranks do not fire.
            if weaker_group_rank < stronger_group_rank:
                constraints.append(
                    ReversalConstraint(
                        preferred_mask=int(weaker_individual_mask),
                        dispreferred_mask=int(stronger_individual_mask),
                        coalition_size=k,
                    )
                )

    return tuple(constraints)


def generate_reversal_constraints_by_size(
    game: CoalitionGame,
    target_sizes: Iterable[int],
) -> dict[int, tuple[ReversalConstraint, ...]]:
    """Generate Reversal constraints for multiple group sizes."""

    return {
        int(coalition_size): generate_reversal_constraints(game, int(coalition_size))
        for coalition_size in target_sizes
    }


__all__ = [
    "ReversalConstraint",
    "generate_reversal_constraints",
    "generate_reversal_constraints_by_size",
]
