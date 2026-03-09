from __future__ import annotations

import csv

from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.ranking.result import RankingResult, RuleRankSet, RuleScoreSet
from srs_calculation.infrastructure.persistence.csv_ranking_repository import (
    serialize_legacy_ranking_columns,
    write_legacy_rankings_csv,
)


def test_serialize_legacy_ranking_columns_for_shapley_dense() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=3,
        scores_by_mask={
            0b000: 0.0,
            0b001: 4.0,
            0b010: 3.0,
            0b011: 7.0,
            0b100: 2.0,
            0b101: 6.0,
            0b110: 5.0,
            0b111: 8.0,
        },
    )
    result = RankingResult(
        rule_id="shapley",
        score_set=RuleScoreSet.from_mapping({0: 1.25, 1: 0.75, 2: 0.5}),
        rank_set=RuleRankSet.from_mapping({0: 1, 1: 2, 2: 3}),
    )

    columns = serialize_legacy_ranking_columns(game, result, rank_style="dense")

    assert set(columns) == {"score_shapley", "rank_shapley"}
    assert columns["score_shapley"] == {
        0b000: "",
        0b001: "1.25",
        0b010: "0.75",
        0b011: "",
        0b100: "0.5",
        0b101: "",
        0b110: "",
        0b111: "",
    }
    assert columns["rank_shapley"] == {
        0b000: "",
        0b001: "1",
        0b010: "2",
        0b011: "",
        0b100: "3",
        0b101: "",
        0b110: "",
        0b111: "",
    }


def test_serialize_legacy_ranking_columns_for_ordinal_banzhaf_uses_legacy_name() -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=2,
        scores_by_mask={
            0b00: 0.0,
            0b01: 2.0,
            0b10: 1.0,
            0b11: 3.0,
        },
    )
    result = RankingResult(
        rule_id="ordinal_banzhaf",
        score_set=RuleScoreSet.from_mapping({0: 5.0, 1: 1.0}),
        rank_set=RuleRankSet.from_mapping({0: 1, 1: 2}),
    )

    columns = serialize_legacy_ranking_columns(game, result)

    assert set(columns) == {"rank_o-banzhaf"}
    assert columns["rank_o-banzhaf"] == {
        0b00: "",
        0b01: "1",
        0b10: "2",
        0b11: "",
    }


def test_write_legacy_rankings_csv_writes_competition_ranks_and_canonical_header(tmp_path) -> None:
    game = CoalitionGame.from_scores_by_mask(
        player_count=3,
        scores_by_mask={
            0b000: 0.0,
            0b001: 4.0,
            0b010: 3.0,
            0b011: 7.0,
            0b100: 2.0,
            0b101: 6.0,
            0b110: 5.0,
            0b111: 8.0,
        },
    )
    results = [
        RankingResult(
            rule_id="lexcel",
            rank_set=RuleRankSet.from_mapping({0: 1, 1: 1, 2: 2}),
        ),
        RankingResult(
            rule_id="shapley",
            score_set=RuleScoreSet.from_mapping({0: 1.5, 1: 1.5, 2: 0.25}),
            rank_set=RuleRankSet.from_mapping({0: 1, 1: 1, 2: 2}),
        ),
    ]

    output_path = tmp_path / "rankings.csv"
    written_columns = write_legacy_rankings_csv(
        output_path,
        game,
        results,
        rank_style="competition",
    )

    assert written_columns == ("score_shapley", "rank_shapley", "rank_lexcel")

    with output_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))

    assert rows[0] == [
        "player1",
        "player2",
        "player3",
        "score",
        "rank",
        "score_shapley",
        "rank_shapley",
        "rank_lexcel",
    ]
    assert rows[1] == ["1", "1", "1", "8", "1", "", "", ""]
    assert rows[2] == ["1", "1", "0", "7", "2", "", "", ""]
    assert rows[5] == ["1", "0", "0", "4", "5", "1.5", "1", "1"]
    assert rows[6] == ["0", "1", "0", "3", "6", "1.5", "1", "1"]
    assert rows[7] == ["0", "0", "1", "2", "7", "0.25", "3", "3"]
    assert rows[8] == ["0", "0", "0", "0", "8", "", "", ""]
