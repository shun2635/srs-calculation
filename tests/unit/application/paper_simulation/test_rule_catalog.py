"""Guards for the paper rule catalog (Step1 structure).

These pin the role membership and per-heatmap display order so a future change
to the catalog cannot silently alter which rules appear in which analysis or in
what column/legend order.
"""

from __future__ import annotations

from srs_calculation.application.paper_simulation.rule_catalog import (
    PAPER_LENS_RULE_SPECS,
    PAPER_RANK_RULE_SPECS,
    PAPER_RULE_CATALOG,
    PAPER_RULE_SPECS,
    ROLE_FOCAL,
    ROLE_LENS_HEATMAP,
    ROLE_RANK_HEATMAP,
    focal_rule_specs,
)


def test_catalog_rule_ids_and_labels() -> None:
    assert [(spec.rule_id, spec.label) for spec in PAPER_RULE_CATALOG] == [
        ("group_lexcel", "Group Lex-cel"),
        ("rankdiff", "Rankdiff"),
        ("group_shapley", "Group Shapley Value"),
        ("shapley_interaction", "Shapley Interaction Index"),
        ("banzhaf_interaction", "Banzhaf Interaction Index"),
    ]
    assert PAPER_RULE_SPECS == PAPER_RULE_CATALOG


def test_lens_and_rank_heatmap_order_match_history() -> None:
    assert [spec.label for spec in PAPER_LENS_RULE_SPECS] == [
        "Group Lex-cel",
        "Rankdiff",
        "Group Shapley Value",
        "Shapley Interaction Index",
        "Banzhaf Interaction Index",
    ]
    assert [spec.label for spec in PAPER_RANK_RULE_SPECS] == [
        "Group Lex-cel",
        "Group Shapley Value",
        "Rankdiff",
        "Shapley Interaction Index",
        "Banzhaf Interaction Index",
    ]


def test_role_membership() -> None:
    lens_ids = {spec.rule_id for spec in PAPER_RULE_CATALOG if spec.has_role(ROLE_LENS_HEATMAP)}
    rank_ids = {spec.rule_id for spec in PAPER_RULE_CATALOG if spec.has_role(ROLE_RANK_HEATMAP)}
    all_ids = {
        "group_lexcel",
        "rankdiff",
        "group_shapley",
        "shapley_interaction",
        "banzhaf_interaction",
    }
    assert lens_ids == all_ids
    assert rank_ids == all_ids
    assert {spec.rule_id for spec in PAPER_RULE_CATALOG if spec.has_role(ROLE_FOCAL)} == {
        "group_lexcel",
        "rankdiff",
    }
    assert [spec.rule_id for spec in focal_rule_specs()] == ["group_lexcel", "rankdiff"]


def test_catalog_rule_instances_are_real_rules() -> None:
    for spec in PAPER_RULE_CATALOG:
        result = spec.rule.evaluate.__name__
        assert result == "evaluate"
