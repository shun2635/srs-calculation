from __future__ import annotations

import csv

from srs_calculation.application.ranking.apply_ranking_rules_to_game_csv import (
    apply_ranking_rules_in_directory,
    apply_ranking_rules_to_game_csv,
)


def _write_game_csv(path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_apply_ranking_rules_to_game_csv_writes_rankings_file(tmp_path) -> None:
    game_csv_path = tmp_path / "game_000001.csv"
    _write_game_csv(
        game_csv_path,
        [
            "player1,player2,score,rank",
            "1,1,3,1",
            "1,0,2,2",
            "0,1,1,3",
            "0,0,0,4",
        ],
    )
    rankings_csv_path = tmp_path / "rankings" / "game_000001.csv"

    result = apply_ranking_rules_to_game_csv(
        game_csv_path,
        rankings_csv_path,
        ["shapley", "banzhaf"],
    )

    assert result.game_csv_path == game_csv_path
    assert result.rankings_csv_path == rankings_csv_path
    assert result.written_columns == (
        "score_shapley",
        "score_banzhaf",
        "rank_shapley",
        "rank_banzhaf",
    )
    assert set(result.results_by_rule_id) == {"shapley", "banzhaf"}

    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_shapley",
        "score_banzhaf",
        "rank_shapley",
        "rank_banzhaf",
    ]
    assert rows[2] == ["1", "0", "2", "2", "2", "2", "1", "1"]
    assert rows[3] == ["0", "1", "1", "3", "1", "1", "2", "2"]


def test_apply_ranking_rules_in_directory_processes_multiple_games(tmp_path) -> None:
    games_dir = tmp_path / "games"
    rankings_dir = tmp_path / "rankings"
    games_dir.mkdir()
    _write_game_csv(
        games_dir / "game_000001.csv",
        [
            "player1,player2,score,rank",
            "1,1,3,1",
            "1,0,2,2",
            "0,1,1,3",
            "0,0,0,4",
        ],
    )
    _write_game_csv(
        games_dir / "game_000002.csv",
        [
            "player1,player2,score,rank",
            "1,1,4,1",
            "1,0,1,2",
            "0,1,1,2",
            "0,0,0,3",
        ],
    )

    results = apply_ranking_rules_in_directory(
        games_dir,
        rankings_dir,
        ["lexcel"],
    )

    assert [result.game_csv_path.name for result in results] == [
        "game_000001.csv",
        "game_000002.csv",
    ]
    assert [result.rankings_csv_path.name for result in results] == [
        "game_000001.csv",
        "game_000002.csv",
    ]
    assert all(result.written_columns == ("rank_lexcel",) for result in results)
    assert (rankings_dir / "game_000001.csv").exists()
    assert (rankings_dir / "game_000002.csv").exists()
