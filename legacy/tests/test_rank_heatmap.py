from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from gamegen.cli import main
from gamegen.rank_heatmap import collect_group_rank_pairs, collect_rank_pairs, collect_rule_correlation_matrix


def _write_csv(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_collect_rank_pairs_aggregates_singletons(tmp_path: Path) -> None:
    rankings_dir = tmp_path / "rankings"
    n3 = rankings_dir / "n3"

    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_lexcel,rank_shapley",
            "1,0,0,10,1,1,2",
            "0,1,0,9,2,2,1",
            "0,0,1,8,3,3,3",
            "0,0,0,0,4,,",
        ],
    )
    _write_csv(
        n3 / "game_000002.csv",
        [
            "player1,player2,player3,score,rank,rank_lexcel,rank_shapley",
            "1,0,0,5,1,2,1",
            "0,1,0,4,2,1,2",
            "0,0,1,3,3,,",
        ],
    )
    _write_csv(
        n3 / "game_000003.csv",
        [
            "player1,player2,player3,score,rank,rank_lexcel",
            "1,0,0,7,1,3",
            "0,1,0,6,2,2",
        ],
    )

    summary = collect_rank_pairs(rankings_dir, players=3)
    assert summary.total_pairs == 5
    assert summary.processed_files == 3
    assert summary.used_files == 2
    assert len(summary.skipped_files) == 1

    expected = pd.DataFrame(
        [
            [0, 2, 0],
            [2, 0, 0],
            [0, 0, 1],
        ],
        index=[1, 2, 3],
        columns=[1, 2, 3],
    )
    expected.index.name = "rank_shapley"
    expected.columns.name = "rank_lexcel"
    pd.testing.assert_frame_equal(summary.matrix, expected)


def test_collect_rank_pairs_uses_strict_better_count_plus_one(tmp_path: Path) -> None:
    rankings_dir = tmp_path / "rankings"
    n3 = rankings_dir / "n3"

    # lex/shap have ties; effective ranks become competition ranks.
    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_lexcel,rank_shapley",
            "1,0,0,10,1,1,1",
            "0,1,0,9,2,1,2",
            "0,0,1,8,3,2,2",
        ],
    )

    summary = collect_rank_pairs(rankings_dir, players=3)
    # lex effective: [1,1,3], shap effective: [1,2,2]
    expected = pd.DataFrame(
        [
            [1, 0],
            [1, 1],
        ],
        index=[1, 2],
        columns=[1, 3],
    )
    expected.index.name = "rank_shapley"
    expected.columns.name = "rank_lexcel"
    pd.testing.assert_frame_equal(summary.matrix, expected)


def test_rank_heatmap_cli_generates_file(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    rankings_dir = tmp_path / "rankings"
    out_dir = tmp_path / "out"
    n3 = rankings_dir / "n3"

    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_lexcel,rank_shapley",
            "1,0,0,10,1,1,2",
            "0,1,0,9,2,2,1",
            "0,0,1,8,3,3,3",
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rank-heatmap",
            "--players",
            "3",
            "--rankings-dir",
            str(rankings_dir),
            "--out",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    heatmap_path = out_dir / "heatmaps" / "n3" / "rank_lexcel_vs_rank_shapley.png"
    assert heatmap_path.exists()
    assert heatmap_path.stat().st_size > 0
    assert "collected 3 player rank pair(s)" in result.output
    assert "saved heatmap" in result.output
    assert "title games=1" in result.output


def test_collect_group_rank_pairs_aggregates_coalitions(tmp_path: Path) -> None:
    rankings_dir = tmp_path / "rankings"
    n3 = rankings_dir / "n3"

    # coalition ranks: use non-empty rows with integer ranks
    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_g-lexcel,rank_g-o-banzhaf",
            # Singletons
            "1,0,0,10,1,1,2",
            "0,1,0,9,2,2,1",
            "0,0,1,8,3,3,3",
            # Pairs
            "1,1,0,7,4,1,1",
            "1,0,1,7,4,2,2",
            "0,1,1,7,4,3,3",
            # Empty coalition -> blank ranks
            "0,0,0,0,5,,",
        ],
    )

    summary = collect_group_rank_pairs(rankings_dir, players=3)
    assert summary.total_pairs > 0
    # Effective ranks are computed as "strictly-better count + 1" (competition ranks),
    # so ties may introduce gaps.
    assert 1 in list(summary.matrix.columns)
    assert 1 in list(summary.matrix.index)


def test_rank_heatmap_cli_coalitions_from_yaml_pairs(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    rankings_dir = tmp_path / "rankings"
    out_dir = tmp_path / "out"
    n3 = rankings_dir / "n3"

    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_g-lexcel,rank_g-o-banzhaf",
            "1,0,0,10,1,1,2",
            "0,1,0,9,2,2,1",
            "0,0,1,8,3,3,3",
            "1,1,0,7,4,1,1",
        ],
    )

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "rank_heatmap:",
                "  pairs:",
                "    - [rank_g-lexcel, rank_g-o-banzhaf]",
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rank-heatmap",
            "--players",
            "3",
            "--rankings-dir",
            str(rankings_dir),
            "--out",
            str(out_dir),
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output
    heatmap_path = out_dir / "heatmaps" / "n3" / "rank_g-lexcel_vs_rank_g-o-banzhaf.png"
    assert heatmap_path.exists()
    assert heatmap_path.stat().st_size > 0


def test_rank_heatmap_pairs_from_yaml_all(tmp_path: Path) -> None:
    from gamegen.commands.heatmaps import pairs_from_config

    pairs = pairs_from_config({"rank_heatmap": {"pairs": "all"}})
    assert ("rank_lexcel", "rank_shapley") in pairs
    assert ("rank_g-lexcel", "rank_g-o-banzhaf") in pairs
def test_rank_heatmap_counts_current_files(tmp_path: Path) -> None:
    """Ensure the title's games count matches current directory CSVs and
    hidden or unrelated CSVs are ignored."""
    pytest.importorskip("matplotlib")
    rankings_dir = tmp_path / "rankings"
    out_dir = tmp_path / "out"
    n3 = rankings_dir / "n3"

    # Create 105 ranking files
    for i in range(1, 106):
        _write_csv(
            n3 / f"game_{i:06d}.csv",
            [
                "player1,player2,player3,score,rank,rank_lexcel,rank_shapley",
                "1,0,0,10,1,1,1",
            ],
        )
    # Add hidden and unrelated files that must be ignored
    (n3 / "._game_000050.csv").write_text("x", encoding="utf-8")
    (n3 / "notes.csv").write_text("x", encoding="utf-8")

    # Now delete 5 to leave exactly 100 files
    for i in range(101, 106):
        (n3 / f"game_{i:06d}.csv").unlink()

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rank-heatmap",
            "--players",
            "3",
            "--rankings-dir",
            str(rankings_dir),
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    # The command prints title games=<count> for verification
    assert "title games=100" in result.output


def test_collect_rule_correlation_matrix_player(tmp_path: Path) -> None:
    rankings_dir = tmp_path / "rankings"
    n3 = rankings_dir / "n3"

    # Perfect inverse ordering between two player columns.
    _write_csv(
        n3 / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_a,rank_b",
            "1,0,0,10,1,1,3",
            "0,1,0,9,2,2,2",
            "0,0,1,8,3,3,1",
        ],
    )

    corr = collect_rule_correlation_matrix(rankings_dir, players=3, rank_cols=["rank_a", "rank_b"], mode="player", method="spearman")
    assert corr.loc["rank_a", "rank_a"] == pytest.approx(1.0)
    assert corr.loc["rank_b", "rank_b"] == pytest.approx(1.0)
    assert corr.loc["rank_a", "rank_b"] == pytest.approx(-1.0)


def test_rule_corr_heatmap_cli_generates_files(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    rankings_dir = tmp_path / "rankings"
    out_dir = tmp_path / "out"
    n2 = rankings_dir / "n2"

    _write_csv(
        n2 / "game_000001.csv",
        [
            "player1,player2,score,rank,rank_lexcel,rank_shapley,rank_g-lexcel,rank_g-o-banzhaf",
            "1,0,3,1,1,2,1,2",
            "0,1,2,2,2,1,2,1",
            "1,1,1,3,, ,1,1",
            "0,0,0,4,, , , ",
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rule-corr-heatmap",
            "--players",
            "2",
            "--rankings-dir",
            str(rankings_dir),
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "heatmaps" / "n2" / "rule_corr_player.png").exists()
    assert (out_dir / "heatmaps" / "n2" / "rule_corr_coalition.png").exists()
