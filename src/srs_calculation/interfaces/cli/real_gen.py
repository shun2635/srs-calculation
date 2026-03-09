"""CLI adapters for real-data workflows in the new implementation."""

from __future__ import annotations

from pathlib import Path

import click

from ...application.dataset_ingestion import import_feature_mask_dataset
from ...application.experiments import (
    render_real_dataset_feature_rule_heatmap,
    render_real_dataset_figures,
)
from ...application.ranking import apply_ranking_rules_to_real_dataset


@click.group()
def main() -> None:
    """Entry point for the new real-data CLI adapters."""


@main.command(name="import-game")
@click.argument("dataset_id", type=str)
@click.option(
    "--inputs-root",
    type=click.Path(path_type=Path),
    default=None,
    help="Inputs root containing feature-mask datasets.",
)
@click.option(
    "--out",
    "out_root",
    type=click.Path(path_type=Path),
    default=Path("outputs") / "real",
    show_default=True,
    help="Real-data output root or one dataset directory.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional config.yaml path used for import_rank_bins.",
)
def import_game_command(
    dataset_id: str,
    inputs_root: Path | None,
    out_root: Path,
    config_path: Path | None,
) -> None:
    """Import one feature-mask dataset into a dataset-scoped game CSV."""

    try:
        result = import_feature_mask_dataset(
            dataset_id,
            inputs_root=inputs_root,
            out_root=out_root,
            config_path=config_path,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"wrote game CSV to {result.game_csv_path}")
    click.echo(f"wrote feature labels to {result.features_yaml_path}")


@main.command(name="apply-rules")
@click.argument("dataset_id", type=str)
@click.option(
    "--out",
    "out_root",
    type=click.Path(path_type=Path),
    default=Path("outputs") / "real",
    show_default=True,
    help="Real-data output root or one dataset directory.",
)
@click.option(
    "--games-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing legacy-style game CSV files for the dataset.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory where dataset-scoped rankings CSV files will be written.",
)
@click.option(
    "--schema",
    "schema_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional schema.yaml path used to resolve default rules.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Reserved for future config-backed defaults.",
)
@click.option(
    "--rule",
    "--rules",
    "rule_ids",
    multiple=True,
    help="Ranking rule to apply. Repeat to apply multiple rules. Defaults to schema rules or all migrated rules.",
)
@click.option(
    "--rank-style",
    type=click.Choice(["dense", "competition"], case_sensitive=False),
    default="competition",
    show_default=True,
    help="Rank style to serialize into the rankings CSV.",
)
@click.option(
    "--allow-incomplete/--require-complete",
    default=False,
    show_default=True,
    help="Allow incomplete game tables when reading game CSV files.",
)
def apply_rules_command(
    dataset_id: str,
    out_root: Path,
    games_dir: Path | None,
    rankings_dir: Path | None,
    schema_path: Path | None,
    config_path: Path | None,
    rule_ids: tuple[str, ...],
    rank_style: str,
    allow_incomplete: bool,
) -> None:
    """Apply migrated ranking rules to one real-data dataset."""

    try:
        result = apply_ranking_rules_to_real_dataset(
            dataset_id,
            out_root=out_root,
            games_dir=games_dir,
            rankings_dir=rankings_dir,
            rule_ids=[str(rule_id) for rule_id in rule_ids],
            rank_style=str(rank_style).lower(),
            require_complete=not allow_incomplete,
            schema_path=schema_path,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except NotADirectoryError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.csv_results:
        click.echo(f"no game CSV found under {result.games_dir}")
        return

    for csv_result in result.csv_results:
        click.echo(
            f"wrote {csv_result.rankings_csv_path} "
            f"({', '.join(csv_result.written_columns) if csv_result.written_columns else 'no derived columns'})"
        )
    click.echo(
        f"processed {len(result.csv_results)} game(s) for dataset {result.dataset_id} "
        f"with {len(result.rule_ids)} rule(s) into {result.rankings_dir}"
    )


@main.command(name="make-figures")
@click.argument("dataset_id", type=str)
@click.option(
    "--out",
    "out_root",
    type=click.Path(path_type=Path),
    default=Path("outputs") / "real",
    show_default=True,
    help="Real-data output root or one dataset directory.",
)
@click.option("--dpi", type=click.IntRange(72, 600), default=150, show_default=True)
@click.option(
    "--max-coalition-size",
    type=click.IntRange(1, 30),
    default=3,
    show_default=True,
    help="Visualization-only filter: show coalitions up to this size.",
)
def make_figures_command(
    dataset_id: str,
    out_root: Path,
    dpi: int,
    max_coalition_size: int,
) -> None:
    """Render table-style ranking figures for one real-data dataset."""

    try:
        result = render_real_dataset_figures(
            dataset_id,
            out_root=out_root,
            dpi=int(dpi),
            max_coalition_size=int(max_coalition_size),
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths:
        click.echo(f"no rankings CSV found under {result.rankings_dir}")
        return
    for path in result.written_paths:
        click.echo(f"saved figure: {path}")


@main.command(name="feature-rule-heatmap")
@click.argument("dataset_id", type=str)
@click.option(
    "--out",
    "out_root",
    type=click.Path(path_type=Path),
    default=Path("outputs") / "real",
    show_default=True,
    help="Real-data output root or one dataset directory.",
)
@click.option("--dpi", type=click.IntRange(72, 600), default=200, show_default=True)
@click.option(
    "--max-coalition-size",
    type=click.IntRange(1, 30),
    default=None,
    help="Show coalitions up to this size. Defaults to schema heatmaps.feature_rule_max_coalition_size or 2.",
)
def feature_rule_heatmap_command(
    dataset_id: str,
    out_root: Path,
    dpi: int,
    max_coalition_size: int | None,
) -> None:
    """Render a feature-by-rule rank heatmap for one dataset."""

    try:
        result = render_real_dataset_feature_rule_heatmap(
            dataset_id,
            out_root=out_root,
            dpi=int(dpi),
            max_coalition_size=max_coalition_size,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"saved heatmap: {result.out_path}")


__all__ = ["main"]


if __name__ == "__main__":  # pragma: no cover
    main()
