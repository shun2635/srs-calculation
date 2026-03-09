"""Redundancy-index rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc


class RedIndexRule(RankingRule):
    """Coalition redundancy-index scores and dense ranks."""

    rule_id = "red_index"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        levels = game.coalition_levels()
        full = game.coalition_count
        all_players_mask = full - 1
        values_by_coalition: dict[int, float] = {}
        for coalition_mask in range(1, full):
            coalition_rank = int(levels[int(coalition_mask)])
            complement = all_players_mask ^ int(coalition_mask)
            count = 0
            sub = complement
            while True:
                if sub != 0:
                    superset = int(coalition_mask) | int(sub)
                    if coalition_rank <= int(levels[superset]):
                        count += 1
                if sub == 0:
                    break
                sub = (sub - 1) & complement
            values_by_coalition[int(coalition_mask)] = float(count)

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
