"""Rankings CSV read/write helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .game_csv import GameTable, _format_score


RANK_COLUMN_ALIASES: dict[str, str] = {
}


CANONICAL_RANK_COLUMN_ORDER: tuple[str, ...] = (
    "rank_shapley",
    "rank_banzhaf",
    "rank_lexcel",
    "rank_o-banzhaf",
    "rank_g-shapley",
    "rank_g-sum-shapley",
    "rank_shapley-interaction",
    "rank_banzhaf-interaction",
    "rank_rp-index",
    "rank_ud",
    "rank_du",
    "rank_red-index",
    "rank_g-lexcel",
    "rank_g-o-banzhaf",
)


CANONICAL_DERIVED_COLUMN_ORDER: tuple[str, ...] = (
    "score_shapley",
    "score_banzhaf",
    "score_g-shapley",
    "score_g-sum-shapley",
    "score_shapley-interaction",
    "score_banzhaf-interaction",
    "score_rp-index",
    "score_ud_up",
    "score_ud_down",
    "score_du_up",
    "score_du_down",
    "score_red-index",
    *CANONICAL_RANK_COLUMN_ORDER,
)


def _player_column_count(header: Sequence[str]) -> int:
    count = 0
    for name in header:
        if str(name).startswith("player"):
            count += 1
        else:
            break
    return count


def _mask_from_row_prefix(row: Sequence[str], n: int) -> int:
    mask = 0
    for i in range(n):
        try:
            v = int(row[i])
        except Exception:
            v = 0
        if v != 0:
            mask |= 1 << i
    return mask


def _is_derived_column(name: str) -> bool:
    label = str(name)
    if label in {"score", "rank"}:
        return False
    return label.startswith("rank_") or label.startswith("score_")


def ordered_derived_columns(cols: Iterable[str]) -> list[str]:
    derived = [c for c in cols if _is_derived_column(str(c))]
    seen: set[str] = set()
    ordered: list[str] = []
    for c in CANONICAL_DERIVED_COLUMN_ORDER:
        if c in derived and c not in seen:
            ordered.append(c)
            seen.add(c)
    for c in derived:
        if c not in seen:
            ordered.append(c)
            seen.add(c)
    return ordered


@dataclass(frozen=True)
class RankingsValues:
    n: int
    rank_columns: tuple[str, ...]
    values_by_mask: dict[int, dict[str, str]]


@dataclass(frozen=True)
class RankingsTable:
    """Parsed rankings CSV including base coalition levels.

    `base_level_by_mask` corresponds to the CSV column named `rank` (1 is best).
    `values_by_mask` contains only `rank_*` columns (canonicalised via aliases).
    """

    n: int
    base_level_by_mask: dict[int, int]
    rank_columns: tuple[str, ...]
    values_by_mask: dict[int, dict[str, str]]


def read_rankings_values(path: Path) -> RankingsValues:
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Rankings CSV is empty.") from exc
        rows = [r for r in reader if r]

    n = _player_column_count(header)
    if n <= 0:
        raise ValueError("Ranking CSV has no player columns.")

    raw_rank_cols = [str(c) for c in header if _is_derived_column(str(c))]
    col_index = {str(name): idx for idx, name in enumerate(header)}

    canonical_rank_cols: list[str] = []
    variants_by_canonical: dict[str, list[str]] = {}
    for col in raw_rank_cols:
        canonical = RANK_COLUMN_ALIASES.get(col, col)
        if canonical not in variants_by_canonical:
            canonical_rank_cols.append(canonical)
            variants_by_canonical[canonical] = []
        variants_by_canonical[canonical].append(col)

    values_by_mask: dict[int, dict[str, str]] = {}
    for row in rows:
        mask = _mask_from_row_prefix(row, n)
        values: dict[str, str] = {}
        for canonical, variants in variants_by_canonical.items():
            preferred = [canonical] + [v for v in variants if v != canonical] if canonical in variants else variants
            cell_value = ""
            for col in preferred:
                idx = col_index.get(col)
                if idx is None or idx >= len(row):
                    continue
                candidate = row[idx]
                if str(candidate).strip() != "":
                    cell_value = candidate
                    break
            values[canonical] = cell_value
        values_by_mask[mask] = values

    return RankingsValues(n=n, rank_columns=tuple(canonical_rank_cols), values_by_mask=values_by_mask)


def read_rankings_table(path: Path) -> RankingsTable:
    """Read a rankings CSV and return base levels + rank_* columns.

    Expected columns: leading player1..playerN, and must include 'rank'.
    """

    with path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Rankings CSV is empty.") from exc
        rows = [r for r in reader if r]

    n = _player_column_count(header)
    if n <= 0:
        raise ValueError("Ranking CSV has no player columns.")
    try:
        base_rank_idx = header.index("rank")
    except ValueError as exc:
        raise ValueError("Ranking CSV must contain a 'rank' column.") from exc

    raw_rank_cols = [str(c) for c in header if _is_derived_column(str(c))]
    col_index = {str(name): idx for idx, name in enumerate(header)}

    canonical_rank_cols: list[str] = []
    variants_by_canonical: dict[str, list[str]] = {}
    for col in raw_rank_cols:
        canonical = RANK_COLUMN_ALIASES.get(col, col)
        if canonical not in variants_by_canonical:
            canonical_rank_cols.append(canonical)
            variants_by_canonical[canonical] = []
        variants_by_canonical[canonical].append(col)

    base_level_by_mask: dict[int, int] = {}
    values_by_mask: dict[int, dict[str, str]] = {}
    for row in rows:
        mask = _mask_from_row_prefix(row, n)
        try:
            base_level_by_mask[mask] = int(row[base_rank_idx])
        except Exception as exc:
            raise ValueError(f"Invalid rank cell for mask={mask}: {row[base_rank_idx]!r}") from exc

        values: dict[str, str] = {}
        for canonical, variants in variants_by_canonical.items():
            preferred = [canonical] + [v for v in variants if v != canonical] if canonical in variants else variants
            cell_value = ""
            for col in preferred:
                idx = col_index.get(col)
                if idx is None or idx >= len(row):
                    continue
                candidate = row[idx]
                if str(candidate).strip() != "":
                    cell_value = candidate
                    break
            values[canonical] = cell_value
        values_by_mask[mask] = values

    return RankingsTable(
        n=n,
        base_level_by_mask=base_level_by_mask,
        rank_columns=tuple(canonical_rank_cols),
        values_by_mask=values_by_mask,
    )


def write_rankings_with_rank_column(
    *,
    rankings_path: Path,
    game: GameTable,
    new_col_name: str,
    new_values_by_mask: dict[int, str],
) -> tuple[bool, tuple[str, ...]]:
    """Write or update a rankings CSV.

    Returns (already_exists, written_rank_columns).
    """
    return write_rankings_with_columns(
        rankings_path=rankings_path,
        game=game,
        new_columns={new_col_name: new_values_by_mask},
        primary_column=new_col_name,
    )


def write_rankings_with_columns(
    *,
    rankings_path: Path,
    game: GameTable,
    new_columns: dict[str, dict[int, str]],
    primary_column: str,
) -> tuple[bool, tuple[str, ...]]:
    """Write or update a rankings CSV with one or more derived columns.

    Derived columns are those that start with `rank_` or `score_` (excluding base `score`/`rank`).

    Returns (primary_already_exists, written_columns).
    """
    already_exists = False
    existing: RankingsValues | None = None
    if rankings_path.exists():
        existing = read_rankings_values(rankings_path)
        if existing.n != game.n:
            raise ValueError("Ranking CSV has incompatible number of player columns.")
        already_exists = primary_column in existing.rank_columns

    if existing is None:
        cols = tuple(ordered_derived_columns(new_columns.keys()))
        out_header = game.player_header() + ["score", "rank"] + list(cols)
        out_rows: list[list[str]] = []
        for mask in game.masks_in_canonical_order:
            cells = [new_columns.get(col, {}).get(mask, "") for col in cols]
            out_rows.append(game.membership_cells(mask) + [_format_score(game.scores_by_mask[mask]), str(game.levels_by_mask[mask])] + cells)
        with rankings_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(out_header)
            writer.writerows(out_rows)
        return (False, cols)

    # Update existing rankings: reorder, and append new col if missing.
    rank_cols_list = list(existing.rank_columns)
    for col in new_columns.keys():
        if col not in rank_cols_list:
            rank_cols_list.append(col)
    rank_cols_ordered = tuple(ordered_derived_columns(rank_cols_list))

    out_header = game.player_header() + ["score", "rank"] + list(rank_cols_ordered)
    out_rows = []
    for mask in game.masks_in_canonical_order:
        base = game.membership_cells(mask) + [
            _format_score(game.scores_by_mask[mask]),
            str(game.levels_by_mask[mask]),
        ]
        cells: list[str] = []
        for col in rank_cols_ordered:
            if col in new_columns and col not in existing.rank_columns:
                cells.append(new_columns[col].get(mask, ""))
            else:
                cells.append(existing.values_by_mask.get(mask, {}).get(col, ""))
        out_rows.append(base + cells)

    with rankings_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(out_header)
        writer.writerows(out_rows)

    return (already_exists, rank_cols_ordered)
