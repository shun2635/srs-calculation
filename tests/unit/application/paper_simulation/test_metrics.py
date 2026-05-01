from __future__ import annotations

import pytest

from srs_calculation.application.paper_simulation.metrics import (
    evaluate_gl_rp_rank_correlation,
    evaluate_reversal_consistency,
    summarize_lens_consistency,
)
from srs_calculation.domain.games.coalition_game import CoalitionGame


def _game(base_ranks_by_mask: dict[int, int]) -> CoalitionGame:
    scores = {mask: float(20 - rank) for mask, rank in base_ranks_by_mask.items()}
    return CoalitionGame.from_scores_by_mask(3, scores, base_ranks_by_mask=base_ranks_by_mask)


def test_reversal_consistency_empty_constraints_are_na() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 1,
            0b100: 1,
            0b011: 3,
            0b101: 2,
            0b110: 3,
            0b111: 4,
        }
    )

    rows = evaluate_reversal_consistency(
        game_id="game_000001",
        game=game,
        rp_rank_by_mask={0b011: 1, 0b101: 2, 0b110: 3},
        target_sizes=(2,),
    )

    assert rows[0].consistency_rate is None
    assert rows[0].is_empty_constraints is True


def test_reversal_consistency_requires_strict_satisfaction() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 2,
            0b100: 3,
            0b011: 3,
            0b101: 1,
            0b110: 3,
            0b111: 4,
        }
    )

    tied = evaluate_reversal_consistency(
        game_id="game_000001",
        game=game,
        rp_rank_by_mask={0b011: 1, 0b101: 1, 0b110: 3},
        target_sizes=(2,),
    )
    strict = evaluate_reversal_consistency(
        game_id="game_000001",
        game=game,
        rp_rank_by_mask={0b011: 2, 0b101: 1, 0b110: 1},
        target_sizes=(2,),
    )

    assert tied[0].consistency_rate == 0.0
    assert strict[0].consistency_rate == 1.0


def test_lens_summary_empty_policy_options() -> None:
    game = _game(
        {
            0b000: 9,
            0b001: 1,
            0b010: 1,
            0b100: 1,
            0b011: 3,
            0b101: 2,
            0b110: 3,
            0b111: 4,
        }
    )
    rows = evaluate_reversal_consistency(
        game_id="game_000001",
        game=game,
        rp_rank_by_mask={0b011: 1, 0b101: 2, 0b110: 3},
        target_sizes=(2,),
    )

    assert summarize_lens_consistency(rows, empty_policy="exclude")[0].num_valid_games == 0
    assert summarize_lens_consistency(rows, empty_policy="zero")[0].mean_consistency == 0.0
    assert summarize_lens_consistency(rows, empty_policy="one")[0].mean_consistency == 1.0


def test_rank_correlation_dense_spearman() -> None:
    rows = evaluate_gl_rp_rank_correlation(
        game_id="game_000001",
        player_count=4,
        gl_rank_by_mask={
            0b0011: 1,
            0b0101: 1,
            0b1001: 2,
            0b0110: 3,
            0b1010: 3,
            0b1100: 4,
        },
        rp_rank_by_mask={
            0b0011: 1,
            0b0101: 1,
            0b1001: 2,
            0b0110: 3,
            0b1010: 3,
            0b1100: 4,
        },
        target_sizes=(2,),
        correlation_method="spearman",
        rank_tie_method="dense",
    )

    assert rows[0].correlation == pytest.approx(1.0)
    assert rows[0].is_na is False


def test_rank_correlation_constant_vector_is_na() -> None:
    rows = evaluate_gl_rp_rank_correlation(
        game_id="game_000001",
        player_count=3,
        gl_rank_by_mask={0b011: 1, 0b101: 1, 0b110: 1},
        rp_rank_by_mask={0b011: 1, 0b101: 2, 0b110: 3},
        target_sizes=(2,),
        correlation_method="spearman",
        rank_tie_method="dense",
    )

    assert rows[0].correlation is None
    assert rows[0].is_na is True
    assert rows[0].reason_if_na == "constant_vector"
