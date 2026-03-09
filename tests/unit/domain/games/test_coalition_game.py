from __future__ import annotations

import pytest

from srs_calculation.domain.games.coalition_game import CoalitionGame


def test_coalition_game_normalizes_scores_and_exposes_helpers() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=2,
        scores_by_mask={
            0: 0,
            1: 1,
            2: 2.5,
            3: 4,
        },
    )

    assert game.scores_by_mask == {
        0: 0.0,
        1: 1.0,
        2: 2.5,
        3: 4.0,
    }
    assert list(game.coalition_masks()) == [0, 1, 2, 3]
    assert game.coalition_members(0) == ()
    assert game.coalition_members(3) == (0, 1)
    assert game.is_complete() is True
    assert game.coalition_value(2) == 2.5
    assert game.coalition_value_or(99, default=-1.0) == -1.0


def test_coalition_game_reports_missing_masks() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=2,
        scores_by_mask={
            0: 0.0,
            1: 1.0,
            3: 4.0,
        },
    )

    assert game.is_complete() is False
    assert game.missing_masks() == [2]

    with pytest.raises(ValueError, match=r"missing 1 coalition\(s\)"):
        game.require_complete()


def test_coalition_game_rejects_out_of_range_masks() -> None:
    with pytest.raises(ValueError, match="coalition mask out of range"):
        CoalitionGame.from_scores_by_mask(
            player_count=2,
            scores_by_mask={
                0: 0.0,
                4: 1.0,
            },
        )
