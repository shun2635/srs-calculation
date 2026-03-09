from __future__ import annotations

import csv

import pytest

from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.infrastructure.persistence.csv_game_repository import (
    read_legacy_game_csv,
    write_legacy_game_csv,
)


def test_read_legacy_game_csv_reads_complete_game(tmp_path) -> None:
    input_path = tmp_path / "game.csv"
    input_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "1,1,3,1",
                "1,0,2,2",
                "0,1,1,3",
                "0,0,0,4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    game = read_legacy_game_csv(input_path)

    assert game.player_count == 2
    assert game.scores_by_mask == {
        0b00: 0.0,
        0b01: 2.0,
        0b10: 1.0,
        0b11: 3.0,
    }


def test_read_legacy_game_csv_rejects_incomplete_game_by_default(tmp_path) -> None:
    input_path = tmp_path / "game.csv"
    input_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "1,0,2,1",
                "0,1,1,2",
                "0,0,0,3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="complete coalition game required"):
        read_legacy_game_csv(input_path)


def test_write_legacy_game_csv_writes_dense_base_ranks(tmp_path) -> None:
    game = CoalitionGame.from_scores_by_mask(
        2,
        {
            0b00: 0.0,
            0b01: 2.0,
            0b10: 2.0,
            0b11: 3.0,
        },
    )
    output_path = tmp_path / "game.csv"

    write_legacy_game_csv(output_path, game)

    with output_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows == [
        ["player1", "player2", "score", "rank"],
        ["1", "1", "3", "1"],
        ["1", "0", "2", "2"],
        ["0", "1", "2", "2"],
        ["0", "0", "0", "3"],
    ]


def test_write_legacy_game_csv_uses_explicit_ranks_when_provided(tmp_path) -> None:
    game = CoalitionGame.from_scores_by_mask(
        2,
        {
            0b00: 0.0,
            0b01: 2.0,
            0b10: 1.0,
            0b11: 3.0,
        },
    )
    output_path = tmp_path / "game.csv"

    write_legacy_game_csv(
        output_path,
        game,
        ranks_by_mask={
            0b11: 1,
            0b01: 3,
            0b10: 2,
            0b00: 4,
        },
    )

    with output_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows == [
        ["player1", "player2", "score", "rank"],
        ["1", "1", "3", "1"],
        ["1", "0", "2", "3"],
        ["0", "1", "1", "2"],
        ["0", "0", "0", "4"],
    ]
