from __future__ import annotations

from srs_calculation.application.synthetic_workflow import (
    game_satisfies_constraints,
    normalize_constraint_selection,
    resolve_synthetic_output_layout,
)
from srs_calculation.domain.games.coalition_game import CoalitionGame


def test_normalize_constraint_selection_expands_tu_profile() -> None:
    selection = normalize_constraint_selection(profile="tu")

    assert selection.constraint_set_id == "tu"
    assert selection.constraints == ("empty_zero", "monotone", "superadditive")


def test_resolve_synthetic_output_layout_uses_constraint_set_slug(tmp_path) -> None:
    layout = resolve_synthetic_output_layout(
        out_dir=tmp_path / "outputs",
        constraints=("empty_zero", "monotone"),
    )

    assert layout.synthetic_root == tmp_path / "outputs" / "synthetic" / "empty_zero+monotone"
    assert layout.rankings_dir(3) == tmp_path / "outputs" / "synthetic" / "empty_zero+monotone" / "rankings" / "n3"


def test_game_satisfies_constraints_checks_monotone_and_superadditive() -> None:
    game = CoalitionGame.from_scores_by_mask(
        2,
        {
            0b00: 0.0,
            0b01: 1.0,
            0b10: 2.0,
            0b11: 3.0,
        },
    )

    assert game_satisfies_constraints(game, ("empty_zero", "monotone", "superadditive"))
