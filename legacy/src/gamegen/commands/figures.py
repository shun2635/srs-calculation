"""Figure generation commands (PNG)."""

from __future__ import annotations

from pathlib import Path

import click

from ..config import Defaults, load_config
from ..figures_png import generate_team_ranking_figure


def _render_png_figures(
    *,
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    rankings_base = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    figures_base = base_out / "figures"
    figures_base.mkdir(parents=True, exist_ok=True)

    if not rankings_base.exists():
        raise click.ClickException(f"Rankings directory not found: {rankings_base}")

    effective_dpi = dpi if dpi is not None else int(cfg.get("figures", {}).get("png_dpi", defaults.figures_png_dpi))

    processed = 0
    skipped = 0
    for csv_path in rankings_base.rglob("*.csv"):
        try:
            relative_dir = csv_path.parent.name  # expect 'nX'
            target_dir = figures_base / relative_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / (csv_path.stem + ".png")
            if target_path.exists():
                try:
                    if target_path.stat().st_mtime >= csv_path.stat().st_mtime:
                        skipped += 1
                        continue
                except OSError:
                    pass
            generate_team_ranking_figure(csv_path, figures_base, dpi=effective_dpi)
            processed += 1
        except Exception as exc:  # pragma: no cover - resilient
            click.echo(f"skip {csv_path}: {exc}")

    click.echo(f"generated {processed} PNG figure(s) under {figures_base} (skipped {skipped} up-to-date)")


@click.command(name="make-figures")
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path, exists=False),
    default=None,
    help="Rankings base directory (defaults to '<output_base>/rankings').",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory for figures (defaults to '<output_base>').",
)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def make_figures(
    rankings_dir: Path | None,
    out_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Render PNG figures from ranking CSV files.

    This command used to output a text representation under `<out>/figures/`.
    The text output was removed; `make-figures` now generates PNG only.
    """
    _render_png_figures(rankings_dir=rankings_dir, out_dir=out_dir, dpi=None, config_path=config_path)


@click.command(name="make-figures-png")
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path, exists=False),
    default=None,
    help="Rankings base directory (defaults to '<output_base>/rankings').",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory for figures (defaults to '<output_base>').",
)
@click.option("--dpi", type=click.IntRange(72, 600), default=None, help="Output PNG DPI (default from config or 150).")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def make_figures_png(
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    """Render PNG figures from ranking CSV files.

    This is an alias of `make-figures` with an explicit `--dpi` option.
    """
    _render_png_figures(rankings_dir=rankings_dir, out_dir=out_dir, dpi=dpi, config_path=config_path)


__all__ = ["make_figures", "make_figures_png"]
