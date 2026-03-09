"""Group Lex-cel rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet
from ..rule import RankingRule, dense_rank_mapping_lex_desc


class GroupLexcelRule(RankingRule):
    """Coalition Lex-cel ranks derived from base coalition levels."""

    rule_id = "group_lexcel"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        player_count = game.player_count
        if player_count <= 0:
            ranks_by_coalition: dict[int, int] = {}
        else:
            levels = game.coalition_levels()
            max_level = max(levels.values(), default=0)
            theta_by_coalition: dict[int, tuple[int, ...]] = {}
            for coalition_mask in range(1, game.coalition_count):
                theta: list[int] = []
                for level in range(1, max_level + 1):
                    count = 0
                    for mask, mask_level in levels.items():
                        if int(mask) == 0 or int(mask_level) != int(level):
                            continue
                        if (int(mask) & int(coalition_mask)) == int(coalition_mask):
                            count += 1
                    theta.append(count)
                theta_by_coalition[int(coalition_mask)] = tuple(theta)
            ranks_by_coalition = dense_rank_mapping_lex_desc(theta_by_coalition)

        return RankingResult(
            rule_id=self.rule_id,
            rank_set=RuleRankSet.from_coalition_mapping(ranks_by_coalition),
        )
