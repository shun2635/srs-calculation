from __future__ import annotations

from srs_calculation.application.paper_simulation.full_comparison import (
    PAPER_LENS_RULE_SPECS,
    PAPER_LENS_SPECS,
    PAPER_RANK_RULE_SPECS,
)


def test_paper_heatmap_rule_sets_use_main_text_comparators() -> None:
    lens_labels = [spec.label for spec in PAPER_LENS_RULE_SPECS]
    rank_labels = [spec.label for spec in PAPER_RANK_RULE_SPECS]

    assert lens_labels == [
        "Group Lex-cel",
        "RP-Difference",
        "Group Shapley Value",
        "Shapley Interaction Index",
        "Banzhaf Interaction Index",
    ]
    assert rank_labels == [
        "Group Lex-cel",
        "Group Shapley Value",
        "RP-Difference",
        "Shapley Interaction Index",
        "Banzhaf Interaction Index",
    ]
    assert "UD" not in lens_labels
    assert "DU" not in lens_labels
    assert "Red" not in lens_labels
    assert "Group Ordinal Banzhaf" not in lens_labels


def test_paper_heatmap_lens_labels_use_paper_names() -> None:
    assert [spec.label for spec in PAPER_LENS_SPECS] == [
        "Reversal",
        "Up",
        "Down",
        "Redundancy",
    ]
