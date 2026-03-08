"""Shapley interaction index for coalition rankings.

Implements:

  I_v^S(S) = Σ_{T ⊆ N\\S} ((n-t-s)! t! / (n-s+1)!) * Σ_{L ⊆ S} (-1)^(s-|L|) v(L ∪ T)

for all non-empty S ⊆ N, given a characteristic function v on 2^N.

This implementation computes all indices in about O(n * 3^n) time by iterating
over every T and performing a subset Möbius transform on the remaining players.
"""

from __future__ import annotations

from math import factorial
from typing import Dict, Mapping


def _popcount(x: int) -> int:
    return x.bit_count()


def _subset_mobius_inplace(values: list[float], r: int) -> None:
    """In-place subset Möbius transform.

    After running, values[mask] becomes:
      Σ_{sub ⊆ mask} (-1)^(|mask|-|sub|) original[sub]
    """
    for i in range(r):
        step = 1 << i
        for mask in range(1 << r):
            if mask & step:
                values[mask] -= values[mask ^ step]


def shapley_interaction_values(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, float]:
    """Return coalition mask -> Shapley interaction index for all non-empty coalitions."""
    if n <= 0:
        return {}
    full = 1 << n
    all_players_mask = full - 1

    facts = [factorial(i) for i in range(n + 2)]

    def weight(t: int, s: int) -> float:
        # (n - t - s)! * t! / (n - s + 1)!
        rem = n - t - s
        if rem < 0:
            return 0.0
        return (facts[rem] * facts[t]) / float(facts[n - s + 1])

    out: Dict[int, float] = {mask: 0.0 for mask in range(1, full)}

    for t_mask in range(full):
        t = _popcount(t_mask)
        remaining = all_players_mask ^ t_mask

        rem_bits = [i for i in range(n) if (remaining >> i) & 1]
        r = len(rem_bits)
        size = 1 << r

        # Map subset index -> original mask, and build f_T(U)=v(T∪U).
        subset_to_mask = [0] * size
        f = [0.0] * size
        for u in range(size):
            m = 0
            for j, bitpos in enumerate(rem_bits):
                if (u >> j) & 1:
                    m |= 1 << bitpos
            subset_to_mask[u] = m
            f[u] = float(scores_by_mask.get(int(t_mask | m), 0.0))

        # Möbius transform over the remaining elements yields Δ_S v(T) for each S ⊆ remaining.
        _subset_mobius_inplace(f, r)

        for u in range(1, size):  # skip empty S
            s_mask = subset_to_mask[u]
            s = _popcount(s_mask)
            out[int(s_mask)] += weight(t, s) * f[u]

    return out


def rank_by_shapley_interaction(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, int]:
    """Return dense ranks (1 is best) for non-empty coalitions by interaction index."""
    values = shapley_interaction_values(scores_by_mask, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    last = None
    current = 0
    for mask in order:
        v = values[mask]
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(mask)] = current
    return ranks


__all__ = ["shapley_interaction_values", "rank_by_shapley_interaction"]

