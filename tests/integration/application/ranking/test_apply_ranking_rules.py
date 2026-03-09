from __future__ import annotations

import pytest

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.domain.games.coalition_game import CoalitionGame


def test_apply_ranking_rules_returns_results_for_requested_rules() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=2,
        scores_by_mask={
            0: 0.0,
            1: 1.0,
            2: 2.0,
            3: 4.0,
        },
    )

    results = apply_ranking_rules(game, ["shapley", "lexcel"])

    assert list(results) == ["shapley", "lexcel"]

    shapley = results["shapley"]
    assert shapley.rule_id == "shapley"
    assert shapley.has_scores() is True
    assert shapley.has_ranks() is True
    assert shapley.score_set is not None
    assert shapley.rank_set is not None
    assert shapley.score_set.values_by_player == pytest.approx({0: 1.25, 1: 2.75})
    assert shapley.rank_set.ranks_by_player == {1: 1, 0: 2}

    lexcel = results["lexcel"]
    assert lexcel.rule_id == "lexcel"
    assert lexcel.has_scores() is False
    assert lexcel.has_ranks() is True
    assert lexcel.rank_set is not None
    assert lexcel.rank_set.ranks_by_player == {1: 1, 0: 2}


def test_apply_ranking_rules_propagates_incomplete_game_validation() -> None:
    incomplete_game = CoalitionGame.from_scores_by_mask(
        player_count=2,
        scores_by_mask={
            0: 0.0,
            1: 1.0,
            3: 4.0,
        },
    )

    with pytest.raises(ValueError, match=r"missing 1 coalition\(s\)"):
        apply_ranking_rules(incomplete_game, ["shapley"])


def test_apply_ranking_rules_raises_for_unknown_rule_id() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=1,
        scores_by_mask={
            0: 0.0,
            1: 1.0,
        },
    )

    with pytest.raises(KeyError, match="unknown rule_id 'missing'"):
        apply_ranking_rules(game, ["missing"])
