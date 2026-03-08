"""Heatmap commands."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Callable

import click

from ..config import Defaults, load_config
from ..ranking.registry import RuleScope, list_rules
from ..display_names import rank_column_display_name
from ..label_config import apply_order, rule_order
from ..rank_heatmap import (
    collect_group_rank_pairs,
    collect_rank_pairs,
    collect_rule_correlation_matrix,
    render_correlation_heatmap,
    render_heatmap,
)


def _count_games_for_title(rankings_base: Path, base_out: Path, players: int) -> int:
    target_dir = rankings_base / f"n{players}"
    try:
        ranking_files = {p.stem for p in target_dir.glob("game_*.csv")}
        games_dir = base_out / "games" / f"n{players}"
        if games_dir.exists():
            game_files = {p.stem for p in games_dir.glob("game_*.csv")}
            inter = ranking_files & game_files
            return len(inter) if inter else len(ranking_files)
        return len(ranking_files)
    except Exception:
        return 0


def pairs_from_config(cfg: object) -> list[tuple[str, str]]:
    cfg_section = cfg.get("rank_heatmap", {}) if isinstance(cfg, dict) else {}
    pairs_cfg = cfg_section.get("pairs") if isinstance(cfg_section, dict) else None
    if not pairs_cfg:
        return [
            ("rank_lexcel", "rank_shapley"),
        ]

    if isinstance(pairs_cfg, str) and pairs_cfg.strip().lower() in {"all", "auto"}:
        rules = list_rules()
        player_cols = [r.column_name for r in rules if r.scope is RuleScope.PLAYER]
        coalition_cols = [r.column_name for r in rules if r.scope is RuleScope.COALITION]

        pairs: list[tuple[str, str]] = []
        for a, b in itertools.combinations(player_cols, 2):
            pairs.append((a, b) if str(a) < str(b) else (b, a))
        for a, b in itertools.combinations(coalition_cols, 2):
            pairs.append((a, b) if str(a) < str(b) else (b, a))
        return pairs

    pairs: list[tuple[str, str]] = []
    for entry in pairs_cfg:
        try:
            x, y = list(entry)[0], list(entry)[1]
        except Exception:
            try:
                x, y = entry[0], entry[1]
            except Exception:
                continue
        pairs.append((str(x), str(y)))
    return pairs


def generate_rank_heatmaps(
    *,
    players: int,
    rankings_base: Path,
    base_out: Path,
    heatmap_dir: Path,
    pairs: list[tuple[str, str]],
    dpi: int,
    echo: Callable[[str], None] = click.echo,
) -> bool:
    """Generate one or more heatmaps, returning True if any were rendered."""
    current_file_count = _count_games_for_title(rankings_base, base_out, players)
    echo(f"title games={current_file_count}")

    any_rendered = False
    for x_col, y_col in pairs:
        try:
            scope_by_col = {r.column_name: r.scope for r in list_rules()}
            x_scope = scope_by_col.get(str(x_col))
            y_scope = scope_by_col.get(str(y_col))
            if x_scope is None or y_scope is None or x_scope is not y_scope:
                continue

            if x_scope is RuleScope.COALITION:
                summary = collect_group_rank_pairs(rankings_base, players, lex_col=str(x_col), banz_col=str(y_col))
                echo(f"collected {summary.total_pairs} coalition rank pair(s)")
            else:
                summary = collect_rank_pairs(rankings_base, players, lex_col=str(x_col), shap_col=str(y_col))
                echo(f"collected {summary.total_pairs} player rank pair(s)")

            if summary.matrix.empty or summary.total_pairs <= 0:
                continue

            out_path = heatmap_dir / f"{x_col}_vs_{y_col}.png"
            x_label = rank_column_display_name(str(x_col))
            y_label = rank_column_display_name(str(y_col))
            title = f"{y_label} vs {x_label} (n={players}, games={current_file_count})"
            render_heatmap(
                summary.matrix,
                out_path,
                lex_label=str(x_col),
                shap_label=str(y_col),
                dpi=dpi,
                title=title,
            )
            echo(f"saved heatmap: {out_path}")
            any_rendered = True
        except Exception as exc:
            echo(f"skip heatmap {x_col} vs {y_col}: {exc}")

    return any_rendered


@click.command(name="rank-heatmap")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True, help="Number of players (n).")
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
    help="Output base directory for the heatmap (defaults to '<output_base>').",
)
@click.option("--dpi", type=click.IntRange(72, 600), default=None, help="Output PNG DPI (default from config or 150).")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def rank_heatmap(
    players: int,
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    """Generate heatmap(s) for configured rank column pairs."""
    cfg = load_config(config_path)
    defaults = Defaults()

    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    rankings_base = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    heatmap_dir = base_out / "heatmaps" / f"n{players}"
    heatmap_dir.mkdir(parents=True, exist_ok=True)

    cfg_section = cfg.get("rank_heatmap", {}) if isinstance(cfg, dict) else {}
    effective_dpi = dpi if dpi is not None else int(cfg_section.get("dpi", defaults.figures_png_dpi))

    pairs = pairs_from_config(cfg)
    any_rendered = generate_rank_heatmaps(
        players=players,
        rankings_base=rankings_base,
        base_out=base_out,
        heatmap_dir=heatmap_dir,
        pairs=pairs,
        dpi=effective_dpi,
        echo=click.echo,
    )
    if not any_rendered:
        click.echo("no heatmap rendered")


@click.command(name="rule-corr-heatmap")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True, help="Number of players (n).")
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
    help="Output base directory for the heatmap (defaults to '<output_base>').",
)
@click.option("--dpi", type=click.IntRange(72, 600), default=None, help="Output PNG DPI (default from config or 150).")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def rule_corr_heatmap(
    players: int,
    rankings_dir: Path | None,
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    """Generate rule×rule correlation heatmaps (player-scope and coalition-scope)."""
    cfg = load_config(config_path)
    defaults = Defaults()

    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    rankings_base = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    heatmap_dir = base_out / "heatmaps" / f"n{players}"
    heatmap_dir.mkdir(parents=True, exist_ok=True)

    cfg_section = cfg.get("rule_corr_heatmap", {}) if isinstance(cfg, dict) else {}
    method = str(cfg_section.get("method", "spearman"))
    effective_dpi = dpi if dpi is not None else int(cfg.get("figures", {}).get("png_dpi", defaults.figures_png_dpi)) if isinstance(cfg, dict) else defaults.figures_png_dpi

    rules = list_rules()
    by_name = {r.name: r for r in rules}
    ordered_names = apply_order([r.name for r in rules], rule_order())
    player_cols = [by_name[name].column_name for name in ordered_names if by_name[name].scope is RuleScope.PLAYER]
    coalition_cols = [by_name[name].column_name for name in ordered_names if by_name[name].scope is RuleScope.COALITION]

    player_corr = collect_rule_correlation_matrix(rankings_base, players, rank_cols=player_cols, mode="player", method=method)
    if not player_corr.empty:
        out_path = heatmap_dir / "rule_corr_player.png"
        render_correlation_heatmap(
            player_corr,
            out_path,
            dpi=effective_dpi,
            title="ルール間の順位相関",
        )
        click.echo(f"saved heatmap: {out_path}")

    coalition_corr = collect_rule_correlation_matrix(rankings_base, players, rank_cols=coalition_cols, mode="coalition", method=method)
    if not coalition_corr.empty:
        out_path = heatmap_dir / "rule_corr_coalition.png"
        render_correlation_heatmap(
            coalition_corr,
            out_path,
            dpi=effective_dpi,
            title="ルール間の順位相関",
        )
        click.echo(f"saved heatmap: {out_path}")

    if player_corr.empty and coalition_corr.empty:
        click.echo("no heatmap rendered")


__all__ = ["generate_rank_heatmaps", "pairs_from_config", "rank_heatmap", "rule_corr_heatmap"]
