"""Game CSV reading utilities."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


def _player_column_count(header: Sequence[str]) -> int:
    count = 0
    for name in header:
        if str(name).startswith("player"):
            count += 1
        else:
            break
    return count


def _mask_from_row(row: Sequence[str], n: int) -> int:
    mask = 0
    for i in range(n):
        try:
            v = int(row[i])
        except Exception:
            v = 0
        if v != 0:
            mask |= 1 << i
    return mask


def _format_score(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)


@dataclass(frozen=True)
class GameTable:
    """Canonical in-memory representation of a game CSV."""

    n: int
    scores_by_mask: dict[int, float]
    levels_by_mask: dict[int, int]
    masks_in_canonical_order: tuple[int, ...]

    def player_header(self) -> list[str]:
        return [f"player{i+1}" for i in range(self.n)]

    def membership_cells(self, mask: int) -> list[str]:
        return ["1" if (mask >> i) & 1 else "0" for i in range(self.n)]

    def score_cell(self, mask: int) -> str:
        return _format_score(float(self.scores_by_mask[mask]))

    def rank_cell(self, mask: int) -> str:
        return str(int(self.levels_by_mask[mask]))


def read_game_csv(path: Path) -> GameTable:
    """Read a game CSV and return a canonical GameTable.

    Expected columns: leading player1..playerN, and must include 'score' and 'rank'.
    Requires a complete 2^N set of coalitions.
    """
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Game CSV is empty.") from exc
        rows = [r for r in reader if r]

    n = _player_column_count(header)
    if n <= 0:
        raise ValueError("Game CSV must start with player columns.")
    try:
        score_idx = header.index("score")
    except ValueError as exc:
        raise ValueError("Game CSV must contain a 'score' column.") from exc
    try:
        rank_idx = header.index("rank")
    except ValueError as exc:
        raise ValueError("Game CSV must contain a 'rank' column.") from exc

    scores_by_mask: dict[int, float] = {}
    levels_by_mask: dict[int, int] = {}
    for row in rows:
        mask = _mask_from_row(row, n)
        try:
            score = float(row[score_idx])
        except Exception as exc:
            raise ValueError(f"Invalid score cell for mask={mask}: {row[score_idx]!r}") from exc
        try:
            level = int(row[rank_idx])
        except Exception as exc:
            raise ValueError(f"Invalid rank cell for mask={mask}: {row[rank_idx]!r}") from exc
        scores_by_mask[mask] = score
        levels_by_mask[mask] = level

    expected = 1 << n
    missing = [m for m in range(expected) if m not in scores_by_mask]
    if missing:
        raise ValueError(f"Expected {expected} coalitions, found {len(scores_by_mask)}")

    masks_in_order = tuple(sorted(scores_by_mask.keys(), key=lambda m: (-scores_by_mask[m], m)))
    return GameTable(
        n=n,
        scores_by_mask=scores_by_mask,
        levels_by_mask=levels_by_mask,
        masks_in_canonical_order=masks_in_order,
    )

