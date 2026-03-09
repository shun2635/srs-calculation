"""Group sum-of-Shapley rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc
from .shapley import ShapleyRule


class GroupSumShapleyRule(RankingRule):
    """Coalition ranking by the sum of member Shapley values."""

    rule_id = "group_sum_shapley"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_scores = ShapleyRule().evaluate(game).score_set
        values_by_coalition: dict[int, float] = {}
        if player_scores is not None:
            player_values = player_scores.values_by_player
            for coalition_mask in range(1, game.coalition_count):
                total = 0.0
                for player in game.coalition_members(coalition_mask):
                    total += player_values.get(int(player), 0.0)
                values_by_coalition[int(coalition_mask)] = total

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(values_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(values_by_coalition)),
        )
