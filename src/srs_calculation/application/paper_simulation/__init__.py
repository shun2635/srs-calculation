"""Paper-facing simulation workflow for AAMAS analysis."""

from .config import (
    DEFAULT_COUNT,
    DEFAULT_PLAYERS,
    DEFAULT_SEED,
    PaperSimulationConfig,
    build_paper_simulation_config,
    parse_target_sizes,
)
from .run import PaperSimulationResult, run_paper_simulation

__all__ = [
    "DEFAULT_COUNT",
    "DEFAULT_PLAYERS",
    "DEFAULT_SEED",
    "PaperSimulationConfig",
    "PaperSimulationResult",
    "build_paper_simulation_config",
    "parse_target_sizes",
    "run_paper_simulation",
]
