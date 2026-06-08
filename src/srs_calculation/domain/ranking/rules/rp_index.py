"""RP-index rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount


class RpIndexRule(RankingRule):
    """Coalition Rankdiff scores and dense ranks.

    Implements the paper definition directly:

        Rankdiff(S) = (1 / |S|) * sum_{i in S} r({i})  -  r(S)

    where the rank value ``r(C) = |{C' : C' > C}|`` is the number of coalitions
    strictly above ``C`` (ties are not counted; the most preferred coalition has
    ``r = 0``). The count ranges over the whole non-empty coalition pool, matching
    the ``better`` prefix used elsewhere in the codebase. A larger Rankdiff means
    the coalition outperforms its members' individual standing (more synergy).
    """

    rule_id = "rp_index"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        levels = game.coalition_levels()
        ranks = {mask: int(levels[int(mask)]) for mask in range(1, game.coalition_count)}
        size_by_rank: dict[int, int] = {}
        for rank in ranks.values():
            size_by_rank[rank] = size_by_rank.get(rank, 0) + 1

        # better_count_by_rank[level] == r(C) for any coalition C at that level:
        # the number of coalitions strictly above it (ties excluded).
        better_count_by_rank: dict[int, int] = {}
        prefix = 0
        for rank in sorted(size_by_rank):
            better_count_by_rank[rank] = prefix
            prefix += size_by_rank[rank]

        rank_value_by_coalition = {
            int(mask): int(better_count_by_rank[rank]) for mask, rank in ranks.items()
        }

        values_by_coalition: dict[int, float] = {}
        for coalition_mask, rank_value in rank_value_by_coalition.items():
            if popcount(coalition_mask) < 2:
                continue
            members = game.coalition_members(coalition_mask)
            avg_single = sum(
                rank_value_by_coalition[1 << int(player)] for player in members
            ) / float(len(members))
            # Rankdiff = mean individual rank value - team rank value.
            values_by_coalition[int(coalition_mask)] = float(avg_single) - float(rank_value)

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
