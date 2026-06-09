"""Aggregation axes for paper-simulation summaries.

This module owns *how rows are grouped* (the aggregation axis), decoupled from
*what statistic is computed per group* (the reducers in ``metrics.py``). Keeping
the axis here means a new aggregation axis -- e.g. a future n-sweep that groups
by (n, k) -- can be added as a new grouping function without touching the metric
calculation or the per-group reducers.

The only axis used today is "by coalition size k, plus an overall bucket", which
reproduces the historical summary order exactly (sorted distinct k values, then
``overall``). Structure-only: no numbers change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")

OVERALL_KEY = "overall"


@dataclass(frozen=True)
class RowGroup(Generic[T]):
    """A named group of rows produced by an aggregation axis."""

    key: str
    rows: tuple[T, ...]


def group_by_k_with_overall(
    rows: Iterable[T],
    *,
    k_of: Callable[[T], int],
) -> tuple[RowGroup[T], ...]:
    """Group rows by coalition size ``k`` (sorted), then an ``overall`` bucket.

    Returns an empty tuple for empty input, matching the historical summaries
    which returned ``()`` when there were no rows.
    """

    row_list = list(rows)
    if not row_list:
        return ()

    groups: list[RowGroup[T]] = [
        RowGroup(str(k), tuple(row for row in row_list if k_of(row) == k))
        for k in sorted({k_of(row) for row in row_list})
    ]
    groups.append(RowGroup(OVERALL_KEY, tuple(row_list)))
    return tuple(groups)


def group_by_n_and_k_with_overall(
    rows: Iterable[T],
    *,
    n_of: Callable[[T], int],
    k_of: Callable[[T], int],
) -> tuple[RowGroup[T], ...]:
    """Group rows by player count ``n``, then by ``k`` with an overall bucket.

    For each ``n`` (sorted) this yields that ``n``'s ``group_by_k_with_overall``
    groups, so every returned group stays within a single ``n``. Existing
    per-group reducers (which read ``n`` from the rows themselves) therefore work
    unchanged -- this is the n-sweep aggregation axis, added without touching the
    reducers or the metric calculation.
    """

    row_list = list(rows)
    if not row_list:
        return ()

    groups: list[RowGroup[T]] = []
    for n in sorted({n_of(row) for row in row_list}):
        n_rows = [row for row in row_list if n_of(row) == n]
        groups.extend(group_by_k_with_overall(n_rows, k_of=k_of))
    return tuple(groups)


__all__ = [
    "OVERALL_KEY",
    "RowGroup",
    "group_by_k_with_overall",
    "group_by_n_and_k_with_overall",
]
