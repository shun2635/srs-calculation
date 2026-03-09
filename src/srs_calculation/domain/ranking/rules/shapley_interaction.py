"""Shapley interaction rule in the new domain layer."""

from __future__ import annotations

from math import factorial

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount


def _subset_mobius_inplace(values: list[float], width: int) -> None:
    for bit in range(width):
        step = 1 << bit
        for mask in range(1 << width):
            if mask & step:
                values[mask] -= values[mask ^ step]


class ShapleyInteractionRule(RankingRule):
    """Coalition Shapley interaction indices and dense ranks."""

    rule_id = "shapley_interaction"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        if player_count <= 0:
            values_by_coalition: dict[int, float] = {}
        else:
            full = 1 << player_count
            all_players_mask = full - 1
            facts = [factorial(i) for i in range(player_count + 2)]
            values_by_coalition = {mask: 0.0 for mask in range(1, full)}
            for t_mask in range(full):
                t = popcount(t_mask)
                remaining = all_players_mask ^ t_mask
                rem_bits = [player for player in range(player_count) if (remaining >> player) & 1]
                size = 1 << len(rem_bits)
                subset_to_mask = [0] * size
                f = [0.0] * size
                for subset in range(size):
                    coalition_mask = 0
                    for index, bitpos in enumerate(rem_bits):
                        if (subset >> index) & 1:
                            coalition_mask |= 1 << bitpos
                    subset_to_mask[subset] = coalition_mask
                    f[subset] = game.coalition_value_or(t_mask | coalition_mask)
                _subset_mobius_inplace(f, len(rem_bits))
                for subset in range(1, size):
                    coalition_mask = subset_to_mask[subset]
                    coalition_size = popcount(coalition_mask)
                    remainder = player_count - t - coalition_size
                    if remainder < 0:
                        continue
                    coefficient = (
                        facts[remainder] * facts[t]
                    ) / float(facts[player_count - coalition_size + 1])
                    values_by_coalition[int(coalition_mask)] += coefficient * f[subset]

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
