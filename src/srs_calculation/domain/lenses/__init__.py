"""Lens definitions for paper-facing coalition ranking analysis."""

from .reversal import (
    ReversalConstraint,
    generate_reversal_constraints,
    generate_reversal_constraints_by_size,
)

__all__ = [
    "ReversalConstraint",
    "generate_reversal_constraints",
    "generate_reversal_constraints_by_size",
]
