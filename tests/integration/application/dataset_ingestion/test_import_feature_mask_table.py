from __future__ import annotations

import csv

from srs_calculation.application.dataset_ingestion import import_feature_mask_dataset


def _write(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_import_feature_mask_dataset_writes_game_csv_and_features_yaml(tmp_path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy"
    _write(
        dataset_dir / "raw.csv",
        [
            "a,b,value,metric,seed",
            "1,0,0.2,accuracy,42",
            "0,1,0.3,accuracy,42",
            "1,1,0.5,accuracy,42",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: raw.csv",
            "score_column: value",
            "feature_columns: [a, b]",
            "feature_descriptions: {a: feature-a, b: feature-b}",
            "filters: {metric: accuracy, seed: 42}",
            "empty_score: 0.0",
        ],
    )

    result = import_feature_mask_dataset(
        "toy",
        inputs_root=inputs_root,
        out_root=tmp_path / "outputs" / "real",
    )

    assert result.game_csv_path.exists()
    assert result.features_yaml_path.exists()
    assert result.copied_schema_path.exists()

    with result.game_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == ["player1", "player2", "score", "rank"]
    assert len(rows) == 5
    assert "column: a" in result.features_yaml_path.read_text(encoding="utf-8")


def test_import_feature_mask_dataset_uses_configured_binned_ranks(tmp_path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy_bins"
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
        ],
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text("realgen:\n  import_rank_bins: 5\n", encoding="utf-8")

    result = import_feature_mask_dataset(
        "toy_bins",
        inputs_root=inputs_root,
        out_root=tmp_path / "outputs" / "real",
        config_path=config_path,
    )

    with result.game_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    by_bits = {(int(row[0]), int(row[1])): row for row in rows[1:]}
    assert by_bits[(1, 1)][3] == "1"
    assert by_bits[(0, 1)][3] == "3"
    assert by_bits[(1, 0)][3] == "5"
    assert by_bits[(0, 0)][3] == "5"


def test_import_feature_mask_dataset_auto_detects_feature_columns(tmp_path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "credit_g"
    _write(
        dataset_dir / "game_table.csv",
        [
            "f1,f2,order,value,metric,seed",
            "1,0,1,0.7,accuracy,42",
            "0,1,1,0.71,accuracy,42",
            "1,1,1,0.75,accuracy,42",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: game_table.csv",
            "score_column: value",
            "feature_exclude: [order, metric, seed]",
            "filters: {metric: accuracy, seed: 42}",
            "empty_score: 0.0",
            "allow_incomplete: true",
        ],
    )

    result = import_feature_mask_dataset(
        "credit_g",
        inputs_root=inputs_root,
        out_root=tmp_path / "outputs" / "real",
    )

    with result.game_csv_path.open("r", encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))

    assert header[:2] == ["player1", "player2"]
