from __future__ import annotations

import csv

from srs_calculation.application.axiom_evaluation import (
    evaluate_synthetic_axioms,
    render_synthetic_axiom_summary_heatmaps,
)
from srs_calculation.application.game_generation import generate_synthetic_games
from srs_calculation.application.ranking.apply_ranking_rules_to_game_csv import apply_ranking_rules_in_directory


def test_evaluate_synthetic_axioms_writes_summary_and_heatmap(tmp_path) -> None:
    out_dir = tmp_path / "outputs"
    generated = generate_synthetic_games(
        players=2,
        count=1,
        max_score=3,
        seed=1,
        out_dir=out_dir,
    )
    rankings_dir = out_dir / "synthetic" / "unconstrained" / "rankings" / "n2"
    apply_ranking_rules_in_directory(
        generated.games_dir,
        rankings_dir,
        ["group_shapley", "shapley"],
    )

    result = evaluate_synthetic_axioms(
        players=2,
        out_dir=out_dir,
        scope="coalition",
        dpi=80,
    )

    coalition_report = result.reports[0]
    assert coalition_report.summary_csv_path is not None
    assert coalition_report.summary_heatmap_path is not None
    assert coalition_report.summary_csv_path.exists()
    assert coalition_report.summary_heatmap_path.exists()

    with coalition_report.summary_csv_path.open("r", encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))

    assert header == ["rule", "axiom", "constraints", "satisfied", "satisfied_rate"]


def test_render_synthetic_axiom_summary_heatmaps_renders_existing_summary(tmp_path) -> None:
    summary_dir = (
        tmp_path
        / "outputs"
        / "synthetic"
        / "unconstrained"
        / "analysis"
        / "n2"
        / "axiom"
        / "coalition"
    )
    summary_dir.mkdir(parents=True, exist_ok=True)
    (summary_dir / "summary.csv").write_text(
        "\n".join(
            [
                "rule,axiom,constraints,satisfied,satisfied_rate",
                "group_shapley,redundancy,1,1,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = render_synthetic_axiom_summary_heatmaps(
        players=2,
        out_dir=tmp_path / "outputs",
        scope="coalition",
        dpi=80,
    )

    assert result.written_paths == (summary_dir / "summary_heatmap.png",)
    assert result.written_paths[0].exists()
