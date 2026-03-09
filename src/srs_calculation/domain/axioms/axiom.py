"""Shared axiom abstractions for migrated axiom evaluators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..games.coalition_game import CoalitionGame
from ..ranking.result import RuleRankSet


@dataclass(frozen=True)
class AxiomEvaluationResult:
    """Summary of one axiom evaluation against one coalition ranking."""

    axiom_id: str
    constrained_comparisons: int
    satisfied_comparisons: int
    violation_examples: tuple[tuple[int, int], ...] = ()

    @property
    def satisfaction_ratio(self) -> float:
        if self.constrained_comparisons <= 0:
            return 1.0
        return float(self.satisfied_comparisons) / float(self.constrained_comparisons)


class CoalitionRankingAxiom(ABC):
    """Axiom evaluator over coalition-level ranking outputs."""

    axiom_id: str

    @abstractmethod
    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        """Evaluate the axiom on one coalition-scoped ranking result."""
