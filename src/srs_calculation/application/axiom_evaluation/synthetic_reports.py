"""Synthetic-workflow axiom summaries."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ...domain.axioms import AxiomEvaluationResult
from ...domain.games.coalition_game import CoalitionGame
from ...domain.ranking.registry import build_default_ranking_rule_registry
from ...infrastructure.config import load_yaml_config
from ...infrastructure.persistence import get_compatible_ranking_rule_spec, read_compatible_game_csv
from ...infrastructure.plotting import render_axiom_summary_heatmap
from ..ranking.apply_ranking_rules import apply_ranking_rules
from ..synthetic_workflow import resolve_synthetic_output_layout
from .evaluate_axioms import evaluate_axioms_for_results

AxiomScope = Literal["coalition", "individual"]


@dataclass(frozen=True)
class SyntheticAxiomScopeReport:
    """Materialized axiom artifacts for one scope."""

    scope: AxiomScope
    scope_dir: Path
    written_count_paths: tuple[Path, ...]
    summary_csv_path: Path | None
    summary_heatmap_path: Path | None
    evaluated_rule_ids: tuple[str, ...]
    evaluated_axiom_ids: tuple[str, ...]
    skipped_reason: str | None = None


@dataclass(frozen=True)
class EvaluatedSyntheticAxioms:
    """Summary of synthetic axiom evaluation outputs."""

    games_dir: Path
    rankings_dir: Path
    reports: tuple[SyntheticAxiomScopeReport, ...]


@dataclass(frozen=True)
class RenderedSyntheticAxiomSummaryHeatmaps:
    """Rendered axiom summary heatmaps."""

    written_paths: tuple[Path, ...]
    scope_dirs: tuple[Path, ...]


def _default_figures_dpi(config_path: Path | None, *, default: int = 150) -> int:
    config = load_yaml_config(config_path)
    figures = config.get("figures")
    if not isinstance(figures, dict):
        return int(default)
    try:
        return int(figures.get("png_dpi", default))
    except Exception:
        return int(default)


def _selected_scopes(scope: str) -> tuple[AxiomScope, ...]:
    normalized = str(scope).strip().lower()
    if normalized == "all":
        return ("coalition", "individual")
    if normalized in {"coalition", "individual"}:
        return (normalized,)  # type: ignore[return-value]
    raise ValueError("scope must be one of: coalition, individual, all")


def _rule_ids_present_in_rankings_csv(rankings_csv_path: Path) -> list[str]:
    with rankings_csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"rankings CSV is empty: {rankings_csv_path}") from exc

    present_rank_columns = {str(name) for name in header if str(name).startswith("rank_")}
    rule_ids: list[str] = []
    registry = build_default_ranking_rule_registry()
    for rule_id in registry.list_rule_ids():
        spec = get_compatible_ranking_rule_spec(rule_id)
        if spec.rank_column_name in present_rank_columns:
            rule_ids.append(rule_id)
    return rule_ids


def _write_axiom_counts_csv(path: Path, rows: list[tuple[str, int, int, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["game", "constraints", "satisfied", "satisfied_rate"])
        for game_name, constraints, satisfied, rate in rows:
            writer.writerow([game_name, int(constraints), int(satisfied), str(rate)])
    return path


def _write_summary_csv(path: Path, rows: list[tuple[str, str, int, int, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["rule", "axiom", "constraints", "satisfied", "satisfied_rate"])
        for rule_id, axiom_id, constraints, satisfied, rate in rows:
            writer.writerow([str(rule_id), str(axiom_id), int(constraints), int(satisfied), str(rate)])
    return path


def _empty_scope_report(scope_dir: Path, scope: AxiomScope, *, reason: str) -> SyntheticAxiomScopeReport:
    return SyntheticAxiomScopeReport(
        scope=scope,
        scope_dir=scope_dir,
        written_count_paths=(),
        summary_csv_path=None,
        summary_heatmap_path=None,
        evaluated_rule_ids=(),
        evaluated_axiom_ids=(),
        skipped_reason=reason,
    )


def _evaluate_scope_for_game(
    *,
    scope: AxiomScope,
    game: CoalitionGame,
    rule_ids: list[str],
) -> dict[str, dict[str, AxiomEvaluationResult]]:
    if scope == "individual":
        return {}
    results_by_rule = apply_ranking_rules(game, rule_ids)
    return evaluate_axioms_for_results(game, results_by_rule)


def evaluate_synthetic_axioms(
    *,
    players: int,
    games_dir: Path | None = None,
    rankings_dir: Path | None = None,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    constraints: tuple[str, ...] = (),
    profile: str | None = None,
    scope: str = "all",
    render_heatmaps: bool = True,
    dpi: int | None = None,
) -> EvaluatedSyntheticAxioms:
    """Evaluate synthetic ranking outputs against available axiom registries."""

    layout = resolve_synthetic_output_layout(
        out_dir=out_dir,
        config_path=config_path,
        constraints=constraints,
        profile=profile,
    )
    resolved_games_dir = Path(games_dir) if games_dir is not None else layout.games_dir(int(players))
    resolved_rankings_dir = Path(rankings_dir) if rankings_dir is not None else layout.rankings_dir(int(players))
    if not resolved_games_dir.exists():
        raise FileNotFoundError(f"games directory not found: {resolved_games_dir}")
    if not resolved_rankings_dir.exists():
        raise FileNotFoundError(f"rankings directory not found: {resolved_rankings_dir}")

    effective_dpi = int(dpi) if dpi is not None else _default_figures_dpi(config_path)
    reports: list[SyntheticAxiomScopeReport] = []

    rankings_files = [path for path in sorted(resolved_rankings_dir.glob("game_*.csv")) if path.is_file()]
    if not rankings_files:
        reports.append(
            _empty_scope_report(
                layout.axiom_scope_dir(int(players), "coalition"),
                "coalition",
                reason=f"no rankings CSV found under {resolved_rankings_dir}",
            )
        )
        return EvaluatedSyntheticAxioms(
            games_dir=resolved_games_dir,
            rankings_dir=resolved_rankings_dir,
            reports=tuple(reports),
        )

    for selected_scope in _selected_scopes(scope):
        scope_dir = layout.axiom_scope_dir(int(players), selected_scope)
        rows_by_axiom_and_rule: dict[tuple[str, str], list[tuple[str, int, int, str]]] = {}
        evaluated_rule_ids: set[str] = set()
        evaluated_axiom_ids: set[str] = set()

        for rankings_csv_path in rankings_files:
            game_csv_path = resolved_games_dir / rankings_csv_path.name
            if not game_csv_path.exists():
                raise FileNotFoundError(f"matching game CSV not found: {game_csv_path}")

            present_rule_ids = _rule_ids_present_in_rankings_csv(rankings_csv_path)
            if not present_rule_ids:
                continue
            game = read_compatible_game_csv(game_csv_path, require_complete=True)
            evaluations_by_rule = _evaluate_scope_for_game(
                scope=selected_scope,
                game=game,
                rule_ids=present_rule_ids,
            )
            for rule_id, evaluations_by_axiom in evaluations_by_rule.items():
                evaluated_rule_ids.add(str(rule_id))
                for axiom_id, evaluation in evaluations_by_axiom.items():
                    evaluated_axiom_ids.add(str(axiom_id))
                    rate = "0" if evaluation.constrained_comparisons <= 0 else f"{evaluation.satisfaction_ratio:.10g}"
                    rows_by_axiom_and_rule.setdefault((str(axiom_id), str(rule_id)), []).append(
                        (
                            rankings_csv_path.stem,
                            int(evaluation.constrained_comparisons),
                            int(evaluation.satisfied_comparisons),
                            rate,
                        )
                    )

        if not rows_by_axiom_and_rule:
            reports.append(
                _empty_scope_report(
                    scope_dir,
                    selected_scope,
                    reason=f"no axioms evaluated for scope={selected_scope}",
                )
            )
            continue

        written_count_paths: list[Path] = []
        summary_rows: list[tuple[str, str, int, int, str]] = []
        for (axiom_id, rule_id), rows in sorted(rows_by_axiom_and_rule.items()):
            written_count_paths.append(
                _write_axiom_counts_csv(
                    scope_dir / axiom_id / f"{rule_id}.csv",
                    rows,
                )
            )
            constraints_total = sum(int(row[1]) for row in rows)
            satisfied_total = sum(int(row[2]) for row in rows)
            rate = "0" if constraints_total <= 0 else f"{(satisfied_total / constraints_total):.10g}"
            summary_rows.append((rule_id, axiom_id, constraints_total, satisfied_total, rate))

        summary_csv_path = _write_summary_csv(scope_dir / "summary.csv", summary_rows)
        summary_heatmap_path = None
        if render_heatmaps:
            summary_heatmap_path = render_axiom_summary_heatmap(
                summary_csv_path,
                scope_dir / "summary_heatmap.png",
                dpi=effective_dpi,
                title=f"Axiom Satisfaction Rate ({selected_scope})",
            )

        reports.append(
            SyntheticAxiomScopeReport(
                scope=selected_scope,
                scope_dir=scope_dir,
                written_count_paths=tuple(written_count_paths),
                summary_csv_path=summary_csv_path,
                summary_heatmap_path=summary_heatmap_path,
                evaluated_rule_ids=tuple(sorted(evaluated_rule_ids)),
                evaluated_axiom_ids=tuple(sorted(evaluated_axiom_ids)),
            )
        )

    return EvaluatedSyntheticAxioms(
        games_dir=resolved_games_dir,
        rankings_dir=resolved_rankings_dir,
        reports=tuple(reports),
    )


def render_synthetic_axiom_summary_heatmaps(
    *,
    players: int,
    out_dir: Path | None = None,
    config_path: Path | None = None,
    constraints: tuple[str, ...] = (),
    profile: str | None = None,
    scope: str = "all",
    dpi: int | None = None,
) -> RenderedSyntheticAxiomSummaryHeatmaps:
    """Render summary heatmaps from previously materialized axiom summary CSVs."""

    layout = resolve_synthetic_output_layout(
        out_dir=out_dir,
        config_path=config_path,
        constraints=constraints,
        profile=profile,
    )
    effective_dpi = int(dpi) if dpi is not None else _default_figures_dpi(config_path)

    written_paths: list[Path] = []
    scope_dirs: list[Path] = []
    for selected_scope in _selected_scopes(scope):
        scope_dir = layout.axiom_scope_dir(int(players), selected_scope)
        summary_csv_path = scope_dir / "summary.csv"
        if not summary_csv_path.exists():
            continue
        scope_dirs.append(scope_dir)
        written_paths.append(
            render_axiom_summary_heatmap(
                summary_csv_path,
                scope_dir / "summary_heatmap.png",
                dpi=effective_dpi,
                title=f"Axiom Satisfaction Rate ({selected_scope})",
            )
        )

    return RenderedSyntheticAxiomSummaryHeatmaps(
        written_paths=tuple(written_paths),
        scope_dirs=tuple(scope_dirs),
    )


__all__ = [
    "EvaluatedSyntheticAxioms",
    "RenderedSyntheticAxiomSummaryHeatmaps",
    "SyntheticAxiomScopeReport",
    "evaluate_synthetic_axioms",
    "render_synthetic_axiom_summary_heatmaps",
]
