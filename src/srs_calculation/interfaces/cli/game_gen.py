"""CLI adapters for synthetic-game workflows in the new implementation."""

from __future__ import annotations

from pathlib import Path

import click

from ...application.game_generation import generate_synthetic_games
from ...application.ranking.apply_ranking_rules_to_game_csv import (
    apply_ranking_rules_to_game_csv,
    apply_ranking_rules_in_directory,
)
from ...domain.ranking.registry import build_default_ranking_rule_registry


def _default_rule_ids() -> list[str]:
    return build_default_ranking_rule_registry().list_rule_ids()


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
    out_dir: Path,
    games_dir: Path | None,
    rankings_dir: Path | None,
) -> tuple[Path, Path]:
    if games_dir is None:
        if players is None:
            raise click.ClickException("either --games-dir or --players must be provided")
        resolved_games_dir = out_dir / "games" / f"n{players}"
    else:
        resolved_games_dir = games_dir

    if rankings_dir is None:
        if players is not None:
            resolved_rankings_dir = out_dir / "rankings" / f"n{players}"
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
    help="Optional config.yaml path.",
)
def gen_games_command(
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    out_dir: Path | None,
    config_path: Path | None,
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
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.written_paths:
        click.echo("no games generated")
        return
    click.echo(
        f"wrote {len(result.written_paths)} game(s) to {result.games_dir} "
        f"(players={result.player_count}, max_score={result.max_score})"
    )


@main.command(name="apply-rules")
@click.option(
    "--players",
    "-p",
    type=click.IntRange(1, 12),
    default=None,
    help="Number of players. Used to resolve legacy-style directories under --out.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=Path("outputs"),
    show_default=True,
    help="Base output directory used with --players.",
)
@click.option(
    "--games-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory containing legacy-style game CSV files.",
)
@click.option(
    "--rankings-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory where legacy-style rankings CSV files will be written.",
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
def apply_rules_command(
    players: int | None,
    out_dir: Path,
    games_dir: Path | None,
    rankings_dir: Path | None,
    rule_ids: tuple[str, ...],
    rank_style: str,
    allow_incomplete: bool,
) -> None:
    """Apply migrated ranking rules to legacy-style game CSV files."""

    resolved_games_dir, resolved_rankings_dir = _resolve_apply_rules_dirs(
        players=players,
        out_dir=out_dir,
        games_dir=games_dir,
        rankings_dir=rankings_dir,
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


@main.command(name="rank-game")
@click.option(
    "--game",
    "game_csv_path",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Path to one legacy-style game CSV.",
)
@click.option(
    "--rankings",
    "rankings_csv_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output rankings CSV path. Defaults to the legacy-style sibling rankings location.",
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
    """Apply one migrated ranking rule to one legacy-style game CSV."""

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
