"""Banzhaf rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_desc


class BanzhafRule(RankingRule):
    """Player Banzhaf values and dense ranks."""

    rule_id = "banzhaf"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        scores_by_player: dict[int, float] = {}
        if player_count > 0:
            denominator = float(1 << (player_count - 1))
            for player in range(player_count):
                player_bit = 1 << player
                total = 0.0
                for coalition_mask in range(game.coalition_count):
                    if coalition_mask & player_bit:
                        continue
                    with_player = coalition_mask | player_bit
                    total += game.coalition_value(with_player) - game.coalition_value(coalition_mask)
                scores_by_player[player] = total / denominator

        ordered_scores = [scores_by_player[player] for player in range(player_count)]
        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_player_mapping(scores_by_player),
            rank_set=RuleRankSet.from_player_mapping(dense_rank_desc(ordered_scores)),
        )
