"""Application use cases for real-data plotting workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ...infrastructure.datasets import resolve_real_dataset_out_base
from ...infrastructure.plotting import (
    generate_give_topk_table,
    generate_interaction_index_figure,
    generate_kset_rank_occurrence_distribution_heatmap,
    generate_lexcel_rank_count_heatmap,
    generate_ordinal_banzhaf_values_plot,
    generate_rank_occurrence_distribution_heatmap,
    generate_real_ranking_figure,
    generate_red_index_scatter_plot,
    generate_red_index_topk_by_size_figures,
    generate_rp_index_top_size2_figure,
    generate_shapley_values_plot,
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


def _load_figures_config(dataset_out_base: Path) -> dict[str, object]:
    schema_path = dataset_out_base / "schema.yaml"
    if not schema_path.exists():
        return {}
    try:
        schema = _load_schema_yaml(schema_path)
    except Exception:
        return {}
    figures = schema.get("figures")
    if not isinstance(figures, dict):
        return {}
    return {str(key): value for key, value in figures.items()}


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

    figures_config = _load_figures_config(dataset_out_base)
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

    canonical_rankings_csv = resolved_rankings_dir / f"game_{dataset_id}.csv"
    if canonical_rankings_csv.exists():
        disable_red_index_figures = bool(figures_config.get("disable_red_index_figures", False)) or bool(
            figures_config.get("disable_red_index_tables", False)
        )
        occ_mode = str(figures_config.get("rank_occurrence_mode", "count")).strip().lower()
        occ_size2 = bool(figures_config.get("rank_occurrence_size2", False))
        occ_size3 = bool(figures_config.get("rank_occurrence_size3", False))
        occ_xlabel = figures_config.get("rank_occurrence_xlabel")
        occ_ylabel = figures_config.get("rank_occurrence_ylabel")
        occ_title = figures_config.get("rank_occurrence_title")
        occ_size2_xlabel = figures_config.get("rank_occurrence_size2_xlabel")
        occ_size2_focus_features = figures_config.get("rank_occurrence_size2_focus_features")
        interaction_index_size2 = bool(figures_config.get("interaction_index_size2", False))
        interaction_index_size3 = bool(figures_config.get("interaction_index_size3", False))

        try:
            written_paths.append(
                generate_interaction_index_figure(
                    rankings_csv=canonical_rankings_csv,
                    output_dir=resolved_figures_dir,
                    dpi=int(dpi),
                    top_k=30,
                )
            )
        except Exception:
            pass
        if interaction_index_size2:
            try:
                written_paths.append(
                    generate_interaction_index_figure(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                        top_k=30,
                        max_coalition_size=2,
                        out_name="interaction_index_size2.png",
                        include_game_score=True,
                        include_game_rank=True,
                    )
                )
            except Exception:
                pass
        if interaction_index_size3:
            try:
                written_paths.append(
                    generate_interaction_index_figure(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                        top_k=30,
                        max_coalition_size=3,
                        out_name="interaction_index_size3.png",
                    )
                )
            except Exception:
                pass

        if not disable_red_index_figures:
            try:
                written_paths.extend(
                    generate_red_index_topk_by_size_figures(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                        top_k=10,
                    )
                )
            except Exception:
                pass
            try:
                written_paths.append(
                    generate_red_index_scatter_plot(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                    )
                )
            except Exception:
                pass

        for generator in (
            generate_shapley_values_plot,
            generate_ordinal_banzhaf_values_plot,
        ):
            try:
                written_paths.append(
                    generator(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                    )
                )
            except Exception:
                pass

        try:
            if occ_mode == "proportion":
                written_paths.append(
                    generate_rank_occurrence_distribution_heatmap(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                        out_name="lexcel_rank_counts.png",
                        x_label=str(occ_xlabel) if occ_xlabel is not None else None,
                        y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                        title=str(occ_title) if occ_title is not None else None,
                    )
                )
            else:
                written_paths.append(
                    generate_lexcel_rank_count_heatmap(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                    )
                )
        except Exception:
            pass

        if occ_size2:
            try:
                if occ_mode == "proportion":
                    written_paths.append(
                        generate_kset_rank_occurrence_distribution_heatmap(
                            rankings_csv=canonical_rankings_csv,
                            output_dir=resolved_figures_dir,
                            dpi=int(dpi),
                            out_name="lexcel_rank_counts_size2.png",
                            subset_size=2,
                            x_label=str(occ_size2_xlabel) if occ_size2_xlabel is not None else None,
                            y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                            title=str(occ_title) if occ_title is not None else None,
                            focus_features=tuple(str(item) for item in occ_size2_focus_features)
                            if isinstance(occ_size2_focus_features, (list, tuple))
                            else None,
                        )
                    )
                else:
                    written_paths.append(
                        generate_rank_occurrence_distribution_heatmap(
                            rankings_csv=canonical_rankings_csv,
                            output_dir=resolved_figures_dir,
                            dpi=int(dpi),
                            out_name="lexcel_rank_counts_size2.png",
                            coalition_size=2,
                            x_label=str(occ_xlabel) if occ_xlabel is not None else None,
                            y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                            title=str(occ_title) if occ_title is not None else None,
                        )
                    )
            except Exception:
                pass
        if occ_size3:
            try:
                written_paths.append(
                    generate_rank_occurrence_distribution_heatmap(
                        rankings_csv=canonical_rankings_csv,
                        output_dir=resolved_figures_dir,
                        dpi=int(dpi),
                        out_name="lexcel_rank_counts_size3.png",
                        coalition_size=3,
                        x_label=str(occ_xlabel) if occ_xlabel is not None else None,
                        y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                        title=str(occ_title) if occ_title is not None else None,
                    )
                )
            except Exception:
                pass

        try:
            written_paths.append(
                generate_rp_index_top_size2_figure(
                    rankings_csv=canonical_rankings_csv,
                    output_dir=resolved_figures_dir,
                    dpi=int(dpi),
                    top_k=10,
                    coalition_size=2,
                )
            )
        except Exception:
            pass
        try:
            written_paths.append(
                generate_give_topk_table(
                    rankings_csv=canonical_rankings_csv,
                    output_dir=resolved_figures_dir,
                    dpi=int(dpi),
                    top_k=10,
                )
            )
        except Exception:
            pass
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
