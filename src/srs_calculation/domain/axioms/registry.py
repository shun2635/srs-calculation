"""Axiom registry for migrated coalition-ranking axioms."""

from __future__ import annotations

from dataclasses import dataclass, field

from .axiom import CoalitionRankingAxiom
from .evaluators import (
    Give2pAxiom,
    GiveWeakNAxiom,
    RedundancyAxiom,
    Reversal2pAxiom,
    ReversalWeakNAxiom,
    Take2pAxiom,
    TakeWeakNAxiom,
)


@dataclass
class AxiomRegistry:
    """Simple in-memory registry for axiom evaluators."""

    _axioms: dict[str, CoalitionRankingAxiom] = field(default_factory=dict)

    def register(self, axiom: CoalitionRankingAxiom) -> None:
        self._axioms[str(axiom.axiom_id)] = axiom

    def get(self, axiom_id: str) -> CoalitionRankingAxiom:
        try:
            return self._axioms[str(axiom_id)]
        except KeyError as exc:
            known = ", ".join(sorted(self._axioms))
            raise KeyError(f"unknown axiom_id '{axiom_id}'; known axioms: {known}") from exc

    def list_axiom_ids(self) -> list[str]:
        return sorted(self._axioms)


def build_default_axiom_registry() -> AxiomRegistry:
    """Build the migrated default axiom registry."""

    registry = AxiomRegistry()
    for axiom in (
        Reversal2pAxiom(),
        ReversalWeakNAxiom(),
        Give2pAxiom(),
        Take2pAxiom(),
        GiveWeakNAxiom(),
        TakeWeakNAxiom(),
        RedundancyAxiom(),
    ):
        registry.register(axiom)
    return registry
