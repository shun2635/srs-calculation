"""Domain layer for the new srs-calculation implementation."""

from .games.coalition_game import CoalitionGame
from .ranking.registry import RankingRuleRegistry, build_default_ranking_rule_registry
from .ranking.result import RankingResult

__all__ = [
    "CoalitionGame",
    "RankingResult",
    "RankingRuleRegistry",
    "build_default_ranking_rule_registry",
]
