"""Ordinal Banzhaf ranking for cooperative games.

日本語補足:
与えられた連合の順位構造（スコアの大小から誘導される等級）に対して、
各プレイヤー i の序数的 Banzhaf スコア s_i = u_i^+ - u_i^- を計算し、
その降順で個人の密順位 (dense rank) を返します。

実装の要点:
- レベルは「小さいほど上位」（1 が最上位）。
- m_i^S = sign(level[S] - level[S∪{i}]) に基づき u^+, u^- を集計。
- スコア差分 s を降順、同点はインデックス昇順で安定化。
"""

from __future__ import annotations

from typing import Dict, List


def build_levels_from_scores(scores_by_mask: Dict[int, float]) -> Dict[int, int]:
    """スコア辞書から level 辞書を構築（1 が最上位）。

    スコア降順（同点はビットマスク昇順）で走査し、同点の連合に同一レベルを与える。
    戻り値は `mask -> level (>=1)` の辞書。
    """

    # 安定順序: スコア降順、マスク昇順
    items = sorted(scores_by_mask.items(), key=lambda kv: (-kv[1], kv[0]))
    level_of_mask: Dict[int, int] = {}
    current_level = 0
    last_score: float | None = None
    for m, s in items:
        if last_score is None or s != last_score:
            current_level += 1
            last_score = s
        level_of_mask[m] = current_level
    return level_of_mask


def ordinal_banzhaf_detail(level_of_mask: Dict[int, int], n: int) -> Dict[int, Dict[str, int]]:
    """各プレイヤーの u_plus, u_minus, s（差分スコア）を返す。

    前提: level_of_mask は 0..(2^n-1) の全てのマスクを網羅していること。
    欠落がある場合は ValueError。
    """

    if n < 0:
        raise ValueError("Player count cannot be negative.")
    size = 1 << n
    # 入力検証: 必要なマスクが全て存在するか
    missing = [mask for mask in range(size) if mask not in level_of_mask]
    if missing:
        raise ValueError(
            f"level_of_mask is missing {len(missing)} coalition(s); e.g., {missing[:5]}"
        )

    u_plus: List[int] = [0] * n
    u_minus: List[int] = [0] * n
    for S in range(size):
        base_level = level_of_mask[S]
        for i in range(n):
            if (S >> i) & 1:
                continue  # i ∈ S は対象外
            with_i = S | (1 << i)
            li = level_of_mask[with_i]
            if li < base_level:
                u_plus[i] += 1
            elif li > base_level:
                u_minus[i] += 1
            # 同レベルは 0 とみなす

    detail: Dict[int, Dict[str, int]] = {}
    for i in range(n):
        s = u_plus[i] - u_minus[i]
        detail[i] = {"u_plus": u_plus[i], "u_minus": u_minus[i], "s": s}
    return detail


def rank_by_ordinal_banzhaf_from_levels(level_of_mask: Dict[int, int], n: int) -> Dict[int, int]:
    """レベル構造（順位情報）に基づいて Banzhaf ランクを計算。"""

    if n <= 0:
        return {}
    detail = ordinal_banzhaf_detail(level_of_mask, n)
    s = [detail[i]["s"] for i in range(n)]
    order = sorted(range(n), key=lambda i: (-s[i], i))
    rank: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for i in order:
        if last is None or s[i] != last:
            current += 1
            last = s[i]
        rank[i] = current
    return rank


def rank_by_ordinal_banzhaf_from_scores(scores_by_mask: Dict[int, float], n: int) -> Dict[int, int]:
    """値関数 v(S) に基づき、序数的Banzhafスコアと個人ランキングを返す。"""

    if n <= 0:
        return {}
    levels = build_levels_from_scores({int(k): float(v) for k, v in scores_by_mask.items()})
    return rank_by_ordinal_banzhaf_from_levels(levels, n)


__all__ = [
    "build_levels_from_scores",
    "ordinal_banzhaf_detail",
    "rank_by_ordinal_banzhaf_from_levels",
    "rank_by_ordinal_banzhaf_from_scores",
]

