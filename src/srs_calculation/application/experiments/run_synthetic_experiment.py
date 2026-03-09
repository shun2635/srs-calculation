"""Application use cases for synthetic-game plotting workflows."""

from __future__ import annotations

from dataclasses import dataclass
import itertools
from pathlib import Path

from ...infrastructure.config import load_yaml_config
from ...infrastructure.plotting import generate_synthetic_ranking_figure
from ...infrastructure.plotting import (
    collect_rank_pairs,
    collect_rule_correlation_matrix,
    infer_rank_column_scopes,
    render_correlation_heatmap,
    render_rank_pair_heatmap,
)


@dataclass(frozen=True)
class RenderedSyntheticFigures:
    """Summary of synthetic ranking figures produced from ranking CSV files."""

    rankings_dir: Path
    figures_dir: Path
    written_paths: tuple[Path, ...]
    skipped_count: int


@dataclass(frozen=True)
class RenderedSyntheticRankHeatmaps:
    """Summary of pairwise synthetic rank heatmaps."""

    rankings_dir: Path
    heatmaps_dir: Path
    written_paths: tuple[Path, ...]
    pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RenderedSyntheticRuleCorrelationHeatmaps:
    """Summary of synthetic rule-correlation heatmaps."""

    rankings_dir: Path
    heatmaps_dir: Path
    written_paths: tuple[Path, ...]
    method: str


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


def _rank_heatmap_pairs_from_config(config_path: Path | None) -> list[tuple[str, str]] | str | None:
    config = load_yaml_config(config_path)
    section = config.get("rank_heatmap")
    if not isinstance(section, dict):
        return None
    pairs_config = section.get("pairs")
    if isinstance(pairs_config, str):
        normalized = pairs_config.strip().lower()
        if normalized in {"all", "auto"}:
            return normalized
    if not isinstance(pairs_config, list):
        return None

    pairs: list[tuple[str, str]] = []
    for entry in pairs_config:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            pairs.append((str(entry[0]), str(entry[1])))
    return pairs or None


def _default_rank_heatmap_pairs(
    rankings_dir: Path,
    *,
    players: int,
    config_path: Path | None,
) -> list[tuple[str, str]]:
    configured = _rank_heatmap_pairs_from_config(config_path)
    scopes = infer_rank_column_scopes(rankings_dir, players)
    if isinstance(configured, list):
        return configured
    if configured in {"all", "auto"}:
        ordered_player = [name for name, scope in scopes.items() if scope == "player"]
        ordered_coalition = [name for name, scope in scopes.items() if scope == "coalition"]
        pairs: list[tuple[str, str]] = []
        for left, right in itertools.combinations(ordered_player, 2):
            pairs.append((left, right))
        for left, right in itertools.combinations(ordered_coalition, 2):
            pairs.append((left, right))
        return pairs
    if "rank_lexcel" in scopes and "rank_shapley" in scopes:
        return [("rank_lexcel", "rank_shapley")]

    ordered = list(scopes)
    return [(ordered[0], ordered[1])] if len(ordered) >= 2 else []


def _scope_for_pair(
    rankings_dir: Path,
    *,
    players: int,
    x_col: str,
    y_col: str,
) -> str:
    scopes = infer_rank_column_scopes(rankings_dir, players)
    x_scope = scopes.get(str(x_col))
    y_scope = scopes.get(str(y_col))
    if x_scope is None or y_scope is None:
        raise ValueError(f"unknown rank column pair: {x_col}, {y_col}")
    if x_scope != y_scope:
        raise ValueError(f"rank columns must share the same scope: {x_col}, {y_col}")
    return x_scope


def _rule_corr_method(config_path: Path | None, *, default: str = "spearman") -> str:
    config = load_yaml_config(config_path)
    section = config.get("rule_corr_heatmap")
    if not isinstance(section, dict):
        return str(default)
    raw = section.get("method", default)
    return str(raw)


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


def render_synthetic_rank_heatmaps(
    *,
    players: int,
    rankings_dir: Path | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    dpi: int | None = None,
) -> RenderedSyntheticRankHeatmaps:
    """Render pairwise synthetic rank heatmaps from rankings CSV files."""

    base_out = Path(out_dir) if out_dir is not None else _default_output_base(config_path)
    resolved_rankings_dir = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    heatmaps_dir = base_out / "heatmaps" / f"n{int(players)}"
    if not resolved_rankings_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {resolved_rankings_dir}")

    effective_dpi = int(dpi) if dpi is not None else _default_figures_dpi(config_path)
    pairs = _default_rank_heatmap_pairs(
        resolved_rankings_dir,
        players=int(players),
        config_path=config_path,
    )
    written_paths: list[Path] = []
    for x_col, y_col in pairs:
        scope = _scope_for_pair(
            resolved_rankings_dir,
            players=int(players),
            x_col=x_col,
            y_col=y_col,
        )
        summary = collect_rank_pairs(
            resolved_rankings_dir,
            int(players),
            x_col=x_col,
            y_col=y_col,
            scope=scope,
        )
        if summary.matrix.empty or summary.total_pairs <= 0:
            continue
        out_path = heatmaps_dir / f"{x_col}_vs_{y_col}.png"
        title = f"{y_col} vs {x_col} (n={int(players)})"
        written_paths.append(
            render_rank_pair_heatmap(
                summary.matrix,
                out_path,
                x_col=x_col,
                y_col=y_col,
                dpi=effective_dpi,
                title=title,
            )
        )

    return RenderedSyntheticRankHeatmaps(
        rankings_dir=resolved_rankings_dir,
        heatmaps_dir=heatmaps_dir,
        written_paths=tuple(written_paths),
        pairs=tuple(pairs),
    )


def render_synthetic_rule_correlation_heatmaps(
    *,
    players: int,
    rankings_dir: Path | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    dpi: int | None = None,
    method: str | None = None,
) -> RenderedSyntheticRuleCorrelationHeatmaps:
    """Render rule-by-rule synthetic rank-correlation heatmaps."""

    base_out = Path(out_dir) if out_dir is not None else _default_output_base(config_path)
    resolved_rankings_dir = Path(rankings_dir) if rankings_dir is not None else base_out / "rankings"
    heatmaps_dir = base_out / "heatmaps" / f"n{int(players)}"
    if not resolved_rankings_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {resolved_rankings_dir}")

    effective_dpi = int(dpi) if dpi is not None else _default_figures_dpi(config_path)
    effective_method = str(method) if method is not None else _rule_corr_method(config_path)
    scopes = infer_rank_column_scopes(resolved_rankings_dir, int(players))
    written_paths: list[Path] = []

    player_cols = [name for name, scope in scopes.items() if scope == "player"]
    if player_cols:
        player_corr = collect_rule_correlation_matrix(
            resolved_rankings_dir,
            int(players),
            rank_cols=player_cols,
            scope="player",
            method=effective_method,
        )
        if not player_corr.empty:
            written_paths.append(
                render_correlation_heatmap(
                    player_corr,
                    heatmaps_dir / "rule_corr_player.png",
                    dpi=effective_dpi,
                    title="Rule Rank Correlation",
                )
            )

    coalition_cols = [name for name, scope in scopes.items() if scope == "coalition"]
    if coalition_cols:
        coalition_corr = collect_rule_correlation_matrix(
            resolved_rankings_dir,
            int(players),
            rank_cols=coalition_cols,
            scope="coalition",
            method=effective_method,
        )
        if not coalition_corr.empty:
            written_paths.append(
                render_correlation_heatmap(
                    coalition_corr,
                    heatmaps_dir / "rule_corr_coalition.png",
                    dpi=effective_dpi,
                    title="Rule Rank Correlation",
                )
            )

    return RenderedSyntheticRuleCorrelationHeatmaps(
        rankings_dir=resolved_rankings_dir,
        heatmaps_dir=heatmaps_dir,
        written_paths=tuple(written_paths),
        method=effective_method,
    )


__all__ = [
    "RenderedSyntheticFigures",
    "RenderedSyntheticRankHeatmaps",
    "RenderedSyntheticRuleCorrelationHeatmaps",
    "render_synthetic_figures",
    "render_synthetic_rank_heatmaps",
    "render_synthetic_rule_correlation_heatmaps",
]
