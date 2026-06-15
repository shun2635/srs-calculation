"""Full rule/lens comparison metrics for paper heatmaps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...domain.ranking.result import RuleRankSet
from .lens_catalog import (
    PAPER_LENS_CATALOG,
    PAPER_LENS_SPECS,
    PaperLensSpec,
)
from .metrics import _masks_of_size, correlation_for_method
from .rule_catalog import (
    PAPER_LENS_RULE_SPECS,
    PAPER_RANK_RULE_SPECS,
    PAPER_RULE_SPECS,
    PaperRuleSpec,
)


@dataclass(frozen=True)
class LensConsistencyObservation:
    game_id: str
    rule_id: str
    rule: str
    lens_id: str
    lens: str
    consistency: float | None
    # Raw per-game counts so the matrix can pool a micro (case-weighted) average
    # in addition to the macro (per-game equal-weight) average.
    num_satisfied: int
    num_constraints: int
    is_empty_or_na: bool


@dataclass(frozen=True)
class LensConsistencyMatrixCell:
    rule_id: str
    rule: str
    lens_id: str
    lens: str
    # Macro: per-game rates averaged with equal weight across games.
    mean_consistency: float | None
    # Micro: pooled sum(num_satisfied) / sum(num_constraints) over firing cases.
    micro_consistency: float | None
    num_games: int
    num_valid: int
    num_empty_or_na: int


@dataclass(frozen=True)
class RankCorrelationObservation:
    game_id: str
    k: int
    rule_a_id: str
    rule_a: str
    rule_b_id: str
    rule_b: str
    correlation: float | None
    is_na: bool


@dataclass(frozen=True)
class RankCorrelationMatrixCell:
    rule_a_id: str
    rule_a: str
    rule_b_id: str
    rule_b: str
    mean_correlation: float | None
    num_valid: int
    num_na: int


def evaluate_paper_rules(game: CoalitionGame) -> dict[str, RuleRankSet]:
    """Evaluate all paper heatmap rules and return coalition rank sets."""

    rank_sets: dict[str, RuleRankSet] = {}
    for spec in PAPER_RULE_SPECS:
        result = spec.rule.evaluate(game)
        if result.rank_set is None or result.rank_set.scope != "coalition":
            continue
        rank_sets[spec.rule_id] = result.rank_set
    return rank_sets


def evaluate_lens_consistency_observations(
    *,
    game_id: str,
    game: CoalitionGame,
    rank_sets_by_rule: dict[str, RuleRankSet],
    target_sizes: Iterable[int],
) -> tuple[LensConsistencyObservation, ...]:
    """Evaluate every paper rule against every paper lens for one game."""

    observations: list[LensConsistencyObservation] = []
    for rule_spec in PAPER_LENS_RULE_SPECS:
        rank_set = rank_sets_by_rule.get(rule_spec.rule_id)
        for lens in PAPER_LENS_CATALOG:
            satisfied = 0
            constraints = 0
            if rank_set is not None:
                satisfied, constraints = lens.counts(game, rank_set, target_sizes)
            consistency = None if constraints <= 0 else float(satisfied) / float(constraints)
            observations.append(
                LensConsistencyObservation(
                    game_id=str(game_id),
                    rule_id=rule_spec.rule_id,
                    rule=rule_spec.label,
                    lens_id=lens.lens_id,
                    lens=lens.label,
                    consistency=consistency,
                    num_satisfied=int(satisfied),
                    num_constraints=int(constraints),
                    is_empty_or_na=consistency is None,
                )
            )
    return tuple(observations)


def summarize_lens_consistency_matrix(
    observations: Iterable[LensConsistencyObservation],
) -> tuple[LensConsistencyMatrixCell, ...]:
    """Summarize lens consistency observations into heatmap cells."""

    observation_list = list(observations)
    cells: list[LensConsistencyMatrixCell] = []
    for rule_spec in PAPER_LENS_RULE_SPECS:
        for lens_spec in PAPER_LENS_SPECS:
            selected = [
                observation
                for observation in observation_list
                if observation.rule_id == rule_spec.rule_id
                and observation.lens_id == lens_spec.lens_id
            ]
            values = [
                float(observation.consistency)
                for observation in selected
                if observation.consistency is not None
            ]
            total_satisfied = sum(int(observation.num_satisfied) for observation in selected)
            total_constraints = sum(int(observation.num_constraints) for observation in selected)
            micro = (
                None
                if total_constraints <= 0
                else float(total_satisfied) / float(total_constraints)
            )
            cells.append(
                LensConsistencyMatrixCell(
                    rule_id=rule_spec.rule_id,
                    rule=rule_spec.label,
                    lens_id=lens_spec.lens_id,
                    lens=lens_spec.label,
                    mean_consistency=(
                        None if not values else sum(values) / float(len(values))
                    ),
                    micro_consistency=micro,
                    num_games=len(selected),
                    num_valid=len(values),
                    num_empty_or_na=len(selected) - len(values),
                )
            )
    return tuple(cells)


def evaluate_rank_correlation_observations(
    *,
    game_id: str,
    player_count: int,
    rank_sets_by_rule: dict[str, RuleRankSet],
    target_sizes: Iterable[int],
    correlation_method: str,
    rank_tie_method: str,
) -> tuple[RankCorrelationObservation, ...]:
    """Evaluate off-diagonal rule-pair rank correlations for one game."""

    observations: list[RankCorrelationObservation] = []
    for index, rule_a in enumerate(PAPER_RANK_RULE_SPECS):
        rank_set_a = rank_sets_by_rule.get(rule_a.rule_id)
        for rule_b in PAPER_RANK_RULE_SPECS[index + 1 :]:
            rank_set_b = rank_sets_by_rule.get(rule_b.rule_id)
            for coalition_size in target_sizes:
                correlation: float | None = None
                reason = "missing_rank_set"
                if rank_set_a is not None and rank_set_b is not None:
                    masks = _masks_of_size(int(player_count), int(coalition_size))
                    correlation, reason = correlation_for_method(
                        rank_set_a.ranks_by_coalition,
                        rank_set_b.ranks_by_coalition,
                        masks,
                        method=correlation_method,
                        tie_method=rank_tie_method,
                    )

                observations.append(
                    RankCorrelationObservation(
                        game_id=str(game_id),
                        k=int(coalition_size),
                        rule_a_id=rule_a.rule_id,
                        rule_a=rule_a.label,
                        rule_b_id=rule_b.rule_id,
                        rule_b=rule_b.label,
                        correlation=correlation,
                        is_na=correlation is None or bool(reason),
                    )
                )
    return tuple(observations)


def summarize_rank_correlation_matrix(
    observations: Iterable[RankCorrelationObservation],
    *,
    num_game_size_rows: int,
) -> tuple[RankCorrelationMatrixCell, ...]:
    """Summarize rule-pair correlations into a symmetric heatmap matrix."""

    observation_list = list(observations)
    cells: list[RankCorrelationMatrixCell] = []
    for row_index, rule_a in enumerate(PAPER_RANK_RULE_SPECS):
        for col_index, rule_b in enumerate(PAPER_RANK_RULE_SPECS):
            if rule_a.rule_id == rule_b.rule_id:
                cells.append(
                    RankCorrelationMatrixCell(
                        rule_a_id=rule_a.rule_id,
                        rule_a=rule_a.label,
                        rule_b_id=rule_b.rule_id,
                        rule_b=rule_b.label,
                        mean_correlation=1.0,
                        num_valid=int(num_game_size_rows),
                        num_na=0,
                    )
                )
                continue

            left_index = min(row_index, col_index)
            right_index = max(row_index, col_index)
            left = PAPER_RANK_RULE_SPECS[left_index]
            right = PAPER_RANK_RULE_SPECS[right_index]
            selected = [
                observation
                for observation in observation_list
                if observation.rule_a_id == left.rule_id
                and observation.rule_b_id == right.rule_id
            ]
            values = [
                float(observation.correlation)
                for observation in selected
                if observation.correlation is not None
            ]
            cells.append(
                RankCorrelationMatrixCell(
                    rule_a_id=rule_a.rule_id,
                    rule_a=rule_a.label,
                    rule_b_id=rule_b.rule_id,
                    rule_b=rule_b.label,
                    mean_correlation=(
                        None if not values else sum(values) / float(len(values))
                    ),
                    num_valid=len(values),
                    num_na=len(selected) - len(values),
                )
            )
    return tuple(cells)


__all__ = [
    "LensConsistencyMatrixCell",
    "LensConsistencyObservation",
    "PAPER_LENS_SPECS",
    "PAPER_LENS_RULE_SPECS",
    "PAPER_RANK_RULE_SPECS",
    "PAPER_RULE_SPECS",
    "PaperLensSpec",
    "PaperRuleSpec",
    "RankCorrelationMatrixCell",
    "RankCorrelationObservation",
    "evaluate_lens_consistency_observations",
    "evaluate_paper_rules",
    "evaluate_rank_correlation_observations",
    "summarize_lens_consistency_matrix",
    "summarize_rank_correlation_matrix",
]
