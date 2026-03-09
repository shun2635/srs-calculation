from __future__ import annotations

import pytest

from gamegen.rules import banzhaf as legacy_banzhaf
from gamegen.rules import lexcel as legacy_lexcel
from gamegen.rules import ordinal_banzhaf as legacy_ordinal_banzhaf
from gamegen.rules import shapley as legacy_shapley

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.domain.games.coalition_game import CoalitionGame


FIXTURES = [
    (
        "strict_3p",
        3,
        {
            0b000: 0.0,
            0b001: 4.0,
            0b010: 3.0,
            0b011: 7.0,
            0b100: 2.0,
            0b101: 6.0,
            0b110: 5.0,
            0b111: 8.0,
        },
    ),
    (
        "ties_3p",
        3,
        {
            0b000: 0.0,
            0b001: 1.0,
            0b010: 1.0,
            0b011: 2.0,
            0b100: 1.0,
            0b101: 2.0,
            0b110: 2.0,
            0b111: 2.0,
        },
    ),
]


def _legacy_expected(rule_id: str, scores_by_mask: dict[int, float], player_count: int) -> tuple[dict[int, float] | None, dict[int, int]]:
    if rule_id == "shapley":
        scores = {
            player: score
            for player, score in enumerate(
                legacy_shapley.player_shapley_values(scores_by_mask, player_count)
            )
        }
        ranks = legacy_shapley.rank_by_shapley(scores_by_mask, player_count)
        return scores, ranks

    if rule_id == "banzhaf":
        scores = {
            player: score
            for player, score in enumerate(
                legacy_banzhaf.player_banzhaf_values(scores_by_mask, player_count)
            )
        }
        ranks = legacy_banzhaf.rank_by_banzhaf(scores_by_mask, player_count)
        return scores, ranks

    if rule_id == "lexcel":
        ranks = legacy_lexcel.rank_by_lexcel(scores_by_mask, player_count)
        return None, ranks

    if rule_id == "ordinal_banzhaf":
        levels = legacy_ordinal_banzhaf.build_levels_from_scores(scores_by_mask)
        detail = legacy_ordinal_banzhaf.ordinal_banzhaf_detail(levels, player_count)
        scores = {player: float(values["s"]) for player, values in detail.items()}
        ranks = legacy_ordinal_banzhaf.rank_by_ordinal_banzhaf_from_scores(
            scores_by_mask,
            player_count,
        )
        return scores, ranks

    raise AssertionError(f"unsupported rule_id: {rule_id}")


@pytest.mark.parametrize(
    ("fixture_name", "player_count", "scores_by_mask"),
    FIXTURES,
    ids=[fixture[0] for fixture in FIXTURES],
)
@pytest.mark.parametrize(
    "rule_id",
    ["shapley", "banzhaf", "lexcel", "ordinal_banzhaf"],
)
def test_first_batch_rules_match_legacy_outputs(
    fixture_name: str,
    player_count: int,
    scores_by_mask: dict[int, float],
    rule_id: str,
) -> None:
    del fixture_name

    game = CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)
    actual_result = apply_ranking_rules(game, [rule_id])[rule_id]
    expected_scores, expected_ranks = _legacy_expected(rule_id, scores_by_mask, player_count)

    if expected_scores is None:
        assert actual_result.score_set is None
    else:
        assert actual_result.score_set is not None
        for player, expected_score in expected_scores.items():
            assert actual_result.score_set.values_by_player[player] == pytest.approx(expected_score)

    assert actual_result.rank_set is not None
    assert actual_result.rank_set.ranks_by_player == expected_ranks
