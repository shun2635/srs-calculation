"""Redundancy axiom for interaction comparison rules.

For any coalition S and player i not in S:
  if S ≽ S∪{i} (base order from `rank`) then S R^I (S∪{i}) (interaction weak order).

Base weak order (≽):
  A ≽ B  <=>  rank(A) <= rank(B)   (1 is best)

Interaction weak order (R^I):
  A R^I B  <=>  rank_I(A) <= rank_I(B)   (1 is best)

We count how many comparisons (S, S∪{i}) are constrained and satisfied.
Comparisons are counted only when both sides have interaction ranks.
"""

from __future__ import annotations

from typing import Mapping


def count_redundancy(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
) -> tuple[int, int]:
    if n_players <= 0:
        return (0, 0)

    full = 1 << int(n_players)
    constraints = 0
    satisfied = 0

    for s in range(0, full):
        r_is = interaction_rank_by_mask.get(int(s))
        if r_is is None:
            continue
        r_s = base_rank_by_mask.get(int(s))
        if r_s is None:
            continue
        complement = (full - 1) ^ int(s)
        add = complement
        while add:
            bit = add & -add
            t = int(s) | int(bit)
            add &= add - 1
            r_it = interaction_rank_by_mask.get(int(t))
            if r_it is None:
                continue
            r_t = base_rank_by_mask.get(int(t))
            if r_t is None:
                continue
            if int(r_s) <= int(r_t):
                constraints += 1
                if int(r_is) <= int(r_it):
                    satisfied += 1

    return int(constraints), int(satisfied)


def collect_redundancy_violations(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
    max_examples: int,
) -> list[tuple[int, int]]:
    """Return up to max_examples violating (S, S∪{i}) pairs."""
    out: list[tuple[int, int]] = []
    if max_examples <= 0 or n_players <= 0:
        return out

    full = 1 << int(n_players)
    for s in range(0, full):
        r_is = interaction_rank_by_mask.get(int(s))
        if r_is is None:
            continue
        r_s = base_rank_by_mask.get(int(s))
        if r_s is None:
            continue
        complement = (full - 1) ^ int(s)
        add = complement
        while add:
            bit = add & -add
            t = int(s) | int(bit)
            add &= add - 1
            r_it = interaction_rank_by_mask.get(int(t))
            if r_it is None:
                continue
            r_t = base_rank_by_mask.get(int(t))
            if r_t is None:
                continue
            if int(r_s) <= int(r_t) and int(r_is) > int(r_it):
                out.append((int(s), int(t)))
                if len(out) >= max_examples:
                    return out

    return out


__all__ = ["count_redundancy", "collect_redundancy_violations"]

