from __future__ import annotations

import csv

from srs_calculation.application.ranking.apply_ranking_rules import apply_ranking_rules
from srs_calculation.infrastructure.persistence.csv_game_repository import (
    read_compatible_game_csv,
)
from srs_calculation.infrastructure.persistence.csv_ranking_repository import (
    write_compatible_rankings_csv,
)


def test_apply_ranking_rules_from_compatible_game_csv_round_trip(tmp_path) -> None:
    game_csv_path = tmp_path / "game.csv"
    game_csv_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank",
                "1,1,1,8,1",
                "1,1,0,7,2",
                "1,0,1,6,3",
                "0,1,1,5,4",
                "1,0,0,4,5",
                "0,1,0,3,6",
                "0,0,1,2,7",
                "0,0,0,0,8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    game = read_compatible_game_csv(game_csv_path)
    results = apply_ranking_rules(game, ["shapley", "banzhaf"])

    rankings_csv_path = tmp_path / "rankings.csv"
    write_compatible_rankings_csv(
        rankings_csv_path,
        game,
        results.values(),
        rank_style="competition",
    )

    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "player3",
        "score",
        "rank",
        "score_shapley",
        "score_banzhaf",
        "rank_shapley",
        "rank_banzhaf",
    ]
    assert rows[5] == [
        "1",
        "0",
        "0",
        "4",
        "5",
        "3.666666667",
        "3.75",
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
        "2.75",
        "2",
        "2",
    ]
    assert rows[7] == [
        "0",
        "0",
        "1",
        "2",
        "7",
        "1.666666667",
        "1.75",
        "3",
        "3",
    ]
