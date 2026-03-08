from __future__ import annotations

import csv
from pathlib import Path

from gamegen.io.game_csv import GameTable
from gamegen.io.rankings_csv import write_rankings_with_columns, write_rankings_with_rank_column


def test_write_rankings_preserves_score_columns(tmp_path: Path) -> None:
    game = GameTable(
        n=2,
        scores_by_mask={0: 0, 1: 3, 2: 3, 3: 4},
        levels_by_mask={0: 3, 1: 2, 2: 2, 3: 1},
        masks_in_canonical_order=(3, 1, 2, 0),
    )

    rankings_path = tmp_path / "rankings.csv"

    score_shapley = {0: "", 1: "0.1", 2: "0.2", 3: "", 4: ""}  # extra key ignored
    rank_shapley = {0: "", 1: "2", 2: "1", 3: "", 4: ""}  # extra key ignored
    already_exists, cols = write_rankings_with_columns(
        rankings_path=rankings_path,
        game=game,
        new_columns={"score_shapley": score_shapley, "rank_shapley": rank_shapley},
        primary_column="rank_shapley",
    )
    assert already_exists is False
    assert "score_shapley" in cols
    assert "rank_shapley" in cols

    with rankings_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    assert header == [
        "player1",
        "player2",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
    ]

    idx_score_shap = header.index("score_shapley")
    idx_rank_shap = header.index("rank_shapley")

    # Singleton rows only.
    by_bits = {(int(r[0]), int(r[1])): r for r in rows}
    assert by_bits[(1, 0)][idx_score_shap] == "0.1"
    assert by_bits[(0, 1)][idx_score_shap] == "0.2"
    assert by_bits[(0, 0)][idx_score_shap] == ""
    assert by_bits[(1, 1)][idx_score_shap] == ""
    assert by_bits[(1, 0)][idx_rank_shap] == "2"
    assert by_bits[(0, 1)][idx_rank_shap] == "1"

    # Applying another rank rule should not drop score_shapley.
    write_rankings_with_rank_column(
        rankings_path=rankings_path,
        game=game,
        new_col_name="rank_lexcel",
        new_values_by_mask={0: "", 1: "1", 2: "1", 3: "", 4: ""},
    )
    with rankings_path.open("r", encoding="utf-8") as fh:
        header2 = next(csv.reader(fh))
    assert "score_shapley" in header2

