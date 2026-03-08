"""Compute contribution indices from a resignation-rate coalition table."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping

import click

from gamegen.rules import banzhaf as banzhaf_rules
from gamegen.rules import shapley as shapley_rules

from ..datasets import resolve_dataset_out_base


RISK_FACTOR_COLUMNS: tuple[str, ...] = (
    "low_income",
    "long_overtime",
    "low_remote",
    "large_team",
    "low_promotion",
)


def _dense_rank_desc(values: Mapping[int, float]) -> dict[int, int]:
    order = sorted(values.keys(), key=lambda k: (-float(values[k]), int(k)))
    ranks: dict[int, int] = {}
    last: float | None = None
    current = 0
    for k in order:
        v = float(values[k])
        if last is None or v != last:
            current += 1
            last = v
        ranks[int(k)] = int(current)
    return ranks


def _read_resignation_table(path: Path) -> tuple[int, dict[int, float]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise click.ClickException(f"CSV has no header: {path}")

        required = set(RISK_FACTOR_COLUMNS) | {"resignation_rate"}
        missing = [c for c in required if c not in set(reader.fieldnames)]
        if missing:
            raise click.ClickException(f"missing required columns: {missing}")

        n = len(RISK_FACTOR_COLUMNS)
        scores_by_mask: dict[int, float] = {}
        for row in reader:
            mask = 0
            for i, col in enumerate(RISK_FACTOR_COLUMNS):
                raw = (row.get(col) or "0").strip()
                try:
                    bit = int(raw)
                except Exception as exc:
                    raise click.ClickException(f"invalid 0/1 cell for {col!r}: {raw!r}") from exc
                if bit not in (0, 1):
                    raise click.ClickException(f"invalid 0/1 cell for {col!r}: {raw!r}")
                if bit:
                    mask |= 1 << i

            raw_score = (row.get("resignation_rate") or "").strip()
            try:
                score = float(raw_score)
            except Exception as exc:
                raise click.ClickException(f"invalid resignation_rate cell: {raw_score!r}") from exc

            if mask in scores_by_mask and scores_by_mask[mask] != score:
                raise click.ClickException(
                    f"duplicate mask with conflicting resignation_rate: mask={mask} {scores_by_mask[mask]} != {score}"
                )
            scores_by_mask[int(mask)] = float(score)

    expected = 1 << n
    missing_masks = [m for m in range(expected) if m not in scores_by_mask]
    if missing_masks:
        raise click.ClickException(
            f"missing coalitions: {len(missing_masks)} (expected={expected}, found={len(scores_by_mask)}), "
            f"examples={missing_masks[:5]}"
        )
    return n, scores_by_mask


def _write_game_csv(*, out_path: Path, n: int, scores_by_mask: Mapping[int, float]) -> None:
    ranks_by_mask = _dense_rank_desc(scores_by_mask)
    header = [f"player{i+1}" for i in range(n)] + ["score", "rank"]

    def membership(mask: int) -> list[str]:
        return ["1" if (mask >> i) & 1 else "0" for i in range(n)]

    order = sorted(scores_by_mask.keys(), key=lambda m: (-float(scores_by_mask[m]), int(m)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for mask in order:
            writer.writerow(membership(int(mask)) + [f"{float(scores_by_mask[mask]):.10g}", str(int(ranks_by_mask[int(mask)]))])


@click.command(name="resignation-contrib")
@click.argument("dataset_id", type=str)
@click.option("--table", "table_path", type=click.Path(path_type=Path), default=None, help="Input coalition table CSV.")
@click.option(
    "--out-dir",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: outputs/real/<dataset_id>/resignation).",
)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def resignation_contrib(dataset_id: str, table_path: Path | None, out_dir: Path | None, config_path: Path | None) -> None:
    """Compute Shapley/Banzhaf contributions from resignation_rate_table.csv (no model training)."""
    base_out = resolve_dataset_out_base(dataset_id, out_root=None, config_path=config_path)
    default_table = base_out / "resignation" / "resignation_rate_table.csv"
    table = table_path if table_path is not None else default_table
    if not table.exists():
        raise click.ClickException(f"table not found: {table}")

    out_base = out_dir if out_dir is not None else (base_out / "resignation")
    out_base.mkdir(parents=True, exist_ok=True)

    n, scores_by_mask = _read_resignation_table(table)
    game_csv = out_base / "game_resignation.csv"
    _write_game_csv(out_path=game_csv, n=n, scores_by_mask=scores_by_mask)

    phi_shapley = shapley_rules.player_shapley_values(scores_by_mask, n)
    phi_banzhaf = banzhaf_rules.player_banzhaf_values(scores_by_mask, n)
    rank_shapley = _dense_rank_desc({i: float(phi_shapley[i]) for i in range(n)})
    rank_banzhaf = _dense_rank_desc({i: float(phi_banzhaf[i]) for i in range(n)})

    out_csv = out_base / "contributions.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["factor", "player", "shapley", "banzhaf", "rank_shapley", "rank_banzhaf"])
        for i, col in enumerate(RISK_FACTOR_COLUMNS):
            w.writerow(
                [
                    col,
                    f"player{i+1}",
                    f"{float(phi_shapley[i]):.10g}",
                    f"{float(phi_banzhaf[i]):.10g}",
                    str(int(rank_shapley[i])),
                    str(int(rank_banzhaf[i])),
                ]
            )

    click.echo(f"wrote: {out_csv}")
    click.echo(f"wrote: {game_csv}")


__all__ = ["resignation_contrib"]

