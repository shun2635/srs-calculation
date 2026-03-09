"""Application services for ranking workflows."""

from __future__ import annotations

from typing import Any

__all__ = [
    "AppliedRankingCsvResult",
    "AppliedRealDatasetRankingResult",
    "apply_ranking_rules",
    "apply_ranking_rules_in_directory",
    "apply_ranking_rules_to_game_csv",
    "apply_ranking_rules_to_real_dataset",
    "resolve_real_dataset_out_base",
]


def __getattr__(name: str) -> Any:
    """Load heavier adapters only when they are actually requested."""

    if name == "apply_ranking_rules":
        from .apply_ranking_rules import apply_ranking_rules

        return apply_ranking_rules

    if name in {"AppliedRankingCsvResult", "apply_ranking_rules_in_directory", "apply_ranking_rules_to_game_csv"}:
        from .apply_ranking_rules_to_game_csv import (
            AppliedRankingCsvResult,
            apply_ranking_rules_in_directory,
            apply_ranking_rules_to_game_csv,
        )

        mapping = {
            "AppliedRankingCsvResult": AppliedRankingCsvResult,
            "apply_ranking_rules_in_directory": apply_ranking_rules_in_directory,
            "apply_ranking_rules_to_game_csv": apply_ranking_rules_to_game_csv,
        }
        return mapping[name]

    if name in {
        "AppliedRealDatasetRankingResult",
        "apply_ranking_rules_to_real_dataset",
        "resolve_real_dataset_out_base",
    }:
        from .apply_ranking_rules_to_real_dataset import (
            AppliedRealDatasetRankingResult,
            apply_ranking_rules_to_real_dataset,
            resolve_real_dataset_out_base,
        )

        mapping = {
            "AppliedRealDatasetRankingResult": AppliedRealDatasetRankingResult,
            "apply_ranking_rules_to_real_dataset": apply_ranking_rules_to_real_dataset,
            "resolve_real_dataset_out_base": resolve_real_dataset_out_base,
        }
        return mapping[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
