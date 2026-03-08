"""Enumerate all strict total orders over 2^N coalitions for small N.

日本語補足: N プレイヤーの全ての連合 (2^N) に対して、全順位 (順序) を全列挙します。
組合せ爆発を避けるため、N は最大 3 に制限します (8! = 40,320 通り)。
"""

from __future__ import annotations

from itertools import permutations
from typing import Iterable, List, Tuple

from ..prelim.types import Coalition, CoalitionEncoding


def _bitmask(coalition: Coalition, n: int) -> int:
    mask = 0
    for p in coalition:
        if 1 <= p <= n:
            mask |= 1 << (p - 1)
    return mask


def all_coalitions_sorted(n: int) -> List[Coalition]:
    """Return all coalitions over N, sorted by increasing bitmask.

    日本語補足: ビットマスク (プレイヤー番号順) の昇順で安定に並べます。
    """
    enc = CoalitionEncoding(n)
    coals = list(enc.iter_coalitions(range(1, n + 1)))
    coals.sort(key=lambda c: _bitmask(c, n))
    return coals


def enumerate_orders(n: int) -> Iterable[Tuple[Coalition, ...]]:
    """Yield every strict total order (permutation) of 2^N coalitions for small N.

    Raises ValueError if n > 3 to avoid combinatorial explosion.

    日本語補足: N > 3 は 16! 以上となり実用的でないため禁止します。
    """
    if not 1 <= n <= 3:
        raise ValueError("enumerate-orders supports players n in [1, 3].")
    base = all_coalitions_sorted(n)
    yield from permutations(base)


__all__ = ["enumerate_orders", "all_coalitions_sorted"]
