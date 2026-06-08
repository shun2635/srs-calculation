"""Paper-facing lens catalog: the single source for consistency lenses.

A *lens* is an axiomatic constraint set whose satisfaction against a coalition
ranking we measure. Historically the lens evaluation was bifurcated: the
Reversal lens was special-cased (``if lens_id == "reversal"``) and the Up / Down
/ Redundancy lenses were looked up in a separate dict of axioms. This module
unifies both behind one interface:

    counts(game, rank_set, target_sizes) -> (satisfied, constraints)

so adding a lens means registering one object in ``PAPER_LENS_CATALOG``.

Structure-only: the lens set, order, labels and the per-lens counting logic are
identical to the previous implementation, so no numbers change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from ...domain.axioms.axiom import CoalitionRankingAxiom
from ...domain.axioms.evaluators import GiveWeakNAxiom, RedundancyAxiom, TakeWeakNAxiom
from ...domain.games.coalition_game import CoalitionGame
from ...domain.lenses import generate_reversal_constraints
from ...domain.ranking.result import RuleRankSet


@dataclass(frozen=True)
class PaperLensSpec:
    """Lightweight (id, label) view of a lens for headers and figures."""

    lens_id: str
    label: str


class PaperLens(ABC):
    """A lens that counts satisfied / constrained comparisons for a ranking."""

    lens_id: str
    label: str

    @abstractmethod
    def counts(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        target_sizes: Iterable[int],
    ) -> tuple[int, int]:
        """Return (satisfied, constraints); constraints == 0 means NA."""


@dataclass(frozen=True)
class ReversalLens(PaperLens):
    """Reversal lens backed by the formation-value constraint generator."""

    lens_id: str = "reversal"
    label: str = "Reversal"

    def counts(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        target_sizes: Iterable[int],
    ) -> tuple[int, int]:
        constraints = 0
        satisfied = 0
        rank_by_mask = rank_set.ranks_by_coalition
        for coalition_size in target_sizes:
            current_constraints = generate_reversal_constraints(game, int(coalition_size))
            constraints += len(current_constraints)
            for constraint in current_constraints:
                preferred_rank = rank_by_mask.get(int(constraint.preferred_mask))
                dispreferred_rank = rank_by_mask.get(int(constraint.dispreferred_mask))
                # Strict requirement: ties are counted as unsatisfied (fixed spec).
                if (
                    preferred_rank is not None
                    and dispreferred_rank is not None
                    and int(preferred_rank) < int(dispreferred_rank)
                ):
                    satisfied += 1
        return satisfied, constraints


@dataclass(frozen=True)
class AxiomLens(PaperLens):
    """Lens backed by a weak-N coalition-ranking axiom evaluator.

    The wrapped axiom evaluates over its own constrained comparison set and does
    not depend on ``target_sizes`` (matching the historical behaviour).
    """

    lens_id: str
    label: str
    axiom: CoalitionRankingAxiom

    def counts(
        self,
        game: CoalitionGame,
        rank_set: RuleRankSet,
        target_sizes: Iterable[int],
    ) -> tuple[int, int]:
        result = self.axiom.evaluate(game, rank_set)
        return int(result.satisfied_comparisons), int(result.constrained_comparisons)


# The single authoritative lens catalog. Order == historical lens column order.
_PAPER_LENSES: list[PaperLens] = [
    ReversalLens(),
    AxiomLens("up", "Up", GiveWeakNAxiom()),
    AxiomLens("down", "Down", TakeWeakNAxiom()),
    AxiomLens("redundancy", "Redundancy", RedundancyAxiom()),
]
PAPER_LENS_CATALOG: tuple[PaperLens, ...] = tuple(_PAPER_LENSES)

_LENS_BY_ID: dict[str, PaperLens] = {lens.lens_id: lens for lens in PAPER_LENS_CATALOG}

# Derived (id, label) view consumed by headers, metadata and figure code.
PAPER_LENS_SPECS: tuple[PaperLensSpec, ...] = tuple(
    PaperLensSpec(lens.lens_id, lens.label) for lens in PAPER_LENS_CATALOG
)


def get_lens(lens_id: str) -> PaperLens:
    """Return the registered lens for ``lens_id``."""

    return _LENS_BY_ID[str(lens_id)]


__all__ = [
    "PAPER_LENS_CATALOG",
    "PAPER_LENS_SPECS",
    "AxiomLens",
    "PaperLens",
    "PaperLensSpec",
    "ReversalLens",
    "get_lens",
]
