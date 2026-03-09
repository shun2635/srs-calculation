"""UD and DU rules in the new domain layer."""

from __future__ import annotations

from dataclasses import dataclass

from ...games.coalition_game import CoalitionGame
from ..result import RankingResult, RuleRankSet, RuleScoreSet
from ..rule import RankingRule, dense_rank_mapping_desc, popcount


def _updown_counts(game: CoalitionGame) -> dict[int, tuple[int, int]]:
    levels = game.coalition_levels()
    single_rank = {1 << player: int(levels.get(1 << player, 0)) for player in range(game.player_count)}
    counts: dict[int, tuple[int, int]] = {}
    for coalition_mask in range(1, game.coalition_count):
        if popcount(coalition_mask) < 2:
            continue
        coalition_rank = int(levels.get(int(coalition_mask), 0))
        if coalition_rank <= 0:
            continue
        up = 0
        down = 0
        for player in game.coalition_members(coalition_mask):
            singleton_rank = int(single_rank.get(1 << int(player), 0))
            if singleton_rank <= 0:
                continue
            if coalition_rank < singleton_rank:
                up += 1
            elif singleton_rank < coalition_rank:
                down += 1
        counts[int(coalition_mask)] = (int(up), int(down))
    return counts


@dataclass(frozen=True)
class _UpDownCommon:
    score_up_column: str
    score_down_column: str


class UdRule(RankingRule):
    """Coalition UD ranks and auxiliary up/down counts."""

    rule_id = "ud"
    _columns = _UpDownCommon(score_up_column="score_ud_up", score_down_column="score_ud_down")

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        counts = _updown_counts(game)
        base = int(game.player_count) + 1
        scores_by_coalition = {
            int(mask): int(up) * base - int(down) for mask, (up, down) in counts.items()
        }
        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(scores_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(scores_by_coalition)),
            auxiliary_score_sets={
                self._columns.score_up_column: RuleScoreSet.from_coalition_mapping(
                    {int(mask): float(up) for mask, (up, _) in counts.items()}
                ),
                self._columns.score_down_column: RuleScoreSet.from_coalition_mapping(
                    {int(mask): float(down) for mask, (_, down) in counts.items()}
                ),
            },
        )


class DuRule(RankingRule):
    """Coalition DU ranks and auxiliary up/down counts."""

    rule_id = "du"
    _columns = _UpDownCommon(score_up_column="score_du_up", score_down_column="score_du_down")

    def evaluate(self, game: CoalitionGame) -> RankingResult:
        game.require_complete()
        counts = _updown_counts(game)
        base = int(game.player_count) + 1
        scores_by_coalition = {
            int(mask): -int(down) * base + int(up) for mask, (up, down) in counts.items()
        }
        return RankingResult(
            rule_id=self.rule_id,
            score_set=RuleScoreSet.from_coalition_mapping(scores_by_coalition),
            rank_set=RuleRankSet.from_coalition_mapping(dense_rank_mapping_desc(scores_by_coalition)),
            auxiliary_score_sets={
                self._columns.score_up_column: RuleScoreSet.from_coalition_mapping(
                    {int(mask): float(up) for mask, (up, _) in counts.items()}
                ),
                self._columns.score_down_column: RuleScoreSet.from_coalition_mapping(
                    {int(mask): float(down) for mask, (_, down) in counts.items()}
                ),
            },
        )
