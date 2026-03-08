from __future__ import annotations

import csv
from pathlib import Path

from click.testing import CliRunner

from realgen.cli import main


def _write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def test_realgen_import_game_writes_game_csv_and_features(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "ontario_bridge_conditions"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    _write(
        dataset_dir / "ontario.csv",
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
            "raw_csv: ontario.csv",
            "score_column: value",
            "feature_columns: [a, b]",
            "feature_descriptions: {a: feature-a, b: feature-b}",
            "filters: {metric: accuracy, seed: 42}",
            "empty_score: 0.0",
        ],
    )

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "ontario_bridge_conditions",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    out_csv = out_base / "ontario_bridge_conditions" / "games" / "game_ontario_bridge_conditions.csv"
    out_yaml = out_base / "ontario_bridge_conditions" / "games" / "game_ontario_bridge_conditions.features.yaml"
    assert out_csv.exists()
    assert out_yaml.exists()

    with out_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert header == ["player1", "player2", "score", "rank"]
    assert len(rows) == 4  # 2^2


def test_realgen_import_game_rank_is_binned_via_config(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy"
    dataset_dir.mkdir(parents=True, exist_ok=True)
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
            "empty_score: 0.0",
        ],
    )

    cfg = tmp_path / "config.yaml"
    cfg.write_text("realgen:\n  import_rank_bins: 5\n", encoding="utf-8")

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "toy",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output

    out_csv = out_base / "toy" / "games" / "game_toy.csv"
    with out_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == ["player1", "player2", "score", "rank"]
    by_bits = {(int(r[0]), int(r[1])): r for r in rows}
    # bins=5 over [1,3] (exclude empty coalition) => width=0.4
    assert by_bits[(1, 1)][3] == "1"  # 3.0 in top bin
    assert by_bits[(0, 1)][3] == "3"  # 2.0
    assert by_bits[(1, 0)][3] == "5"  # 1.0 (min non-empty)
    assert by_bits[(0, 0)][3] == "5"  # 0.0


def test_realgen_import_game_supports_score_transform_and_dense_rank(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy_transform"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    _write(
        dataset_dir / "raw.csv",
        [
            "a,b,value",
            "0,0,1.0",
            "1,0,0.2",
            "0,1,0.4",
            "1,1,0.3",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: raw.csv",
            "score_column: value",
            "score_transform: negate",
            "rank_method: dense",
            "feature_columns: [a, b]",
        ],
    )

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "toy_transform",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    out_csv = out_base / "toy_transform" / "games" / "game_toy_transform.csv"
    with out_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == ["player1", "player2", "score", "rank"]
    by_bits = {(int(r[0]), int(r[1])): r for r in rows}
    assert float(by_bits[(1, 0)][2]) == -0.2
    assert by_bits[(1, 0)][3] == "1"
    assert by_bits[(1, 1)][3] == "2"
    assert by_bits[(0, 1)][3] == "3"
    assert by_bits[(0, 0)][3] == "4"


def test_realgen_import_game_uses_rank_column_if_provided(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy_ranked"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    _write(
        dataset_dir / "raw.csv",
        [
            "a,b,value,class_id",
            "0,0,0.0,4",
            "1,0,1.0,3",
            "0,1,2.0,2",
            "1,1,3.0,1",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: raw.csv",
            "score_column: value",
            "rank_column: class_id",
            "feature_columns: [a, b]",
        ],
    )

    cfg = tmp_path / "config.yaml"
    # This would change ranks if binning were used; rank_column must override it.
    cfg.write_text("realgen:\n  import_rank_bins: 1\n", encoding="utf-8")

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "toy_ranked",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output

    out_csv = out_base / "toy_ranked" / "games" / "game_toy_ranked.csv"
    with out_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == ["player1", "player2", "score", "rank"]
    by_bits = {(int(r[0]), int(r[1])): r for r in rows}
    assert by_bits[(0, 0)][3] == "4"
    assert by_bits[(1, 0)][3] == "3"
    assert by_bits[(0, 1)][3] == "2"
    assert by_bits[(1, 1)][3] == "1"


def test_realgen_import_game_allow_incomplete(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "credit_g"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    _write(
        dataset_dir / "game_table.csv",
        [
            "a,b,c,value,metric,seed",
            "1,0,0,0.7,accuracy,42",
            "0,1,0,0.71,accuracy,42",
            "0,0,1,0.72,accuracy,42",
            "1,1,0,0.75,accuracy,42",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: game_table.csv",
            "score_column: value",
            "feature_columns: [a, b, c]",
            "filters: {metric: accuracy, seed: 42}",
            "allow_incomplete: true",
        ],
    )

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "credit_g",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    out_csv = out_base / "credit_g" / "games" / "game_credit_g.csv"
    assert out_csv.exists()
    # Should have exactly the observed coalitions (no completeness requirement).
    with out_csv.open("r", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 1 + 4


def test_realgen_import_game_auto_detects_feature_columns(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "credit_g"
    dataset_dir.mkdir(parents=True, exist_ok=True)
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

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "credit_g",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    out_csv = out_base / "credit_g" / "games" / "game_credit_g.csv"
    with out_csv.open("r", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header[:2] == ["player1", "player2"]


def test_realgen_apply_rules_produces_group_columns(tmp_path: Path) -> None:
    # Prepare imported game CSV directly.
    out_base = tmp_path / "out"
    dataset_out = out_base / "toy"
    games_dir = dataset_out / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    (games_dir / "game_toy.csv").write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0.0,4",
                "1,0,0.2,3",
                "0,1,0.3,2",
                "1,1,0.5,1",
            ]
        ),
        encoding="utf-8",
    )
    (games_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "- player: player2",
                "  column: b",
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "toy",
            "--rules",
            "g-shapley",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    rankings_csv = out_base / "toy" / "rankings" / "game_toy.csv"
    assert rankings_csv.exists()
    text = rankings_csv.read_text(encoding="utf-8")
    assert "rank_g-shapley" in text
    assert (out_base / "toy" / "rankings" / "game_toy.features.yaml").exists()


def test_realgen_apply_rules_uses_schema_rules_by_default(tmp_path: Path) -> None:
    inputs_root = tmp_path / "inputs"
    dataset_dir = inputs_root / "toy_schema_rules"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    _write(
        dataset_dir / "raw.csv",
        [
            "a,b,value",
            "0,0,0.0",
            "1,0,0.2",
            "0,1,0.3",
            "1,1,0.5",
        ],
    )
    _write(
        dataset_dir / "schema.yaml",
        [
            "raw_csv: raw.csv",
            "score_column: value",
            "feature_columns: [a, b]",
            "empty_score: 0.0",
            "rules: [lexcel]",
        ],
    )

    out_base = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "import-game",
            "toy_schema_rules",
            "--inputs-root",
            str(inputs_root),
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output

    cfg = tmp_path / "config.yaml"
    cfg.write_text("pipeline:\n  rules: [shapley]\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "apply-rules",
            "toy_schema_rules",
            "--out",
            str(out_base),
            "--config",
            str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output

    rankings_csv = out_base / "toy_schema_rules" / "rankings" / "game_toy_schema_rules.csv"
    text = rankings_csv.read_text(encoding="utf-8")
    assert "rank_lexcel" in text
    assert "rank_shapley" not in text


def test_realgen_apply_rules_incomplete_supports_more_rank_based_rules(tmp_path: Path) -> None:
    # Incomplete coalition table with 3 players.
    out_base = tmp_path / "out"
    dataset_out = out_base / "credit_g"
    games_dir = dataset_out / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    (games_dir / "game_credit_g.csv").write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank",
                "1,0,0,0.7,1",
                "0,1,0,0.71,1",
                "0,0,1,0.72,1",
                "1,1,0,0.75,1",
            ]
        ),
        encoding="utf-8",
    )
    (games_dir / "game_credit_g.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "- player: player2",
                "  column: b",
                "- player: player3",
                "  column: c",
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "credit_g",
            "--rules",
            "o-banzhaf",
            "--rules",
            "g-o-banzhaf",
            "--rules",
            "rp-index",
            "--rules",
            "ud",
            "--rules",
            "du",
            "--rules",
            "red-index",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    rankings_csv = dataset_out / "rankings" / "game_credit_g.csv"
    text = rankings_csv.read_text(encoding="utf-8")
    assert "rank_o-banzhaf" in text
    assert "rank_g-o-banzhaf" in text
    assert "rank_rp-index" in text
    assert "rank_ud" in text
    assert "rank_du" in text
    assert "rank_red-index" in text


def test_realgen_apply_rules_incomplete_can_compute_group_shapley(tmp_path: Path) -> None:
    # Incomplete coalition table with 2 players; g-shapley should not crash.
    out_base = tmp_path / "out"
    dataset_out = out_base / "toy2"
    games_dir = dataset_out / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    (games_dir / "game_toy2.csv").write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "1,0,1.0,1",
                "0,1,2.0,1",
                "1,1,3.0,1",
            ]
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "toy2",
            "--rules",
            "g-shapley",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    rankings_csv = dataset_out / "rankings" / "game_toy2.csv"
    text = rankings_csv.read_text(encoding="utf-8")
    assert "rank_g-shapley" in text


def test_realgen_apply_rules_skips_intractable_rules_for_large_n(tmp_path: Path) -> None:
    # n=16 triggers the hard guard; include one tractable rule so output is written.
    out_base = tmp_path / "out"
    dataset_out = out_base / "big"
    games_dir = dataset_out / "games"
    games_dir.mkdir(parents=True, exist_ok=True)

    header = [f"player{i}" for i in range(1, 17)] + ["score", "rank"]
    # Only 2 rows; lexcel is fine on observed masks.
    row1 = ["1"] + ["0"] * 15 + ["1.0", "1"]
    row2 = ["0", "1"] + ["0"] * 14 + ["0.5", "2"]
    (games_dir / "game_big.csv").write_text(
        "\n".join([",".join(header), ",".join(row1), ",".join(row2)]),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "apply-rules",
            "big",
            "--rules",
            "lexcel",
            "--rules",
            "shapley-interaction",
            "--out",
            str(out_base),
        ],
    )
    assert result.exit_code == 0, result.output
    rankings_csv = dataset_out / "rankings" / "game_big.csv"
    text = rankings_csv.read_text(encoding="utf-8")
    assert "rank_lexcel" in text
    assert "rank_shapley-interaction" not in text


def test_realgen_figures_filter_by_coalition_size(tmp_path: Path) -> None:
    pytest = __import__("pytest")  # lazy import to keep this test optional-ish
    pd = pytest.importorskip("pandas")
    plt = pytest.importorskip("matplotlib.pyplot")

    from realgen.figures_png import _filter_by_coalition_size

    df = pd.DataFrame(
        [
            {"player1": 1, "player2": 1, "player3": 1, "player4": 1, "score": 1.0, "rank": 1},
            {"player1": 1, "player2": 0, "player3": 1, "player4": 0, "score": 0.9, "rank": 2},
        ]
    )
    out = _filter_by_coalition_size(df, ["player1", "player2", "player3", "player4"], max_size=3)
    assert len(out) == 1
    assert int(out.iloc[0]["player4"]) == 0


def test_realgen_rank_occurrence_distribution_heatmap_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")
    pd = pytest.importorskip("pandas")

    from realgen.figures_png import generate_rank_occurrence_distribution_heatmap

    out_dir = tmp_path / "figs"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = tmp_path / "game_toy.csv"

    df = pd.DataFrame(
        [
            {"player1": 1, "player2": 0, "score": 1.0, "rank": 1},
            {"player1": 0, "player2": 1, "score": 0.9, "rank": 2},
            {"player1": 1, "player2": 1, "score": 0.8, "rank": 2},
        ]
    )
    df.to_csv(rankings_csv, index=False)

    p1 = generate_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv, output_dir=out_dir, out_name="lexcel_rank_counts.png", dpi=80
    )
    assert p1.exists()
    p2 = generate_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        out_name="lexcel_rank_counts_size2.png",
        coalition_size=2,
        dpi=80,
    )
    assert p2.exists()


def test_realgen_pair_rank_occurrence_distribution_heatmap_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")
    pd = pytest.importorskip("pandas")

    from realgen.figures_png import generate_kset_rank_occurrence_distribution_heatmap

    out_dir = tmp_path / "figs"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = tmp_path / "game_toy.csv"

    # Coalitions (rows) with ranks; pairs will be counted as subsets of coalitions.
    df = pd.DataFrame(
        [
            {"player1": 1, "player2": 1, "player3": 0, "score": 1.0, "rank": 1},  # pair (1,2) at level 1
            {"player1": 1, "player2": 0, "player3": 1, "score": 0.9, "rank": 2},  # pair (1,3) at level 2
            {"player1": 1, "player2": 1, "player3": 1, "score": 0.8, "rank": 2},  # pairs (1,2),(1,3),(2,3) at level 2
        ]
    )
    df.to_csv(rankings_csv, index=False)

    p = generate_kset_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        out_name="lexcel_rank_counts_size2.png",
        subset_size=2,
        dpi=80,
    )
    assert p.exists()
    p3 = generate_kset_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        out_name="lexcel_rank_counts_size3.png",
        subset_size=3,
        dpi=80,
    )
    assert p3.exists()


def test_realgen_kset_rank_occurrence_distribution_heatmap_supports_focus_features(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")
    pd = pytest.importorskip("pandas")

    from realgen.figures_png import generate_kset_rank_occurrence_distribution_heatmap

    out_dir = tmp_path / "figs"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = tmp_path / "game_toy.csv"

    df = pd.DataFrame(
        [
            {"player1": 1, "player2": 1, "player3": 0, "score": 1.0, "rank": 1},
            {"player1": 0, "player2": 1, "player3": 1, "score": 0.9, "rank": 2},
            {"player1": 1, "player2": 0, "player3": 1, "score": 0.8, "rank": 2},
        ]
    )
    df.to_csv(rankings_csv, index=False)

    # For k=2, focus on player1 => keep {player1,player2} and {player1,player3}, drop {player2,player3}.
    p = generate_kset_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        out_name="focused.png",
        subset_size=2,
        focus_features=["player1"],
        dpi=80,
    )
    assert p.exists()


def test_realgen_feature_rule_heatmap_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")
    pd = pytest.importorskip("pandas")

    dataset_dir = tmp_path / "out" / "toy"
    rankings_dir = dataset_dir / "rankings"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Minimal rankings CSV with 2 players and 2 rules.
    df = pd.DataFrame(
        [
            # empty
            {"player1": 0, "player2": 0, "score": 0.0, "rank": 4, "rank_shapley": None, "rank_g-shapley": None},
            # singleton 1
            {"player1": 1, "player2": 0, "score": 1.0, "rank": 3, "rank_shapley": 2, "rank_g-shapley": 3},
            # singleton 2
            {"player1": 0, "player2": 1, "score": 2.0, "rank": 2, "rank_shapley": 1, "rank_g-shapley": 2},
            # pair
            {"player1": 1, "player2": 1, "score": 3.0, "rank": 1, "rank_shapley": None, "rank_g-shapley": 1},
        ]
    )
    rankings_csv = rankings_dir / "game_toy.csv"
    df.to_csv(rankings_csv, index=False)

    (rankings_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.heatmaps import render_feature_rule_rank_heatmap

    out_path = dataset_dir / "heatmaps" / "feature_rule_rank.png"
    render_feature_rule_rank_heatmap(
        rankings_csv=rankings_csv,
        features_yaml=rankings_dir / "game_toy.features.yaml",
        out_path=out_path,
        dpi=80,
        max_coalition_size=2,
    )
    assert out_path.exists()

    from realgen.heatmaps import feature_rule_rank_table

    table, _features, _rules = feature_rule_rank_table(
        rankings_csv=rankings_csv,
        features_yaml=rankings_dir / "game_toy.features.yaml",
        max_coalition_size=2,
    )
    # size<=2 includes {特徴A}, {特徴B}, {特徴A,特徴B}
    assert "{特徴A}" in table.index
    assert "{特徴B}" in table.index
    assert "{特徴A,特徴B}" in table.index


def test_realgen_heatmap_per_rule_normalization_changes_color_scale() -> None:
    pd = __import__("pytest").importorskip("pandas")
    from realgen.heatmaps import normalize_ranks_per_rule

    mat = pd.DataFrame(
        {
            # narrow range 1..10
            "rank_rule_small": [1, 5, 10],
            # wide range 1..1000
            "rank_rule_large": [1, 5, 1000],
        },
        index=["a", "b", "c"],
    )
    norm = normalize_ranks_per_rule(mat)
    # Same absolute rank=5 should normalize much smaller under the wide-range rule.
    assert float(norm.loc["b", "rank_rule_small"]) > float(norm.loc["b", "rank_rule_large"])


def test_realgen_make_figures_writes_interaction_index_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    dataset_dir = tmp_path / "out" / "wine"
    rankings_dir = dataset_dir / "rankings"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    # Minimal rankings CSV with interaction/rp-index columns on coalitions.
    (rankings_dir / "game_wine.csv").write_text(
        "\n".join(
            [
                "player1,player2,score,rank,rank_shapley-interaction,score_shapley-interaction,rank_banzhaf-interaction,score_banzhaf-interaction,rank_rp-index,score_rp-index",
                "0,0,0.0,4,,,,,,,",
                "1,0,1.0,3,2,0.1,3,0.2,2,10",
                "0,1,2.0,2,3,0.05,2,0.3,3,5",
                "1,1,3.0,1,1,0.5,1,0.6,1,20",
            ]
        ),
        encoding="utf-8",
    )
    (rankings_dir / "game_wine.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_interaction_index_figure

    out_dir = dataset_dir / "figures"
    generate_interaction_index_figure(
        rankings_csv=rankings_dir / "game_wine.csv",
        output_dir=out_dir,
        dpi=80,
        top_k=30,
    )
    out_png = out_dir / "interaction_index.png"
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_red_index_topk_by_size_figures_writes_pngs(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "rankings.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,score_red-index",
                "0,0,0,0.0,4,",
                "1,0,0,1.0,3,5",
                "0,1,0,1.0,3,6",
                "0,0,1,1.0,3,7",
                "1,1,0,2.0,2,10",
                "1,0,1,2.0,2,11",
                "0,1,1,2.0,2,12",
                "1,1,1,3.0,1,20",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "rankings.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: A",
                "- player: player2",
                "  column: b",
                "  label: B",
                "- player: player3",
                "  column: c",
                "  label: C",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_red_index_topk_by_size_figures

    figs = generate_red_index_topk_by_size_figures(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        dpi=80,
        top_k=30,
    )
    # Sizes 1..3 all have at least one coalition.
    assert len(figs) == 3
    for p in figs:
        assert p.exists()
        assert p.stat().st_size > 0


def test_realgen_generate_red_index_scatter_plot_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "rankings.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,score_red-index",
                "0,0,0,0.0,4,",
                "1,0,0,1.0,3,5",
                "0,1,0,1.0,3,6",
                "0,0,1,1.0,3,7",
                "1,1,0,2.0,2,10",
                "1,0,1,2.0,2,11",
                "0,1,1,2.0,2,12",
                "1,1,1,3.0,1,20",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_red_index_scatter_plot

    out_png = generate_red_index_scatter_plot(rankings_csv=rankings_csv, output_dir=out_dir, dpi=80)
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_shapley_values_plot_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "game_toy.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,score,rank,score_shapley,rank_shapley",
                "0,0,0.0,4,,",
                "1,0,1.0,3,0.1,2",
                "0,1,2.0,2,0.2,1",
                "1,1,3.0,1,,",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_shapley_values_plot

    out_png = generate_shapley_values_plot(rankings_csv=rankings_csv, output_dir=out_dir, dpi=80)
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_ordinal_banzhaf_values_plot_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "game_toy.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,rank",
                "0,0,4",
                "1,0,3",
                "0,1,2",
                "1,1,1",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_ordinal_banzhaf_values_plot

    out_png = generate_ordinal_banzhaf_values_plot(rankings_csv=rankings_csv, output_dir=out_dir, dpi=80)
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_lexcel_rank_count_heatmap_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "game_toy.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,score,rank",
                "0,0,0.0,3",
                "1,0,1.0,2",
                "0,1,1.0,2",
                "1,1,2.0,1",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_lexcel_rank_count_heatmap

    out_png = generate_lexcel_rank_count_heatmap(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        dpi=80,
        out_name="lexcel_rank_counts.png",
    )
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_rp_index_top_size2_figure_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "game_crop.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank,rank_rp-index,score_rp-index",
                "0,0,0,0.0,3,,,",
                "1,0,0,1.0,2,5,10",
                "0,1,0,1.0,2,6,11",
                "0,0,1,1.0,2,7,12",
                "1,1,0,2.0,1,1,100",
                "1,0,1,2.0,1,2,90",
                "0,1,1,2.0,1,3,80",
                "1,1,1,3.0,1,4,70",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "game_crop.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
                "- player: player3",
                "  column: c",
                "  label: 特徴C",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_rp_index_top_size2_figure

    out_png = generate_rp_index_top_size2_figure(
        rankings_csv=rankings_csv,
        output_dir=out_dir,
        dpi=80,
        top_k=10,
        coalition_size=2,
        out_name="rp_index_top_size2_k10.png",
    )
    assert out_png.exists()
    assert out_png.stat().st_size > 0


def test_realgen_generate_give_topk_table_writes_png(tmp_path: Path) -> None:
    pytest = __import__("pytest")
    pytest.importorskip("matplotlib")

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    rankings_csv = out_dir / "game_toy.csv"
    rankings_csv.write_text(
        "\n".join(
            [
                "player1,player2,player3,score,rank",
                "0,0,0,0.0,4",
                # singletons
                "1,0,0,0.0,3",
                "0,1,0,0.0,3",
                "0,0,1,0.0,3",
                # size-2 coalitions
                "1,1,0,0.0,2",
                "1,0,1,0.0,1",
                "0,1,1,0.0,2",
                # size-3 coalition
                "1,1,1,0.0,1",
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "game_toy.features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "- player: player1",
                "  column: a",
                "  label: 特徴A",
                "- player: player2",
                "  column: b",
                "  label: 特徴B",
                "- player: player3",
                "  column: c",
                "  label: 特徴C",
            ]
        ),
        encoding="utf-8",
    )

    from realgen.figures_png import generate_give_topk_table

    out_png = generate_give_topk_table(rankings_csv=rankings_csv, output_dir=out_dir, dpi=80, top_k=10)
    assert out_png.exists()
    assert out_png.stat().st_size > 0
