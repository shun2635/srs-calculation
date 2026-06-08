"""Guards for the aggregation axis (Step3 structure).

Pins the "by k, then overall" grouping that the paper summaries rely on, so the
axis can be reused/extended (e.g. a future n-sweep) without silently changing
the historical group order.
"""

from __future__ import annotations

from dataclasses import dataclass

from srs_calculation.application.paper_simulation.aggregation import (
    OVERALL_KEY,
    group_by_k_with_overall,
)


@dataclass(frozen=True)
class _Row:
    k: int
    value: int


def test_group_by_k_with_overall_orders_sorted_k_then_overall() -> None:
    rows = [_Row(3, 1), _Row(2, 2), _Row(3, 3), _Row(2, 4)]

    groups = group_by_k_with_overall(rows, k_of=lambda row: row.k)

    assert [group.key for group in groups] == ["2", "3", OVERALL_KEY]
    assert [row.value for row in groups[0].rows] == [2, 4]
    assert [row.value for row in groups[1].rows] == [1, 3]
    # The overall bucket keeps every row in original order.
    assert [row.value for row in groups[2].rows] == [1, 2, 3, 4]


def test_group_by_k_with_overall_empty_input_returns_empty() -> None:
    assert group_by_k_with_overall([], k_of=lambda row: row.k) == ()
