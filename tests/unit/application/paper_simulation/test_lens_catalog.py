"""Guards for the paper lens catalog (Step2 structure).

Pins the registered lens set, order and labels, and checks that every lens
exposes the unified ``counts`` interface so the bifurcated dispatch cannot
silently come back.
"""

from __future__ import annotations

from srs_calculation.application.paper_simulation.lens_catalog import (
    PAPER_LENS_CATALOG,
    PAPER_LENS_SPECS,
    AxiomLens,
    PaperLens,
    ReversalLens,
    get_lens,
)
from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.ranking.rules.rankdiff import RankdiffRule


def test_lens_catalog_order_and_labels() -> None:
    assert [(lens.lens_id, lens.label) for lens in PAPER_LENS_CATALOG] == [
        ("reversal", "Reversal"),
        ("up", "Up"),
        ("down", "Down"),
        ("redundancy", "Redundancy"),
    ]
    # The (id, label) view must mirror the catalog exactly.
    assert [(spec.lens_id, spec.label) for spec in PAPER_LENS_SPECS] == [
        (lens.lens_id, lens.label) for lens in PAPER_LENS_CATALOG
    ]


def test_every_lens_implements_the_unified_interface() -> None:
    for lens in PAPER_LENS_CATALOG:
        assert isinstance(lens, PaperLens)
    assert isinstance(get_lens("reversal"), ReversalLens)
    assert isinstance(get_lens("up"), AxiomLens)


def test_lens_counts_returns_satisfied_and_constraints() -> None:
    scores = {mask: float(mask) for mask in range(1 << 3)}
    game = CoalitionGame.from_scores_by_mask(3, scores)
    rank_set = RankdiffRule().evaluate(game).rank_set
    assert rank_set is not None

    for lens in PAPER_LENS_CATALOG:
        satisfied, constraints = lens.counts(game, rank_set, (2,))
        assert 0 <= satisfied <= constraints
