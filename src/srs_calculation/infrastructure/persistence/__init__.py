"""Persistence adapters."""

from .csv_game_repository import read_legacy_game_csv, write_legacy_game_csv
from .csv_ranking_repository import (
    LegacyRankingRuleSpec,
    get_legacy_ranking_rule_spec,
    ordered_legacy_derived_columns,
    serialize_legacy_ranking_columns,
    write_legacy_rankings_csv,
)

__all__ = [
    "read_legacy_game_csv",
    "write_legacy_game_csv",
    "LegacyRankingRuleSpec",
    "get_legacy_ranking_rule_spec",
    "ordered_legacy_derived_columns",
    "serialize_legacy_ranking_columns",
    "write_legacy_rankings_csv",
]
