"""Gekokujou axiom evaluators."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ...ranking.result import RuleRankSet
from ..axiom import AxiomEvaluationResult, CoalitionRankingAxiom


def _popcount(mask: int) -> int:
    return int(mask).bit_count()


def _sorted_singleton_ranks(mask: int, base_rank_by_mask: dict[int, int], n_players: int) -> list[int]:
    ranks: list[int] = []
    for player in range(int(n_players)):
        singleton = 1 << player
        if int(mask) & singleton:
            ranks.append(int(base_rank_by_mask[int(singleton)]))
    ranks.sort()
    return ranks


def _matching_exists_and_has_strict(singleton_ranks_s: list[int], singleton_ranks_t: list[int]) -> tuple[bool, bool]:
    if len(singleton_ranks_s) != len(singleton_ranks_t):
        return False, False
    has_strict = False
    for rs, rt in zip(singleton_ranks_s, singleton_ranks_t, strict=True):
        if int(rs) > int(rt):
            return False, False
        if int(rs) < int(rt):
            has_strict = True
    return True, has_strict


def _count_gekokujou_for_size(
    *,
    game: CoalitionGame,
    interaction_rank_by_mask: dict[int, int],
    coalition_size: int,
    max_examples: int,
) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    n_players = int(game.player_count)
    if coalition_size < 2 or coalition_size > n_players:
        return 0, 0, ()

    masks = [mask for mask in range(1, game.coalition_count) if _popcount(mask) == int(coalition_size)]
    if len(masks) <= 1:
        return 0, 0, ()

    base_rank_by_mask = game.coalition_levels()
    singleton_cache = {
        int(mask): _sorted_singleton_ranks(mask, base_rank_by_mask, n_players) for mask in masks
    }
    constraints = 0
    satisfied = 0
    examples: list[tuple[int, int]] = []

    for s_mask in masks:
        base_rank_s = int(base_rank_by_mask[int(s_mask)])
        interaction_rank_s = interaction_rank_by_mask.get(int(s_mask))
        for t_mask in masks:
            if int(t_mask) == int(s_mask):
                continue
            base_rank_t = int(base_rank_by_mask[int(t_mask)])
            if base_rank_s < base_rank_t:
                continue
            ok, strict_singleton = _matching_exists_and_has_strict(
                singleton_cache[int(s_mask)],
                singleton_cache[int(t_mask)],
            )
            if not ok:
                continue
            strict_group = base_rank_s > base_rank_t
            if not (strict_singleton or strict_group):
                continue
            constraints += 1
            interaction_rank_t = interaction_rank_by_mask.get(int(t_mask))
            if (
                interaction_rank_s is not None
                and interaction_rank_t is not None
                and int(interaction_rank_t) < int(interaction_rank_s)
            ):
                satisfied += 1
            elif max_examples > 0 and len(examples) < int(max_examples):
                examples.append((int(s_mask), int(t_mask)))

    return constraints, satisfied, tuple(examples)


class Gekokujou2pAxiom(CoalitionRankingAxiom):
    """2-player gekokujou axiom."""

    axiom_id = "gekokujou-2p"

    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        constraints, satisfied, examples = _count_gekokujou_for_size(
            game=game,
            interaction_rank_by_mask=rank_set.ranks_by_coalition,
            coalition_size=2,
            max_examples=max_examples,
        )
        return AxiomEvaluationResult(
            axiom_id=self.axiom_id,
            constrained_comparisons=constraints,
            satisfied_comparisons=satisfied,
            violation_examples=examples,
        )


class GekokujouWeakNAxiom(CoalitionRankingAxiom):
    """Weak n-person extension of gekokujou."""

    axiom_id = "gekokujou-weak-n"

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
            c, s, current_examples = _count_gekokujou_for_size(
                game=game,
                interaction_rank_by_mask=rank_set.ranks_by_coalition,
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
