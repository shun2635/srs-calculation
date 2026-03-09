"""CLI adapters for synthetic-game workflows in the new implementation."""

from __future__ import annotations

from pathlib import Path

import click

from ...application.ranking.apply_ranking_rules_to_game_csv import (
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


__all__ = ["main"]
