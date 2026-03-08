"""Ranking rules on an observed subset of coalitions.

Some real datasets provide only an observed subset of coalition masks rather than
the full 2^N set. For those datasets, we define "observed-set" variants of rank-
based rules by restricting comparisons/sums to the observed masks.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping


def _popcount(x: int) -> int:
    return int(x).bit_count()


def ordinal_banzhaf_detail_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, Dict[str, int]]:
    """Observed-set variant of ordinal Banzhaf detail for players.

    Counts only pairs (S, S∪{i}) that are both present in the observed mask set.
    """
    masks_set = {int(m) for m in masks}
    u_plus = [0] * n
    u_minus = [0] * n
    for s in masks_set:
        base_level = int(level_of_mask.get(int(s), 0))
        if base_level <= 0:
            continue
        for i in range(n):
            bit = 1 << i
            if s & bit:
                continue
            with_i = s | bit
            if with_i not in masks_set:
                continue
            li = int(level_of_mask.get(int(with_i), 0))
            if li <= 0:
                continue
            if li < base_level:
                u_plus[i] += 1
            elif li > base_level:
                u_minus[i] += 1
    detail: Dict[int, Dict[str, int]] = {}
    for i in range(n):
        detail[i] = {"u_plus": int(u_plus[i]), "u_minus": int(u_minus[i]), "s": int(u_plus[i] - u_minus[i])}
    return detail


def rank_by_ordinal_banzhaf_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    """Dense ranks (1 is best) for players by observed-set ordinal Banzhaf score."""
    if n <= 0:
        return {}
    detail = ordinal_banzhaf_detail_observed(level_of_mask, masks, n)
    s = [detail[i]["s"] for i in range(n)]
    order = sorted(range(n), key=lambda i: (-s[i], i))
    ranks: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for i in order:
        if last is None or s[i] != last:
            current += 1
            last = s[i]
        ranks[int(i)] = int(current)
    return ranks


def group_ordinal_banzhaf_detail_observed(level_of_mask: Mapping[int, int], masks: Iterable[int]) -> Dict[int, Dict[str, int]]:
    """Observed-set variant of group ordinal Banzhaf detail for coalitions.

    For each non-empty T in observed masks, counts only pairs (S, S∪T) that are
    both present in the observed mask set and disjoint (S∩T=∅).
    """
    masks_set = {int(m) for m in masks}
    non_empty = [m for m in masks_set if m != 0]
    detail: Dict[int, Dict[str, int]] = {}
    for t in non_empty:
        u_plus = 0
        u_minus = 0
        for s in masks_set:
            if s & t:
                continue
            u = s | t
            if u not in masks_set:
                continue
            l_u = int(level_of_mask.get(int(u), 0))
            l_s = int(level_of_mask.get(int(s), 0))
            if l_u <= 0 or l_s <= 0:
                continue
            if l_u < l_s:
                u_plus += 1
            elif l_u > l_s:
                u_minus += 1
        detail[int(t)] = {"u_plus": int(u_plus), "u_minus": int(u_minus), "s": int(u_plus - u_minus)}
    return detail


def rank_by_group_ordinal_banzhaf_observed(level_of_mask: Mapping[int, int], masks: Iterable[int]) -> Dict[int, int]:
    """Dense ranks (1 is best) for observed non-empty coalitions by observed G-OB score."""
    detail = group_ordinal_banzhaf_detail_observed(level_of_mask, masks)
    order = sorted(detail.keys(), key=lambda t: (-detail[t]["s"], int(t)))
    ranks: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for t in order:
        s = int(detail[t]["s"])
        if last is None or s != last:
            current += 1
            last = s
        ranks[int(t)] = int(current)
    return ranks


def rp_scores_observed(level_of_mask: Mapping[int, int], masks: Iterable[int]) -> Dict[int, int]:
    """Observed-set RP(S) for non-empty observed masks."""
    observed = [int(m) for m in masks if int(m) != 0 and int(level_of_mask.get(int(m), 0)) > 0]
    if not observed:
        return {}
    ranks = {m: int(level_of_mask[int(m)]) for m in observed}
    size_by_rank: Dict[int, int] = {}
    for r in ranks.values():
        size_by_rank[r] = size_by_rank.get(r, 0) + 1
    ordered_ranks = sorted(size_by_rank.keys())
    total = sum(size_by_rank.values())
    better_count_by_rank: Dict[int, int] = {}
    prefix = 0
    for r in ordered_ranks:
        better_count_by_rank[r] = prefix
        prefix += size_by_rank[r]

    rp_by_mask: Dict[int, int] = {}
    for m, r in ranks.items():
        better = better_count_by_rank[r]
        equal = size_by_rank[r]
        worse = total - better - equal
        rp_by_mask[int(m)] = int(worse - better)
    return rp_by_mask


def rp_index_values_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, float]:
    """Observed-set Δ^RP(S) for observed coalitions with |S|>=2."""
    rp = rp_scores_observed(level_of_mask, masks)
    out: Dict[int, float] = {}
    for m, rp_s in rp.items():
        if _popcount(m) < 2:
            continue
        members = [i for i in range(n) if (m >> i) & 1]
        if not members:
            continue
        avg_single = sum(rp.get(1 << i, 0) for i in members) / float(len(members))
        out[int(m)] = float(rp_s) - float(avg_single)
    return out


def rank_by_rp_index_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    values = rp_index_values_observed(level_of_mask, masks, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    current = 0
    last: float | None = None
    for m in order:
        v = float(values[m])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(m)] = int(current)
    return ranks


def updown_counts_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, tuple[int, int]]:
    masks_set = {int(m) for m in masks}
    single_rank = {1 << i: int(level_of_mask.get(1 << i, 0)) for i in range(n)}
    out: Dict[int, tuple[int, int]] = {}
    for m in masks_set:
        if _popcount(m) < 2:
            continue
        r_s = int(level_of_mask.get(int(m), 0))
        if r_s <= 0:
            continue
        up = 0
        down = 0
        for i in range(n):
            bit = 1 << i
            if not (m & bit):
                continue
            r_i = int(single_rank.get(bit, 0))
            if r_i <= 0:
                continue
            if r_s < r_i:
                up += 1
            elif r_i < r_s:
                down += 1
        out[int(m)] = (int(up), int(down))
    return out


def ud_score_values_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    counts = updown_counts_observed(level_of_mask, masks, n)
    base = int(n) + 1
    return {int(m): int(up) * base - int(down) for m, (up, down) in counts.items()}


def du_score_values_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    counts = updown_counts_observed(level_of_mask, masks, n)
    base = int(n) + 1
    return {int(m): -int(down) * base + int(up) for m, (up, down) in counts.items()}


def rank_by_ud_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    values = ud_score_values_observed(level_of_mask, masks, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for m in order:
        v = int(values[m])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(m)] = int(current)
    return ranks


def rank_by_du_observed(level_of_mask: Mapping[int, int], masks: Iterable[int], n: int) -> Dict[int, int]:
    values = du_score_values_observed(level_of_mask, masks, n)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for m in order:
        v = int(values[m])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(m)] = int(current)
    return ranks


def red_index_values_observed(level_of_mask: Mapping[int, int], masks: Iterable[int]) -> Dict[int, int]:
    """Observed-set Red(S) for observed non-empty coalitions."""
    masks_set = {int(m) for m in masks}
    observed = [m for m in masks_set if m != 0 and int(level_of_mask.get(int(m), 0)) > 0]
    ranks = {m: int(level_of_mask[int(m)]) for m in observed}
    out: Dict[int, int] = {}
    for s, r_s in ranks.items():
        count = 0
        for t, r_t in ranks.items():
            if s == t:
                continue
            if (s & t) == s and r_s <= r_t:
                count += 1
        out[int(s)] = int(count)
    return out


def rank_by_red_index_observed(level_of_mask: Mapping[int, int], masks: Iterable[int]) -> Dict[int, int]:
    values = red_index_values_observed(level_of_mask, masks)
    order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
    ranks: Dict[int, int] = {}
    current = 0
    last: int | None = None
    for m in order:
        v = int(values[m])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(m)] = int(current)
    return ranks


__all__ = [
    "du_score_values_observed",
    "ordinal_banzhaf_detail_observed",
    "rank_by_du_observed",
    "rank_by_group_ordinal_banzhaf_observed",
    "rank_by_ordinal_banzhaf_observed",
    "rank_by_red_index_observed",
    "rank_by_rp_index_observed",
    "red_index_values_observed",
    "rank_by_ud_observed",
    "ud_score_values_observed",
    "updown_counts_observed",
    "rp_index_values_observed",
]
