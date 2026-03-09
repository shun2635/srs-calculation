"""Application use cases for real-data plotting workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ...infrastructure.datasets import resolve_real_dataset_out_base
from ...infrastructure.plotting import (
    generate_real_ranking_figure,
    render_feature_rule_rank_heatmap,
)


@dataclass(frozen=True)
class RenderedRealDatasetFigures:
    """Summary of figure files produced for one dataset."""

    dataset_id: str
    dataset_out_base: Path
    rankings_dir: Path
    figures_dir: Path
    written_paths: tuple[Path, ...]


@dataclass(frozen=True)
class RenderedRealDatasetHeatmap:
    """Summary of one feature-rule heatmap render."""

    dataset_id: str
    dataset_out_base: Path
    rankings_csv: Path
    features_yaml: Path
    out_path: Path


def _load_schema_yaml(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def _default_max_coalition_size(dataset_out_base: Path) -> int:
    schema_path = dataset_out_base / "schema.yaml"
    if not schema_path.exists():
        return 2
    try:
        schema = _load_schema_yaml(schema_path)
        heatmaps = schema.get("heatmaps")
        if isinstance(heatmaps, dict) and "feature_rule_max_coalition_size" in heatmaps:
            return int(heatmaps["feature_rule_max_coalition_size"])
    except Exception:
        return 2
    return 2


def _default_rule_label(column_name: str) -> str:
    return str(column_name).removeprefix("rank_")


def render_real_dataset_figures(
    dataset_id: str,
    *,
    out_root: Path | None = None,
    rankings_dir: Path | None = None,
    figures_dir: Path | None = None,
    dpi: int = 150,
    max_coalition_size: int = 3,
) -> RenderedRealDatasetFigures:
    """Render the canonical table-style ranking figures for one dataset."""

    dataset_out_base = resolve_real_dataset_out_base(dataset_id, out_root=out_root)
    resolved_rankings_dir = rankings_dir if rankings_dir is not None else dataset_out_base / "rankings"
    resolved_figures_dir = figures_dir if figures_dir is not None else dataset_out_base / "figures"
    if not resolved_rankings_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {resolved_rankings_dir}")

    written_paths: list[Path] = []
    for rankings_csv in sorted(resolved_rankings_dir.glob("game_*.csv")):
        if not rankings_csv.is_file():
            continue
        written_paths.append(
            generate_real_ranking_figure(
                rankings_csv=rankings_csv,
                output_dir=resolved_figures_dir,
                dpi=int(dpi),
                max_coalition_size=int(max_coalition_size),
            )
        )
    return RenderedRealDatasetFigures(
        dataset_id=str(dataset_id),
        dataset_out_base=dataset_out_base,
        rankings_dir=resolved_rankings_dir,
        figures_dir=resolved_figures_dir,
        written_paths=tuple(written_paths),
    )


def render_real_dataset_feature_rule_heatmap(
    dataset_id: str,
    *,
    out_root: Path | None = None,
    rankings_csv: Path | None = None,
    features_yaml: Path | None = None,
    out_path: Path | None = None,
    dpi: int = 200,
    max_coalition_size: int | None = None,
) -> RenderedRealDatasetHeatmap:
    """Render the feature-rule heatmap for one dataset."""

    dataset_out_base = resolve_real_dataset_out_base(dataset_id, out_root=out_root)
    resolved_rankings_csv = rankings_csv if rankings_csv is not None else dataset_out_base / "rankings" / f"game_{dataset_id}.csv"
    resolved_features_yaml = features_yaml if features_yaml is not None else resolved_rankings_csv.with_suffix(".features.yaml")
    resolved_out_path = out_path if out_path is not None else dataset_out_base / "heatmaps" / "feature_rule_rank.png"

    if not resolved_rankings_csv.exists():
        raise FileNotFoundError(f"rankings CSV not found: {resolved_rankings_csv}")
    if not resolved_features_yaml.exists():
        raise FileNotFoundError(f"features mapping not found: {resolved_features_yaml}")

    render_feature_rule_rank_heatmap(
        rankings_csv=resolved_rankings_csv,
        features_yaml=resolved_features_yaml,
        out_path=resolved_out_path,
        dpi=int(dpi),
        max_coalition_size=int(max_coalition_size) if max_coalition_size is not None else _default_max_coalition_size(dataset_out_base),
        rule_labeler=_default_rule_label,
    )
    return RenderedRealDatasetHeatmap(
        dataset_id=str(dataset_id),
        dataset_out_base=dataset_out_base,
        rankings_csv=resolved_rankings_csv,
        features_yaml=resolved_features_yaml,
        out_path=resolved_out_path,
    )


__all__ = [
    "RenderedRealDatasetFigures",
    "RenderedRealDatasetHeatmap",
    "render_real_dataset_feature_rule_heatmap",
    "render_real_dataset_figures",
]
