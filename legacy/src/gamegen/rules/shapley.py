"""Shapley value for player rankings (exact).

Implements the standard Shapley value for cooperative games given v(S)=score.

  φ_i(v) = Σ_{S ⊆ N\\{i}} (|S|! (n-|S|-1)! / n!) * ( v(S∪{i}) - v(S) )
"""

from __future__ import annotations

import csv
from math import factorial
from typing import Dict, List, Mapping


# ----------------
# 共通ユーティリティ
# ----------------

def mask_from_bits(bits: List[int]) -> int:
    """0/1 ベクトル（下位ビットが player0）を coalition bitmask に変換。"""
    mask = 0
    for idx, bit in enumerate(bits):
        if bit:
            mask |= 1 << idx
    return mask


def read_value_function_csv(path: str, n: int) -> Dict[int, float]:
    """CSV から値関数を読み込んで bitmask -> v(S) の辞書を返す。"""
    scores: Dict[int, float] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            bits = [int(row[f"player{i+1}"]) for i in range(n)]
            score = float(row["score"])
            mask = mask_from_bits(bits)
            scores[mask] = score
    full = 1 << n
    missing = [mask for mask in range(full) if mask not in scores]
    if missing:
        raise ValueError(
            f"CSV に欠落した連合が {len(missing)} 個あります（例: {missing[:5]}）。"
        )
    return scores


# --------------
# 公開 API
# --------------

def player_shapley_values(scores_by_mask: Mapping[int, float], n: int) -> List[float]:
    """Return exact Shapley values for each player (length n)."""
    if n <= 0:
        return []
    full = 1 << n
    facts = [factorial(i) for i in range(n + 1)]
    n_fact = float(facts[n])
    phi = [0.0] * n
    for i in range(n):
        bit = 1 << i
        total = 0.0
        for s_mask in range(full):
            if s_mask & bit:
                continue
            s = (s_mask).bit_count()
            coef = (facts[s] * facts[n - s - 1]) / n_fact
            with_i = s_mask | bit
            total += coef * (float(scores_by_mask.get(with_i, 0.0)) - float(scores_by_mask.get(s_mask, 0.0)))
        phi[i] = total
    return phi


def rank_by_shapley(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, int]:
    """プレイヤー Shapley 値に基づく個人 dense rank を返す。"""
    phi = player_shapley_values(scores_by_mask, n)
    order = sorted(range(n), key=lambda i: (-phi[i], i))
    ranks: Dict[int, int] = {}
    last = None
    current = 0
    for idx in order:
        value = phi[idx]
        if last is None or value != last:
            current += 1
            last = value
        ranks[idx] = current
    return ranks


__all__ = [
    "rank_by_shapley",
    "player_shapley_values",
    "read_value_function_csv",
]
