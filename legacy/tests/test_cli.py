from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from click.testing import CliRunner
import pytest

from gamegen.cli import main


def test_cli_gen_games_writes_csv(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    result = runner.invoke(
        main,
        [
            "gen-games",
            "-p",
            "2",
            "-c",
            "2",
            "--max-score",
            "3",
            "--seed",
            "1",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    out_dir = out_base / "games" / "n2"
    assert out_dir.exists()
    files = sorted(p for p in out_dir.iterdir() if p.suffix == ".csv")
    assert len(files) == 2
    # Check header includes score and rank
    head = files[0].read_text(encoding="utf-8").splitlines()[0]
    assert head.endswith(",score,rank")


def test_cli_rank_game_lexcel(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,3",
                "1,0,3,2",
                "0,1,3,2",
                "1,1,4,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "lexcel",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    assert out_path.exists()

    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    scores = [int(row[2]) for row in rows]
    assert scores == sorted(scores, reverse=True)

    assert "rank_lexcel" in header
    rank_idx = header.index("rank_lexcel")

    mask_to_bits = {
        (1, 0): "1",
        (0, 1): "1",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        expected = mask_to_bits.get(bits, "")
        assert row[rank_idx] == expected


def test_cli_rank_game_shapley_exact(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # v(00)=0, v(10)=1, v(01)=2, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "shapley",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_shapley" in header
    assert "rank_shapley" in header
    sidx = header.index("score_shapley")
    ridx = header.index("rank_shapley")

    # Shapley:
    # φ1 = ((v(1)-v(∅)) + (v(12)-v(2)))/2 = (1 + 3)/2 = 2
    # φ2 = ((v(2)-v(∅)) + (v(12)-v(1)))/2 = (2 + 4)/2 = 3
    expected_score = {
        (1, 0): "2",
        (0, 1): "3",
        (1, 1): "",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "2",
        (0, 1): "1",
        (1, 1): "",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_group_lexcel(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # ranks define layers: Σ1={11}, Σ2={01,10}, Σ3={00}
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,3",
                "1,0,3,2",
                "0,1,3,2",
                "1,1,4,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "g-lexcel",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "rank_g-lexcel" in header
    ridx = header.index("rank_g-lexcel")
    # Non-empty coalitions only. Expected dense ranks by Θ in desc lex order:
    # Θ(01)=(1,1,0), Θ(10)=(1,1,0) -> rank 1; Θ(11)=(1,0,0) -> rank 2; empty -> blank
    expected = {
        (1, 1): "2",
        (1, 0): "1",
        (0, 1): "1",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[ridx] == expected[bits]


def test_cli_rank_game_group_o_banzhaf(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # Scores induce levels: 11 > {01,10} > 00
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,3",
                "1,0,2,2",
                "0,1,2,2",
                "1,1,3,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "g-o-banzhaf",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "rank_g-o-banzhaf" in header
    ridx = header.index("rank_g-o-banzhaf")
    # Expected dense ranks by G-OB s_T: s_{1}=2, s_{2}=2, s_{12}=1, empty -> blank
    expected = {
        (1, 1): "2",
        (1, 0): "1",
        (0, 1): "1",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[ridx] == expected[bits]


def test_cli_rank_game_banzhaf_value(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # scores:
    # v(00)=0, v(10)=3, v(01)=1, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,3,2",
                "0,1,1,3",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "banzhaf",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_banzhaf" in header
    assert "rank_banzhaf" in header
    sidx = header.index("score_banzhaf")
    ridx = header.index("rank_banzhaf")

    # Banzhaf:
    # φ1 = ( (v(10)-v(00)) + (v(11)-v(01)) ) / 2 = (3 + 4)/2 = 3.5
    # φ2 = ( (v(01)-v(00)) + (v(11)-v(10)) ) / 2 = (1 + 2)/2 = 1.5
    expected_score = {
        (1, 0): "3.5",
        (0, 1): "1.5",
        (0, 0): "",
        (1, 1): "",
    }
    expected_rank = {
        (1, 0): "1",
        (0, 1): "2",
        (0, 0): "",
        (1, 1): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_shapley_group_value(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # scores:
    # v(00)=0, v(10)=1, v(01)=2, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "g-shapley",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_g-shapley" in header
    assert "rank_g-shapley" in header
    sidx = header.index("score_g-shapley")
    ridx = header.index("rank_g-shapley")

    # Group Shapley values:
    # C={1}: ((v(1)-v(∅)) + (v(12)-v(2)))/2 = (1 + 3)/2 = 2
    # C={2}: ((v(2)-v(∅)) + (v(12)-v(1)))/2 = (2 + 4)/2 = 3
    # C={12}: v(12)-v(∅) = 5
    expected_score = {
        (1, 0): "2",
        (0, 1): "3",
        (1, 1): "5",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "3",
        (0, 1): "2",
        (1, 1): "1",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_group_sum_shapley(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # scores:
    # v(00)=0, v(10)=1, v(01)=2, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "g-sum-shapley",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_g-sum-shapley" in header
    assert "rank_g-sum-shapley" in header
    sidx = header.index("score_g-sum-shapley")
    ridx = header.index("rank_g-sum-shapley")

    # φ1 = 2, φ2 = 3 -> sum(C) = Σ_{i∈C} φ_i
    expected_score = {
        (1, 0): "2",
        (0, 1): "3",
        (1, 1): "5",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "3",
        (0, 1): "2",
        (1, 1): "1",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_shapley_interaction_index(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # scores:
    # v(00)=0, v(10)=1, v(01)=2, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "shapley-interaction",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_shapley-interaction" in header
    assert "rank_shapley-interaction" in header
    sidx = header.index("score_shapley-interaction")
    ridx = header.index("rank_shapley-interaction")

    # For n=2:
    # I({1}) = Shapley(1) = ((v(1)-v(∅)) + (v(12)-v(2)))/2 = (1 + 3)/2 = 2
    # I({2}) = Shapley(2) = ((v(2)-v(∅)) + (v(12)-v(1)))/2 = (2 + 4)/2 = 3
    # I({12}) = v(∅) - v(1) - v(2) + v(12) = 2
    expected_score = {
        (1, 0): "2",
        (0, 1): "3",
        (1, 1): "2",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "2",
        (0, 1): "1",
        (1, 1): "2",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_banzhaf_interaction_index(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # scores:
    # v(00)=0, v(10)=1, v(01)=2, v(11)=5
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,5,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "banzhaf-interaction",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_banzhaf-interaction" in header
    assert "rank_banzhaf-interaction" in header
    sidx = header.index("score_banzhaf-interaction")
    ridx = header.index("rank_banzhaf-interaction")

    # For n=2:
    # I^B({1}) = ( (v(1)-v(∅)) + (v(12)-v(2)) ) / 2 = (1 + 3)/2 = 2
    # I^B({2}) = ( (v(2)-v(∅)) + (v(12)-v(1)) ) / 2 = (2 + 4)/2 = 3
    # I^B({12}) = v(∅) - v(1) - v(2) + v(12) = 2
    expected_score = {
        (1, 0): "2",
        (0, 1): "3",
        (1, 1): "2",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "2",
        (0, 1): "1",
        (1, 1): "2",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_rp_index(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # Base ranks (dense): 12 > 2 > 1 > empty, so within X=non-empty:
    # RP(12)=2, RP(2)=0, RP(1)=-2 -> Δ^RP(12)=2 - (-2+0)/2 = 3
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,1,3",
                "0,1,2,2",
                "1,1,3,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "rp-index",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_rp-index" in header
    assert "rank_rp-index" in header
    sidx = header.index("score_rp-index")
    ridx = header.index("rank_rp-index")

    expected_score = {
        (1, 1): "3",
        (1, 0): "",
        (0, 1): "",
        (0, 0): "",
    }
    expected_rank = {
        (1, 1): "1",
        (1, 0): "",
        (0, 1): "",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_ud_rule(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # Construct a case where UD and DU differ:
    # singletons: {3} is best; coalition {1,2,3} is worse than {3} but better than {1},{2}.
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank",
                "0,0,0,0,6",
                "1,0,0,1,4",
                "0,1,0,2,3",
                "0,0,1,3,1",
                "1,1,0,4,3",
                "1,0,1,5,2",
                "0,1,1,6,5",
                "1,1,1,7,2",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "ud",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n3" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_ud_up" in header
    assert "score_ud_down" in header
    assert "rank_ud" in header
    sidx_up = header.index("score_ud_up")
    sidx_down = header.index("score_ud_down")
    ridx = header.index("rank_ud")

    expected_up = {
        (1, 1, 0): "1",
        (1, 0, 1): "1",
        (0, 1, 1): "0",
        (1, 1, 1): "2",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    expected_down = {
        (1, 1, 0): "0",
        (1, 0, 1): "1",
        (0, 1, 1): "2",
        (1, 1, 1): "1",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    expected_rank = {
        (1, 1, 0): "2",
        (1, 0, 1): "3",
        (0, 1, 1): "4",
        (1, 1, 1): "1",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]), int(row[2]))
        assert row[sidx_up] == expected_up[bits]
        assert row[sidx_down] == expected_down[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_rank_game_du_rule(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank",
                "0,0,0,0,6",
                "1,0,0,1,4",
                "0,1,0,2,3",
                "0,0,1,3,1",
                "1,1,0,4,3",
                "1,0,1,5,2",
                "0,1,1,6,5",
                "1,1,1,7,2",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "du",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n3" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_du_up" in header
    assert "score_du_down" in header
    assert "rank_du" in header
    sidx_up = header.index("score_du_up")
    sidx_down = header.index("score_du_down")
    ridx = header.index("rank_du")

    expected_up = {
        (1, 1, 0): "1",
        (1, 0, 1): "1",
        (0, 1, 1): "0",
        (1, 1, 1): "2",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    expected_down = {
        (1, 1, 0): "0",
        (1, 0, 1): "1",
        (0, 1, 1): "2",
        (1, 1, 1): "1",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    expected_rank = {
        (1, 1, 0): "1",
        (1, 0, 1): "3",
        (0, 1, 1): "4",
        (1, 1, 1): "2",
        (1, 0, 0): "",
        (0, 1, 0): "",
        (0, 0, 1): "",
        (0, 0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]), int(row[2]))
        assert row[sidx_up] == expected_up[bits]
        assert row[sidx_down] == expected_down[bits]
        assert row[ridx] == expected_rank[bits]

def test_cli_rank_game_red_index(tmp_path: Path) -> None:
    runner = CliRunner()
    game_path = tmp_path / "game.csv"
    # Base ranks (dense): 1 > 2 > 12 > empty, so:
    # Red(1)=1 (since 1 ≽ 12), Red(2)=1 (since 2 ≽ 12), Red(12)=0
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,4",
                "1,0,3,1",
                "0,1,2,2",
                "1,1,1,3",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "rank-game",
            "--game",
            str(game_path),
            "--rule",
            "red-index",
            "--out",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = tmp_path / "rankings" / "n2" / game_path.name
    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "score_red-index" in header
    assert "rank_red-index" in header
    sidx = header.index("score_red-index")
    ridx = header.index("rank_red-index")

    expected_score = {
        (1, 0): "1",
        (0, 1): "1",
        (1, 1): "0",
        (0, 0): "",
    }
    expected_rank = {
        (1, 0): "1",
        (0, 1): "1",
        (1, 1): "2",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[sidx] == expected_score[bits]
        assert row[ridx] == expected_rank[bits]


def test_cli_apply_rules_uses_competition_ranks(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    games_dir = out_base / "games" / "n2"
    games_dir.mkdir(parents=True, exist_ok=True)
    game_path = games_dir / "game_000001.csv"
    # levels: 11 > {01,10} > 00
    game_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0,3",
                "1,0,2,2",
                "0,1,2,2",
                "1,1,3,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "apply-rules",
            "-p",
            "2",
            "--out",
            str(out_base),
            "--rules",
            "g-o-banzhaf",
        ],
    )
    assert result.exit_code == 0, result.output

    rankings_path = out_base / "rankings" / "n2" / game_path.name
    with rankings_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert "rank_g-o-banzhaf" in header
    ridx = header.index("rank_g-o-banzhaf")

    # Dense ranks would be: 1,1,2 (for {1},{2},{12}); apply-rules uses competition ranks: 1,1,3.
    expected = {
        (1, 1): "3",
        (1, 0): "1",
        (0, 1): "1",
        (0, 0): "",
    }
    for row in rows:
        bits = (int(row[0]), int(row[1]))
        assert row[ridx] == expected[bits]


def test_cli_check_axioms_gekokujou(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    rankings_dir = out_base / "rankings" / "n3"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Construct a minimal rankings CSV with base `rank` and one interaction column `rank_rp-index`.
    # Singletons: {1}≻{2}≻{3}. Pairs: {13}≻{12}≻{23}.
    # Constraint triggers for (S,T)=({12},{13}) only, and rank_rp-index respects T P^I S.
    rankings_path = rankings_dir / "game_000001.csv"
    rankings_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,rank_rp-index",
                "0,0,0,0,8,",
                "1,0,0,0,1,",
                "0,1,0,0,2,",
                "0,0,1,0,3,",
                "1,1,0,0,2,2",
                "1,0,1,0,1,1",
                "0,1,1,0,3,3",
                "1,1,1,0,4,",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "check-axioms",
            "-p",
            "3",
            "--rules",
            "rp-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    out_dir = out_base / "axiom" / "n3"
    out_2p = out_dir / "gekokujou-2p" / "rp-index.csv"
    out_w = out_dir / "gekokujou-weak-n" / "rp-index.csv"
    out_g = out_dir / "give-2p" / "rp-index.csv"
    out_t = out_dir / "take-2p" / "rp-index.csv"
    out_gw = out_dir / "give-weak-n" / "rp-index.csv"
    out_tw = out_dir / "take-weak-n" / "rp-index.csv"
    out_red = out_dir / "redundancy" / "rp-index.csv"
    assert out_2p.exists()
    assert out_w.exists()
    assert out_g.exists()
    assert out_t.exists()
    assert out_gw.exists()
    assert out_tw.exists()
    assert out_red.exists()

    for out_path in (out_2p, out_w):
        with out_path.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = list(reader)
        assert header == ["game", "constraints", "satisfied", "satisfied_rate"]
        assert rows == [["game_000001.csv", "1", "1", "1"]]

    for out_path in (out_g, out_t):
        with out_path.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = list(reader)
        assert header == ["game", "constraints", "satisfied", "satisfied_rate"]
        assert rows == [["game_000001.csv", "2", "2", "1"]]

    for out_path in (out_gw, out_tw):
        with out_path.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = list(reader)
        assert header == ["game", "constraints", "satisfied", "satisfied_rate"]
        assert rows == [["game_000001.csv", "2", "2", "1"]]

    with out_red.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == ["game", "constraints", "satisfied", "satisfied_rate"]
    assert rows == [["game_000001.csv", "0", "0", "0"]]

    summary_path = out_dir / "summary.csv"
    assert summary_path.exists()
    with summary_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == ["rule", "axiom", "constraints", "satisfied", "satisfied_rate"]
    rows_by_key = {(r[0], r[1]): r for r in rows}
    assert rows_by_key[("rp-index", "gekokujou-2p")] == ["rp-index", "gekokujou-2p", "1", "1", "1"]
    assert rows_by_key[("rp-index", "gekokujou-weak-n")] == ["rp-index", "gekokujou-weak-n", "1", "1", "1"]
    assert rows_by_key[("rp-index", "give-2p")] == ["rp-index", "give-2p", "2", "2", "1"]
    assert rows_by_key[("rp-index", "take-2p")] == ["rp-index", "take-2p", "2", "2", "1"]
    assert rows_by_key[("rp-index", "give-weak-n")] == ["rp-index", "give-weak-n", "2", "2", "1"]
    assert rows_by_key[("rp-index", "take-weak-n")] == ["rp-index", "take-weak-n", "2", "2", "1"]
    assert rows_by_key[("rp-index", "redundancy")] == ["rp-index", "redundancy", "0", "0", "0"]


def test_cli_summarize_axioms(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    axiom_dir = out_base / "axiom" / "n2"
    (axiom_dir / "gekokujou-2p").mkdir(parents=True, exist_ok=True)
    (axiom_dir / "gekokujou-weak-n").mkdir(parents=True, exist_ok=True)

    # New layout: <axiom_id>/<rule>.csv
    (axiom_dir / "gekokujou-2p" / "rp-index.csv").write_text(
        "\n".join(
            [
                "game,constraints,satisfied,satisfied_rate",
                "game_000001.csv,2,1,0.5",
                "game_000002.csv,3,3,1",
            ]
        ),
        encoding="utf-8",
    )
    (axiom_dir / "gekokujou-weak-n" / "rp-index.csv").write_text(
        "\n".join(
            [
                "game,constraints,satisfied,satisfied_rate",
                "game_000001.csv,0,0,0",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "summarize-axioms",
            "-p",
            "2",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    out_path = axiom_dir / "summary.csv"
    assert out_path.exists()

    with out_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert header == ["rule", "axiom", "constraints", "satisfied", "satisfied_rate"]
    rows_by_key = {(r[0], r[1]): r for r in rows}

    # 2+3=5 constraints, 1+3=4 satisfied -> 0.8
    assert rows_by_key[("rp-index", "gekokujou-2p")] == ["rp-index", "gekokujou-2p", "5", "4", "0.8"]
    # constraints=0 -> rate=0
    assert rows_by_key[("rp-index", "gekokujou-weak-n")] == ["rp-index", "gekokujou-weak-n", "0", "0", "0"]


def test_cli_pipeline_axioms_creates_summary(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    result = runner.invoke(
        main,
        [
            "pipeline",
            "-p",
            "2",
            "-c",
            "1",
            "--seed",
            "1",
            "--max-score",
            "3",
            "--rules",
            "rp-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    summary_path = out_base / "axiom" / "n2" / "summary.csv"
    assert summary_path.exists()
    if importlib.util.find_spec("matplotlib") is not None:
        assert (out_base / "axiom" / "n2" / "summary_heatmap.png").exists()


def test_cli_pipeline_generates_rule_corr_heatmaps(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "output_base: outputs",
                "figures:",
                "  png_dpi: 100",
                "rank_heatmap:",
                "  pairs: [[rank_lexcel, rank_shapley]]",
                "rule_corr_heatmap:",
                "  method: spearman",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "pipeline",
            "-p",
            "2",
            "-c",
            "1",
            "--seed",
            "1",
            "--max-score",
            "3",
            "--rules",
            "lexcel",
            "--rules",
            "shapley",
            "--rules",
            "g-lexcel",
            "--rules",
            "g-o-banzhaf",
            "--out",
            str(out_base),
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output

    heatmap_dir = out_base / "heatmaps" / "n2"
    assert (heatmap_dir / "rule_corr_player.png").exists()
    assert (heatmap_dir / "rule_corr_coalition.png").exists()


def test_cli_axiom_summary_heatmap(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    ax_dir = out_base / "axiom" / "n3"
    ax_dir.mkdir(parents=True, exist_ok=True)
    (ax_dir / "summary.csv").write_text(
        "\n".join(
            [
                "rule,axiom,constraints,satisfied,satisfied_rate",
                "rp-index,gekokujou-2p,10,5,0.5",
                "rp-index,take-2p,10,10,1",
                "ud,gekokujou-2p,10,0,0",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "axiom-summary-heatmap",
            "-p",
            "3",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (ax_dir / "summary_heatmap.png").exists()


def test_axiom_summary_heatmap_orders_axioms() -> None:
    pytest.importorskip("matplotlib")
    from gamegen.axioms.summary_heatmap import order_axiom_labels

    labels = [
        "take-2p",
        "gekokujou-weak-n",
        "redundancy",
        "give-2p",
        "gekokujou-2p",
        "take-weak-n",
        "give-weak-n",
    ]
    assert order_axiom_labels(labels) == [
        "gekokujou-2p",
        "gekokujou-weak-n",
        "give-2p",
        "give-weak-n",
        "take-2p",
        "take-weak-n",
        "redundancy",
    ]


def test_cli_check_axioms_writes_violation_png_examples(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    rankings_dir = out_base / "rankings" / "n3"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Craft a violation for give-2p under rank_rp-index:
    # give(13)=2 (13 ≻ 1 and 13 ≻ 3), give(12)=0, but rank_I(13) is worse than rank_I(12).
    rankings_path = rankings_dir / "game_000001.csv"
    rankings_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,rank_rp-index",
                "0,0,0,0,8,",
                "1,0,0,0,4,",
                "0,1,0,0,2,",
                "0,0,1,0,5,",
                "1,1,0,0,6,1",
                "1,0,1,0,1,2",
                "0,1,1,0,7,3",
                "1,1,1,0,3,",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "check-axioms",
            "-p",
            "3",
            "--rules",
            "rp-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    examples_dir = out_base / "axiom" / "n3" / "give-2p" / "examples" / "rp-index"
    pngs = sorted(p for p in examples_dir.glob("*.png"))
    assert len(pngs) >= 1


def test_cli_check_axioms_writes_violation_png_examples_gekokujou(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    rankings_dir = out_base / "rankings" / "n3"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Craft a violation for gekokujou-2p under rank_rp-index:
    # Singletons: 1 ≻ 2 ≻ 3. Pairs: 13 ≻ 12 ≻ 23.
    # Constraint applies to (S,T)=(12,13), but rank_I prefers 12 over 13 (violation).
    rankings_path = rankings_dir / "game_000001.csv"
    rankings_path.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,rank_rp-index",
                "0,0,0,0,8,",
                "1,0,0,0,1,",
                "0,1,0,0,2,",
                "0,0,1,0,3,",
                "1,1,0,0,2,1",
                "1,0,1,0,1,2",
                "0,1,1,0,3,3",
                "1,1,1,0,4,",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "check-axioms",
            "-p",
            "3",
            "--rules",
            "rp-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    examples_dir = out_base / "axiom" / "n3" / "gekokujou-2p" / "examples" / "rp-index"
    pngs = sorted(p for p in examples_dir.glob("*.png"))
    assert len(pngs) >= 1


def test_cli_check_axioms_writes_violation_png_examples_redundancy(tmp_path: Path) -> None:
    runner = CliRunner()
    out_base = tmp_path / "outputs"
    rankings_dir = out_base / "rankings" / "n2"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Redundancy violation for rank_red-index:
    # Base: {1} ≽ {12} (rank 1 <= 3), but interaction ranks prefer {12} over {1}.
    rankings_path = rankings_dir / "game_000001.csv"
    rankings_path.write_text(
        "\n".join(
            [
                "player1,player2,score,rank,rank_red-index",
                "0,0,0,4,",
                "1,0,3,1,2",
                "0,1,2,2,1",
                "1,1,1,3,1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "check-axioms",
            "-p",
            "2",
            "--rules",
            "red-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    examples_dir = out_base / "axiom" / "n2" / "redundancy" / "examples" / "red-index"
    pngs = sorted(p for p in examples_dir.glob("*.png"))
    assert len(pngs) >= 1
