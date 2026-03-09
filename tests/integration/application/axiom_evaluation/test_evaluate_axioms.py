from __future__ import annotations

import pytest

from srs_calculation.application.axiom_evaluation import (
    evaluate_axioms_for_ranking_result,
    evaluate_axioms_for_results,
)
from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.ranking.result import RankingResult, RuleRankSet


def test_evaluate_axioms_for_coalition_ranking_result_returns_default_axioms() -> None:
    game = CoalitionGame.from_scores_by_mask(
        3,
        {
            0b000: 0.0,
            0b001: 1.0,
            0b010: 1.0,
            0b011: 1.0,
            0b100: 1.0,
            0b101: 1.0,
            0b110: 1.0,
            0b111: 1.0,
        },
        base_ranks_by_mask={
            0b000: 1,
            0b001: 1,
            0b010: 1,
            0b011: 1,
            0b100: 1,
            0b101: 1,
            0b110: 1,
            0b111: 1,
        },
    )
    ranking_result = RankingResult(
        rule_id="group_shapley",
        rank_set=RuleRankSet.from_coalition_mapping(
            {
                0b001: 1,
                0b010: 1,
                0b011: 1,
                0b100: 1,
                0b101: 1,
                0b110: 1,
                0b111: 1,
            }
        ),
    )

    evaluations = evaluate_axioms_for_ranking_result(game, ranking_result, max_examples=2)

    assert set(evaluations) == {
        "gekokujou-2p",
        "gekokujou-weak-n",
        "give-2p",
        "take-2p",
        "give-weak-n",
        "take-weak-n",
        "redundancy",
    }
    assert evaluations["redundancy"].constrained_comparisons == 9
    assert evaluations["redundancy"].satisfied_comparisons == 9
    assert evaluations["redundancy"].violation_examples == ()


def test_evaluate_axioms_skips_player_scoped_results_in_bulk() -> None:
    game = CoalitionGame.from_scores_by_mask(
        2,
        {
            0b00: 0.0,
            0b01: 1.0,
            0b10: 1.0,
            0b11: 2.0,
        },
    )
    results = {
        "shapley": RankingResult(
            rule_id="shapley",
            rank_set=RuleRankSet.from_player_mapping({0: 1, 1: 1}),
        ),
        "group_shapley": RankingResult(
            rule_id="group_shapley",
            rank_set=RuleRankSet.from_coalition_mapping({0b01: 1, 0b10: 1, 0b11: 1}),
        ),
    }

    evaluations = evaluate_axioms_for_results(game, results)

    assert list(evaluations) == ["group_shapley"]


def test_evaluate_axioms_rejects_player_scoped_result() -> None:
    game = CoalitionGame.from_scores_by_mask(
        2,
        {
            0b00: 0.0,
            0b01: 1.0,
            0b10: 1.0,
            0b11: 2.0,
        },
    )
    ranking_result = RankingResult(
        rule_id="shapley",
        rank_set=RuleRankSet.from_player_mapping({0: 1, 1: 1}),
    )

    with pytest.raises(ValueError, match="coalition-scoped ranks"):
        evaluate_axioms_for_ranking_result(game, ranking_result)
