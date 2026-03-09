"""Application use case for applying ranking rules to one real-data dataset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ...domain.ranking.registry import build_default_ranking_rule_registry
from ...infrastructure.datasets import resolve_real_dataset_out_base
from .apply_ranking_rules_to_game_csv import (
    AppliedRankingCsvResult,
    apply_ranking_rules_in_directory,
)


@dataclass(frozen=True)
class AppliedRealDatasetRankingResult:
    """Summary of applying ranking rules to one real-data dataset."""

    dataset_id: str
    dataset_out_base: Path
    games_dir: Path
    rankings_dir: Path
    rule_ids: tuple[str, ...]
    csv_results: tuple[AppliedRankingCsvResult, ...]

def _load_rule_ids_from_schema(schema_path: Path) -> list[str]:
    raw = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return []

    rules_raw = raw.get("rules")
    if isinstance(rules_raw, (list, tuple)):
        return [str(rule_id) for rule_id in rules_raw]
    if rules_raw is None:
        return []
    return [part.strip() for part in str(rules_raw).split(",") if part.strip()]


def apply_ranking_rules_to_real_dataset(
    dataset_id: str,
    *,
    out_root: Path | None = None,
    games_dir: Path | None = None,
    rankings_dir: Path | None = None,
    rule_ids: list[str] | None = None,
    rank_style: str = "competition",
    require_complete: bool = True,
    schema_path: Path | None = None,
) -> AppliedRealDatasetRankingResult:
    """Apply migrated ranking rules to the dataset-scoped real-data game CSV directory."""

    dataset_out_base = resolve_real_dataset_out_base(dataset_id, out_root=out_root)
    resolved_games_dir = games_dir if games_dir is not None else dataset_out_base / "games"
    resolved_rankings_dir = rankings_dir if rankings_dir is not None else dataset_out_base / "rankings"
    resolved_schema_path = schema_path if schema_path is not None else dataset_out_base / "schema.yaml"

    selected_rule_ids = list(rule_ids or [])
    if not selected_rule_ids and resolved_schema_path.exists():
        selected_rule_ids = _load_rule_ids_from_schema(resolved_schema_path)
    if not selected_rule_ids:
        selected_rule_ids = build_default_ranking_rule_registry().list_rule_ids()

    csv_results = tuple(
        apply_ranking_rules_in_directory(
            resolved_games_dir,
            resolved_rankings_dir,
            selected_rule_ids,
            rank_style=rank_style,
            require_complete=require_complete,
        )
    )
    return AppliedRealDatasetRankingResult(
        dataset_id=str(dataset_id),
        dataset_out_base=dataset_out_base,
        games_dir=resolved_games_dir,
        rankings_dir=resolved_rankings_dir,
        rule_ids=tuple(selected_rule_ids),
        csv_results=csv_results,
    )


__all__ = [
    "AppliedRealDatasetRankingResult",
    "apply_ranking_rules_to_real_dataset",
    "resolve_real_dataset_out_base",
]
