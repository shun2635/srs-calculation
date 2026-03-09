from __future__ import annotations

import csv

from srs_calculation.application.ranking import apply_ranking_rules_to_real_dataset


def _write(path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_apply_ranking_rules_to_real_dataset_uses_schema_rules_by_default(tmp_path) -> None:
    out_root = tmp_path / "outputs" / "real"
    dataset_base = out_root / "toy"
    _write(
        dataset_base / "games" / "game_toy.csv",
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
            "  - shapley",
            "  - ordinal_banzhaf",
        ],
    )

    result = apply_ranking_rules_to_real_dataset(
        "toy",
        out_root=out_root,
    )

    assert result.rule_ids == ("shapley", "ordinal_banzhaf")
    assert len(result.csv_results) == 1

    rankings_csv_path = dataset_base / "rankings" / "game_toy.csv"
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
        "rank_o-banzhaf",
    ]
