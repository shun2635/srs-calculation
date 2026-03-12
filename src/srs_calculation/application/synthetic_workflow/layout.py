"""Path layout helpers for synthetic workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...infrastructure.config import load_yaml_config
from .constraints import SyntheticConstraintSelection, resolve_constraint_selection


@dataclass(frozen=True)
class SyntheticOutputLayout:
    """Canonical artifact paths for one synthetic constraint set."""

    output_base: Path
    constraint_selection: SyntheticConstraintSelection

    @property
    def synthetic_root(self) -> Path:
        return self.output_base / "synthetic" / self.constraint_selection.constraint_set_id

    @property
    def games_base_dir(self) -> Path:
        return self.synthetic_root / "games"

    @property
    def rankings_base_dir(self) -> Path:
        return self.synthetic_root / "rankings"

    @property
    def figures_base_dir(self) -> Path:
        return self.synthetic_root / "figures"

    @property
    def heatmaps_base_dir(self) -> Path:
        return self.synthetic_root / "heatmaps"

    @property
    def analysis_base_dir(self) -> Path:
        return self.synthetic_root / "analysis"

    def games_dir(self, players: int) -> Path:
        return self.games_base_dir / f"n{int(players)}"

    def rankings_dir(self, players: int) -> Path:
        return self.rankings_base_dir / f"n{int(players)}"

    def figures_dir(self, players: int) -> Path:
        return self.figures_base_dir / f"n{int(players)}"

    def heatmaps_dir(self, players: int) -> Path:
        return self.heatmaps_base_dir / f"n{int(players)}"

    def analysis_dir(self, players: int) -> Path:
        return self.analysis_base_dir / f"n{int(players)}"

    def axiom_scope_dir(self, players: int, scope: str) -> Path:
        return self.analysis_dir(players) / "axiom" / str(scope)


def resolve_output_base(
    *,
    out_dir: Path | None = None,
    config_path: Path | None = None,
) -> Path:
    """Resolve the synthetic output base directory."""

    if out_dir is not None:
        return Path(out_dir)

    config = load_yaml_config(config_path)
    configured = Path(str(config.get("output_base", "outputs")))
    if configured.is_absolute() or config_path is None:
        return configured
    return Path(config_path).parent / configured


def resolve_synthetic_output_layout(
    *,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    constraints: tuple[str, ...] = (),
    profile: str | None = None,
) -> SyntheticOutputLayout:
    """Resolve the canonical synthetic output layout."""

    return SyntheticOutputLayout(
        output_base=resolve_output_base(out_dir=out_dir, config_path=config_path),
        constraint_selection=resolve_constraint_selection(
            constraints=constraints,
            profile=profile,
            config_path=config_path,
        ),
    )


__all__ = [
    "SyntheticOutputLayout",
    "resolve_output_base",
    "resolve_synthetic_output_layout",
]
