"""Banzhaf interaction rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount
from .shapley_interaction import _subset_mobius_inplace


class BanzhafInteractionRule(RankingRule):
    """Coalition Banzhaf interaction indices and dense ranks."""

    rule_id = "banzhaf_interaction"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        if player_count <= 0:
            values_by_coalition: dict[int, float] = {}
        else:
            full = 1 << player_count
            all_players_mask = full - 1
            values_by_coalition = {mask: 0.0 for mask in range(1, full)}
            for t_mask in range(full):
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
                    values_by_coalition[int(coalition_mask)] += f[subset] / float(
                        1 << (player_count - coalition_size)
                    )

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
