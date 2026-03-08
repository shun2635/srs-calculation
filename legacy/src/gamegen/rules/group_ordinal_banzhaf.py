"""Group Ordinal Banzhaf (G-OB) ranking for coalitions.

日本語補足:
与えられた連合の順位構造（スコアの大小から誘導される等級 or 等級の直接入力）に対して、
各非空提携 T の序数的 Banzhaf スコア s_T = u_T^+ - u_T^- を計算し、
その降順で密順位 (dense rank) を返します。土台 S は T と互いに素 (S ∩ T = ∅)。

等級の取り扱い: 数値が小さいほど上位（1 が最上位）。
m_T^S は以下で定義:
    - 1  : level(S ∪ T) < level(S)
    - -1 : level(S ∪ T) > level(S)
    - 0  : それ以外

計算量は理論上 O(3^n)。n≲16 程度での利用を想定。
"""

from __future__ import annotations

from typing import Dict, Tuple


def build_levels_from_scores(scores_by_mask: Dict[int, float]) -> Tuple[Dict[int, int], int]:
    """スコア辞書から level 辞書を構築して返す（1 が最上位）。

    返り値: (mask -> level, distinct level count)
    スコア降順（同点はビットマスク昇順）の安定順序で同点に同一レベルを割り当てます。
    """

    items = sorted(scores_by_mask.items(), key=lambda kv: (-kv[1], kv[0]))
    level_of_mask: Dict[int, int] = {}
    current_level = 0
    last_score: float | None = None
    for m, s in items:
        if last_score is None or s != last_score:
            current_level += 1
            last_score = s
        level_of_mask[int(m)] = int(current_level)
    return level_of_mask, current_level


def group_ordinal_banzhaf_detail_from_levels(
    level_of_mask: Dict[int, int], n: int
) -> Dict[int, Dict[str, int]]:
    """各非空 T について {u_plus, u_minus, s} を返す。

    前提: level_of_mask は 0..(2^n-1) の全てのマスクを網羅していること。
    欠落がある場合は ValueError。
    """

    if n < 0:
        raise ValueError("Player count cannot be negative.")
    size = 1 << n
    missing = [mask for mask in range(size) if mask not in level_of_mask]
    if missing:
        raise ValueError(
            f"level_of_mask is missing {len(missing)} coalition(s); e.g., {missing[:5]}"
        )

    detail: Dict[int, Dict[str, int]] = {}
    full = size - 1
    for T in range(1, size):  # 非空 T
        base = full ^ T  # N\T（S ⊆ base を列挙）
        u_plus = 0
        u_minus = 0
        S = base
        while True:  # S を base の部分集合で列挙
            U = S | T
            l_u = level_of_mask[U]
            l_s = level_of_mask[S]
            if l_u < l_s:
                u_plus += 1
            elif l_u > l_s:
                u_minus += 1
            if S == 0:
                break
            S = (S - 1) & base
        detail[T] = {"u_plus": u_plus, "u_minus": u_minus, "s": u_plus - u_minus}
    return detail


def rank_by_group_ordinal_banzhaf_from_levels(
    level_of_mask: Dict[int, int], n: int
) -> Dict[int, int]:
    """G-OB の dense rank（mask -> rank、非空のみ）を返す。"""

    if n <= 0:
        return {}
    detail = group_ordinal_banzhaf_detail_from_levels(level_of_mask, n)
    # 降順ソート、同値は同順位（dense）、タイブレークは mask 昇順
    order = sorted(detail.keys(), key=lambda T: (-detail[T]["s"], T))
    ranks: Dict[int, int] = {}
    r = 0
    last: int | None = None
    for T in order:
        s_val = detail[T]["s"]
        if last is None or s_val != last:
            r += 1
            last = s_val
        ranks[T] = r
    return ranks


def rank_by_group_ordinal_banzhaf_from_scores(
    scores_by_mask: Dict[int, float], n: int
) -> Dict[int, int]:
    """値関数 -> 等級 -> G-OB ランクを一括で計算して返す。"""

    levels, _ = build_levels_from_scores({int(k): float(v) for k, v in scores_by_mask.items()})
    return rank_by_group_ordinal_banzhaf_from_levels(levels, n)


__all__ = [
    "build_levels_from_scores",
    "group_ordinal_banzhaf_detail_from_levels",
    "rank_by_group_ordinal_banzhaf_from_levels",
    "rank_by_group_ordinal_banzhaf_from_scores",
]

