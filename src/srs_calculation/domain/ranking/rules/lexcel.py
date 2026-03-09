"""Lex-cel rule in the new domain layer."""

from __future__ import annotations

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet
from ..rule import RankingRule, dense_rank_lex_desc


def _build_level_map(game: CoalitionGame) -> dict[int, int]:
    ordered = sorted(game.scores_by_mask.items(), key=lambda item: (-item[1], item[0]))
    level_by_mask: dict[int, int] = {}
    current_level = 0
    last_score: float | None = None
    for mask, score in ordered:
        if last_score is None or score != last_score:
            current_level += 1
            last_score = score
        level_by_mask[mask] = current_level
    return level_by_mask


class LexcelRule(RankingRule):
    """Lex-cel player ranks."""

    rule_id = "lexcel"

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        if game.player_count <= 0:
            ranks_by_player: dict[int, int] = {}
        else:
            level_by_mask = _build_level_map(game)
            level_count = max(level_by_mask.values(), default=0)
            theta = [[0 for _ in range(level_count)] for _ in range(game.player_count)]
            for mask, level in level_by_mask.items():
                if mask == 0:
                    continue
                level_index = level - 1
                for player in range(game.player_count):
                    if (mask >> player) & 1:
                        theta[player][level_index] += 1
            ranks_by_player = dense_rank_lex_desc(theta)

        return RankingResult(
            rule_id=self.rule_id,
            rank_set=RuleRankSet.from_mapping("rank_lexcel", ranks_by_player),
        )
