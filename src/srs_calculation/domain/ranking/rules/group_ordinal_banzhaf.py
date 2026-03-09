"""Group ordinal Banzhaf rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc


class GroupOrdinalBanzhafRule(RankingRule):
    """Coalition ordinal-Banzhaf scores and dense ranks."""

    rule_id = "group_ordinal_banzhaf"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        level_by_mask = game.coalition_levels()
        full = 1 << player_count
        all_players_mask = full - 1
        scores_by_coalition: dict[int, float] = {}

        for coalition_mask in range(1, full):
            complement = all_players_mask ^ coalition_mask
            u_plus = 0
            u_minus = 0
            sub = complement
            while True:
                with_coalition = sub | coalition_mask
                if level_by_mask[with_coalition] < level_by_mask[sub]:
                    u_plus += 1
                elif level_by_mask[with_coalition] > level_by_mask[sub]:
                    u_minus += 1
                if sub == 0:
                    break
                sub = (sub - 1) & complement
            scores_by_coalition[int(coalition_mask)] = float(u_plus - u_minus)

        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(scores_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(scores_by_coalition)),
        )
