"""Application service for running ranking rules on a coalition game."""

from __future__ import annotations

from ...domain.games.coalition_game import CoalitionGame
from ...domain.ranking.registry import RankingRuleRegistry, build_default_ranking_rule_registry
from ...domain.ranking.result import RankingResult


def apply_ranking_rules(
    game: CoalitionGame,
    rule_ids: list[str],
    registry: RankingRuleRegistry | None = None,
) -> dict[str, RankingResult]:
    """Evaluate a set of ranking rules on an in-memory coalition game."""

    active_registry = registry or build_default_ranking_rule_registry()
    results: dict[str, RankingResult] = {}
    for rule_id in rule_ids:
        rule = active_registry.get(rule_id)
        results[rule_id] = rule.evaluate(game)
    return results
