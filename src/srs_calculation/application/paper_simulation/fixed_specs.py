"""Immutable specifications that must NOT be made configurable.

These encode decisions on which the paper's correctness depends. They are
declared as constants here -- deliberately NOT as ``PaperSimulationConfig``
fields or CLI options -- so they cannot be flipped by configuration. The
enforcing code references this module so the intent is discoverable; changing
any of these behaviours requires a deliberate code change reviewed against the
paper, never a config flag.

See also ``CLAUDE.md`` for the project-level statement of these fixed specs.
"""

from __future__ import annotations

# Reverse Axiom firing: the coalition ordering S > T must be STRICT. A group-rank
# tie does not fire a constraint. Enforced in domain/lenses/reversal.py.
REVERSAL_STRICT_GROUP_ORDERING: bool = True

# Satisfaction of a required strict output S >^R T: only a strict rank
# improvement counts as satisfied; a tied output counts as UNSATISFIED.
# Enforced in metrics.evaluate_reversal_consistency and
# lens_catalog.ReversalLens.counts.
OUTPUT_TIES_COUNT_AS_UNSATISFIED: bool = True

# Rank value r(C) counts strictly-better coalitions only (ties are not counted);
# smaller is more preferred, r = 0 at the top. Enforced in RankdiffRule.
RANK_VALUE_TIES_NOT_COUNTED: bool = True

# The paper Rankdiff definition (documentation constant). Enforced in
# RankdiffRule.evaluate.
RANKDIFF_DEFINITION: str = "Rankdiff(S) = (1/|S|) * sum_{i in S} r({i}) - r(S)"

# The main-text adequacy / consistency figure uses the MACRO (per-game
# equal-weight) average. The micro (case-weighted) average is reported alongside,
# but the headline value is macro.
MAIN_TEXT_ADEQUACY_AVERAGE: str = "macro"

__all__ = [
    "MAIN_TEXT_ADEQUACY_AVERAGE",
    "OUTPUT_TIES_COUNT_AS_UNSATISFIED",
    "RANKDIFF_DEFINITION",
    "RANK_VALUE_TIES_NOT_COUNTED",
    "REVERSAL_STRICT_GROUP_ORDERING",
]
