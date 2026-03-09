"""Persistence adapters, including the compatibility-format CSV boundary."""

from .csv_game_repository import (
    read_compatible_game_csv,
    read_legacy_game_csv,
    write_compatible_game_csv,
    write_legacy_game_csv,
)
from .csv_ranking_repository import (
    CompatibleRankingRuleSpec,
    LegacyRankingRuleSpec,
    get_compatible_ranking_rule_spec,
    get_legacy_ranking_rule_spec,
    ordered_compatible_derived_columns,
    ordered_legacy_derived_columns,
    serialize_compatible_ranking_columns,
    serialize_legacy_ranking_columns,
    write_compatible_rankings_csv,
    write_legacy_rankings_csv,
)

__all__ = [
    "read_compatible_game_csv",
    "write_compatible_game_csv",
    "read_legacy_game_csv",
    "write_legacy_game_csv",
    "CompatibleRankingRuleSpec",
    "LegacyRankingRuleSpec",
    "get_compatible_ranking_rule_spec",
    "get_legacy_ranking_rule_spec",
    "ordered_compatible_derived_columns",
    "ordered_legacy_derived_columns",
    "serialize_compatible_ranking_columns",
    "serialize_legacy_ranking_columns",
    "write_compatible_rankings_csv",
    "write_legacy_rankings_csv",
]
