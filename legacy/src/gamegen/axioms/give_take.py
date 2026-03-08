"""Give/Take axioms for 2-player coalitions.

We use `rank` (1 is best) to derive a strict order:
  A ≻ B  <=>  rank(A) < rank(B)

Ordinal marginal contribution for i ∉ S:
  m_i^S =  1 if S∪{i} ≻ S
         -1 if S ≻ S∪{i}
          0 otherwise (ties)

For a 2-player coalition T, define:
  give(T) = |{ i∈T : m_i^{T\\{i}} =  1 }|
  take(T) = |{ i∈T : m_i^{T\\{i}} = -1 }|

Give axiom (2p):  give(T) > give(U)  =>  T P^I U
Take axiom (2p):  take(T) > take(U)  =>  U P^I T

We count how many ordered comparisons (T,U) are constrained, and how many satisfy the conclusion.
"""

from __future__ import annotations

from typing import Mapping


def _popcount(x: int) -> int:
    return int(x).bit_count()


def _members(mask: int, n_players: int) -> list[int]:
    return [i for i in range(int(n_players)) if (int(mask) >> i) & 1]


def _give_take_for_pair(
    *,
    mask: int,
    base_rank_by_mask: Mapping[int, int],
    n_players: int,
) -> tuple[int, int]:
    r_t = int(base_rank_by_mask[int(mask)])
    give = 0
    take = 0
    for i in _members(mask, n_players):
        s_mask = int(mask) & ~(1 << int(i))
        if s_mask == 0:
            continue
        r_s = int(base_rank_by_mask[int(s_mask)])
        if r_t < r_s:
            give += 1
        elif r_s < r_t:
            take += 1
    return int(give), int(take)

def _give_take_for_coalition(
    *,
    mask: int,
    base_rank_by_mask: Mapping[int, int],
    n_players: int,
) -> tuple[int, int]:
    """Compute give/take for an arbitrary non-empty coalition mask."""
    r_t = int(base_rank_by_mask[int(mask)])
    give = 0
    take = 0
    for i in _members(mask, n_players):
        singleton = 1 << int(i)
        r_i = int(base_rank_by_mask[int(singleton)])
        if r_t < r_i:
            give += 1
        elif r_i < r_t:
            take += 1
    return int(give), int(take)


def count_give_2p(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
) -> tuple[int, int]:
    if n_players < 2:
        return (0, 0)
    full = 1 << int(n_players)
    pairs = [m for m in range(1, full) if _popcount(m) == 2]
    if len(pairs) <= 1:
        return (0, 0)

    give_by_mask = {m: _give_take_for_pair(mask=m, base_rank_by_mask=base_rank_by_mask, n_players=n_players)[0] for m in pairs}

    constraints = 0
    satisfied = 0
    for t in pairs:
        r_it = interaction_rank_by_mask.get(int(t))
        for u in pairs:
            if u == t:
                continue
            if int(give_by_mask[int(t)]) <= int(give_by_mask[int(u)]):
                continue
            constraints += 1
            r_iu = interaction_rank_by_mask.get(int(u))
            if r_it is not None and r_iu is not None and int(r_it) < int(r_iu):
                satisfied += 1
    return int(constraints), int(satisfied)


def count_take_2p(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
) -> tuple[int, int]:
    if n_players < 2:
        return (0, 0)
    full = 1 << int(n_players)
    pairs = [m for m in range(1, full) if _popcount(m) == 2]
    if len(pairs) <= 1:
        return (0, 0)

    take_by_mask = {m: _give_take_for_pair(mask=m, base_rank_by_mask=base_rank_by_mask, n_players=n_players)[1] for m in pairs}

    constraints = 0
    satisfied = 0
    for t in pairs:
        r_it = interaction_rank_by_mask.get(int(t))
        for u in pairs:
            if u == t:
                continue
            if int(take_by_mask[int(t)]) <= int(take_by_mask[int(u)]):
                continue
            constraints += 1
            r_iu = interaction_rank_by_mask.get(int(u))
            # Requires U P^I T
            if r_it is not None and r_iu is not None and int(r_iu) < int(r_it):
                satisfied += 1
    return int(constraints), int(satisfied)


def count_give_weak_n(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
    min_coalition_size: int = 2,
) -> tuple[int, int]:
    """Give axiom (weak n-person extension), aggregated across coalition sizes."""
    if n_players < 2:
        return (0, 0)
    full = 1 << int(n_players)
    constraints = 0
    satisfied = 0
    for k in range(int(min_coalition_size), int(n_players) + 1):
        masks = [m for m in range(1, full) if _popcount(m) == int(k)]
        if len(masks) <= 1:
            continue
        give_by = {m: _give_take_for_coalition(mask=m, base_rank_by_mask=base_rank_by_mask, n_players=n_players)[0] for m in masks}
        for s in masks:
            r_is = interaction_rank_by_mask.get(int(s))
            for t in masks:
                if t == s:
                    continue
                if int(give_by[int(s)]) <= int(give_by[int(t)]):
                    continue
                constraints += 1
                r_it = interaction_rank_by_mask.get(int(t))
                if r_is is not None and r_it is not None and int(r_is) < int(r_it):
                    satisfied += 1
    return int(constraints), int(satisfied)


def count_take_weak_n(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
    min_coalition_size: int = 2,
) -> tuple[int, int]:
    """Take axiom (weak n-person extension), aggregated across coalition sizes."""
    if n_players < 2:
        return (0, 0)
    full = 1 << int(n_players)
    constraints = 0
    satisfied = 0
    for k in range(int(min_coalition_size), int(n_players) + 1):
        masks = [m for m in range(1, full) if _popcount(m) == int(k)]
        if len(masks) <= 1:
            continue
        take_by = {m: _give_take_for_coalition(mask=m, base_rank_by_mask=base_rank_by_mask, n_players=n_players)[1] for m in masks}
        for s in masks:
            r_is = interaction_rank_by_mask.get(int(s))
            for t in masks:
                if t == s:
                    continue
                if int(take_by[int(s)]) <= int(take_by[int(t)]):
                    continue
                constraints += 1
                r_it = interaction_rank_by_mask.get(int(t))
                if r_is is not None and r_it is not None and int(r_it) < int(r_is):
                    satisfied += 1
    return int(constraints), int(satisfied)


__all__ = [
    "count_give_2p",
    "count_take_2p",
    "count_give_weak_n",
    "count_take_weak_n",
]
