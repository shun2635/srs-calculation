from __future__ import annotations

import csv

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.ranking.registry import build_default_ranking_rule_registry
from srs_calculation.infrastructure.persistence.csv_ranking_repository import write_compatible_rankings_csv


def _rows_by_mask(path) -> dict[int, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [row for row in reader]

    out: dict[int, dict[str, str]] = {}
    for row in rows:
        mask = 0
        player_columns = [name for name in row if name.startswith("player")]
        for index, column_name in enumerate(player_columns):
            if str(row[column_name]).strip() == "1":
                mask |= 1 << index
        out[mask] = row
    return out


def test_all_legacy_rules_can_be_serialized_to_compatible_rankings_csv(tmp_path) -> None:
    game = CoalitionGame.from_scores_by_mask(
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
    )
    registry = build_default_ranking_rule_registry()
    results = apply_ranking_rules(game, registry.list_rule_ids(), registry=registry)

    assert len(results) == 14
    assert results["group_shapley"].rank_set is not None
    assert results["group_shapley"].rank_set.scope == "coalition"
    assert results["shapley"].rank_set is not None
    assert results["shapley"].rank_set.scope == "player"

    output_path = tmp_path / "rankings.csv"
    written_columns = write_compatible_rankings_csv(
        output_path,
        game,
        results.values(),
        rank_style="competition",
    )

    assert written_columns == (
        "score_shapley",
        "score_banzhaf",
        "score_g-shapley",
        "score_g-sum-shapley",
        "score_shapley-interaction",
        "score_banzhaf-interaction",
        "score_rp-index",
        "score_ud_up",
        "score_ud_down",
        "score_du_up",
        "score_du_down",
        "score_red-index",
        "rank_shapley",
        "rank_banzhaf",
        "rank_lexcel",
        "rank_o-banzhaf",
        "rank_g-shapley",
        "rank_g-sum-shapley",
        "rank_shapley-interaction",
        "rank_banzhaf-interaction",
        "rank_rp-index",
        "rank_ud",
        "rank_du",
        "rank_red-index",
        "rank_g-lexcel",
        "rank_g-o-banzhaf",
    )

    rows = _rows_by_mask(output_path)
    assert rows[0b001]["rank_shapley"] != ""
    assert rows[0b001]["rank_g-shapley"] != ""
    assert rows[0b011]["rank_shapley"] == ""
    assert rows[0b011]["rank_g-shapley"] != ""
    assert rows[0b011]["score_ud_up"] != ""
    assert rows[0b011]["score_ud_down"] != ""
    assert rows[0b111]["rank_red-index"] != ""
    assert rows[0b000]["rank_red-index"] == ""
