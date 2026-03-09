from __future__ import annotations

from pathlib import Path

from srs_calculation.application.experiments import (
    render_real_dataset_feature_rule_heatmap,
    render_real_dataset_figures,
)
from srs_calculation.application.experiments import run_real_data_experiment as module


def _write(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_render_real_dataset_figures_writes_png(tmp_path, monkeypatch) -> None:
    dataset_base = tmp_path / "outputs" / "real" / "toy"
    _write(
        dataset_base / "rankings" / "game_toy.csv",
        [
            "player1,player2,score,rank,rank_shapley,rank_lexcel",
            "0,0,0.0,4,,",
            "1,0,1.0,3,2,1",
            "0,1,2.0,2,1,1",
            "1,1,3.0,1,,",
        ],
    )
    _write(
        dataset_base / "rankings" / "game_toy.features.yaml",
        [
            "features:",
            "- player: player1",
            "  column: a",
            "  label: Feature A",
            "- player: player2",
            "  column: b",
            "  label: Feature B",
        ],
    )

    def _fake_generate_real_ranking_figure(*, rankings_csv: Path, output_dir: Path, dpi: int, max_coalition_size: int) -> Path:
        out_path = output_dir / f"{rankings_csv.stem}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("png", encoding="utf-8")
        return out_path

    monkeypatch.setattr(module, "generate_real_ranking_figure", _fake_generate_real_ranking_figure)

    result = render_real_dataset_figures("toy", out_root=tmp_path / "outputs" / "real", dpi=80)

    assert len(result.written_paths) == 1
    assert result.written_paths[0].exists()
    assert result.written_paths[0].suffix == ".png"


def test_render_real_dataset_feature_rule_heatmap_writes_png(tmp_path, monkeypatch) -> None:
    dataset_base = tmp_path / "outputs" / "real" / "toy"
    _write(
        dataset_base / "rankings" / "game_toy.csv",
        [
            "player1,player2,score,rank,rank_shapley,rank_lexcel",
            "0,0,0.0,4,,",
            "1,0,1.0,3,2,1",
            "0,1,2.0,2,1,1",
            "1,1,3.0,1,1,2",
        ],
    )
    _write(
        dataset_base / "rankings" / "game_toy.features.yaml",
        [
            "features:",
            "- player: player1",
            "  column: a",
            "  label: Feature A",
            "- player: player2",
            "  column: b",
            "  label: Feature B",
        ],
    )
    _write(
        dataset_base / "schema.yaml",
        [
            "heatmaps:",
            "  feature_rule_max_coalition_size: 2",
        ],
    )

    def _fake_render_feature_rule_rank_heatmap(
        *,
        rankings_csv: Path,
        features_yaml: Path,
        out_path: Path,
        dpi: int,
        max_coalition_size: int,
        rule_labeler,
    ) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("png", encoding="utf-8")

    monkeypatch.setattr(module, "render_feature_rule_rank_heatmap", _fake_render_feature_rule_rank_heatmap)

    result = render_real_dataset_feature_rule_heatmap(
        "toy",
        out_root=tmp_path / "outputs" / "real",
        dpi=80,
    )

    assert result.out_path.exists()
    assert result.out_path.name == "feature_rule_rank.png"
