from __future__ import annotations

import pytest

from srs_calculation.application.paper_simulation.metrics import (
    LensConsistencyRow,
    correlation_for_method,
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


def test_lens_summary_reports_micro_and_macro_averages() -> None:
    # Game A: 1/4 firing cases satisfied; Game B: 3/3 satisfied.
    # Macro = mean(0.25, 1.0) = 0.625; micro = (1 + 3) / (4 + 3) = 4/7.
    rows = [
        LensConsistencyRow(
            game_id="A",
            n=4,
            k=2,
            num_constraints=4,
            num_satisfied=1,
            consistency_rate=0.25,
            is_empty_constraints=False,
        ),
        LensConsistencyRow(
            game_id="B",
            n=4,
            k=2,
            num_constraints=3,
            num_satisfied=3,
            consistency_rate=1.0,
            is_empty_constraints=False,
        ),
    ]

    summary = summarize_lens_consistency(rows, empty_policy="exclude")
    overall = next(row for row in summary if row.k == "overall")

    assert overall.mean_consistency == pytest.approx(0.625)
    assert overall.micro_consistency == pytest.approx(4.0 / 7.0)
    assert overall.num_constraints == 7
    assert overall.num_satisfied == 4


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


def test_spearman_forces_average_ties_and_differs_from_pearson_dense() -> None:
    masks = [10, 20, 30, 40]
    ranks_x = {10: 1, 20: 1, 30: 2, 40: 3}  # uneven tie group at the top
    ranks_y = {10: 1, 20: 2, 30: 3, 40: 4}

    spearman, _ = correlation_for_method(
        ranks_x, ranks_y, masks, method="spearman", tie_method="dense"
    )
    pearson_dense, _ = correlation_for_method(
        ranks_x, ranks_y, masks, method="pearson", tie_method="dense"
    )

    # Spearman overrides the dense tie method with average, so the two differ;
    # this is exactly what makes the "Spearman" label truthful now.
    assert spearman is not None and pearson_dense is not None
    assert spearman != pytest.approx(pearson_dense)


def test_correlation_methods_agree_for_strictly_monotone_input() -> None:
    masks = [10, 20, 30, 40]
    ranks_x = {10: 1, 20: 2, 30: 3, 40: 4}
    ranks_y = {10: 1, 20: 2, 30: 3, 40: 4}

    for method in ("spearman", "pearson", "kendall"):
        value, reason = correlation_for_method(
            ranks_x, ranks_y, masks, method=method, tie_method="dense"
        )
        assert reason == ""
        assert value == pytest.approx(1.0)


def test_kendall_tau_known_value() -> None:
    masks = [10, 20, 30, 40]
    ranks_x = {10: 1, 20: 2, 30: 3, 40: 4}
    ranks_y = {10: 1, 20: 2, 30: 4, 40: 3}  # one discordant pair

    value, reason = correlation_for_method(
        ranks_x, ranks_y, masks, method="kendall", tie_method="dense"
    )

    assert reason == ""
    # C=5, D=1, no ties -> tau-b = (5 - 1) / 6.
    assert value == pytest.approx(4.0 / 6.0)


def test_unsupported_correlation_method_is_na() -> None:
    masks = [10, 20]
    ranks = {10: 1, 20: 2}
    value, reason = correlation_for_method(
        ranks, ranks, masks, method="bogus", tie_method="dense"
    )
    assert value is None
    assert reason == "unsupported_correlation_method"


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
