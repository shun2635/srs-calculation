from __future__ import annotations

import pytest

from srs_calculation.domain.ranking.registry import build_default_ranking_rule_registry


def test_default_ranking_rule_registry_contains_legacy_rule_set() -> None:
    registry = build_default_ranking_rule_registry()

    assert registry.list_rule_ids() == [
        "banzhaf",
        "banzhaf_interaction",
        "du",
        "group_lexcel",
        "group_ordinal_banzhaf",
        "group_shapley",
        "group_sum_shapley",
        "lexcel",
        "ordinal_banzhaf",
        "red_index",
        "rp_index",
        "shapley",
        "shapley_interaction",
        "ud",
    ]
    assert registry.get("shapley").rule_id == "shapley"
    assert registry.get("ordinal_banzhaf").rule_id == "ordinal_banzhaf"
    assert registry.get("o-banzhaf").rule_id == "ordinal_banzhaf"
    assert registry.get("g-shapley").rule_id == "group_shapley"
    assert registry.get("rp-index").rule_id == "rp_index"


def test_registry_raises_clear_error_for_unknown_rule_id() -> None:
    registry = build_default_ranking_rule_registry()

    with pytest.raises(KeyError, match="unknown rule_id 'missing'"):
        registry.get("missing")
