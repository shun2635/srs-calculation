from __future__ import annotations

import csv

from srs_calculation.application.game_generation import generate_synthetic_games


def test_generate_synthetic_games_writes_complete_game_csvs(tmp_path) -> None:
    result = generate_synthetic_games(
        players=2,
        count=2,
        max_score=3,
        seed=1,
        out_dir=tmp_path / "outputs",
    )

    assert len(result.written_paths) == 2
    assert result.games_dir == tmp_path / "outputs" / "games" / "n2"

    with result.written_paths[0].open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == ["player1", "player2", "score", "rank"]
    assert len(rows) == 5


def test_generate_synthetic_games_uses_config_defaults(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "output_base: generated",
                "gen_games:",
                "  count: 1",
                "  max_score: 2",
                "  seed: 7",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = generate_synthetic_games(
        players=2,
        config_path=config_path,
    )

    assert result.count == 1
    assert result.max_score == 2
    assert result.seed == 7
    assert result.games_dir == tmp_path / "generated" / "games" / "n2"
