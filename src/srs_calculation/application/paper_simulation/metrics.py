"""Metrics for the paper simulation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...domain.lenses import generate_reversal_constraints
from .aggregation import RowGroup, group_by_k_with_overall


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
    num_constraints: int
    num_satisfied: int
    # Macro average: per-game consistency rates averaged with equal weight.
    mean_consistency: float | None
    std_consistency: float | None
    min_consistency: float | None
    max_consistency: float | None
    # Micro average: total satisfied / total constraints, pooled over all
    # firing cases (case-weighted). Reported alongside the macro average so the
    # paper can adopt either; see summarize_lens_consistency for the definition.
    micro_consistency: float | None


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
    rankdiff_rank_by_mask: dict[int, int],
    target_sizes: Iterable[int],
) -> tuple[LensConsistencyRow, ...]:
    """Evaluate Rankdiff against Reversal constraints by game and size.

    Satisfaction criterion (fixed specification, not configurable): a firing
    case counts as satisfied only when the rule output is the *strict* required
    ordering ``preferred > dispreferred`` (i.e. ``preferred_rank <
    dispreferred_rank``). A tie in the output (``preferred_rank ==
    dispreferred_rank``) is counted as NOT satisfied, because the paper requires
    a strict ``S >^R T``. This is a fixed spec (see
    fixed_specs.OUTPUT_TIES_COUNT_AS_UNSATISFIED) and is not configurable.
    """

    rows: list[LensConsistencyRow] = []
    for coalition_size in target_sizes:
        constraints = generate_reversal_constraints(game, int(coalition_size))
        satisfied = 0
        for constraint in constraints:
            preferred_rank = rankdiff_rank_by_mask.get(int(constraint.preferred_mask))
            dispreferred_rank = rankdiff_rank_by_mask.get(int(constraint.dispreferred_mask))
            # Strict requirement: ties (preferred_rank == dispreferred_rank) are
            # deliberately treated as unsatisfied. This is a fixed spec.
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
    """Summarize Reversal consistency rows by k and overall.

    Two averages are reported per group:

    - ``mean_consistency`` (macro): per-game consistency rates averaged with
      equal weight across games, subject to ``empty_policy`` for empty rows.
    - ``micro_consistency`` (micro): the pooled ratio ``sum(num_satisfied) /
      sum(num_constraints)`` over all firing cases, i.e. case-weighted. Empty
      rows contribute no constraints and therefore drop out naturally.

    Paper correspondence: the main-text adequacy / consistency value is the
    macro average (``fixed_specs.MAIN_TEXT_ADEQUACY_AVERAGE == "macro"``); the
    micro average is reported alongside but is not the headline figure. A firing
    case counts as satisfied only on a strict output improvement; a tied output
    is unsatisfied (``fixed_specs.OUTPUT_TIES_COUNT_AS_UNSATISFIED``).
    """

    groups = group_by_k_with_overall(rows, k_of=lambda row: int(row.k))
    return tuple(
        _reduce_lens_consistency_group(group, empty_policy=empty_policy) for group in groups
    )


def _reduce_lens_consistency_group(
    group: RowGroup[LensConsistencyRow],
    *,
    empty_policy: str,
) -> LensConsistencySummaryRow:
    """Reduce one row group into a lens-consistency summary row.

    This is the per-group statistic (macro + micro) and is independent of the
    aggregation axis that produced ``group``.
    """

    selected = list(group.rows)
    n = int(selected[0].n)
    values = [
        value
        for value in (_consistency_summary_value(row, empty_policy) for row in selected)
        if value is not None
    ]
    mean, std, min_value, max_value = _summary_stats(values)
    total_constraints = sum(int(row.num_constraints) for row in selected)
    total_satisfied = sum(int(row.num_satisfied) for row in selected)
    micro = None if total_constraints <= 0 else float(total_satisfied) / float(total_constraints)
    return LensConsistencySummaryRow(
        n=n,
        k=group.key,
        num_games=len(selected),
        num_valid_games=len(values),
        num_empty_constraint_games=sum(1 for row in selected if row.is_empty_constraints),
        num_constraints=total_constraints,
        num_satisfied=total_satisfied,
        mean_consistency=mean,
        std_consistency=std,
        min_consistency=min_value,
        max_consistency=max_value,
        micro_consistency=micro,
    )


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


def _kendall_tau_b(values_x: list[float], values_y: list[float]) -> tuple[float | None, str]:
    """Kendall tau-b (tie-corrected) over paired rank values."""

    if len(values_x) != len(values_y):
        return None, "length_mismatch"
    if len(values_x) < 2:
        return None, "not_enough_items"
    if len(set(values_x)) <= 1 or len(set(values_y)) <= 1:
        return None, "constant_vector"

    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0
    n = len(values_x)
    for i in range(n):
        for j in range(i + 1, n):
            dx = values_x[i] - values_x[j]
            dy = values_y[i] - values_y[j]
            if dx == 0.0 and dy == 0.0:
                continue
            if dx == 0.0:
                ties_x += 1
                continue
            if dy == 0.0:
                ties_y += 1
                continue
            if (dx > 0.0) == (dy > 0.0):
                concordant += 1
            else:
                discordant += 1

    total_pairs = concordant + discordant
    denominator = sqrt(
        float(total_pairs + ties_x) * float(total_pairs + ties_y)
    )
    if denominator == 0.0:
        return None, "constant_vector"
    return float(concordant - discordant) / denominator, ""


def correlation_for_method(
    ranks_x_by_mask: dict[int, int],
    ranks_y_by_mask: dict[int, int],
    masks: list[int],
    *,
    method: str,
    tie_method: str,
) -> tuple[float | None, str]:
    """Compute the rank correlation that matches the requested method label.

    - ``spearman``: Pearson correlation on average-tie rank values, i.e. the
      exact (tie-corrected) Spearman rho. The configured ``tie_method`` is
      overridden with ``average`` so the result is a genuine Spearman.
    - ``pearson``: Pearson correlation on rank values using ``tie_method``.
    - ``kendall``: tie-corrected Kendall tau-b.
    """

    normalized_method = str(method).strip().lower()
    if normalized_method == "spearman":
        effective_tie = "average"
    elif normalized_method == "kendall":
        # Kendall only depends on order and tie structure; dense encodes both.
        effective_tie = "dense"
    elif normalized_method == "pearson":
        effective_tie = str(tie_method)
    else:
        return None, "unsupported_correlation_method"

    values_x, reason_x = _rank_values(ranks_x_by_mask, masks, tie_method=effective_tie)
    values_y, reason_y = _rank_values(ranks_y_by_mask, masks, tie_method=effective_tie)
    reason = reason_x or reason_y
    if reason or values_x is None or values_y is None:
        return None, reason

    if normalized_method == "kendall":
        return _kendall_tau_b(values_x, values_y)
    return _correlation(values_x, values_y)


def evaluate_gl_rankdiff_rank_correlation(
    *,
    game_id: str,
    player_count: int,
    gl_rank_by_mask: dict[int, int],
    rankdiff_rank_by_mask: dict[int, int],
    target_sizes: Iterable[int],
    correlation_method: str,
    rank_tie_method: str,
) -> tuple[RankCorrelationRow, ...]:
    """Evaluate the focal Group Lex-cel vs Rankdiff rank correlation per game/size.

    Paper correspondence: this is the main-text comparison of the two focal
    rules. With ``correlation_method="spearman"`` (the default) it is a genuine
    tie-corrected Spearman rho; the headline value reported is the ``overall``
    summary row from :func:`summarize_rank_correlation`.
    """

    rows: list[RankCorrelationRow] = []
    for coalition_size in target_sizes:
        masks = _masks_of_size(int(player_count), int(coalition_size))
        correlation_value, reason = correlation_for_method(
            gl_rank_by_mask,
            rankdiff_rank_by_mask,
            masks,
            method=correlation_method,
            tie_method=rank_tie_method,
        )

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

    groups = group_by_k_with_overall(rows, k_of=lambda row: int(row.k))
    return tuple(_reduce_rank_correlation_group(group) for group in groups)


def _reduce_rank_correlation_group(
    group: RowGroup[RankCorrelationRow],
) -> RankCorrelationSummaryRow:
    """Reduce one row group into a rank-correlation summary row."""

    selected = list(group.rows)
    n = int(selected[0].n)
    values = [float(row.correlation) for row in selected if row.correlation is not None]
    mean, std, min_value, max_value = _summary_stats(values)
    return RankCorrelationSummaryRow(
        n=n,
        k=group.key,
        num_games=len(selected),
        num_valid_games=len(values),
        num_na_games=sum(1 for row in selected if row.is_na),
        mean_correlation=mean,
        std_correlation=std,
        min_correlation=min_value,
        max_correlation=max_value,
    )


__all__ = [
    "LensConsistencyRow",
    "LensConsistencySummaryRow",
    "RankCorrelationRow",
    "RankCorrelationSummaryRow",
    "correlation_for_method",
    "evaluate_gl_rankdiff_rank_correlation",
    "evaluate_reversal_consistency",
    "summarize_lens_consistency",
    "summarize_rank_correlation",
]
