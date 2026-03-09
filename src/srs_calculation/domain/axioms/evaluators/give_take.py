"""Give/take axiom evaluators."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ...ranking.result import RuleRankSet
from ..axiom import AxiomEvaluationResult, CoalitionRankingAxiom


def _popcount(mask: int) -> int:
    return int(mask).bit_count()


def _members(mask: int, n_players: int) -> list[int]:
    return [player for player in range(int(n_players)) if (int(mask) >> player) & 1]


def _give_take_for_pair(mask: int, base_rank_by_mask: dict[int, int], n_players: int) -> tuple[int, int]:
    coalition_rank = int(base_rank_by_mask[int(mask)])
    give = 0
    take = 0
    for player in _members(mask, n_players):
        subset_mask = int(mask) & ~(1 << int(player))
        if subset_mask == 0:
            continue
        subset_rank = int(base_rank_by_mask[int(subset_mask)])
        if coalition_rank < subset_rank:
            give += 1
        elif subset_rank < coalition_rank:
            take += 1
    return int(give), int(take)


def _give_take_for_coalition(mask: int, base_rank_by_mask: dict[int, int], n_players: int) -> tuple[int, int]:
    coalition_rank = int(base_rank_by_mask[int(mask)])
    give = 0
    take = 0
    for player in _members(mask, n_players):
        singleton_rank = int(base_rank_by_mask[1 << int(player)])
        if coalition_rank < singleton_rank:
            give += 1
        elif singleton_rank < coalition_rank:
            take += 1
    return int(give), int(take)


class _BaseGiveTakeAxiom(CoalitionRankingAxiom):
    compare_mode: str
    weak_n: bool

    def _evaluate_for_masks(
        self,
        *,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        masks: list[int],
        use_coalition_variant: bool,
        max_examples: int,
    ) -> tuple[int, int, list[tuple[int, int]]]:
        base_rank_by_mask = game.coalition_levels()
        interaction_rank_by_mask = rank_set.ranks_by_coalition
        measure_by_mask: dict[int, int] = {}
        for mask in masks:
            if use_coalition_variant:
                give, take = _give_take_for_coalition(mask, base_rank_by_mask, game.player_count)
            else:
                give, take = _give_take_for_pair(mask, base_rank_by_mask, game.player_count)
            measure_by_mask[int(mask)] = int(give if self.compare_mode == "give" else take)

        constraints = 0
        satisfied = 0
        examples: list[tuple[int, int]] = []
        for left_mask in masks:
            interaction_rank_left = interaction_rank_by_mask.get(int(left_mask))
            for right_mask in masks:
                if int(right_mask) == int(left_mask):
                    continue
                if measure_by_mask[int(left_mask)] <= measure_by_mask[int(right_mask)]:
                    continue
                constraints += 1
                interaction_rank_right = interaction_rank_by_mask.get(int(right_mask))
                if self.compare_mode == "give":
                    ok = (
                        interaction_rank_left is not None
                        and interaction_rank_right is not None
                        and int(interaction_rank_left) < int(interaction_rank_right)
                    )
                else:
                    ok = (
                        interaction_rank_left is not None
                        and interaction_rank_right is not None
                        and int(interaction_rank_right) < int(interaction_rank_left)
                    )
                if ok:
                    satisfied += 1
                elif max_examples > 0 and len(examples) < int(max_examples):
                    examples.append((int(left_mask), int(right_mask)))
        return constraints, satisfied, examples

    def evaluate(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        *,
        max_examples: int = 0,
    ) -> AxiomEvaluationResult:
        if self.weak_n:
            constraints = 0
            satisfied = 0
            examples: list[tuple[int, int]] = []
            for coalition_size in range(2, int(game.player_count) + 1):
                masks = [mask for mask in range(1, game.coalition_count) if _popcount(mask) == int(coalition_size)]
                if len(masks) <= 1:
                    continue
                c, s, current_examples = self._evaluate_for_masks(
                    game=game,
                    rank_set=rank_set,
                    masks=masks,
                    use_coalition_variant=True,
                    max_examples=max(0, int(max_examples) - len(examples)),
                )
                constraints += int(c)
                satisfied += int(s)
                examples.extend(current_examples)
        else:
            masks = [mask for mask in range(1, game.coalition_count) if _popcount(mask) == 2]
            constraints, satisfied, examples = self._evaluate_for_masks(
                game=game,
                rank_set=rank_set,
                masks=masks,
                use_coalition_variant=False,
                max_examples=max_examples,
            )

        return AxiomEvaluationResult(
            axiom_id=self.axiom_id,
            constrained_comparisons=int(constraints),
            satisfied_comparisons=int(satisfied),
            violation_examples=tuple(examples),
        )


class Give2pAxiom(_BaseGiveTakeAxiom):
    axiom_id = "give-2p"
    compare_mode = "give"
    weak_n = False


class Take2pAxiom(_BaseGiveTakeAxiom):
    axiom_id = "take-2p"
    compare_mode = "take"
    weak_n = False


class GiveWeakNAxiom(_BaseGiveTakeAxiom):
    axiom_id = "give-weak-n"
    compare_mode = "give"
    weak_n = True


class TakeWeakNAxiom(_BaseGiveTakeAxiom):
    axiom_id = "take-weak-n"
    compare_mode = "take"
    weak_n = True
