"""Lex-cel ranking for cooperative games.

日本語補足:
値関数 v(S) のスコアに基づき、連合をスコア同値クラスへ分類し、
各プレイヤーが所属できるクラスごとの連合数分布 (θ ベクトル) を
辞書式降順比較することで個人順位を求めます。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class LevelInfo:
    """Stable representation of a coalition level."""

    score: float
    members: Tuple[int, ...]


def build_levels(scores_by_mask: Dict[int, float]) -> Tuple[List[LevelInfo], Dict[int, int]]:
    """Assign descending score levels to coalitions.

    Returns a tuple of (levels, level_of_mask) where level numbers start at 1.
    """

    ordered = sorted(scores_by_mask.items(), key=lambda item: (-item[1], item[0]))
    levels: List[LevelInfo] = []
    level_of_mask: Dict[int, int] = {}
    current_level = 0
    last_score: float | None = None
    for mask, score in ordered:
        if last_score is None or score != last_score:
            current_level += 1
            levels.append(LevelInfo(score=score, members=(mask,)))
            last_score = score
        else:
            last = levels[-1]
            merged = last.members + (mask,)
            levels[-1] = LevelInfo(score=last.score, members=merged)
        level_of_mask[mask] = current_level
    return levels, level_of_mask


def theta_vectors(level_of_mask: Dict[int, int], n: int, level_count: int) -> List[List[int]]:
    """Build θ(i) vectors of length level_count for each player."""

    theta = [[0 for _ in range(level_count)] for _ in range(n)]
    for mask, level in level_of_mask.items():
        if mask == 0:
            continue
        idx = level - 1
        for player in range(n):
            if (mask >> player) & 1:
                theta[player][idx] += 1
    return theta


def lex_order_dense_rank(vectors: List[List[int]]) -> Dict[int, int]:
    """Assign dense ranks by lexicographic (descending) comparison."""

    order = sorted(range(len(vectors)), key=lambda i: tuple([-v for v in vectors[i]] + [i]))
    ranks: Dict[int, int] = {}
    last_vec: List[int] | None = None
    current_rank = 0
    for idx in order:
        vec = vectors[idx]
        if last_vec is None or vec != last_vec:
            current_rank += 1
            last_vec = vec
        ranks[idx] = current_rank
    return ranks


def rank_by_lexcel(scores_by_mask: Dict[int, float], n: int) -> Dict[int, int]:
    """Compute dense ranks of players following the lex-cel rule."""

    if n <= 0:
        return {}

    _, level_of_mask = build_levels(scores_by_mask)
    level_count = max(level_of_mask.values(), default=0)
    theta = theta_vectors(level_of_mask, n, level_count)
    return lex_order_dense_rank(theta)


__all__ = [
    "build_levels",
    "theta_vectors",
    "lex_order_dense_rank",
    "rank_by_lexcel",
]
