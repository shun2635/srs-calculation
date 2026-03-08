"""Redundancy Index rule based on ranking information only.

Comparison set: X = 2^N \\ {∅}.

For S in X:
  Red(S) = |{ T in X : S ⊂ T and S ≽ T }|

Using the `rank` column (dense rank; 1 is best), the weak order is:
  S ≽ T  <=>  rank(S) <= rank(T)
"""

from __future__ import annotations

from typing import Dict, Mapping


def red_index_values_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return Red(S) for all non-empty coalitions S."""
    if n <= 0:
        return {}
    full = 1 << n
    all_players_mask = full - 1

    ranks = {mask: int(level_of_mask[int(mask)]) for mask in range(1, full)}
    out: Dict[int, int] = {}

    for s_mask, r_s in ranks.items():
        complement = all_players_mask ^ s_mask
        count = 0
        sub = complement
        while True:
            if sub != 0:
                t_mask = s_mask | sub
                # S ≽ T  <=>  rank(S) <= rank(T)
                if r_s <= ranks[int(t_mask)]:
                    count += 1
            if sub == 0:
                break
            sub = (sub - 1) & complement
        out[int(s_mask)] = int(count)

    return out


def rank_by_red_index_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return dense ranks for non-empty coalitions by Red(S) (higher is better)."""
    values = red_index_values_from_levels(level_of_mask, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks_out: Dict[int, int] = {}
    last = None
    current = 0
    for mask in order:
        v = values[mask]
        if last is None or v != last:
            current += 1
            last = v
        ranks_out[int(mask)] = current
    return ranks_out


__all__ = ["red_index_values_from_levels", "rank_by_red_index_from_levels"]

