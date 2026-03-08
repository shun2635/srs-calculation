"""RP Index rule based on ranking information only.

Uses the base weak order encoded by the `rank` column (dense rank, 1 is best).

Comparison set: X = 2^N \\ {∅}.

Rank Point:
  RP(S) = |{T in X : S ≻ T}| - |{T in X : T ≻ S}|

RP Index for |S|>=2:
  Δ^RP(S) = RP(S) - (1/|S|) Σ_{i in S} RP({i})
"""

from __future__ import annotations

from typing import Dict, Mapping


def _popcount(x: int) -> int:
    return x.bit_count()


def rp_scores_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return RP(S) for all non-empty coalitions S."""
    if n <= 0:
        return {}
    full = 1 << n

    # Collect non-empty coalitions only.
    ranks = {mask: int(level_of_mask[int(mask)]) for mask in range(1, full)}
    # Group sizes per rank.
    size_by_rank: Dict[int, int] = {}
    for r in ranks.values():
        size_by_rank[r] = size_by_rank.get(r, 0) + 1

    ordered_ranks = sorted(size_by_rank.keys())
    total = sum(size_by_rank.values())

    # prefix count for strictly better (smaller rank number).
    better_count_by_rank: Dict[int, int] = {}
    prefix = 0
    for r in ordered_ranks:
        better_count_by_rank[r] = prefix
        prefix += size_by_rank[r]

    rp_by_mask: Dict[int, int] = {}
    for mask, r in ranks.items():
        better = better_count_by_rank[r]
        equal = size_by_rank[r]
        worse = total - better - equal
        rp_by_mask[int(mask)] = int(worse - better)
    return rp_by_mask


def rp_index_values_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, float]:
    """Return Δ^RP(S) for coalitions with |S|>=2."""
    rp = rp_scores_from_levels(level_of_mask, n)
    out: Dict[int, float] = {}
    for mask, rp_s in rp.items():
        if _popcount(mask) < 2:
            continue
        members = [i for i in range(n) if (mask >> i) & 1]
        if not members:
            continue
        avg_single = sum(rp.get(1 << i, 0) for i in members) / float(len(members))
        out[int(mask)] = float(rp_s) - float(avg_single)
    return out


def rank_by_rp_index_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return dense ranks for |S|>=2 by Δ^RP(S) (higher is better)."""
    values = rp_index_values_from_levels(level_of_mask, n)
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


__all__ = ["rp_scores_from_levels", "rp_index_values_from_levels", "rank_by_rp_index_from_levels"]

