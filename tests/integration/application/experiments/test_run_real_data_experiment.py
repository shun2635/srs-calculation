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

    assert any(path.name == "game_toy.png" for path in result.written_paths)
    assert all(path.exists() for path in result.written_paths)
    assert all(path.suffix == ".png" for path in result.written_paths)


def test_render_real_dataset_figures_invokes_extra_generators_for_canonical_game(tmp_path, monkeypatch) -> None:
    dataset_base = tmp_path / "outputs" / "real" / "wine"
    _write(
        dataset_base / "rankings" / "game_wine.csv",
        [
            "player1,player2,score,rank,score_shapley,score_red-index,rank_rp-index,score_rp-index,rank_shapley-interaction,score_shapley-interaction",
            "0,0,0.0,4,,,,,,",
            "1,0,1.0,3,0.1,1,2,10,2,0.3",
            "0,1,2.0,2,0.2,2,1,20,1,0.4",
            "1,1,3.0,1,,3,1,30,1,0.5",
        ],
    )
    _write(
        dataset_base / "rankings" / "game_wine.features.yaml",
        [
            "features:",
            "- player: player1",
            "  column: a",
            "- player: player2",
            "  column: b",
        ],
    )
    _write(
        dataset_base / "schema.yaml",
        [
            "figures:",
            "  interaction_index_size2: true",
            "  rank_occurrence_size2: true",
        ],
    )

    called: list[str] = []

    def _mark(name: str):
        def _fn(*args, **kwargs):
            out_path = kwargs.get("output_dir", dataset_base / "figures") / {
                "generate_real_ranking_figure": "game_wine.png",
                "generate_interaction_index_figure": kwargs.get("out_name", "interaction_index.png"),
                "generate_red_index_scatter_plot": "red_index_scatter.png",
                "generate_shapley_values_plot": "shapley_values.png",
                "generate_ordinal_banzhaf_values_plot": "ordinal_banzhaf_values.png",
                "generate_lexcel_rank_count_heatmap": "lexcel_rank_counts.png",
                "generate_rank_occurrence_distribution_heatmap": kwargs.get("out_name", "rank_occurrence_distribution.png"),
                "generate_rp_index_top_size2_figure": "rp_index_top_size2_k10.png",
                "generate_give_topk_table": "give_top10.png",
            }.get(name, "generated.png")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(name, encoding="utf-8")
            called.append(name)
            if name == "generate_red_index_topk_by_size_figures":
                extra = kwargs.get("output_dir", dataset_base / "figures") / "red_index_top01_k10.png"
                extra.write_text(name, encoding="utf-8")
                return [extra]
            return out_path

        return _fn

    for name in [
        "generate_real_ranking_figure",
        "generate_interaction_index_figure",
        "generate_red_index_topk_by_size_figures",
        "generate_red_index_scatter_plot",
        "generate_shapley_values_plot",
        "generate_ordinal_banzhaf_values_plot",
        "generate_lexcel_rank_count_heatmap",
        "generate_rank_occurrence_distribution_heatmap",
        "generate_rp_index_top_size2_figure",
        "generate_give_topk_table",
    ]:
        monkeypatch.setattr(module, name, _mark(name))

    result = render_real_dataset_figures("wine", out_root=tmp_path / "outputs" / "real", dpi=80)

    assert "generate_real_ranking_figure" in called
    assert "generate_interaction_index_figure" in called
    assert "generate_shapley_values_plot" in called
    assert "generate_ordinal_banzhaf_values_plot" in called
    assert "generate_rp_index_top_size2_figure" in called
    assert "generate_give_topk_table" in called
    assert len(result.written_paths) >= 6


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
