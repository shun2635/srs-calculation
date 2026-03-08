from __future__ import annotations

import pytest

from gamegen.rules.group_lexcel import (
    coalition_comparator_by_lexcel,
    coalition_groups_by_lexcel,
    sort_coalitions_by_lexcel,
)


def test_coalition_groups_simple_layers() -> None:
    layers = [
        {0b11},
        {0b01, 0b10},
    ]
    groups = coalition_groups_by_lexcel(layers, n=2)
    assert groups == [{0b01, 0b10}, {0b11}]


def test_coalition_groups_complex_case() -> None:
    layers = [
        {0b111},
        {0b011, 0b101},
        {0b001, 0b010, 0b100},
    ]
    groups = coalition_groups_by_lexcel(layers, n=3)
    assert groups == [
        {0b001},
        {0b010, 0b100},
        {0b011, 0b101},
        {0b110, 0b111},
    ]


def test_comparator_obeys_lexicographic_order() -> None:
    layers = [
        {0b111},
        {0b011, 0b101},
        {0b001, 0b010, 0b100},
    ]
    cmp_fn = coalition_comparator_by_lexcel(layers, n=3)
    assert cmp_fn(0b001, 0b111) == -1
    assert cmp_fn(0b010, 0b100) == 0
    assert cmp_fn(0b011, 0b101) == 0
    assert cmp_fn(0b110, 0b011) == 1


def test_sort_uses_comparator() -> None:
    layers = [
        {0b11},
        {0b01, 0b10},
    ]
    coalitions = [0b10, 0b11, 0b01]
    assert sort_coalitions_by_lexcel(coalitions, layers, n=2) == [0b01, 0b10, 0b11]


def test_duplicate_coalition_raises() -> None:
    layers = [
        [0b01, 0b10],
        [0b01],
    ]
    with pytest.raises(ValueError):
        coalition_groups_by_lexcel(layers, n=2)


def test_comparator_rejects_zero_mask() -> None:
    layers = [{0b01}]
    cmp_fn = coalition_comparator_by_lexcel(layers, n=1)
    with pytest.raises(ValueError):
        cmp_fn(0b00, 0b01)
