"""Group Shapley rule in the new domain layer."""

from __future__ import annotations

from math import factorial

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount


class GroupShapleyRule(RankingRule):
    """Exact coalition Shapley group values and dense ranks."""

    rule_id = "group_shapley"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        if player_count <= 0:
            values_by_coalition: dict[int, float] = {}
        else:
            facts = [factorial(i) for i in range(player_count + 2)]
            full = 1 << player_count
            all_players_mask = full - 1
            values_by_coalition = {}
            for coalition_mask in range(1, full):
                coalition_size = popcount(coalition_mask)
                merged_player_count = player_count - coalition_size + 1
                complement = all_players_mask ^ coalition_mask
                total = 0.0
                sub = complement
                while True:
                    t = popcount(sub)
                    coefficient = (
                        facts[t] * facts[merged_player_count - t - 1]
                    ) / float(facts[merged_player_count])
                    total += coefficient * (
                        game.coalition_value(sub | coalition_mask) - game.coalition_value(sub)
                    )
                    if sub == 0:
                        break
                    sub = (sub - 1) & complement
                values_by_coalition[coalition_mask] = total

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
