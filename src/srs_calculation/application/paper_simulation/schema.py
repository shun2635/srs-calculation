"""Single source of truth for paper-simulation CSV column schemas.

The orchestrator writes several CSVs whose columns must stay in lock-step with
the corresponding dataclass fields. Previously each header list was written
inline at the call site; collecting them here keeps the column names and order
in exactly one place. Structure-only: the column names and order are unchanged.

The two heatmap matrix CSVs (lens-consistency matrix, rank-correlation matrix)
have a dynamic ``rule`` column plus one column per rule/lens label and are built
from the catalogs at write time, so they are not represented as fixed schemas
here.
"""

from __future__ import annotations

LENS_CONSISTENCY_COLUMNS: tuple[str, ...] = (
    "game_id",
    "n",
    "k",
    "num_constraints",
    "num_satisfied",
    "consistency_rate",
    "is_empty_constraints",
)

LENS_CONSISTENCY_SUMMARY_COLUMNS: tuple[str, ...] = (
    "n",
    "k",
    "num_games",
    "num_valid_games",
    "num_empty_constraint_games",
    "num_constraints",
    "num_satisfied",
    "mean_consistency",
    "std_consistency",
    "min_consistency",
    "max_consistency",
    "micro_consistency",
)

RANK_CORRELATION_COLUMNS: tuple[str, ...] = (
    "game_id",
    "n",
    "k",
    "correlation_method",
    "rank_tie_method",
    "correlation",
    "is_na",
    "reason_if_na",
)

RANK_CORRELATION_SUMMARY_COLUMNS: tuple[str, ...] = (
    "n",
    "k",
    "num_games",
    "num_valid_games",
    "num_na_games",
    "mean_correlation",
    "std_correlation",
    "min_correlation",
    "max_correlation",
)

LENS_CONSISTENCY_LONG_COLUMNS: tuple[str, ...] = (
    "rule",
    "lens",
    "mean_consistency",
    "micro_consistency",
    "num_valid",
    "num_empty_or_na",
)

RANK_CORRELATION_LONG_COLUMNS: tuple[str, ...] = (
    "rule_a",
    "rule_b",
    "mean_correlation",
    "num_valid",
    "num_na",
)

SIMULATION_SUMMARY_COLUMNS: tuple[str, ...] = (
    "metric",
    "n",
    "k",
    "num_games",
    "num_valid",
    "num_excluded",
    "mean",
    "std",
    "min",
    "max",
    "micro",
)

__all__ = [
    "LENS_CONSISTENCY_COLUMNS",
    "LENS_CONSISTENCY_LONG_COLUMNS",
    "LENS_CONSISTENCY_SUMMARY_COLUMNS",
    "RANK_CORRELATION_COLUMNS",
    "RANK_CORRELATION_LONG_COLUMNS",
    "RANK_CORRELATION_SUMMARY_COLUMNS",
    "SIMULATION_SUMMARY_COLUMNS",
]
