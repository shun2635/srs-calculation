"""Game generation commands."""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path

import click

from ..config import Defaults, load_config
from ..io.paths import OutputPaths
from ..ordinal.enumerator import all_coalitions_sorted


def generate_games_csvs(
    *,
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    out_dir: Path | None,
    config_path: Path | None,
) -> list[Path]:
    """Generate one or more game CSV files and return their paths."""
    try:
        coalitions = list(all_coalitions_sorted(players))
    except ValueError as exc:  # pragma: no cover - defensive
        raise click.ClickException(str(exc)) from exc

    cfg = load_config(config_path)
    defaults = Defaults()

    effective_count = (
        count if count is not None else int(cfg.get("gen_games", {}).get("count", defaults.gen_games_count))
    )
    effective_seed = (
        seed if seed is not None else cfg.get("gen_games", {}).get("seed", defaults.gen_games_seed)
    )
    score_cap = (
        max_score
        if max_score is not None
        else (
            cfg.get("gen_games", {}).get("max_score", defaults.gen_games_max_score)
            if cfg.get("gen_games", {}).get("max_score", None) is not None
            else (2**players - 1)
        )
    )

    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    paths = OutputPaths(base_out)
    rng = random.Random(effective_seed)

    header = [f"player{i}" for i in range(1, players + 1)] + ["score", "rank"]
    target = paths.games_dir(players)
    target.mkdir(parents=True, exist_ok=True)

    # Determine indices already used and prepare to fill gaps.
    pattern = re.compile(r"^game_(\d+)\.csv$")
    used_indices: set[int] = set()
    for existing in target.glob("game_*.csv"):
        m = pattern.match(existing.name)
        if not m:
            continue
        try:
            used_indices.add(int(m.group(1)))
        except ValueError:
            continue

    to_write: list[int] = []
    next_candidate = 1
    while len(to_write) < effective_count:
        if next_candidate not in used_indices:
            to_write.append(next_candidate)
        next_candidate += 1

    def bitmask(coal: frozenset[int]) -> int:
        mask = 0
        for p in coal:
            mask |= 1 << (p - 1)
        return mask

    written: list[Path] = []
    player_ids = list(range(1, players + 1))
    for idx in to_write:
        scores = {coal: rng.randint(0, int(score_cap)) for coal in coalitions}
        ordered = sorted(coalitions, key=lambda c: (-scores[c], bitmask(c)))

        csv_path = target / f"game_{idx:06d}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            last_score: int | None = None
            current_rank = 0
            for coal in ordered:
                s = int(scores[coal])
                if last_score is None or s != last_score:
                    current_rank += 1
                    last_score = s
                row = [1 if p in coal else 0 for p in player_ids] + [s, current_rank]
                writer.writerow(row)
        written.append(csv_path)

    return written


@click.command(name="gen-games")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True, help="Number of players (n).")
@click.option(
    "--count",
    "count",
    "-c",
    type=click.IntRange(1, None),
    default=None,
    help="Number of games to generate (default from config or 1).",
)
@click.option(
    "--max-score",
    "max_score",
    type=click.IntRange(0, None),
    default=None,
    help="Maximum integer score for a coalition (default from config or 2^n - 1).",
)
@click.option("--seed", type=int, default=None, help="Optional random seed (default from config).")
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory (default from config or 'outputs').",
)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def gen_games(
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    out_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Randomly generate games as CSV files."""
    written = generate_games_csvs(
        players=players,
        count=count,
        max_score=max_score,
        seed=seed,
        out_dir=out_dir,
        config_path=config_path,
    )
    if written:
        click.echo(f"wrote {len(written)} CSV files to {written[0].parent}")
    else:
        click.echo("no games generated")


__all__ = ["gen_games", "generate_games_csvs"]

