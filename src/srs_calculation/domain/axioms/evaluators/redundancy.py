"""Redundancy axiom evaluator."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ...ranking.result import RuleRankSet
from ..axiom import AxiomEvaluationResult, CoalitionRankingAxiom


class RedundancyAxiom(CoalitionRankingAxiom):
    """Redundancy axiom for coalition-scoped interaction rules."""

    axiom_id = "redundancy"

    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        base_rank_by_mask = game.coalition_levels()
        interaction_rank_by_mask = rank_set.ranks_by_coalition
        constraints = 0
        satisfied = 0
        examples: list[tuple[int, int]] = []
        full = game.coalition_count

        for coalition_mask in range(0, full):
            interaction_rank_s = interaction_rank_by_mask.get(int(coalition_mask))
            if interaction_rank_s is None:
                continue
            base_rank_s = base_rank_by_mask.get(int(coalition_mask))
            if base_rank_s is None:
                continue
            complement = (full - 1) ^ int(coalition_mask)
            add = complement
            while add:
                bit = add & -add
                superset_mask = int(coalition_mask) | int(bit)
                add &= add - 1
                interaction_rank_t = interaction_rank_by_mask.get(int(superset_mask))
                if interaction_rank_t is None:
                    continue
                base_rank_t = base_rank_by_mask.get(int(superset_mask))
                if base_rank_t is None:
                    continue
                if int(base_rank_s) <= int(base_rank_t):
                    constraints += 1
                    if int(interaction_rank_s) <= int(interaction_rank_t):
                        satisfied += 1
                    elif max_examples > 0 and len(examples) < int(max_examples):
                        examples.append((int(coalition_mask), int(superset_mask)))

        return AxiomEvaluationResult(
            axiom_id=self.axiom_id,
            constrained_comparisons=int(constraints),
            satisfied_comparisons=int(satisfied),
            violation_examples=tuple(examples),
        )
