"""Ordinal Banzhaf rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_desc


class OrdinalBanzhafRule(RankingRule):
    """Ordinal Banzhaf score and dense rank."""

    rule_id = "ordinal_banzhaf"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        scores_by_player: dict[int, float] = {}
        if player_count > 0:
            level_by_mask = game.coalition_levels()
            u_plus = [0] * player_count
            u_minus = [0] * player_count
            for coalition_mask in range(game.coalition_count):
                base_level = level_by_mask[coalition_mask]
                for player in range(player_count):
                    if (coalition_mask >> player) & 1:
                        continue
                    with_player = coalition_mask | (1 << player)
                    candidate_level = level_by_mask[with_player]
                    if candidate_level < base_level:
                        u_plus[player] += 1
                    elif candidate_level > base_level:
                        u_minus[player] += 1
            scores_by_player = {
                player: float(u_plus[player] - u_minus[player]) for player in range(player_count)
            }

        ordered_scores = [scores_by_player[player] for player in range(player_count)]
        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_player_mapping(scores_by_player),
            rank_set=RuleRankSet.from_player_mapping(dense_rank_desc(ordered_scores)),
        )
