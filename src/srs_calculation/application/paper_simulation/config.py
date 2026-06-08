"""Configuration objects for the paper simulation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_PLAYERS = 5
DEFAULT_COUNT = 1000
DEFAULT_SEED = 42
DEFAULT_OUT_DIR = Path("outputs/paper/main")
CORRELATION_METHODS = {"spearman", "pearson", "kendall"}
RANK_TIE_METHODS = {"dense", "average", "min", "max"}
EMPTY_CONSTRAINT_POLICIES = {"exclude", "zero", "one"}


@dataclass(frozen=True)
class PaperSimulationConfig:
    """Effective configuration for one paper simulation run."""

    players: int
    count: int
    seed: int
    max_score: int
    out_dir: Path
    target_sizes: tuple[int, ...]
    correlation_method: str
    rank_tie_method: str
    empty_constraints: str

    @property
    def results_dir(self) -> Path:
        return self.out_dir / "results"

    @property
    def figures_dir(self) -> Path:
        return self.out_dir / "figures"

    @property
    def docs_dir(self) -> Path:
        return self.out_dir / "docs"


def parse_target_sizes(raw_value: str | None, players: int) -> tuple[int, ...]:
    """Parse a comma/range target-size spec such as '2,3,5' or '2-5'."""

    if raw_value is None or not str(raw_value).strip():
        return tuple(range(2, int(players) + 1))

    selected: list[int] = []
    seen: set[int] = set()
    for raw_part in str(raw_value).split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            bounds = [piece.strip() for piece in part.split("-", 1)]
            if len(bounds) != 2 or not bounds[0] or not bounds[1]:
                raise ValueError(f"invalid target size range: {raw_part!r}")
            start = int(bounds[0])
            end = int(bounds[1])
            if start > end:
                raise ValueError(f"target size range must be ascending: {raw_part!r}")
            values = range(start, end + 1)
        else:
            values = (int(part),)
        for value in values:
            if value < 2 or value > int(players):
                raise ValueError(f"target size must satisfy 2 <= k <= players: {value}")
            if value not in seen:
                selected.append(int(value))
                seen.add(int(value))

    if not selected:
        raise ValueError("target sizes cannot be empty")
    return tuple(selected)


def build_paper_simulation_config(
    *,
    players: int = DEFAULT_PLAYERS,
    count: int = DEFAULT_COUNT,
    seed: int = DEFAULT_SEED,
    max_score: int | None = None,
    out_dir: Path = DEFAULT_OUT_DIR,
    target_sizes: str | None = None,
    correlation_method: str = "spearman",
    rank_tie_method: str = "dense",
    empty_constraints: str = "exclude",
) -> PaperSimulationConfig:
    """Build and validate the effective paper simulation configuration."""

    normalized_players = int(players)
    normalized_count = int(count)
    if normalized_players < 2:
        raise ValueError("players must be at least 2")
    if normalized_count <= 0:
        raise ValueError("count must be positive")

    normalized_correlation_method = str(correlation_method).strip().lower()
    if normalized_correlation_method not in CORRELATION_METHODS:
        known = ", ".join(sorted(CORRELATION_METHODS))
        raise ValueError(f"correlation_method must be one of: {known}")

    normalized_rank_tie_method = str(rank_tie_method).strip().lower()
    if normalized_rank_tie_method not in RANK_TIE_METHODS:
        known = ", ".join(sorted(RANK_TIE_METHODS))
        raise ValueError(f"rank_tie_method must be one of: {known}")

    normalized_empty_constraints = str(empty_constraints).strip().lower()
    if normalized_empty_constraints not in EMPTY_CONSTRAINT_POLICIES:
        known = ", ".join(sorted(EMPTY_CONSTRAINT_POLICIES))
        raise ValueError(f"empty_constraints must be one of: {known}")

    effective_max_score = (1 << normalized_players) - 1 if max_score is None else int(max_score)
    if effective_max_score < 0:
        raise ValueError("max_score must be non-negative")

    return PaperSimulationConfig(
        players=normalized_players,
        count=normalized_count,
        seed=int(seed),
        max_score=effective_max_score,
        out_dir=Path(out_dir),
        target_sizes=parse_target_sizes(target_sizes, normalized_players),
        correlation_method=normalized_correlation_method,
        rank_tie_method=normalized_rank_tie_method,
        empty_constraints=normalized_empty_constraints,
    )


__all__ = [
    "CORRELATION_METHODS",
    "DEFAULT_COUNT",
    "DEFAULT_OUT_DIR",
    "DEFAULT_PLAYERS",
    "DEFAULT_SEED",
    "EMPTY_CONSTRAINT_POLICIES",
    "PaperSimulationConfig",
    "RANK_TIE_METHODS",
    "build_paper_simulation_config",
    "parse_target_sizes",
]
