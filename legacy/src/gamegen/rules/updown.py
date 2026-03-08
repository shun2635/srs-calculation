"""UD/DU rules based on (up, down) counts from ranking information only.

Uses the base weak order encoded by the `rank` column (dense rank, 1 is best).

For a non-empty coalition T:
  up(T)   = |{ i in T : T ≻ {i} }|
  down(T) = |{ i in T : {i} ≻ T }|

Rules for |S|>=2:
  UD: maximize up, then minimize down  (lexicographic (up, -down))
  DU: minimize down, then maximize up  (lexicographic (-down, up))

Internally we compute an integer "score" that preserves the lexicographic order
for ranking, but the rankings CSV outputs the (up, down) vector instead:
  score_ud(S) = up(S) * (n+1) - down(S)
  score_du(S) = -down(S) * (n+1) + up(S)
"""

from __future__ import annotations

from typing import Dict, Mapping, Tuple


def _popcount(x: int) -> int:
    return int(x).bit_count()


def updown_counts_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, Tuple[int, int]]:
    """Return (up(S), down(S)) for coalitions with |S|>=2."""
    if n <= 0:
        return {}
    full = 1 << n

    single_rank = {1 << i: int(level_of_mask.get(1 << i, 0)) for i in range(n)}

    out: Dict[int, Tuple[int, int]] = {}
    for mask in range(1, full):
        if _popcount(mask) < 2:
            continue
        r_s = int(level_of_mask.get(int(mask), 0))
        if r_s <= 0:
            continue
        up = 0
        down = 0
        for i in range(n):
            bit = 1 << i
            if not (mask & bit):
                continue
            r_i = int(single_rank.get(bit, 0))
            if r_i <= 0:
                continue
            if r_s < r_i:
                up += 1
            elif r_i < r_s:
                down += 1
        out[int(mask)] = (int(up), int(down))
    return out


def ud_score_values_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return score_ud(S) for coalitions with |S|>=2 (higher is better)."""
    counts = updown_counts_from_levels(level_of_mask, n)
    base = int(n) + 1
    return {int(m): int(up) * base - int(down) for m, (up, down) in counts.items()}


def du_score_values_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Return score_du(S) for coalitions with |S|>=2 (higher is better)."""
    counts = updown_counts_from_levels(level_of_mask, n)
    base = int(n) + 1
    return {int(m): -int(down) * base + int(up) for m, (up, down) in counts.items()}


def rank_by_ud_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Dense ranks for |S|>=2 by UD rule (higher score_ud is better)."""
    values = ud_score_values_from_levels(level_of_mask, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    last: int | None = None
    current = 0
    for mask in order:
        v = int(values[mask])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(mask)] = int(current)
    return ranks


def rank_by_du_from_levels(level_of_mask: Mapping[int, int], n: int) -> Dict[int, int]:
    """Dense ranks for |S|>=2 by DU rule (higher score_du is better)."""
    values = du_score_values_from_levels(level_of_mask, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    last: int | None = None
    current = 0
    for mask in order:
        v = int(values[mask])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(mask)] = int(current)
    return ranks


__all__ = [
    "du_score_values_from_levels",
    "rank_by_du_from_levels",
    "rank_by_ud_from_levels",
    "ud_score_values_from_levels",
    "updown_counts_from_levels",
]
