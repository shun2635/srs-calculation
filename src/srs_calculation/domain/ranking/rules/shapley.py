"""Shapley rule in the new domain layer."""

from __future__ import annotations

from math import factorial

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_desc, popcount


class ShapleyRule(RankingRule):
    """Exact player Shapley values and dense ranks."""

    rule_id = "shapley"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        if player_count <= 0:
            scores_by_player: dict[int, float] = {}
        else:
            facts = [factorial(i) for i in range(player_count + 1)]
            n_fact = float(facts[player_count])
            scores_by_player = {}
            for player in range(player_count):
                player_bit = 1 << player
                total = 0.0
                for coalition_mask in range(game.coalition_count):
                    if coalition_mask & player_bit:
                        continue
                    coalition_size = popcount(coalition_mask)
                    coefficient = (facts[coalition_size] * facts[player_count - coalition_size - 1]) / n_fact
                    with_player = coalition_mask | player_bit
                    total += coefficient * (
                        game.coalition_value(with_player) - game.coalition_value(coalition_mask)
                    )
                scores_by_player[player] = total

        ordered_scores = [scores_by_player[player] for player in range(player_count)]
        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_mapping(scores_by_player),
            rank_set=RuleRankSet.from_mapping(dense_rank_desc(ordered_scores)),
        )
