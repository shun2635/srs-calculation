from __future__ import annotations

import pandas as pd

from srs_calculation.infrastructure.plotting.heatmap_renderer import (
    feature_rule_rank_table,
    normalize_ranks_per_rule,
)


def _write(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_feature_rule_rank_table_builds_expected_rows(tmp_path) -> None:
    rankings_csv = tmp_path / "rankings" / "game_toy.csv"
    features_yaml = tmp_path / "rankings" / "game_toy.features.yaml"
    _write(
        rankings_csv,
        [
            "player1,player2,score,rank,rank_shapley,rank_lexcel",
            "0,0,0.0,4,,",
            "1,0,1.0,3,2,1",
            "0,1,2.0,2,1,1",
            "1,1,3.0,1,1,2",
        ],
    )
    _write(
        features_yaml,
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

    table, _feature_names, column_labels = feature_rule_rank_table(
        rankings_csv=rankings_csv,
        features_yaml=features_yaml,
        max_coalition_size=2,
        rule_labeler=lambda column: column.removeprefix("rank_"),
    )

    assert "{Feature A}" in table.index
    assert "{Feature B}" in table.index
    assert "{Feature A,Feature B}" in table.index
    assert column_labels == ["shapley", "lexcel"]


def test_normalize_ranks_per_rule_normalizes_each_column_independently() -> None:
    matrix = pd.DataFrame(
        {
            "rank_rule_small": [1, 5, 10],
            "rank_rule_large": [1, 5, 1000],
        },
        index=["a", "b", "c"],
    )

    normalized = normalize_ranks_per_rule(matrix)

    assert float(normalized.loc["b", "rank_rule_small"]) > float(normalized.loc["b", "rank_rule_large"])
