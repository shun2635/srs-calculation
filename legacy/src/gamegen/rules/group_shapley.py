"""Shapley group value for coalition rankings.

For a coalition C (non-empty), the Shapley group value is defined as the
Shapley value of the proxy player c in the merged game v_C.

This implementation computes it directly over the original characteristic
function v on 2^N:

Let n=|N|, k=|C|, m=|N_C| = n-k+1.
For T ⊆ N\\C:

  v_C(T) = v(T)
  v_C(T ∪ {c}) = v(T ∪ C)

So:

  φ^g_v(C) = Σ_{T ⊆ N\\C} ( |T|! (m-|T|-1)! / m! ) * ( v(T∪C) - v(T) )
"""

from __future__ import annotations

from math import factorial
from typing import Dict, Mapping


def _popcount(x: int) -> int:
    return x.bit_count()


def group_shapley_values(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, float]:
    """Return coalition mask -> Shapley group value for all non-empty coalitions."""
    if n <= 0:
        return {}
    full = 1 << n
    all_players_mask = full - 1

    out: Dict[int, float] = {}
    for c_mask in range(1, full):
        k = _popcount(c_mask)
        m = n - k + 1
        m_fact = factorial(m)

        # Weights depend only on |T| and m.
        max_t = n - k
        weights = [0.0] * (max_t + 1)
        for t in range(max_t + 1):
            weights[t] = (factorial(t) * factorial(m - t - 1)) / float(m_fact)

        complement = all_players_mask ^ c_mask
        total = 0.0
        sub = complement
        while True:
            t = _popcount(sub)
            diff = float(scores_by_mask[int(sub | c_mask)]) - float(scores_by_mask[int(sub)])
            total += weights[t] * diff
            if sub == 0:
                break
            sub = (sub - 1) & complement

        out[int(c_mask)] = total
    return out


def rank_by_group_shapley(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, int]:
    """Return dense ranks (1 is best) for non-empty coalitions by group Shapley value."""
    values = group_shapley_values(scores_by_mask, n)
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


__all__ = ["group_shapley_values", "rank_by_group_shapley"]

