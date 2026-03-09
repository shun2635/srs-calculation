from __future__ import annotations

import csv
from pathlib import Path

from click.testing import CliRunner

from srs_calculation.interfaces.cli.game_gen import main


def test_synthetic_cli_workflow_generates_rankings_and_figures(tmp_path: Path) -> None:
    runner = CliRunner()
    out_dir = tmp_path / "outputs"

    gen_result = runner.invoke(
        main,
        [
            "gen-games",
            "-p",
            "2",
            "-c",
            "1",
            "--max-score",
            "3",
            "--seed",
            "1",
            "--out",
            str(out_dir),
        ],
    )

    assert gen_result.exit_code == 0
    assert "wrote 1 game(s)" in gen_result.output

    game_csv_path = out_dir / "games" / "n2" / "game_000001.csv"
    assert game_csv_path.exists()

    apply_result = runner.invoke(
        main,
        [
            "apply-rules",
            "-p",
            "2",
            "--out",
            str(out_dir),
            "--rule",
            "shapley",
            "--rule",
            "lexcel",
        ],
    )

    assert apply_result.exit_code == 0
    assert "processed 1 game(s) with 2 rule(s)" in apply_result.output

    rankings_csv_path = out_dir / "rankings" / "n2" / "game_000001.csv"
    assert rankings_csv_path.exists()

    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))

    assert header == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
        "rank_lexcel",
    ]

    figures_result = runner.invoke(
        main,
        [
            "make-figures",
            "--rankings-dir",
            str(out_dir / "rankings"),
            "--out",
            str(out_dir),
            "--dpi",
            "80",
        ],
    )

    assert figures_result.exit_code == 0
    assert "generated 1 PNG figure(s)" in figures_result.output

    figure_path = out_dir / "figures" / "n2" / "game_000001.png"
    assert figure_path.exists()
    assert figure_path.stat().st_size > 0
