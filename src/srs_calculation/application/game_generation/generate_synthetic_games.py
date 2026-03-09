"""Application use case for synthetic cooperative-game generation."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.config import load_yaml_config
from ...infrastructure.persistence import write_legacy_game_csv


@dataclass(frozen=True)
class GeneratedSyntheticGamesResult:
    """Summary of one synthetic game generation workflow."""

    player_count: int
    games_dir: Path
    written_paths: tuple[Path, ...]
    count: int
    max_score: int
    seed: int | None


def _effective_gen_games_config(
    *,
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    out_dir: Path | None,
    config_path: Path | None,
) -> tuple[int, int, int | None, Path]:
    config = load_yaml_config(config_path)
    gen_games = config.get("gen_games")
    output_base = config.get("output_base", "outputs")
    gen_games_cfg = gen_games if isinstance(gen_games, dict) else {}

    effective_count = int(count if count is not None else gen_games_cfg.get("count", 1))
    effective_seed = seed if seed is not None else gen_games_cfg.get("seed")
    default_max_score = (1 << int(players)) - 1
    effective_max_score = int(
        max_score
        if max_score is not None
        else gen_games_cfg.get("max_score", default_max_score)
    )
    if out_dir is not None:
        effective_out_dir = Path(out_dir)
    else:
        configured_out_dir = Path(str(output_base))
        if not configured_out_dir.is_absolute() and config_path is not None:
            effective_out_dir = Path(config_path).parent / configured_out_dir
        else:
            effective_out_dir = configured_out_dir
    return effective_count, effective_max_score, effective_seed, effective_out_dir


def _next_game_indices(games_dir: Path, count: int) -> list[int]:
    pattern = re.compile(r"^game_(\d+)\.csv$")
    used_indices: set[int] = set()
    for existing in games_dir.glob("game_*.csv"):
        match = pattern.match(existing.name)
        if match is None:
            continue
        try:
            used_indices.add(int(match.group(1)))
        except ValueError:
            continue

    selected: list[int] = []
    candidate = 1
    while len(selected) < int(count):
        if candidate not in used_indices:
            selected.append(candidate)
        candidate += 1
    return selected


def _random_complete_game(player_count: int, *, max_score: int, rng: random.Random) -> CoalitionGame:
    scores_by_mask = {
        mask: float(rng.randint(0, int(max_score)))
        for mask in range(1 << int(player_count))
    }
    return CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)


def generate_synthetic_games(
    *,
    players: int,
    count: int | None = None,
    max_score: int | None = None,
    seed: int | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
) -> GeneratedSyntheticGamesResult:
    """Generate one or more complete synthetic games as legacy-style CSV files."""

    effective_count, effective_max_score, effective_seed, effective_out_dir = _effective_gen_games_config(
        players=players,
        count=count,
        max_score=max_score,
        seed=seed,
        out_dir=out_dir,
        config_path=config_path,
    )
    games_dir = effective_out_dir / "games" / f"n{int(players)}"
    games_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(effective_seed)
    written_paths: list[Path] = []
    for index in _next_game_indices(games_dir, effective_count):
        game = _random_complete_game(
            int(players),
            max_score=effective_max_score,
            rng=rng,
        )
        path = games_dir / f"game_{index:06d}.csv"
        write_legacy_game_csv(path, game)
        written_paths.append(path)

    return GeneratedSyntheticGamesResult(
        player_count=int(players),
        games_dir=games_dir,
        written_paths=tuple(written_paths),
        count=effective_count,
        max_score=effective_max_score,
        seed=effective_seed if effective_seed is None else int(effective_seed),
    )


__all__ = [
    "GeneratedSyntheticGamesResult",
    "generate_synthetic_games",
]
