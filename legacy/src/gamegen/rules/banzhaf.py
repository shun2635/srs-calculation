"""Banzhaf Value for player rankings.

Implements the Banzhaf value:

  φ_v(i) = (1 / 2^(n-1)) * Σ_{S ⊆ N\\{i}} (v(S∪{i}) - v(S))
"""

from __future__ import annotations

from typing import Dict


def player_banzhaf_values(scores_by_mask: Dict[int, float], n: int) -> list[float]:
    """Return Banzhaf values for each player (length n)."""
    if n <= 0:
        return []
    full = 1 << n
    denom = float(1 << (n - 1))
    values = [0.0] * n
    for i in range(n):
        bit = 1 << i
        total = 0.0
        for mask in range(full):
            if mask & bit:
                continue
            with_i = mask | bit
            total += float(scores_by_mask.get(with_i, 0.0)) - float(scores_by_mask.get(mask, 0.0))
        values[i] = total / denom
    return values


def rank_by_banzhaf(scores_by_mask: Dict[int, float], n: int) -> Dict[int, int]:
    """Return dense ranks of players by Banzhaf value (higher is better)."""
    phi = player_banzhaf_values(scores_by_mask, n)
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


__all__ = ["player_banzhaf_values", "rank_by_banzhaf"]

