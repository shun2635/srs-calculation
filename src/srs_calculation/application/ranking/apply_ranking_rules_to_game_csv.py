"""Application use case for applying ranking rules to compatibility-format game CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ...domain.ranking.registry import RankingRuleRegistry
from ...domain.ranking.result import RankingResult
from ...infrastructure.persistence.csv_game_repository import read_compatible_game_csv
from ...infrastructure.persistence.csv_ranking_repository import write_compatible_rankings_csv
from .apply_ranking_rules import apply_ranking_rules


@dataclass(frozen=True)
class AppliedRankingCsvResult:
    """Summary of one apply-rules workflow from game CSV to rankings CSV."""

    game_csv_path: Path
    rankings_csv_path: Path
    written_columns: tuple[str, ...]
    results_by_rule_id: dict[str, RankingResult]


def apply_ranking_rules_to_game_csv(
    game_csv_path: Path,
    rankings_csv_path: Path,
    rule_ids: list[str],
    *,
    registry: RankingRuleRegistry | None = None,
    rank_style: str = "competition",
    require_complete: bool = True,
) -> AppliedRankingCsvResult:
    """Read one game CSV, apply ranking rules, and write a rankings CSV."""

    game = read_compatible_game_csv(
        game_csv_path,
        require_complete=require_complete,
    )
    results_by_rule_id = apply_ranking_rules(
        game,
        rule_ids,
        registry=registry,
    )
    written_columns = write_compatible_rankings_csv(
        rankings_csv_path,
        game,
        results_by_rule_id.values(),
        rank_style=rank_style,
    )
    return AppliedRankingCsvResult(
        game_csv_path=game_csv_path,
        rankings_csv_path=rankings_csv_path,
        written_columns=written_columns,
        results_by_rule_id=results_by_rule_id,
    )


def apply_ranking_rules_in_directory(
    games_dir: Path,
    rankings_dir: Path,
    rule_ids: list[str],
    *,
    registry: RankingRuleRegistry | None = None,
    rank_style: str = "competition",
    require_complete: bool = True,
    glob_pattern: str = "game_*.csv",
) -> list[AppliedRankingCsvResult]:
    """Apply ranking rules to each matching game CSV under a directory."""

    if not games_dir.exists():
        raise FileNotFoundError(f"games directory not found: {games_dir}")
    if not games_dir.is_dir():
        raise NotADirectoryError(f"games path is not a directory: {games_dir}")

    rankings_dir.mkdir(parents=True, exist_ok=True)
    results: list[AppliedRankingCsvResult] = []
    for game_csv_path in sorted(games_dir.glob(glob_pattern)):
        if not game_csv_path.is_file():
            continue
        result = apply_ranking_rules_to_game_csv(
            game_csv_path,
            rankings_dir / game_csv_path.name,
            rule_ids,
            registry=registry,
            rank_style=rank_style,
            require_complete=require_complete,
        )
        results.append(result)
    return results


__all__ = [
    "AppliedRankingCsvResult",
    "apply_ranking_rules_to_game_csv",
    "apply_ranking_rules_in_directory",
]
