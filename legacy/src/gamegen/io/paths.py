"""Output path conventions.

This module centralizes the directory structure under a single output base.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputPaths:
    """Resolve standard output directories from a base path."""

    base: Path

    def games_dir(self, players: int) -> Path:
        return self.base / "games" / f"n{int(players)}"

    def rankings_dir(self, players: int) -> Path:
        return self.base / "rankings" / f"n{int(players)}"

    def figures_dir(self, players: int) -> Path:
        return self.base / "figures" / f"n{int(players)}"

    def heatmaps_dir(self, players: int) -> Path:
        return self.base / "heatmaps" / f"n{int(players)}"

    def axioms_dir(self, players: int) -> Path:
        return self.base / "axiom" / f"n{int(players)}"

    def analysis_dir(self) -> Path:
        return self.base / "analysis"
