from __future__ import annotations

import json
from pathlib import Path

import pytest

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.domain.games.coalition_game import CoalitionGame


FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "parity" / "ranking" / "first_batch_rule_expected.json"


def _load_expected_fixtures() -> dict[str, dict[str, object]]:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


EXPECTED_FIXTURES = _load_expected_fixtures()


def _fixture_case(fixture_name: str) -> tuple[str, int, dict[int, float]]:
    fixture = EXPECTED_FIXTURES[fixture_name]
    player_count = int(fixture["player_count"])
    raw_scores_by_mask = fixture["scores_by_mask"]
    assert isinstance(raw_scores_by_mask, dict)
    scores_by_mask = {int(mask): float(score) for mask, score in raw_scores_by_mask.items()}
    return fixture_name, player_count, scores_by_mask


FIXTURES = [
    _fixture_case("strict_3p"),
    _fixture_case("ties_3p"),
]


def _expected_rule_payload(fixture_name: str, rule_id: str) -> tuple[dict[int, float] | None, dict[int, int]]:
    rule_payload = EXPECTED_FIXTURES[fixture_name]["rules"][rule_id]
    assert isinstance(rule_payload, dict)
    raw_scores_by_player = rule_payload["scores_by_player"]
    raw_ranks_by_player = rule_payload["ranks_by_player"]
    assert isinstance(raw_ranks_by_player, dict)
    scores_by_player = (
        None
        if raw_scores_by_player is None
        else {int(player): float(score) for player, score in raw_scores_by_player.items()}
    )
    ranks_by_player = {int(player): int(rank) for player, rank in raw_ranks_by_player.items()}
    return scores_by_player, ranks_by_player


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
    game = CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)
    actual_result = apply_ranking_rules(game, [rule_id])[rule_id]
    expected_scores, expected_ranks = _expected_rule_payload(fixture_name, rule_id)

    if expected_scores is None:
        assert actual_result.score_set is None
    else:
        assert actual_result.score_set is not None
        for player, expected_score in expected_scores.items():
            assert actual_result.score_set.values_by_player[player] == pytest.approx(expected_score)

    assert actual_result.rank_set is not None
    assert actual_result.rank_set.ranks_by_player == expected_ranks
