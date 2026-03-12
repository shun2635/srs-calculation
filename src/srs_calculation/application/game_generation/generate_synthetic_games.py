"""Application use case for synthetic cooperative-game generation."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

from ..synthetic_workflow import SyntheticConstraintSelection, resolve_synthetic_output_layout
from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.persistence import write_compatible_game_csv


@dataclass(frozen=True)
class GeneratedSyntheticGamesResult:
    """Summary of one synthetic game generation workflow."""

    player_count: int
    games_dir: Path
    written_paths: tuple[Path, ...]
    count: int
    max_score: int
    seed: int | None
    constraint_selection: SyntheticConstraintSelection
    synthetic_root: Path


def _effective_gen_games_config(
    *,
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    config_path: Path | None,
) -> tuple[int, int, int | None]:
    from ...infrastructure.config import load_yaml_config

    config = load_yaml_config(config_path)
    gen_games_cfg = config.get("gen_games") if isinstance(config.get("gen_games"), dict) else {}

    effective_count = int(count if count is not None else gen_games_cfg.get("count", 1))
    effective_seed = seed if seed is not None else gen_games_cfg.get("seed")
    default_max_score = (1 << int(players)) - 1
    effective_max_score = int(
        max_score
        if max_score is not None
        else gen_games_cfg.get("max_score", default_max_score)
    )
    return effective_count, effective_max_score, effective_seed


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


def _random_weights(player_count: int, *, max_score: int, rng: random.Random) -> list[int]:
    remaining = int(max_score)
    weights = [0 for _ in range(int(player_count))]
    for index in range(int(player_count) - 1):
        value = rng.randint(0, remaining)
        weights[index] = value
        remaining -= value
    if player_count > 0:
        weights[-1] = remaining
    rng.shuffle(weights)
    return weights


def _constrained_complete_game(
    player_count: int,
    *,
    max_score: int,
    rng: random.Random,
    constraints: tuple[str, ...],
) -> CoalitionGame:
    # A non-negative additive game with zero empty coalition satisfies
    # empty_zero, monotonicity, and superadditivity simultaneously.
    weights = _random_weights(player_count, max_score=int(max_score), rng=rng)
    scores_by_mask: dict[int, float] = {0: 0.0}
    for mask in range(1, 1 << int(player_count)):
        value = 0
        for player_index in range(int(player_count)):
            if (int(mask) >> player_index) & 1:
                value += int(weights[player_index])
        scores_by_mask[int(mask)] = float(value)

    if "empty_zero" not in constraints and not {"monotone", "superadditive"} & set(constraints):
        scores_by_mask[0] = float(rng.randint(0, int(max_score)))
    return CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)


def _generate_game_for_constraints(
    player_count: int,
    *,
    max_score: int,
    rng: random.Random,
    constraints: tuple[str, ...],
) -> CoalitionGame:
    normalized = tuple(str(name) for name in constraints)
    if not normalized:
        return _random_complete_game(player_count, max_score=max_score, rng=rng)
    if normalized == ("empty_zero",):
        game = _random_complete_game(player_count, max_score=max_score, rng=rng)
        scores_by_mask = {int(mask): game.coalition_value(int(mask)) for mask in game.coalition_masks()}
        scores_by_mask[0] = 0.0
        return CoalitionGame.from_scores_by_mask(player_count, scores_by_mask)
    return _constrained_complete_game(
        player_count,
        max_score=max_score,
        rng=rng,
        constraints=normalized,
    )


def generate_synthetic_games(
    *,
    players: int,
    count: int | None = None,
    max_score: int | None = None,
    seed: int | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    constraints: tuple[str, ...] = (),
    profile: str | None = None,
) -> GeneratedSyntheticGamesResult:
    """Generate one or more complete synthetic games as compatibility-format CSV files."""

    effective_count, effective_max_score, effective_seed = _effective_gen_games_config(
        players=players,
        count=count,
        max_score=max_score,
        seed=seed,
        config_path=config_path,
    )
    layout = resolve_synthetic_output_layout(
        out_dir=out_dir,
        config_path=config_path,
        constraints=constraints,
        profile=profile,
    )
    games_dir = layout.games_dir(int(players))
    games_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(effective_seed)
    written_paths: list[Path] = []
    for index in _next_game_indices(games_dir, effective_count):
        game = _generate_game_for_constraints(
            int(players),
            max_score=effective_max_score,
            rng=rng,
            constraints=layout.constraint_selection.constraints,
        )
        path = games_dir / f"game_{index:06d}.csv"
        write_compatible_game_csv(path, game)
        written_paths.append(path)

    return GeneratedSyntheticGamesResult(
        player_count=int(players),
        games_dir=games_dir,
        written_paths=tuple(written_paths),
        count=effective_count,
        max_score=effective_max_score,
        seed=effective_seed if effective_seed is None else int(effective_seed),
        constraint_selection=layout.constraint_selection,
        synthetic_root=layout.synthetic_root,
    )


__all__ = [
    "GeneratedSyntheticGamesResult",
    "generate_synthetic_games",
]
