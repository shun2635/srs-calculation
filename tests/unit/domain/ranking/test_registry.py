from __future__ import annotations

import pytest

from srs_calculation.domain.ranking.registry import build_default_ranking_rule_registry


def test_default_ranking_rule_registry_contains_first_batch_rules() -> None:
    registry = build_default_ranking_rule_registry()

    assert registry.list_rule_ids() == [
        "banzhaf",
        "lexcel",
        "ordinal_banzhaf",
        "shapley",
    ]
    assert registry.get("shapley").rule_id == "shapley"
    assert registry.get("ordinal_banzhaf").rule_id == "ordinal_banzhaf"


def test_registry_raises_clear_error_for_unknown_rule_id() -> None:
    registry = build_default_ranking_rule_registry()

    with pytest.raises(KeyError, match="unknown rule_id 'missing'"):
        registry.get("missing")
