"""Reversal lens axiom evaluators."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ...lenses import generate_reversal_constraints
from ...ranking.result import RuleRankSet
from ..axiom import AxiomEvaluationResult, CoalitionRankingAxiom


def _count_reversal_for_size(
    *,
    game: CoalitionGame,
    output_rank_by_mask: dict[int, int],
    coalition_size: int,
    max_examples: int,
) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    constraints = generate_reversal_constraints(game, int(coalition_size))
    satisfied = 0
    examples: list[tuple[int, int]] = []

    for constraint in constraints:
        preferred_rank = output_rank_by_mask.get(int(constraint.preferred_mask))
        dispreferred_rank = output_rank_by_mask.get(int(constraint.dispreferred_mask))
        if (
            preferred_rank is not None
            and dispreferred_rank is not None
            and int(preferred_rank) < int(dispreferred_rank)
        ):
            satisfied += 1
        elif max_examples > 0 and len(examples) < int(max_examples):
            examples.append((int(constraint.preferred_mask), int(constraint.dispreferred_mask)))

    return len(constraints), int(satisfied), tuple(examples)


class Reversal2pAxiom(CoalitionRankingAxiom):
    """2-player Reversal lens axiom."""

    axiom_id = "reversal-2p"

    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        constraints, satisfied, examples = _count_reversal_for_size(
            game=game,
            output_rank_by_mask=rank_set.ranks_by_coalition,
            coalition_size=2,
            max_examples=max_examples,
        )
        return AxiomEvaluationResult(
            axiom_id=self.axiom_id,
            constrained_comparisons=constraints,
            satisfied_comparisons=satisfied,
            violation_examples=examples,
        )


class ReversalWeakNAxiom(CoalitionRankingAxiom):
    """Weak n-person extension of the Reversal lens axiom."""

    axiom_id = "reversal-weak-n"

    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        constraints = 0
        satisfied = 0
        examples: list[tuple[int, int]] = []
        for coalition_size in range(2, int(game.player_count) + 1):
            c, s, current_examples = _count_reversal_for_size(
                game=game,
                output_rank_by_mask=rank_set.ranks_by_coalition,
                coalition_size=coalition_size,
                max_examples=max(0, int(max_examples) - len(examples)),
            )
            constraints += int(c)
            satisfied += int(s)
            examples.extend(current_examples)

        return AxiomEvaluationResult(
            axiom_id=self.axiom_id,
            constrained_comparisons=constraints,
            satisfied_comparisons=satisfied,
            violation_examples=tuple(examples),
        )


__all__ = ["Reversal2pAxiom", "ReversalWeakNAxiom"]
