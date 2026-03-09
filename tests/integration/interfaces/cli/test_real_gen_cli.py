from __future__ import annotations

import csv

from click.testing import CliRunner

from srs_calculation.interfaces.cli.real_gen import main


def _write(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_real_gen_cli_help_lists_supported_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "import-game" in result.output
    assert "apply-rules" in result.output


def test_real_gen_import_game_writes_dataset_artifacts(tmp_path) -> None:
    inputs_root = tmp_path / "inputs"
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
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "toy",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(tmp_path / "outputs" / "real"),
        ],
    )

    assert result.exit_code == 0
    assert "wrote game CSV" in result.output

    game_csv_path = tmp_path / "outputs" / "real" / "toy" / "games" / "game_toy.csv"
    assert game_csv_path.exists()


def test_real_gen_apply_rules_uses_dataset_layout_and_schema_rules(tmp_path) -> None:
    out_root = tmp_path / "outputs" / "real"
    dataset_base = out_root / "wine"
    _write(
        dataset_base / "games" / "game_wine.csv",
        [
            "player1,player2,score,rank",
            "1,1,4,1",
            "1,0,1,2",
            "0,1,1,2",
            "0,0,0,3",
        ],
    )
    _write(
        dataset_base / "schema.yaml",
        [
            "rules:",
            "  - lexcel",
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "wine",
            "--out",
            str(out_root),
        ],
    )

    assert result.exit_code == 0
    assert "processed 1 game(s) for dataset wine with 1 rule(s)" in result.output

    rankings_csv_path = dataset_base / "rankings" / "game_wine.csv"
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "rank_lexcel",
    ]
