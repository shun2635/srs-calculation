"""Sum of member Shapley values for coalition rankings.

For a coalition C (non-empty), define:

  φ^sum_v(C) := Σ_{i ∈ C} φ_v(i)

where φ_v(i) is the standard Shapley value in the original game v.
"""

from __future__ import annotations

from typing import Dict, Mapping

from . import shapley as shapley_rules


def group_sum_shapley_values(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, float]:
    """Return coalition mask -> sum of member Shapley values for all non-empty coalitions."""
    if n <= 0:
        return {}
    full = 1 << n
    phi = shapley_rules.player_shapley_values(scores_by_mask, n)

    # DP over bitmasks: sum(mask) = sum(mask without lsb) + phi[lsb_index]
    sums: list[float] = [0.0] * full
    for mask in range(1, full):
        lsb = mask & -mask
        idx = int(lsb).bit_length() - 1
        sums[mask] = sums[mask ^ int(lsb)] + (phi[idx] if 0 <= idx < len(phi) else 0.0)

    return {int(mask): float(sums[mask]) for mask in range(1, full)}


def rank_by_group_sum_shapley(scores_by_mask: Mapping[int, float], n: int) -> Dict[int, int]:
    """Return dense ranks (1 is best) for non-empty coalitions by sum-of-Shapley score."""
    values = group_sum_shapley_values(scores_by_mask, n)
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


__all__ = ["group_sum_shapley_values", "rank_by_group_sum_shapley"]

