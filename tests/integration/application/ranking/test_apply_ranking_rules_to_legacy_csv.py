from __future__ import annotations

import csv

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.infrastructure.persistence.csv_ranking_repository import (
    write_compatible_rankings_csv,
)


def test_apply_ranking_rules_can_be_serialized_to_compatible_rankings_csv(tmp_path) -> None:
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

    results = apply_ranking_rules(
        game,
        ["shapley", "lexcel", "ordinal_banzhaf"],
    )

    output_path = tmp_path / "rankings.csv"
    written_columns = write_compatible_rankings_csv(
        output_path,
        game,
        results.values(),
        rank_style="competition",
    )

    assert written_columns == (
        "score_shapley",
        "rank_shapley",
        "rank_lexcel",
        "rank_o-banzhaf",
    )

    with output_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "player3",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
        "rank_lexcel",
        "rank_o-banzhaf",
    ]
    assert rows[1] == ["1", "1", "1", "8", "1", "", "", "", ""]
    assert rows[2] == ["1", "1", "0", "7", "2", "", "", "", ""]
    assert rows[5] == [
        "1",
        "0",
        "0",
        "4",
        "5",
        "3.666666667",
        "1",
        "1",
        "1",
    ]
    assert rows[6] == [
        "0",
        "1",
        "0",
        "3",
        "6",
        "2.666666667",
        "2",
        "2",
        "1",
    ]
    assert rows[7] == [
        "0",
        "0",
        "1",
        "2",
        "7",
        "1.666666667",
        "3",
        "3",
        "1",
    ]
    assert rows[8] == ["0", "0", "0", "0", "8", "", "", "", ""]
