"""CLI adapters for synthetic-game workflows in the new implementation."""

from __future__ import annotations

from pathlib import Path

import click

from ...application.axiom_evaluation import (
    evaluate_synthetic_axioms,
    render_synthetic_axiom_summary_heatmaps,
)
from ...application.experiments import (
    render_synthetic_figures,
    render_synthetic_rank_heatmaps,
    render_synthetic_rule_correlation_heatmaps,
)
from ...application.game_generation import generate_synthetic_games
from ...application.synthetic_workflow import resolve_synthetic_output_layout
from ...application.ranking.apply_ranking_rules_to_game_csv import (
    apply_ranking_rules_to_game_csv,
    apply_ranking_rules_in_directory,
)
from ...domain.ranking.registry import build_default_ranking_rule_registry


def _default_rule_ids() -> list[str]:
    return build_default_ranking_rule_registry().list_rule_ids()


def _constraint_option() -> click.Option:
    return click.option(
        "--constraint",
        "constraints",
        multiple=True,
        type=click.Choice(["unconstrained", "empty_zero", "monotone", "superadditive"], case_sensitive=False),
        help="Synthetic constraint to enforce. Repeat to stack constraints.",
    )


def _profile_option() -> click.Option:
    return click.option(
        "--profile",
        type=click.Choice(["tu", "unconstrained"], case_sensitive=False),
        default=None,
        help="Optional shorthand profile for a constraint set.",
    )


def _resolve_rankings_dir_from_games_dir(games_dir: Path) -> Path:
    if games_dir.parent.name == "games" and games_dir.name.startswith("n"):
        return games_dir.parent.parent / "rankings" / games_dir.name
    if games_dir.name.startswith("n"):
        return games_dir.parent / "rankings" / games_dir.name
    return games_dir.parent / "rankings"


def _resolve_rankings_path_from_game_path(game_csv_path: Path) -> Path:
    if game_csv_path.parent.name.startswith("n") and game_csv_path.parent.parent.name == "games":
        return game_csv_path.parent.parent.parent / "rankings" / game_csv_path.parent.name / game_csv_path.name
    if game_csv_path.parent.name == "games":
        return game_csv_path.parent.parent / "rankings" / game_csv_path.name
    return game_csv_path.parent / "rankings" / game_csv_path.name


def _resolve_apply_rules_dirs(
    *,
    players: int | None,
    out_dir: Path | None,
    games_dir: Path | None,
    rankings_dir: Path | None,
    constraints: tuple[str, ...],
    profile: str | None,
    config_path: Path | None,
) -> tuple[Path, Path]:
    layout = resolve_synthetic_output_layout(
        out_dir=out_dir,
        config_path=config_path,
        constraints=constraints,
        profile=profile,
    )
    if games_dir is None:
        if players is None:
            raise click.ClickException("either --games-dir or --players must be provided")
        resolved_games_dir = layout.games_dir(int(players))
    else:
        resolved_games_dir = games_dir

    if rankings_dir is None:
        if players is not None:
            resolved_rankings_dir = layout.rankings_dir(int(players))
        else:
            resolved_rankings_dir = _resolve_rankings_dir_from_games_dir(resolved_games_dir)
    else:
        resolved_rankings_dir = rankings_dir

    return resolved_games_dir, resolved_rankings_dir


@click.group()
def main() -> None:
    """Entry point for the new synthetic-game CLI adapters."""


@main.command(name="gen-games")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    required=True,
    help="Number of players.",
)
@click.option(
    "--count",
    "-c",
    type=click.IntRange(1, None),
    default=None,
    help="Number of games to generate. Defaults to config or 1.",
)
@click.option(
    "--max-score",
    type=click.IntRange(0, None),
    default=None,
    help="Maximum coalition score. Defaults to config or 2^n - 1.",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Optional random seed. Defaults to config.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory. Defaults to config or outputs.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def gen_games_command(
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    out_dir: Path | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Generate complete synthetic game CSV files."""

    try:
        result = generate_synthetic_games(
            players=int(players),
            count=count,
            max_score=max_score,
            seed=seed,
            out_dir=out_dir,
            config_path=config_path,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths:
        click.echo("no games generated")
        return
    click.echo(
        f"wrote {len(result.written_paths)} game(s) to {result.games_dir} "
        f"(players={result.player_count}, max_score={result.max_score}, "
        f"constraint_set={result.constraint_selection.constraint_set_id})"
    )


@main.command(name="make-figures")
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Rankings base directory. Defaults to '<output_base>/rankings'.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory for figures. Defaults to explicit config or outputs.",
)
@click.option(
    "--dpi",
    type=click.IntRange(72, 600),
    default=None,
    help="Output PNG DPI. Defaults to explicit config or 150.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def make_figures_command(
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Render PNG figures from synthetic rankings CSV files."""

    try:
        result = render_synthetic_figures(
            rankings_dir=rankings_dir,
            out_dir=out_dir,
            config_path=config_path,
            dpi=dpi,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        f"generated {len(result.written_paths)} PNG figure(s) under {result.figures_dir} "
        f"(skipped {result.skipped_count} up-to-date)"
    )


@main.command(name="rank-heatmap")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    required=True,
    help="Number of players.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Rankings base directory. Defaults to '<output_base>/rankings'.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory for heatmaps. Defaults to explicit config or outputs.",
)
@click.option(
    "--dpi",
    type=click.IntRange(72, 600),
    default=None,
    help="Output PNG DPI. Defaults to explicit config or 150.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def rank_heatmap_command(
    players: int,
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Render pairwise synthetic rank heatmaps from rankings CSV files."""

    try:
        result = render_synthetic_rank_heatmaps(
            players=int(players),
            rankings_dir=rankings_dir,
            out_dir=out_dir,
            config_path=config_path,
            dpi=dpi,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths:
        click.echo("no heatmap rendered")
        return

    for path in result.written_paths:
        click.echo(f"saved heatmap: {path}")


@main.command(name="rule-corr-heatmap")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    required=True,
    help="Number of players.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Rankings base directory. Defaults to '<output_base>/rankings'.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory for heatmaps. Defaults to explicit config or outputs.",
)
@click.option(
    "--dpi",
    type=click.IntRange(72, 600),
    default=None,
    help="Output PNG DPI. Defaults to explicit config or 150.",
)
@click.option(
    "--method",
    type=str,
    default=None,
    help="Correlation method passed to pandas.DataFrame.corr. Defaults to config or 'spearman'.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def rule_corr_heatmap_command(
    players: int,
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    method: str | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Render rule-by-rule synthetic rank-correlation heatmaps."""

    try:
        result = render_synthetic_rule_correlation_heatmaps(
            players=int(players),
            rankings_dir=rankings_dir,
            out_dir=out_dir,
            config_path=config_path,
            dpi=dpi,
            method=method,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths and not result.written_csv_paths:
        click.echo("no heatmap rendered")
        return

    for path in result.written_paths:
        click.echo(f"saved heatmap: {path}")
    for path in result.written_csv_paths:
        click.echo(f"saved summary: {path}")


@main.command(name="apply-rules")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    default=None,
    help="Number of players. Used to resolve compatibility-format directories under --out.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Base output directory used with --players. Defaults to config or outputs.",
)
@click.option(
    "--games-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing compatibility-format game CSV files.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory where compatibility-format rankings CSV files will be written.",
)
@click.option(
    "--rule",
    "--rules",
    "rule_ids",
    multiple=True,
    type=click.Choice(_default_rule_ids(), case_sensitive=False),
    help="Ranking rule to apply. Repeat to apply multiple rules. Defaults to all migrated rules.",
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
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def apply_rules_command(
    players: int | None,
    out_dir: Path | None,
    games_dir: Path | None,
    rankings_dir: Path | None,
    rule_ids: tuple[str, ...],
    rank_style: str,
    allow_incomplete: bool,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Apply migrated ranking rules to compatibility-format game CSV files."""

    resolved_games_dir, resolved_rankings_dir = _resolve_apply_rules_dirs(
        players=players,
        out_dir=out_dir,
        games_dir=games_dir,
        rankings_dir=rankings_dir,
        constraints=tuple(str(name) for name in constraints),
        profile=profile,
        config_path=config_path,
    )
    selected_rule_ids = [str(rule_id) for rule_id in rule_ids] or _default_rule_ids()

    try:
        results = apply_ranking_rules_in_directory(
            resolved_games_dir,
            resolved_rankings_dir,
            selected_rule_ids,
            rank_style=str(rank_style).lower(),
            require_complete=not allow_incomplete,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except NotADirectoryError as exc:
        raise click.ClickException(str(exc)) from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo(f"no game CSV found under {resolved_games_dir}")
        return

    for result in results:
        click.echo(
            f"wrote {result.rankings_csv_path} "
            f"({', '.join(result.written_columns) if result.written_columns else 'no derived columns'})"
        )
    click.echo(
        f"processed {len(results)} game(s) with {len(selected_rule_ids)} rule(s) "
        f"into {resolved_rankings_dir}"
    )


@main.command(name="evaluate-axioms")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    required=True,
    help="Number of players.",
)
@click.option(
    "--games-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing synthetic game CSV files.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing synthetic rankings CSV files.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory. Defaults to config or outputs.",
)
@click.option(
    "--scope",
    type=click.Choice(["all", "coalition", "individual"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Axiom scope to evaluate.",
)
@click.option(
    "--dpi",
    type=click.IntRange(72, 600),
    default=None,
    help="Output PNG DPI for summary heatmaps. Defaults to config or 150.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def evaluate_axioms_command(
    players: int,
    games_dir: Path | None,
    rankings_dir: Path | None,
    out_dir: Path | None,
    scope: str,
    dpi: int | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Evaluate synthetic rankings against available axiom registries."""

    try:
        result = evaluate_synthetic_axioms(
            players=int(players),
            games_dir=games_dir,
            rankings_dir=rankings_dir,
            out_dir=out_dir,
            config_path=config_path,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
            scope=str(scope).lower(),
            dpi=dpi,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    for report in result.reports:
        if report.skipped_reason is not None:
            click.echo(report.skipped_reason)
            continue
        if report.summary_csv_path is not None:
            click.echo(f"saved summary: {report.summary_csv_path}")
        if report.summary_heatmap_path is not None:
            click.echo(f"saved heatmap: {report.summary_heatmap_path}")


@main.command(name="axiom-summary-heatmap")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    required=True,
    help="Number of players.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory. Defaults to config or outputs.",
)
@click.option(
    "--scope",
    type=click.Choice(["all", "coalition", "individual"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Axiom scope to render.",
)
@click.option(
    "--dpi",
    type=click.IntRange(72, 600),
    default=None,
    help="Output PNG DPI. Defaults to config or 150.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional explicit root config.yaml path. If omitted, built-in defaults are used.",
)
@_profile_option()
@_constraint_option()
def axiom_summary_heatmap_command(
    players: int,
    out_dir: Path | None,
    scope: str,
    dpi: int | None,
    config_path: Path | None,
    profile: str | None,
    constraints: tuple[str, ...],
) -> None:
    """Render heatmaps from synthetic axiom summary CSV files."""

    try:
        result = render_synthetic_axiom_summary_heatmaps(
            players=int(players),
            out_dir=out_dir,
            config_path=config_path,
            constraints=tuple(str(name) for name in constraints),
            profile=profile,
            scope=str(scope).lower(),
            dpi=dpi,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths:
        click.echo("no heatmap rendered")
        return

    for path in result.written_paths:
        click.echo(f"saved heatmap: {path}")


@main.command(name="rank-game")
@click.option(
    "--game",
    "game_csv_path",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Path to one compatibility-format game CSV.",
)
@click.option(
    "--rankings",
    "rankings_csv_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output rankings CSV path. Defaults to the compatibility-format sibling rankings location.",
)
@click.option(
    "--rule",
    "rule_id",
    type=click.Choice(_default_rule_ids(), case_sensitive=False),
    required=True,
    help="Ranking rule to apply.",
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
    help="Allow incomplete game tables when reading the game CSV.",
)
def rank_game_command(
    game_csv_path: Path,
    rankings_csv_path: Path | None,
    rule_id: str,
    rank_style: str,
    allow_incomplete: bool,
) -> None:
    """Apply one migrated ranking rule to one compatibility-format game CSV."""

    resolved_rankings_csv_path = (
        rankings_csv_path
        if rankings_csv_path is not None
        else _resolve_rankings_path_from_game_path(game_csv_path)
    )

    try:
        result = apply_ranking_rules_to_game_csv(
            game_csv_path,
            resolved_rankings_csv_path,
            [str(rule_id)],
            rank_style=str(rank_style).lower(),
            require_complete=not allow_incomplete,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        f"wrote {result.rankings_csv_path} "
        f"({', '.join(result.written_columns) if result.written_columns else 'no derived columns'})"
    )


__all__ = ["main"]


if __name__ == "__main__":  # pragma: no cover
    main()
