"""End-to-end pipeline commands."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import click

from ..config import Defaults, load_config
from ..figures_png import generate_team_ranking_figure
from ..axioms import render_axiom_summary_heatmap
from ..rank_heatmap import collect_rule_correlation_matrix, render_correlation_heatmap
from ..ranking.registry import RuleScope, list_rules
from ..label_config import apply_order, rule_order
from .axioms import check_axioms
from .games import generate_games_csvs
from .heatmaps import generate_rank_heatmaps, pairs_from_config
from .rankings import available_rule_names, update_rankings_for_game


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _resolve_rules(
    *,
    rules: tuple[str, ...],
    cfg: object,
    players: int,
) -> list[str]:
    aliases: dict[str, str] = {}

    rules_list = list(rules)
    if not rules_list:
        rules_cfg = cfg.get("pipeline", {}).get("rules", Defaults().pipeline_rules) if isinstance(cfg, dict) else Defaults().pipeline_rules
        if isinstance(rules_cfg, (list, tuple)):
            rules_list = [str(x) for x in rules_cfg]
        else:
            rules_list = [s.strip() for s in str(rules_cfg).split(",") if s.strip()]

    allowed = set(available_rule_names())
    normalized = [aliases.get(str(r).lower(), str(r).lower()) for r in rules_list]
    normalized = [r for r in normalized if r in allowed]
    normalized = _dedupe_preserve_order(normalized)

    return normalized


def _render_png_for_rankings_csv(
    *,
    rankings_csv: Path,
    figures_base: Path,
    dpi: int,
) -> bool:
    fig_target = figures_base / f"n{_infer_n_from_csv_path(rankings_csv)}" / (rankings_csv.stem + ".png")
    if fig_target.exists():
        return False
    generate_team_ranking_figure(rankings_csv, figures_base, dpi=dpi)
    return True


def _infer_n_from_csv_path(rankings_csv: Path) -> int:
    # Rankings CSVs are stored under .../rankings/nN/<file>.csv
    try:
        parent = rankings_csv.parent.name
        if parent.startswith("n") and parent[1:].isdigit():
            return int(parent[1:])
    except Exception:
        pass
    raise ValueError(f"Unable to infer players n from path: {rankings_csv}")


@click.command(name="pipeline")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True)
@click.option("--count", "count", "-c", type=click.IntRange(1, None), default=None)
@click.option("--max-score", "max_score", type=click.IntRange(0, None), default=None)
@click.option("--seed", type=int, default=None)
@click.option(
    "--rules",
    type=click.Choice(available_rule_names(), case_sensitive=False),
    multiple=True,
    default=(),
    help="Decision rules to apply for rankings (repeatable).",
)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
@click.option("--dpi", type=click.IntRange(72, 600), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def pipeline(
    players: int,
    count: int | None,
    max_score: int | None,
    seed: int | None,
    rules: tuple[str, ...],
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    """Generate games -> apply rankings -> output PNG figures -> heatmaps -> axiom checks."""
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))

    pipeline_cfg = cfg.get("pipeline", {}) if isinstance(cfg, dict) else {}
    rank_heatmaps_enabled = bool(pipeline_cfg.get("rank_heatmaps", False))

    rules_list = _resolve_rules(rules=rules, cfg=cfg, players=players)
    if not rules_list:
        click.echo("no valid rules to apply; nothing to do")
        return

    effective_dpi = dpi if dpi is not None else int(cfg.get("figures", {}).get("png_dpi", defaults.figures_png_dpi))

    written_games = generate_games_csvs(
        players=players,
        count=count,
        max_score=max_score,
        seed=seed,
        out_dir=base_out,
        config_path=config_path,
    )
    if not written_games:
        click.echo("no new games generated; nothing to do")
        return

    figures_base = base_out / "figures"
    figures_base.mkdir(parents=True, exist_ok=True)

    processed_png = 0
    for game_csv in written_games:
        rankings_csv: Path | None = None
        for rule_name in rules_list:
            rankings_csv, _already, _game = update_rankings_for_game(
                game_path=game_csv,
                rule=rule_name,
                base_out=base_out,
            )
        if rankings_csv is None or not rankings_csv.exists():  # pragma: no cover - safety
            click.echo(f"skip figure: rankings not found for {game_csv.name}")
            continue
        try:
            if _render_png_for_rankings_csv(rankings_csv=rankings_csv, figures_base=figures_base, dpi=effective_dpi):
                processed_png += 1
        except Exception as exc:  # pragma: no cover
            click.echo(f"skip figure {rankings_csv}: {exc}")

    # Heatmaps (best-effort)
    if rank_heatmaps_enabled:
        try:
            rankings_base = base_out / "rankings"
            heatmap_dir = base_out / "heatmaps" / f"n{players}"
            heatmap_dir.mkdir(parents=True, exist_ok=True)
            pairs = pairs_from_config(cfg)
            any_heatmap = generate_rank_heatmaps(
                players=players,
                rankings_base=rankings_base,
                base_out=base_out,
                heatmap_dir=heatmap_dir,
                pairs=pairs,
                dpi=effective_dpi,
                echo=click.echo,
            )
            if not any_heatmap:
                click.echo("skip heatmap: no data")
        except Exception as exc:  # pragma: no cover
            click.echo(f"skip heatmap: {exc}")
    else:
        click.echo("skip rank-heatmap: disabled (set config pipeline.rank_heatmaps: true)")

    # Rule-correlation heatmaps (best-effort)
    try:
        rankings_base = base_out / "rankings"
        heatmap_dir = base_out / "heatmaps" / f"n{players}"
        heatmap_dir.mkdir(parents=True, exist_ok=True)

        rule_cfg = cfg.get("rule_corr_heatmap", {}) if isinstance(cfg, dict) else {}
        method = str(rule_cfg.get("method", "spearman"))

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
    except Exception as exc:  # pragma: no cover
        click.echo(f"skip rule-corr heatmap: {exc}")

    # Axiom checks (best-effort, based on rules that were actually applied)
    try:
        axiom_rules_cfg = (
            cfg.get("axioms", {}).get("rules", defaults.axiom_rules) if isinstance(cfg, dict) else defaults.axiom_rules
        )
        if isinstance(axiom_rules_cfg, (list, tuple)):
            desired_axiom_rules = [str(x).lower() for x in axiom_rules_cfg]
        else:
            desired_axiom_rules = [s.strip() for s in str(axiom_rules_cfg).split(",") if s.strip()]

        effective_axiom_rules = [r for r in desired_axiom_rules if r in set(rules_list)]
        if not effective_axiom_rules:
            click.echo("skip axiom check: no applicable rules")
        else:
            check_axioms.callback(  # type: ignore[attr-defined]
                players=players,
                rules=tuple(effective_axiom_rules),
                out_dir=base_out,
                config_path=config_path,
                min_coalition_size=int(cfg.get("axioms", {}).get("min_coalition_size", 2)) if isinstance(cfg, dict) else 2,
            )
    except Exception as exc:  # pragma: no cover
        click.echo(f"skip axiom check: {exc}")

    # Axiom summary heatmap (best-effort; requires summary.csv)
    try:
        summary_csv = (base_out / "axiom" / f"n{players}" / "summary.csv")
        if summary_csv.exists():
            out_path = summary_csv.parent / "summary_heatmap.png"
            render_axiom_summary_heatmap(
                summary_csv,
                out_path,
                dpi=effective_dpi,
                title="各ルールの公理整合率",
            )
            click.echo(f"saved heatmap: {out_path}")
        else:
            click.echo("skip axiom summary heatmap: summary.csv not found")
    except Exception as exc:  # pragma: no cover
        click.echo(f"skip axiom summary heatmap: {exc}")

    click.echo(f"pipeline completed: {len(written_games)} game(s), {processed_png} new PNG figure(s)")


@click.command(name="apply-rules")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True)
@click.option(
    "--rules",
    "rules",
    type=click.Choice(available_rule_names(), case_sensitive=False),
    multiple=True,
    help="Decision rules to apply for rankings (repeatable).",
)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
@click.option("--dpi", type=click.IntRange(72, 600), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def apply_rules(
    players: int,
    rules: tuple[str, ...],
    out_dir: Path | None,
    dpi: int | None,
    config_path: Path | None,
) -> None:
    """Apply ranking rules to all existing games for n, then build PNG and heatmap."""
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))

    pipeline_cfg = cfg.get("pipeline", {}) if isinstance(cfg, dict) else {}
    rank_heatmaps_enabled = bool(pipeline_cfg.get("rank_heatmaps", False))

    games_dir = base_out / "games" / f"n{players}"
    if not games_dir.exists():
        raise click.ClickException(f"Games directory not found: {games_dir}")

    rules_list = _resolve_rules(rules=rules, cfg=cfg, players=players)
    if not rules_list:
        click.echo("no valid rules to apply; nothing to do")
        return

    effective_dpi = dpi if dpi is not None else int(cfg.get("figures", {}).get("png_dpi", defaults.figures_png_dpi))

    names = sorted(p for p in games_dir.glob("game_*.csv"))
    processed = 0
    for game_csv in names:
        for rule_name in rules_list:
            update_rankings_for_game(
                game_path=game_csv,
                rule=rule_name,
                base_out=base_out,
                rank_style="competition",
            )
        processed += 1

    # Render PNG figures only for this n
    figures_base = base_out / "figures"
    figures_base.mkdir(parents=True, exist_ok=True)
    rankings_dir = base_out / "rankings" / f"n{players}"
    for rankings_csv in sorted(rankings_dir.glob("game_*.csv")):
        try:
            _render_png_for_rankings_csv(rankings_csv=rankings_csv, figures_base=figures_base, dpi=effective_dpi)
        except Exception as exc:  # pragma: no cover
            click.echo(f"skip figure {rankings_csv}: {exc}")

    # Heatmaps (best-effort)
    if rank_heatmaps_enabled:
        try:
            heatmap_dir = base_out / "heatmaps" / f"n{players}"
            heatmap_dir.mkdir(parents=True, exist_ok=True)
            any_heatmap = generate_rank_heatmaps(
                players=players,
                rankings_base=base_out / "rankings",
                base_out=base_out,
                heatmap_dir=heatmap_dir,
                pairs=pairs_from_config(cfg),
                dpi=effective_dpi,
                echo=click.echo,
            )
            if not any_heatmap:
                click.echo("skip heatmap: no data")
        except Exception as exc:  # pragma: no cover
            click.echo(f"skip heatmap: {exc}")
    else:
        click.echo("skip rank-heatmap: disabled (set config pipeline.rank_heatmaps: true)")

    click.echo(f"applied rules to {processed} game(s) for n={players}")


__all__ = ["pipeline", "apply_rules"]
