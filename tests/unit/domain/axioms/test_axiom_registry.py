from __future__ import annotations

import pytest

from srs_calculation.domain.axioms.registry import build_default_axiom_registry


def test_default_axiom_registry_contains_legacy_axioms() -> None:
    registry = build_default_axiom_registry()

    assert registry.list_axiom_ids() == [
        "gekokujou-2p",
        "gekokujou-weak-n",
        "give-2p",
        "give-weak-n",
        "redundancy",
        "take-2p",
        "take-weak-n",
    ]
    assert registry.get("redundancy").axiom_id == "redundancy"


def test_axiom_registry_raises_clear_error_for_unknown_axiom() -> None:
    registry = build_default_axiom_registry()

    with pytest.raises(KeyError, match="unknown axiom_id 'missing'"):
        registry.get("missing")
