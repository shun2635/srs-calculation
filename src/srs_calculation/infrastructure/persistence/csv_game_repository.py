"""CSV persistence adapter for coalition games."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from ...domain.games.coalition_game import CoalitionGame


def _player_column_count(header: Sequence[str]) -> int:
    count = 0
    for name in header:
        if str(name).startswith("player"):
            count += 1
        else:
            break
    return count


def _mask_from_row_prefix(row: Sequence[str], player_count: int) -> int:
    mask = 0
    for index in range(player_count):
        try:
            value = int(row[index])
        except Exception:
            value = 0
        if value != 0:
            mask |= 1 << index
    return mask


def _ordered_masks_for_output(game: CoalitionGame) -> list[int]:
    return sorted(game.coalition_masks(), key=lambda mask: (-game.coalition_value(mask), int(mask)))


def _dense_base_ranks_by_mask(game: CoalitionGame) -> dict[int, int]:
    ranks: dict[int, int] = {}
    current_rank = 0
    last_score: float | None = None
    for mask in _ordered_masks_for_output(game):
        score = game.coalition_value(mask)
        if last_score is None or score != last_score:
            current_rank += 1
            last_score = score
        ranks[int(mask)] = current_rank
    return ranks


def _format_score(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(float(value))


def read_legacy_game_csv(
    path: Path,
    *,
    require_complete: bool = True,
) -> CoalitionGame:
    """Read a legacy-compatible game CSV into a CoalitionGame."""

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("game CSV is empty") from exc
        rows = [row for row in reader if row]

    player_count = _player_column_count(header)
    if player_count <= 0:
        raise ValueError("game CSV must start with player columns")
    try:
        score_index = header.index("score")
    except ValueError as exc:
        raise ValueError("game CSV must contain a 'score' column") from exc
    try:
        header.index("rank")
    except ValueError as exc:
        raise ValueError("game CSV must contain a 'rank' column") from exc

    scores_by_mask: dict[int, float] = {}
    for row in rows:
        mask = _mask_from_row_prefix(row, player_count)
        try:
            score = float(row[score_index])
        except Exception as exc:
            raise ValueError(f"invalid score cell for mask={mask}: {row[score_index]!r}") from exc
        scores_by_mask[int(mask)] = float(score)

    game = CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)
    if require_complete:
        game.require_complete()
    return game


def write_legacy_game_csv(
    path: Path,
    game: CoalitionGame,
    *,
    ranks_by_mask: dict[int, int] | None = None,
) -> None:
    """Write a CoalitionGame as a legacy-compatible game CSV."""

    effective_ranks_by_mask = (
        {int(mask): int(rank) for mask, rank in ranks_by_mask.items()}
        if ranks_by_mask is not None
        else _dense_base_ranks_by_mask(game)
    )
    ordered_masks = _ordered_masks_for_output(game)
    header = [f"player{i + 1}" for i in range(game.player_count)] + ["score", "rank"]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for mask in ordered_masks:
            membership = ["1" if (int(mask) >> i) & 1 else "0" for i in range(game.player_count)]
            writer.writerow(
                membership
                + [
                    _format_score(game.coalition_value(mask)),
                    str(int(effective_ranks_by_mask[int(mask)])),
                ]
            )


__all__ = ["read_legacy_game_csv", "write_legacy_game_csv"]
