"""Application use case for importing feature-mask tables into game CSVs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.config import get_realgen_import_rank_bins
from ...infrastructure.datasets import (
    resolve_feature_mask_dataset_dir,
    resolve_real_dataset_out_base,
    write_feature_labels_yaml,
)
from ...infrastructure.persistence import write_compatible_game_csv


@dataclass(frozen=True)
class ImportedFeatureMaskGame:
    """In-memory result of importing one feature-mask table."""

    game: CoalitionGame
    ranks_by_mask: dict[int, int]
    feature_columns: tuple[str, ...]
    feature_descriptions: dict[str, str]
    feature_labels: dict[str, str]


@dataclass(frozen=True)
class ImportedDatasetArtifacts:
    """Summary of one dataset import workflow."""

    dataset_id: str
    dataset_dir: Path
    dataset_out_base: Path
    schema_path: Path
    raw_csv_path: Path
    game_csv_path: Path
    features_yaml_path: Path
    copied_schema_path: Path
    imported_game: ImportedFeatureMaskGame


def _load_schema_yaml(path: Path) -> dict[str, Any]:
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _dense_rank_by_score(scores_by_mask: Mapping[int, float]) -> dict[int, int]:
    order = sorted(scores_by_mask.keys(), key=lambda mask: (-float(scores_by_mask[mask]), int(mask)))
    ranks: dict[int, int] = {}
    current_rank = 0
    last_score: float | None = None
    for mask in order:
        score = float(scores_by_mask[mask])
        if last_score is None or score != last_score:
            current_rank += 1
            last_score = score
        ranks[int(mask)] = current_rank
    return ranks


def _binned_rank_by_score(
    scores_by_mask: Mapping[int, float],
    *,
    bins: int,
    exclude_mask_from_range: int | None = 0,
) -> dict[int, int]:
    if int(bins) <= 0:
        raise ValueError("bins must be >= 1")
    if not scores_by_mask:
        return {}

    if exclude_mask_from_range is not None:
        values = [float(value) for mask, value in scores_by_mask.items() if int(mask) != int(exclude_mask_from_range)]
    else:
        values = [float(value) for value in scores_by_mask.values()]
    if not values:
        values = [float(value) for value in scores_by_mask.values()]

    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return {int(mask): 1 for mask in scores_by_mask}

    width = (maximum - minimum) / float(int(bins))
    ranks_by_mask: dict[int, int] = {}
    for mask, score in scores_by_mask.items():
        value = float(score)
        if value >= maximum:
            rank = 1
        elif value <= minimum:
            rank = int(bins)
        else:
            rank = int((maximum - value) / width) + 1
            rank = min(max(rank, 1), int(bins))
        ranks_by_mask[int(mask)] = int(rank)
    return ranks_by_mask


def _transform_score(value: float, transform: str) -> float:
    normalized = str(transform or "identity").strip().lower()
    if normalized in {"identity", "none", ""}:
        return float(value)
    if normalized == "negate":
        return -float(value)
    raise ValueError(
        f"Unsupported score_transform: {transform!r} (supported: identity, negate)"
    )


def detect_feature_columns_from_csv(
    *,
    raw_csv: Path,
    score_column: str,
    filters: Mapping[str, str],
    feature_exclude: set[str],
) -> list[str]:
    """Detect 0/1 feature columns from a feature-mask CSV."""

    with raw_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV is empty.") from exc
        rows = [row for row in reader if row]

    column_index = {str(name): index for index, name in enumerate(header)}
    if score_column not in column_index:
        raise ValueError(f"score_column not found: {score_column}")

    def row_ok(row: list[str]) -> bool:
        for key, expected in filters.items():
            column = column_index.get(key)
            if column is None:
                return False
            actual = row[column] if column < len(row) else ""
            if str(actual) != str(expected):
                return False
        return True

    excluded = set(feature_exclude)
    excluded |= {"score", "rank", "abs_value", "metric", "n_train", "n_test", "seed", "order"}
    excluded.add(str(score_column))
    candidates = [str(name) for name in header if str(name) not in excluded]
    if not candidates:
        raise ValueError("No candidate feature columns after exclusions.")

    filtered_rows = [row for row in rows if (not filters or row_ok(row))]
    if not filtered_rows:
        raise ValueError("No rows left after applying filters.")

    feature_columns: list[str] = []
    for column_name in candidates:
        index = column_index.get(column_name)
        if index is None:
            continue
        seen: set[int] = set()
        is_binary = True
        for row in filtered_rows:
            raw_value = row[index] if index < len(row) else ""
            stripped = str(raw_value).strip()
            if stripped == "":
                continue
            try:
                value = int(stripped)
            except Exception:
                is_binary = False
                break
            if value not in (0, 1):
                is_binary = False
                break
            seen.add(value)
        if is_binary and seen:
            feature_columns.append(column_name)

    if not feature_columns:
        raise ValueError("No binary (0/1) feature columns detected.")
    return feature_columns


def import_feature_mask_csv(
    *,
    raw_csv: Path,
    score_column: str,
    score_transform: str,
    rank_column: str | None,
    feature_columns: list[str],
    filters: Mapping[str, str],
    empty_score: float | None,
    empty_rank: int | None,
    feature_descriptions: Mapping[str, str],
    feature_labels: Mapping[str, str],
    allow_incomplete: bool = False,
    rank_method: str = "binned",
    import_rank_bins: int = 5,
) -> ImportedFeatureMaskGame:
    """Import one raw feature-mask CSV into an in-memory game plus metadata."""

    with raw_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV is empty.") from exc
        rows = [row for row in reader if row]

    column_index = {str(name): index for index, name in enumerate(header)}
    if score_column not in column_index:
        raise ValueError(f"score_column not found: {score_column}")
    if rank_column is not None and str(rank_column) not in column_index:
        raise ValueError(f"rank_column not found: {rank_column}")

    missing = [column for column in feature_columns if column not in column_index]
    if missing:
        raise ValueError(f"feature_columns not found: {missing}")

    player_count = len(feature_columns)
    if player_count <= 0:
        raise ValueError("feature_columns is empty.")

    def row_ok(row: list[str]) -> bool:
        for key, expected in filters.items():
            column = column_index.get(key)
            if column is None:
                return False
            actual = row[column] if column < len(row) else ""
            if str(actual) != str(expected):
                return False
        return True

    scores_by_mask: dict[int, float] = {}
    explicit_ranks_by_mask: dict[int, int] | None = {} if rank_column is not None else None

    for row in rows:
        if filters and not row_ok(row):
            continue

        mask = 0
        for player_index, column_name in enumerate(feature_columns):
            raw_value = row[column_index[column_name]] if column_index[column_name] < len(row) else "0"
            try:
                bit = int(raw_value)
            except Exception as exc:
                raise ValueError(
                    f"Invalid 0/1 cell in feature column {column_name!r}: {raw_value!r}"
                ) from exc
            if bit not in (0, 1):
                raise ValueError(
                    f"Invalid 0/1 cell in feature column {column_name!r}: {raw_value!r}"
                )
            if bit:
                mask |= 1 << player_index

        raw_score = row[column_index[score_column]] if column_index[score_column] < len(row) else ""
        try:
            score = _transform_score(float(raw_score), score_transform)
        except Exception as exc:
            raise ValueError(f"Invalid score cell: {raw_score!r}") from exc

        if rank_column is not None:
            raw_rank = row[column_index[str(rank_column)]] if column_index[str(rank_column)] < len(row) else ""
            stripped_rank = str(raw_rank).strip()
            if stripped_rank == "":
                raise ValueError(f"Missing rank cell for mask={mask}: column={rank_column}")
            try:
                rank = int(float(stripped_rank))
            except Exception as exc:
                raise ValueError(f"Invalid rank cell: {raw_rank!r}") from exc
            if rank <= 0:
                raise ValueError(f"Invalid rank (must be >=1): {rank} (mask={mask})")

        if mask in scores_by_mask and scores_by_mask[mask] != score:
            raise ValueError(
                f"Duplicate mask with conflicting score: mask={mask} {scores_by_mask[mask]} != {score}"
            )
        scores_by_mask[int(mask)] = float(score)

        if explicit_ranks_by_mask is not None:
            if mask in explicit_ranks_by_mask and explicit_ranks_by_mask[mask] != rank:
                raise ValueError(
                    f"Duplicate mask with conflicting rank: mask={mask} "
                    f"{explicit_ranks_by_mask[mask]} != {rank}"
                )
            explicit_ranks_by_mask[int(mask)] = int(rank)

    expected = 1 << player_count
    if 0 not in scores_by_mask and empty_score is not None:
        scores_by_mask[0] = _transform_score(float(empty_score), score_transform)
        if explicit_ranks_by_mask is not None:
            if empty_rank is None:
                raise ValueError(
                    "rank_column is set but empty coalition row is missing; "
                    "provide empty_rank or include the empty row in the CSV."
                )
            explicit_ranks_by_mask[0] = int(empty_rank)

    if not allow_incomplete:
        if 0 not in scores_by_mask:
            raise ValueError(
                "Missing empty coalition row (all-zero mask). Provide it in the CSV or set empty_score. "
                f"(observed rows={len(scores_by_mask)}, expected={expected})"
            )
        missing_masks = [mask for mask in range(expected) if mask not in scores_by_mask]
        if missing_masks:
            raise ValueError(
                f"Missing coalitions: {len(missing_masks)} "
                f"(expected={expected}, found={len(scores_by_mask)})"
            )
        if explicit_ranks_by_mask is not None:
            missing_ranks = [mask for mask in range(expected) if mask not in explicit_ranks_by_mask]
            if missing_ranks:
                raise ValueError(
                    f"Missing ranks for coalitions: {len(missing_ranks)} "
                    f"(expected={expected}, found={len(explicit_ranks_by_mask)})"
                )

    if explicit_ranks_by_mask is not None:
        ranks_by_mask = explicit_ranks_by_mask
    else:
        normalized_rank_method = str(rank_method or "binned").strip().lower()
        if normalized_rank_method == "dense":
            ranks_by_mask = _dense_rank_by_score(scores_by_mask)
        elif normalized_rank_method == "binned":
            ranks_by_mask = _binned_rank_by_score(scores_by_mask, bins=int(import_rank_bins))
        else:
            raise ValueError(
                f"Unsupported rank_method: {rank_method!r} (supported: dense, binned)"
            )

    game = CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)
    return ImportedFeatureMaskGame(
        game=game,
        ranks_by_mask=ranks_by_mask,
        feature_columns=tuple(str(column) for column in feature_columns),
        feature_descriptions={str(key): str(value) for key, value in dict(feature_descriptions).items()},
        feature_labels={str(key): str(value) for key, value in dict(feature_labels).items()},
    )


def import_feature_mask_dataset(
    dataset_id: str,
    *,
    inputs_root: Path | None = None,
    out_root: Path | None = None,
    config_path: Path | None = None,
) -> ImportedDatasetArtifacts:
    """Import one dataset directory into dataset-scoped game artifacts."""

    dataset_dir = resolve_feature_mask_dataset_dir(dataset_id, inputs_root=inputs_root)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"dataset dir not found: {dataset_dir}")

    schema_path = dataset_dir / "schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"schema.yaml not found: {schema_path}")

    schema = _load_schema_yaml(schema_path)
    raw_name = str(schema.get("raw_csv", "raw.csv"))
    raw_csv_path = dataset_dir / raw_name
    if not raw_csv_path.exists():
        raise FileNotFoundError(f"raw CSV not found: {raw_csv_path}")

    score_column = str(schema.get("score_column", "value"))
    score_transform = str(schema.get("score_transform", "identity"))
    rank_column_raw = schema.get("rank_column")
    rank_column = str(rank_column_raw) if rank_column_raw is not None else None
    rank_method = str(schema.get("rank_method", "binned"))

    feature_columns_raw = schema.get("feature_columns")
    feature_exclude_raw = schema.get("feature_exclude", [])
    feature_exclude = {str(item) for item in feature_exclude_raw} if isinstance(feature_exclude_raw, list) else set()
    if rank_column is not None:
        feature_exclude.add(rank_column)

    filters_raw = schema.get("filters", {})
    filters = {str(key): str(value) for key, value in filters_raw.items()} if isinstance(filters_raw, dict) else {}

    empty_score = float(schema["empty_score"]) if "empty_score" in schema else None
    empty_rank = int(schema["empty_rank"]) if "empty_rank" in schema else None

    feature_descriptions_raw = schema.get("feature_descriptions", {})
    feature_descriptions = (
        {str(key): str(value) for key, value in feature_descriptions_raw.items()}
        if isinstance(feature_descriptions_raw, dict)
        else {}
    )
    feature_labels_raw = schema.get("feature_labels", {})
    feature_labels = (
        {str(key): str(value) for key, value in feature_labels_raw.items()}
        if isinstance(feature_labels_raw, dict)
        else {}
    )
    allow_incomplete = bool(schema.get("allow_incomplete", False))

    if isinstance(feature_columns_raw, list) and feature_columns_raw:
        feature_columns = [str(column) for column in feature_columns_raw]
    else:
        feature_columns = detect_feature_columns_from_csv(
            raw_csv=raw_csv_path,
            score_column=score_column,
            filters=filters,
            feature_exclude=feature_exclude,
        )

    imported_game = import_feature_mask_csv(
        raw_csv=raw_csv_path,
        score_column=score_column,
        score_transform=score_transform,
        rank_column=rank_column,
        feature_columns=feature_columns,
        filters=filters,
        empty_score=empty_score,
        empty_rank=empty_rank,
        feature_descriptions=feature_descriptions,
        feature_labels=feature_labels,
        allow_incomplete=allow_incomplete,
        rank_method=rank_method,
        import_rank_bins=get_realgen_import_rank_bins(config_path),
    )

    dataset_out_base = resolve_real_dataset_out_base(dataset_id, out_root=out_root)
    game_csv_path = dataset_out_base / "games" / f"game_{dataset_id}.csv"
    features_yaml_path = game_csv_path.with_suffix(".features.yaml")
    copied_schema_path = dataset_out_base / "schema.yaml"

    write_compatible_game_csv(
        game_csv_path,
        imported_game.game,
        ranks_by_mask=imported_game.ranks_by_mask,
    )
    write_feature_labels_yaml(
        features_yaml_path,
        feature_columns=list(imported_game.feature_columns),
        feature_descriptions=imported_game.feature_descriptions,
        feature_labels=imported_game.feature_labels,
    )
    copied_schema_path.parent.mkdir(parents=True, exist_ok=True)
    copied_schema_path.write_text(schema_path.read_text(encoding="utf-8"), encoding="utf-8")

    return ImportedDatasetArtifacts(
        dataset_id=str(dataset_id),
        dataset_dir=dataset_dir,
        dataset_out_base=dataset_out_base,
        schema_path=schema_path,
        raw_csv_path=raw_csv_path,
        game_csv_path=game_csv_path,
        features_yaml_path=features_yaml_path,
        copied_schema_path=copied_schema_path,
        imported_game=imported_game,
    )


__all__ = [
    "ImportedDatasetArtifacts",
    "ImportedFeatureMaskGame",
    "detect_feature_columns_from_csv",
    "import_feature_mask_csv",
    "import_feature_mask_dataset",
]
