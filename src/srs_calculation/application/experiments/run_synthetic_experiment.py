"""Application use cases for synthetic-game plotting workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...infrastructure.config import load_yaml_config
from ...infrastructure.plotting import generate_synthetic_ranking_figure


@dataclass(frozen=True)
class RenderedSyntheticFigures:
    """Summary of synthetic ranking figures produced from ranking CSV files."""

    rankings_dir: Path
    figures_dir: Path
    written_paths: tuple[Path, ...]
    skipped_count: int


def _default_output_base(config_path: Path | None) -> Path:
    config = load_yaml_config(config_path)
    raw_output_base = config.get("output_base", "outputs")
    configured = Path(str(raw_output_base))
    if configured.is_absolute() or config_path is None:
        return configured
    return Path(config_path).parent / configured


def _default_figures_dpi(config_path: Path | None, *, default: int = 150) -> int:
    config = load_yaml_config(config_path)
    figures = config.get("figures")
    if not isinstance(figures, dict):
        return int(default)
    try:
        return int(figures.get("png_dpi", default))
    except Exception:
        return int(default)


def render_synthetic_figures(
    *,
    rankings_dir: Path | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    dpi: int | None = None,
) -> RenderedSyntheticFigures:
    """Render PNG figures from compatibility-format synthetic rankings CSV files."""

    base_out = Path(out_dir) if out_dir is not None else _default_output_base(config_path)
    resolved_rankings_dir = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    resolved_figures_dir = base_out / "figures"
    if not resolved_rankings_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {resolved_rankings_dir}")

    effective_dpi = int(dpi) if dpi is not None else _default_figures_dpi(config_path)
    written_paths: list[Path] = []
    skipped_count = 0

    for csv_path in sorted(resolved_rankings_dir.rglob("*.csv")):
        if not csv_path.is_file():
            continue
        relative_parent = csv_path.parent.relative_to(resolved_rankings_dir)
        target_dir = resolved_figures_dir / relative_parent
        target_path = target_dir / f"{csv_path.stem}.png"
        if target_path.exists():
            try:
                if target_path.stat().st_mtime >= csv_path.stat().st_mtime:
                    skipped_count += 1
                    continue
            except OSError:
                pass
        written_paths.append(
            generate_synthetic_ranking_figure(
                rankings_csv=csv_path,
                output_dir=target_dir,
                dpi=effective_dpi,
            )
        )

    return RenderedSyntheticFigures(
        rankings_dir=resolved_rankings_dir,
        figures_dir=resolved_figures_dir,
        written_paths=tuple(written_paths),
        skipped_count=skipped_count,
    )


__all__ = ["RenderedSyntheticFigures", "render_synthetic_figures"]
