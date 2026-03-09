from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from click.testing import CliRunner

from srs_calculation.interfaces.cli.game_gen import main


def _write_game_csv(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class _RenderedSyntheticFiguresStub:
    rankings_dir: Path
    figures_dir: Path
    written_paths: tuple[Path, ...]
    skipped_count: int


@dataclass(frozen=True)
class _RenderedSyntheticHeatmapsStub:
    rankings_dir: Path
    heatmaps_dir: Path
    written_paths: tuple[Path, ...]
    pairs: tuple[tuple[str, str], ...] = ()
    method: str = "spearman"


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


def test_game_gen_cli_help_lists_supported_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "gen-games" in result.output
    assert "make-figures" in result.output
    assert "apply-rules" in result.output
    assert "rank-game" in result.output
    assert "rank-heatmap" in result.output
    assert "rule-corr-heatmap" in result.output


def test_gen_games_cli_writes_game_csvs(tmp_path) -> None:
    runner = CliRunner()
    out_dir = tmp_path / "outputs"
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
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    assert "wrote 2 game(s)" in result.output

    game_dir = out_dir / "games" / "n2"
    files = sorted(game_dir.glob("game_*.csv"))
    assert len(files) == 2


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


def test_make_figures_cli_writes_pngs(tmp_path, monkeypatch) -> None:
    import srs_calculation.interfaces.cli.game_gen as module

    rankings_dir = tmp_path / "outputs" / "rankings" / "n2"
    _write_game_csv(
        rankings_dir / "game_000001.csv",
        [
            "player1,player2,score,rank,rank_shapley",
            "0,0,0,4,",
            "1,0,1,3,2",
            "0,1,2,2,1",
            "1,1,3,1,1",
        ],
    )

    def _fake_render_synthetic_figures(*, rankings_dir: Path | None, out_dir: Path | None, config_path: Path | None, dpi: int | None):
        target = tmp_path / "outputs" / "figures" / "n2" / "game_000001.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("png", encoding="utf-8")
        return _RenderedSyntheticFiguresStub(
            rankings_dir=rankings_dir or tmp_path / "outputs" / "rankings",
            figures_dir=(out_dir or tmp_path / "outputs") / "figures",
            written_paths=(target,),
            skipped_count=0,
        )

    monkeypatch.setattr(module, "render_synthetic_figures", _fake_render_synthetic_figures)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "make-figures",
            "--rankings-dir",
            str(tmp_path / "outputs" / "rankings"),
            "--out",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0
    assert "generated 1 PNG figure(s)" in result.output
    assert (tmp_path / "outputs" / "figures" / "n2" / "game_000001.png").exists()


def test_rank_game_cli_writes_one_rankings_csv(tmp_path) -> None:
    game_csv_path = tmp_path / "games" / "n2" / "game_000001.csv"
    _write_game_csv(
        game_csv_path,
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
            "rank-game",
            "--game",
            str(game_csv_path),
            "--rule",
            "lexcel",
        ],
    )

    assert result.exit_code == 0
    assert "rank_lexcel" in result.output

    rankings_csv_path = tmp_path / "rankings" / "n2" / "game_000001.csv"
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "rank_lexcel",
    ]
    assert rows[2] == ["1", "0", "1", "2", "1"]
    assert rows[3] == ["0", "1", "1", "2", "1"]


def test_rank_heatmap_cli_writes_png(tmp_path, monkeypatch) -> None:
    import srs_calculation.interfaces.cli.game_gen as module

    def _fake_render_synthetic_rank_heatmaps(
        *,
        players: int,
        rankings_dir: Path | None,
        out_dir: Path | None,
        config_path: Path | None,
        dpi: int | None,
    ):
        target = tmp_path / "outputs" / "heatmaps" / "n2" / "rank_lexcel_vs_rank_shapley.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("png", encoding="utf-8")
        return _RenderedSyntheticHeatmapsStub(
            rankings_dir=rankings_dir or tmp_path / "outputs" / "rankings",
            heatmaps_dir=(out_dir or tmp_path / "outputs") / "heatmaps" / "n2",
            written_paths=(target,),
            pairs=(("rank_lexcel", "rank_shapley"),),
        )

    monkeypatch.setattr(module, "render_synthetic_rank_heatmaps", _fake_render_synthetic_rank_heatmaps)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rank-heatmap",
            "-p",
            "2",
            "--rankings-dir",
            str(tmp_path / "outputs" / "rankings"),
            "--out",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0
    assert "saved heatmap:" in result.output
    assert (tmp_path / "outputs" / "heatmaps" / "n2" / "rank_lexcel_vs_rank_shapley.png").exists()


def test_rule_corr_heatmap_cli_writes_png(tmp_path, monkeypatch) -> None:
    import srs_calculation.interfaces.cli.game_gen as module

    def _fake_render_synthetic_rule_correlation_heatmaps(
        *,
        players: int,
        rankings_dir: Path | None,
        out_dir: Path | None,
        config_path: Path | None,
        dpi: int | None,
        method: str | None,
    ):
        target = tmp_path / "outputs" / "heatmaps" / "n2" / "rule_corr_player.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("png", encoding="utf-8")
        return _RenderedSyntheticHeatmapsStub(
            rankings_dir=rankings_dir or tmp_path / "outputs" / "rankings",
            heatmaps_dir=(out_dir or tmp_path / "outputs") / "heatmaps" / "n2",
            written_paths=(target,),
            method=method or "spearman",
        )

    monkeypatch.setattr(
        module,
        "render_synthetic_rule_correlation_heatmaps",
        _fake_render_synthetic_rule_correlation_heatmaps,
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "rule-corr-heatmap",
            "-p",
            "2",
            "--rankings-dir",
            str(tmp_path / "outputs" / "rankings"),
            "--out",
            str(tmp_path / "outputs"),
        ],
    )

    assert result.exit_code == 0
    assert "saved heatmap:" in result.output
    assert (tmp_path / "outputs" / "heatmaps" / "n2" / "rule_corr_player.png").exists()
