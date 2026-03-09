"""Application use cases for axiom evaluation workflows."""

from __future__ import annotations

from ...domain.axioms import AxiomEvaluationResult, AxiomRegistry, build_default_axiom_registry
from ...domain.games.coalition_game import CoalitionGame
from ...domain.ranking.result import RankingResult


def evaluate_axioms_for_ranking_result(
    game: CoalitionGame,
    ranking_result: RankingResult,
    axiom_ids: list[str] | None = None,
    *,
    registry: AxiomRegistry | None = None,
    max_examples: int = 0,
) -> dict[str, AxiomEvaluationResult]:
    """Evaluate coalition-ranking axioms for one ranking result."""

    if ranking_result.rank_set is None:
        raise ValueError(f"ranking result '{ranking_result.rule_id}' does not include ranks")
    if ranking_result.rank_set.scope != "coalition":
        raise ValueError(
            f"axiom evaluation requires coalition-scoped ranks; got scope '{ranking_result.rank_set.scope}'"
        )

    active_registry = registry or build_default_axiom_registry()
    selected_axiom_ids = list(axiom_ids or active_registry.list_axiom_ids())
    return {
        str(axiom_id): active_registry.get(str(axiom_id)).evaluate(
            game,
            ranking_result.rank_set,
            max_examples=max_examples,
        )
        for axiom_id in selected_axiom_ids
    }


def evaluate_axioms_for_results(
    game: CoalitionGame,
    results_by_rule_id: dict[str, RankingResult],
    axiom_ids: list[str] | None = None,
    *,
    registry: AxiomRegistry | None = None,
    max_examples: int = 0,
) -> dict[str, dict[str, AxiomEvaluationResult]]:
    """Evaluate coalition-ranking axioms for every coalition-scoped ranking result."""

    evaluations: dict[str, dict[str, AxiomEvaluationResult]] = {}
    for rule_id, ranking_result in results_by_rule_id.items():
        if ranking_result.rank_set is None or ranking_result.rank_set.scope != "coalition":
            continue
        evaluations[str(rule_id)] = evaluate_axioms_for_ranking_result(
            game,
            ranking_result,
            axiom_ids,
            registry=registry,
            max_examples=max_examples,
        )
    return evaluations
