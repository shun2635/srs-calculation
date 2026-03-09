from __future__ import annotations

import csv

from click.testing import CliRunner

from srs_calculation.interfaces.cli.game_gen import main


def _write_game_csv(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_apply_rules_cli_with_explicit_directories(tmp_path) -> None:
    games_dir = tmp_path / "games"
    rankings_dir = tmp_path / "rankings"
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

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "--games-dir",
            str(games_dir),
            "--rankings-dir",
            str(rankings_dir),
            "--rule",
            "shapley",
            "--rule",
            "lexcel",
        ],
    )

    assert result.exit_code == 0
    assert "processed 1 game(s) with 2 rule(s)" in result.output

    rankings_csv_path = rankings_dir / "game_000001.csv"
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
        "rank_lexcel",
    ]


def test_apply_rules_cli_with_legacy_style_players_and_out(tmp_path) -> None:
    out_dir = tmp_path / "outputs"
    _write_game_csv(
        out_dir / "games" / "n2" / "game_000001.csv",
        [
            "player1,player2,score,rank",
            "1,1,4,1",
            "1,0,1,2",
            "0,1,1,2",
            "0,0,0,3",
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "-p",
            "2",
            "--out",
            str(out_dir),
            "--rule",
            "banzhaf",
        ],
    )

    assert result.exit_code == 0
    assert "processed 1 game(s) with 1 rule(s)" in result.output

    rankings_csv_path = out_dir / "rankings" / "n2" / "game_000001.csv"
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_banzhaf",
        "rank_banzhaf",
    ]
    assert rows[2] == ["1", "0", "1", "2", "2", "1"]
    assert rows[3] == ["0", "1", "1", "2", "2", "1"]
