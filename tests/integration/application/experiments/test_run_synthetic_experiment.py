from __future__ import annotations

from pathlib import Path

from srs_calculation.application.experiments import render_synthetic_figures
from srs_calculation.application.experiments import (
    render_synthetic_rank_heatmaps,
    render_synthetic_rule_correlation_heatmaps,
)
from srs_calculation.application.experiments import run_synthetic_experiment as module


def _write(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_render_synthetic_figures_writes_pngs_under_matching_n_dir(tmp_path, monkeypatch) -> None:
    rankings_dir = tmp_path / "outputs" / "rankings"
    _write(
        rankings_dir / "n2" / "game_000001.csv",
        [
            "player1,player2,score,rank,rank_shapley",
            "0,0,0,4,",
            "1,0,1,3,2",
            "0,1,2,2,1",
            "1,1,3,1,1",
        ],
    )

    def _fake_generate_synthetic_ranking_figure(*, rankings_csv: Path, output_dir: Path, dpi: int) -> Path:
        out_path = output_dir / f"{rankings_csv.stem}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f"dpi={dpi}", encoding="utf-8")
        return out_path

    monkeypatch.setattr(module, "generate_synthetic_ranking_figure", _fake_generate_synthetic_ranking_figure)

    result = render_synthetic_figures(
        rankings_dir=rankings_dir,
        out_dir=tmp_path / "outputs",
        dpi=90,
    )

    assert result.figures_dir == tmp_path / "outputs" / "synthetic" / "unconstrained" / "figures"
    assert result.skipped_count == 0
    assert result.written_paths == (
        tmp_path / "outputs" / "synthetic" / "unconstrained" / "figures" / "n2" / "game_000001.png",
    )
    assert result.written_paths[0].read_text(encoding="utf-8") == "dpi=90"


def test_render_synthetic_figures_uses_config_defaults(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    rankings_dir = tmp_path / "custom_outputs" / "synthetic" / "unconstrained" / "rankings" / "n3"
    _write(
        rankings_dir / "game_000001.csv",
        [
            "player1,player2,player3,score,rank,rank_banzhaf",
            "0,0,0,0,8,",
            "1,0,0,1,7,2",
            "0,1,0,1,6,2",
            "0,0,1,1,5,1",
            "1,1,0,2,4,2",
            "1,0,1,2,3,1",
            "0,1,1,2,2,1",
            "1,1,1,3,1,1",
        ],
    )
    _write(
        config_path,
        [
            "output_base: custom_outputs",
            "figures:",
            "  png_dpi: 123",
        ],
    )

    seen: dict[str, object] = {}

    def _fake_generate_synthetic_ranking_figure(*, rankings_csv: Path, output_dir: Path, dpi: int) -> Path:
        seen["rankings_csv"] = rankings_csv
        seen["output_dir"] = output_dir
        seen["dpi"] = dpi
        out_path = output_dir / f"{rankings_csv.stem}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("png", encoding="utf-8")
        return out_path

    monkeypatch.setattr(module, "generate_synthetic_ranking_figure", _fake_generate_synthetic_ranking_figure)

    result = render_synthetic_figures(config_path=config_path)

    assert seen["dpi"] == 123
    assert seen["rankings_csv"] == rankings_dir / "game_000001.csv"
    assert seen["output_dir"] == tmp_path / "custom_outputs" / "synthetic" / "unconstrained" / "figures" / "n3"
    assert result.written_paths[0] == (
        tmp_path / "custom_outputs" / "synthetic" / "unconstrained" / "figures" / "n3" / "game_000001.png"
    )


def test_render_synthetic_rank_heatmaps_writes_png(tmp_path) -> None:
    rankings_dir = tmp_path / "outputs" / "synthetic" / "unconstrained" / "rankings" / "n2"
    _write(
        rankings_dir / "game_000001.csv",
        [
            "player1,player2,score,rank,rank_shapley,rank_lexcel",
            "1,1,4,1,,",
            "1,0,1,2,1,2",
            "0,1,1,2,1,1",
            "0,0,0,3,,",
        ],
    )

    result = render_synthetic_rank_heatmaps(
        players=2,
        rankings_dir=tmp_path / "outputs" / "synthetic" / "unconstrained" / "rankings",
        out_dir=tmp_path / "outputs",
        dpi=80,
    )

    assert result.written_paths == (
        tmp_path / "outputs" / "synthetic" / "unconstrained" / "heatmaps" / "n2" / "rank_lexcel_vs_rank_shapley.png",
    )
    assert result.written_paths[0].exists()
    assert result.written_paths[0].stat().st_size > 0


def test_render_synthetic_rule_correlation_heatmaps_writes_png(tmp_path) -> None:
    rankings_dir = tmp_path / "outputs" / "synthetic" / "unconstrained" / "rankings" / "n2"
    _write(
        rankings_dir / "game_000001.csv",
        [
            "player1,player2,score,rank,rank_shapley,rank_lexcel",
            "1,1,4,1,,",
            "1,0,1,2,1,2",
            "0,1,1,2,2,1",
            "0,0,0,3,,",
        ],
    )

    result = render_synthetic_rule_correlation_heatmaps(
        players=2,
        rankings_dir=tmp_path / "outputs" / "synthetic" / "unconstrained" / "rankings",
        out_dir=tmp_path / "outputs",
        dpi=80,
    )

    assert result.written_paths == (
        tmp_path / "outputs" / "synthetic" / "unconstrained" / "heatmaps" / "n2" / "rule_corr_player.png",
    )
    assert result.written_csv_paths == (
        tmp_path / "outputs" / "synthetic" / "unconstrained" / "analysis" / "n2" / "rule_corr_player.csv",
    )
    assert result.written_paths[0].exists()
    assert result.written_paths[0].stat().st_size > 0
