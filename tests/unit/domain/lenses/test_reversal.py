from __future__ import annotations

from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.lenses import generate_reversal_constraints


def _game(base_ranks_by_mask: dict[int, int]) -> CoalitionGame:
    scores = {mask: float(20 - rank) for mask, rank in base_ranks_by_mask.items()}
    return CoalitionGame.from_scores_by_mask(3, scores, base_ranks_by_mask=base_ranks_by_mask)


def test_reversal_requires_singleton_strict_difference() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 1,
            0b100: 1,
            0b011: 3,
            0b101: 2,
            0b110: 3,
            0b111: 4,
        }
    )

    constraints = generate_reversal_constraints(game, 2)

    assert constraints == ()


def test_reversal_group_strict_difference_alone_does_not_generate_constraint() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 1,
            0b100: 1,
            0b011: 3,
            0b101: 1,
            0b110: 3,
            0b111: 4,
        }
    )

    constraints = generate_reversal_constraints(game, 2)

    assert constraints == ()


def test_reversal_generates_preferred_weaker_group_when_group_is_not_worse() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 2,
            0b100: 3,
            0b011: 3,
            0b101: 1,
            0b110: 3,
            0b111: 4,
        }
    )

    constraints = generate_reversal_constraints(game, 2)

    assert (0b101, 0b011, 2) in {
        (constraint.preferred_mask, constraint.dispreferred_mask, constraint.coalition_size)
        for constraint in constraints
    }
