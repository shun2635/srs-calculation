"""Metrics for the paper simulation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...domain.lenses import generate_reversal_constraints


@dataclass(frozen=True)
class LensConsistencyRow:
    game_id: str
    n: int
    k: int
    num_constraints: int
    num_satisfied: int
    consistency_rate: float | None
    is_empty_constraints: bool


@dataclass(frozen=True)
class LensConsistencySummaryRow:
    n: int
    k: str
    num_games: int
    num_valid_games: int
    num_empty_constraint_games: int
    mean_consistency: float | None
    std_consistency: float | None
    min_consistency: float | None
    max_consistency: float | None


@dataclass(frozen=True)
class RankCorrelationRow:
    game_id: str
    n: int
    k: int
    correlation_method: str
    rank_tie_method: str
    correlation: float | None
    is_na: bool
    reason_if_na: str


@dataclass(frozen=True)
class RankCorrelationSummaryRow:
    n: int
    k: str
    num_games: int
    num_valid_games: int
    num_na_games: int
    mean_correlation: float | None
    std_correlation: float | None
    min_correlation: float | None
    max_correlation: float | None


def _popcount(mask: int) -> int:
    return int(mask).bit_count()


def _masks_of_size(player_count: int, coalition_size: int) -> list[int]:
    return [
        int(mask)
        for mask in range(1, 1 << int(player_count))
        if _popcount(int(mask)) == int(coalition_size)
    ]


def evaluate_reversal_consistency(
    *,
    game_id: str,
    game: CoalitionGame,
    rp_rank_by_mask: dict[int, int],
    target_sizes: Iterable[int],
) -> tuple[LensConsistencyRow, ...]:
    """Evaluate RP-Difference against Reversal constraints by game and size."""

    rows: list[LensConsistencyRow] = []
    for coalition_size in target_sizes:
        constraints = generate_reversal_constraints(game, int(coalition_size))
        satisfied = 0
        for constraint in constraints:
            preferred_rank = rp_rank_by_mask.get(int(constraint.preferred_mask))
            dispreferred_rank = rp_rank_by_mask.get(int(constraint.dispreferred_mask))
            if (
                preferred_rank is not None
                and dispreferred_rank is not None
                and int(preferred_rank) < int(dispreferred_rank)
            ):
                satisfied += 1
        is_empty = len(constraints) == 0
        rows.append(
            LensConsistencyRow(
                game_id=str(game_id),
                n=int(game.player_count),
                k=int(coalition_size),
                num_constraints=len(constraints),
                num_satisfied=int(satisfied),
                consistency_rate=(
                    None if is_empty else float(satisfied) / float(len(constraints))
                ),
                is_empty_constraints=is_empty,
            )
        )
    return tuple(rows)


def _sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / float(len(values))
    return sqrt(sum((value - mean) ** 2 for value in values) / float(len(values) - 1))


def _summary_stats(
    values: list[float],
) -> tuple[float | None, float | None, float | None, float | None]:
    if not values:
        return None, None, None, None
    return (
        sum(values) / float(len(values)),
        _sample_std(values),
        min(values),
        max(values),
    )


def _consistency_summary_value(row: LensConsistencyRow, empty_policy: str) -> float | None:
    if row.consistency_rate is not None:
        return float(row.consistency_rate)
    if empty_policy == "zero":
        return 0.0
    if empty_policy == "one":
        return 1.0
    return None


def summarize_lens_consistency(
    rows: Iterable[LensConsistencyRow],
    *,
    empty_policy: str,
) -> tuple[LensConsistencySummaryRow, ...]:
    """Summarize Reversal consistency rows by k and overall."""

    row_list = list(rows)
    if not row_list:
        return ()

    n = int(row_list[0].n)
    summary_rows: list[LensConsistencySummaryRow] = []
    for key in [str(k) for k in sorted({row.k for row in row_list})] + ["overall"]:
        selected = row_list if key == "overall" else [row for row in row_list if row.k == int(key)]
        values = [
            value
            for value in (_consistency_summary_value(row, empty_policy) for row in selected)
            if value is not None
        ]
        mean, std, min_value, max_value = _summary_stats(values)
        summary_rows.append(
            LensConsistencySummaryRow(
                n=n,
                k=key,
                num_games=len(selected),
                num_valid_games=len(values),
                num_empty_constraint_games=sum(1 for row in selected if row.is_empty_constraints),
                mean_consistency=mean,
                std_consistency=std,
                min_consistency=min_value,
                max_consistency=max_value,
            )
        )
    return tuple(summary_rows)


def _rank_values(
    ranks_by_mask: dict[int, int],
    masks: list[int],
    *,
    tie_method: str,
) -> tuple[list[float] | None, str]:
    missing = [mask for mask in masks if int(mask) not in ranks_by_mask]
    if missing:
        return None, "missing_rank"

    raw_ranks = {int(mask): int(ranks_by_mask[int(mask)]) for mask in masks}
    counts: dict[int, int] = {}
    for rank in raw_ranks.values():
        counts[int(rank)] = counts.get(int(rank), 0) + 1

    ordered_ranks = sorted(counts)
    dense_by_rank = {rank: index + 1 for index, rank in enumerate(ordered_ranks)}
    min_by_rank: dict[int, int] = {}
    max_by_rank: dict[int, int] = {}
    prefix = 0
    for rank in ordered_ranks:
        min_by_rank[rank] = prefix + 1
        prefix += int(counts[rank])
        max_by_rank[rank] = prefix

    values: list[float] = []
    for mask in masks:
        rank = raw_ranks[int(mask)]
        if tie_method == "dense":
            values.append(float(dense_by_rank[rank]))
        elif tie_method == "min":
            values.append(float(min_by_rank[rank]))
        elif tie_method == "max":
            values.append(float(max_by_rank[rank]))
        elif tie_method == "average":
            values.append((float(min_by_rank[rank]) + float(max_by_rank[rank])) / 2.0)
        else:
            return None, "unsupported_rank_tie_method"
    return values, ""


def _correlation(values_x: list[float], values_y: list[float]) -> tuple[float | None, str]:
    if len(values_x) != len(values_y):
        return None, "length_mismatch"
    if len(values_x) < 2:
        return None, "not_enough_items"
    if len(set(values_x)) <= 1 or len(set(values_y)) <= 1:
        return None, "constant_vector"

    mean_x = sum(values_x) / float(len(values_x))
    mean_y = sum(values_y) / float(len(values_y))
    centered_x = [value - mean_x for value in values_x]
    centered_y = [value - mean_y for value in values_y]
    denominator = sqrt(
        sum(value * value for value in centered_x)
        * sum(value * value for value in centered_y)
    )
    if denominator == 0.0:
        return None, "constant_vector"
    return sum(x * y for x, y in zip(centered_x, centered_y, strict=True)) / denominator, ""


def evaluate_gl_rp_rank_correlation(
    *,
    game_id: str,
    player_count: int,
    gl_rank_by_mask: dict[int, int],
    rp_rank_by_mask: dict[int, int],
    target_sizes: Iterable[int],
    correlation_method: str,
    rank_tie_method: str,
) -> tuple[RankCorrelationRow, ...]:
    """Evaluate GL vs RP-Difference rank correlation by game and size."""

    rows: list[RankCorrelationRow] = []
    for coalition_size in target_sizes:
        masks = _masks_of_size(int(player_count), int(coalition_size))
        gl_values, gl_reason = _rank_values(gl_rank_by_mask, masks, tie_method=rank_tie_method)
        rp_values, rp_reason = _rank_values(rp_rank_by_mask, masks, tie_method=rank_tie_method)
        reason = gl_reason or rp_reason
        correlation_value: float | None = None
        if not reason and gl_values is not None and rp_values is not None:
            correlation_value, reason = _correlation(gl_values, rp_values)

        rows.append(
            RankCorrelationRow(
                game_id=str(game_id),
                n=int(player_count),
                k=int(coalition_size),
                correlation_method=str(correlation_method),
                rank_tie_method=str(rank_tie_method),
                correlation=correlation_value,
                is_na=correlation_value is None,
                reason_if_na=reason if correlation_value is None else "",
            )
        )
    return tuple(rows)


def summarize_rank_correlation(
    rows: Iterable[RankCorrelationRow],
) -> tuple[RankCorrelationSummaryRow, ...]:
    """Summarize rank-correlation rows by k and overall."""

    row_list = list(rows)
    if not row_list:
        return ()

    n = int(row_list[0].n)
    summary_rows: list[RankCorrelationSummaryRow] = []
    for key in [str(k) for k in sorted({row.k for row in row_list})] + ["overall"]:
        selected = row_list if key == "overall" else [row for row in row_list if row.k == int(key)]
        values = [float(row.correlation) for row in selected if row.correlation is not None]
        mean, std, min_value, max_value = _summary_stats(values)
        summary_rows.append(
            RankCorrelationSummaryRow(
                n=n,
                k=key,
                num_games=len(selected),
                num_valid_games=len(values),
                num_na_games=sum(1 for row in selected if row.is_na),
                mean_correlation=mean,
                std_correlation=std,
                min_correlation=min_value,
                max_correlation=max_value,
            )
        )
    return tuple(summary_rows)


__all__ = [
    "LensConsistencyRow",
    "LensConsistencySummaryRow",
    "RankCorrelationRow",
    "RankCorrelationSummaryRow",
    "evaluate_gl_rp_rank_correlation",
    "evaluate_reversal_consistency",
    "summarize_lens_consistency",
    "summarize_rank_correlation",
]
