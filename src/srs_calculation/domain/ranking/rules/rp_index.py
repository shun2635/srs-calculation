"""RP-index rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount


class RpIndexRule(RankingRule):
    """Coalition RP-index scores and dense ranks."""

    rule_id = "rp_index"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        levels = game.coalition_levels()
        ranks = {mask: int(levels[int(mask)]) for mask in range(1, game.coalition_count)}
        size_by_rank: dict[int, int] = {}
        for rank in ranks.values():
            size_by_rank[rank] = size_by_rank.get(rank, 0) + 1

        better_count_by_rank: dict[int, int] = {}
        prefix = 0
        for rank in sorted(size_by_rank):
            better_count_by_rank[rank] = prefix
            prefix += size_by_rank[rank]

        rp_by_coalition: dict[int, int] = {}
        total = sum(size_by_rank.values())
        for coalition_mask, rank in ranks.items():
            better = better_count_by_rank[rank]
            equal = size_by_rank[rank]
            worse = total - better - equal
            rp_by_coalition[int(coalition_mask)] = int(worse - better)

        values_by_coalition: dict[int, float] = {}
        for coalition_mask, rp_score in rp_by_coalition.items():
            if popcount(coalition_mask) < 2:
                continue
            members = game.coalition_members(coalition_mask)
            avg_single = sum(rp_by_coalition.get(1 << int(player), 0) for player in members) / float(len(members))
            values_by_coalition[int(coalition_mask)] = float(rp_score) - float(avg_single)

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
