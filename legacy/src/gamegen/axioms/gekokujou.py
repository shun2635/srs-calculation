"""Gekokujou (upheaval) axioms for interaction comparison rules.

Base weak order (≽) is taken from the rankings CSV `rank` column (1 is best):
  A ≽ B  <=>  rank(A) <= rank(B)
  A ≻ B  <=>  rank(A) <  rank(B)

Interaction strict preference (P^I) is taken from an interaction rule rank column:
  T P^I S  <=>  rank_I(T) < rank_I(S)

We count how many ordered comparisons (S, T) are constrained by the axiom, and
how many of those satisfy the required conclusion.
"""

from __future__ import annotations

from typing import Mapping, Tuple


def _popcount(x: int) -> int:
    return int(x).bit_count()


def _singleton_mask(player_index: int) -> int:
    return 1 << int(player_index)


def _sorted_singleton_ranks(mask: int, base_rank_by_mask: Mapping[int, int], n_players: int) -> list[int]:
    ranks: list[int] = []
    for i in range(n_players):
        if mask & (1 << i):
            ranks.append(int(base_rank_by_mask[_singleton_mask(i)]))
    ranks.sort()
    return ranks


def _matching_exists_and_has_strict(singleton_ranks_s: list[int], singleton_ranks_t: list[int]) -> Tuple[bool, bool]:
    """Check existence of a bijection with componentwise rank dominance.

    Condition in the axiom: there exists π s.t. for all i, {s_i} ≽ {t_{π(i)}}.
    Using total preorder by numeric ranks, this is equivalent to checking that the
    sorted singleton ranks satisfy rS[i] <= rT[i] for all i.
    """

    if len(singleton_ranks_s) != len(singleton_ranks_t):
        return False, False
    has_strict = False
    for rs, rt in zip(singleton_ranks_s, singleton_ranks_t, strict=True):
        if int(rs) > int(rt):
            return False, False
        if int(rs) < int(rt):
            has_strict = True
    return True, has_strict


def _count_for_size(
    *,
    n_players: int,
    coalition_size: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
) -> tuple[int, int]:
    if coalition_size < 2 or coalition_size > n_players:
        return (0, 0)

    full = 1 << n_players
    masks = [m for m in range(1, full) if _popcount(m) == coalition_size]
    if len(masks) <= 1:
        return (0, 0)

    constraints = 0
    satisfied = 0

    singleton_ranks_cache: dict[int, list[int]] = {}
    for m in masks:
        singleton_ranks_cache[m] = _sorted_singleton_ranks(m, base_rank_by_mask, n_players)

    for s_mask in masks:
        r_s = int(base_rank_by_mask[int(s_mask)])
        r_is = interaction_rank_by_mask.get(int(s_mask))
        for t_mask in masks:
            if t_mask == s_mask:
                continue
            r_t = int(base_rank_by_mask[int(t_mask)])
            # S ≼ T  <=>  rank(S) >= rank(T)
            if r_s < r_t:
                continue

            ok, strict_singleton = _matching_exists_and_has_strict(
                singleton_ranks_cache[int(s_mask)],
                singleton_ranks_cache[int(t_mask)],
            )
            if not ok:
                continue

            strict_group = r_s > r_t  # S ≺ T
            if not (strict_singleton or strict_group):
                continue

            constraints += 1
            r_it = interaction_rank_by_mask.get(int(t_mask))
            if r_is is not None and r_it is not None and int(r_it) < int(r_is):
                satisfied += 1

    return constraints, satisfied


def count_gekokujou_2p(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
) -> tuple[int, int]:
    """Count constrained/satisfied comparisons for the 2-player version (|S|=|T|=2)."""
    return _count_for_size(
        n_players=n_players,
        coalition_size=2,
        base_rank_by_mask=base_rank_by_mask,
        interaction_rank_by_mask=interaction_rank_by_mask,
    )


def count_gekokujou_weak_n(
    *,
    n_players: int,
    base_rank_by_mask: Mapping[int, int],
    interaction_rank_by_mask: Mapping[int, int],
    min_coalition_size: int = 2,
) -> tuple[int, int]:
    """Count constrained/satisfied comparisons for the weak n-person extension.

    We aggregate across all coalition sizes k where min_coalition_size <= k <= n_players.
    (k=2 overlaps with the 2-player axiom; keep separately if needed.)
    """
    constraints = 0
    satisfied = 0
    for k in range(int(min_coalition_size), int(n_players) + 1):
        c, s = _count_for_size(
            n_players=n_players,
            coalition_size=k,
            base_rank_by_mask=base_rank_by_mask,
            interaction_rank_by_mask=interaction_rank_by_mask,
        )
        constraints += int(c)
        satisfied += int(s)
    return constraints, satisfied


__all__ = ["count_gekokujou_2p", "count_gekokujou_weak_n"]

