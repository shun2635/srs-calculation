from __future__ import annotations

import csv
from pathlib import Path

from click.testing import CliRunner

from srs_calculation.interfaces.cli.real_gen import main


def _write(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_real_data_cli_workflow_generates_rankings_and_heatmap(tmp_path: Path) -> None:
    runner = CliRunner()
    inputs_root = tmp_path / "inputs"
    out_root = tmp_path / "outputs" / "real"
    dataset_dir = inputs_root / "toy"

    _write(
        dataset_dir / "raw.csv",
        [
            "a,b,value",
            "0,0,0.0",
            "1,0,1.0",
            "0,1,2.0",
            "1,1,3.0",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: raw.csv",
            "score_column: value",
            "feature_columns: [a, b]",
            "rules:",
            "  - shapley",
            "  - lexcel",
            "heatmaps:",
            "  feature_rule_max_coalition_size: 2",
        ],
    )

    import_result = runner.invoke(
        main,
        [
            "import-game",
            "toy",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_root),
        ],
    )

    assert import_result.exit_code == 0
    assert "wrote game CSV" in import_result.output
    assert "wrote feature labels" in import_result.output

    game_csv_path = out_root / "toy" / "games" / "game_toy.csv"
    features_yaml_path = out_root / "toy" / "games" / "game_toy.features.yaml"
    assert game_csv_path.exists()
    assert features_yaml_path.exists()

    apply_result = runner.invoke(
        main,
        [
            "apply-rules",
            "toy",
            "--out",
            str(out_root),
        ],
    )

    assert apply_result.exit_code == 0
    assert "processed 1 game(s) for dataset toy with 2 rule(s)" in apply_result.output

    rankings_csv_path = out_root / "toy" / "rankings" / "game_toy.csv"
    rankings_features_yaml_path = out_root / "toy" / "rankings" / "game_toy.features.yaml"
    assert rankings_csv_path.exists()
    assert rankings_features_yaml_path.exists()

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

    heatmap_result = runner.invoke(
        main,
        [
            "feature-rule-heatmap",
            "toy",
            "--out",
            str(out_root),
            "--dpi",
            "80",
        ],
    )

    assert heatmap_result.exit_code == 0
    assert "saved heatmap:" in heatmap_result.output

    heatmap_path = out_root / "toy" / "heatmaps" / "feature_rule_rank.png"
    assert heatmap_path.exists()
    assert heatmap_path.stat().st_size > 0
