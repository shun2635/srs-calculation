"""Render PNG figures for real-data rankings."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from ..figures_png import (
    generate_interaction_index_figure,
    generate_lexcel_rank_count_heatmap,
    generate_give_topk_table,
    generate_ordinal_banzhaf_values_plot,
    generate_real_ranking_figure,
    generate_rank_occurrence_distribution_heatmap,
    generate_kset_rank_occurrence_distribution_heatmap,
    generate_red_index_scatter_plot,
    generate_red_index_topk_by_size_figures,
    generate_rp_index_top_size2_figure,
    generate_shapley_values_plot,
)
from ..datasets import resolve_dataset_dir, resolve_dataset_out_base


def _load_schema_yaml(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items()}


def _load_figures_config(*, dataset_id: str, base_out: Path) -> dict[str, object]:
    """Load dataset-scoped figures config.

    Preference order:
    1) outputs/real/<dataset_id>/schema.yaml:figures (reproducible snapshot)
    2) inputs/feature_mask_tables/<dataset_id>/schema.yaml:figures (authoritative during iteration)
    """
    out_figures: dict[str, object] = {}
    schema_out = base_out / "schema.yaml"
    if schema_out.exists():
        try:
            schema = _load_schema_yaml(schema_out)
            figures = schema.get("figures")
            if isinstance(figures, dict):
                out_figures = {str(k): v for k, v in figures.items()}
        except Exception:
            pass

    in_figures: dict[str, object] = {}
    try:
        dataset_dir = resolve_dataset_dir(dataset_id, inputs_root=None)
        schema_in = dataset_dir / "schema.yaml"
        if schema_in.exists():
            schema = _load_schema_yaml(schema_in)
            figures = schema.get("figures")
            if isinstance(figures, dict):
                in_figures = {str(k): v for k, v in figures.items()}
    except Exception:
        pass

    # Prefer reproducibility but allow iterating by letting input keys override output snapshot keys.
    return {**out_figures, **in_figures}


@click.command(name="make-figures")
@click.argument("dataset_id", type=str)
@click.option("--out", "out_root", type=click.Path(path_type=Path), default=None, help="Output root (default: outputs/real/<dataset_id>).")
@click.option("--dpi", type=click.IntRange(72, 600), default=150, show_default=True)
@click.option(
    "--max-coalition-size",
    type=click.IntRange(1, 30),
    default=3,
    show_default=True,
    help="Visualization-only filter: show coalitions up to this size.",
)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing PNG files.")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def make_figures(dataset_id: str, out_root: Path | None, dpi: int, max_coalition_size: int, force: bool, config_path: Path | None) -> None:
    """Render PNG figures for a dataset under outputs/real/<dataset_id>/rankings/."""
    base_out = resolve_dataset_out_base(dataset_id, out_root=out_root, config_path=config_path)
    rankings_root = base_out / "rankings"
    if not rankings_root.exists():
        raise click.ClickException(f"Rankings directory not found: {rankings_root}")

    figures_base = base_out / "figures"
    figures_base.mkdir(parents=True, exist_ok=True)

    figures_cfg = _load_figures_config(dataset_id=str(dataset_id), base_out=base_out)

    disable_red_index_figures = bool(figures_cfg.get("disable_red_index_figures", False)) or bool(
        figures_cfg.get("disable_red_index_tables", False)
    )
    occ_mode = str(figures_cfg.get("rank_occurrence_mode", "count")).strip().lower()
    occ_size2 = bool(figures_cfg.get("rank_occurrence_size2", False))
    occ_size3 = bool(figures_cfg.get("rank_occurrence_size3", False))
    occ_xlabel = figures_cfg.get("rank_occurrence_xlabel")
    occ_ylabel = figures_cfg.get("rank_occurrence_ylabel")
    occ_title = figures_cfg.get("rank_occurrence_title")
    occ_size2_xlabel = figures_cfg.get("rank_occurrence_size2_xlabel")
    occ_size2_focus_features = figures_cfg.get("rank_occurrence_size2_focus_features")
    interaction_index_size2 = bool(figures_cfg.get("interaction_index_size2", False))
    interaction_index_size3 = bool(figures_cfg.get("interaction_index_size3", False))

    written = 0
    extra_written = 0

    # If configured, ensure red-index PNGs are not present in the output.
    if force and disable_red_index_figures:
        for p in figures_base.glob("red_index_*.png"):
            try:
                p.unlink()
            except Exception:
                pass
    for rankings_csv in sorted(rankings_root.glob("game_*.csv")):
        target = figures_base / (rankings_csv.stem + ".png")
        if target.exists() and not force:
            continue
        generate_real_ranking_figure(
            rankings_csv=rankings_csv,
            output_dir=figures_base,
            dpi=dpi,
            max_coalition_size=int(max_coalition_size),
        )
        written += 1

    # Extra figure: interaction indices top-k table (best-effort; only for the canonical game_<dataset_id>.csv).
    try:
        canonical = rankings_root / f"game_{dataset_id}.csv"
        if canonical.exists():
            out_png = figures_base / "interaction_index.png"
            if force or not out_png.exists():
                generate_interaction_index_figure(
                    rankings_csv=canonical,
                    output_dir=figures_base,
                    dpi=int(dpi),
                    top_k=30,
                    max_coalition_size=3 if str(dataset_id) == "crop" else None,
                    exclude_feature_substrings=("降水量",) if str(dataset_id) == "crop" else (),
                    out_name="interaction_index.png",
                )
                extra_written += 1
            if interaction_index_size2:
                out_png2 = figures_base / "interaction_index_size2.png"
                if force or not out_png2.exists():
                    generate_interaction_index_figure(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                        top_k=30,
                        max_coalition_size=2,
                        out_name="interaction_index_size2.png",
                        include_game_score=True,
                        include_game_rank=True,
                    )
                    extra_written += 1
            if interaction_index_size3:
                out_png3 = figures_base / "interaction_index_size3.png"
                if force or not out_png3.exists():
                    generate_interaction_index_figure(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                        top_k=30,
                        max_coalition_size=3,
                        out_name="interaction_index_size3.png",
                    )
                    extra_written += 1
    except Exception:
        pass

    # Extra figures: red-index top-k per coalition size (best-effort; wine use-case).
    try:
        if not disable_red_index_figures:
            canonical = rankings_root / f"game_{dataset_id}.csv"
            if canonical.exists():
                if force:
                    for p in figures_base.glob("red_index_top*_k*.png"):
                        try:
                            p.unlink()
                        except Exception:
                            pass
                paths = generate_red_index_topk_by_size_figures(
                    rankings_csv=canonical,
                    output_dir=figures_base,
                    dpi=int(dpi),
                    top_k=10,
                )
                extra_written += len(paths)
    except Exception:
        pass

    # Extra figure: red-index scatter plot (best-effort; requires score_red-index).
    try:
        if not disable_red_index_figures:
            canonical = rankings_root / f"game_{dataset_id}.csv"
            if canonical.exists():
                out_png = figures_base / "red_index_scatter.png"
                if force or not out_png.exists():
                    generate_red_index_scatter_plot(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                    )
                    extra_written += 1
    except Exception:
        pass

    # Extra figure: feature × Shapley values (best-effort; requires score_shapley).
    try:
        canonical = rankings_root / f"game_{dataset_id}.csv"
        if canonical.exists():
            out_png = figures_base / "shapley_values.png"
            if force or not out_png.exists():
                generate_shapley_values_plot(
                    rankings_csv=canonical,
                    output_dir=figures_base,
                    dpi=int(dpi),
                )
                extra_written += 1
    except Exception:
        pass

    # Extra figure: feature × Ordinal Banzhaf scores (best-effort; requires rank with full coalitions).
    try:
        canonical = rankings_root / f"game_{dataset_id}.csv"
        if canonical.exists():
            out_png = figures_base / "ordinal_banzhaf_values.png"
            if force or not out_png.exists():
                generate_ordinal_banzhaf_values_plot(
                    rankings_csv=canonical,
                    output_dir=figures_base,
                    dpi=int(dpi),
                )
                extra_written += 1
    except Exception:
        pass

    # Extra figure: feature × Lexcel-rank occurrence counts (best-effort; requires rank_lexcel).
    try:
        canonical = rankings_root / f"game_{dataset_id}.csv"
        if canonical.exists():
            if occ_mode == "proportion":
                # Keep legacy filename but change semantics to normalized distribution for this dataset.
                out_png = figures_base / "lexcel_rank_counts.png"
                if force or not out_png.exists():
                    generate_rank_occurrence_distribution_heatmap(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                        out_name="lexcel_rank_counts.png",
                        x_label=str(occ_xlabel) if occ_xlabel is not None else None,
                        y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                        title=str(occ_title) if occ_title is not None else None,
                    )
                    extra_written += 1
                if occ_size2:
                    out_png2 = figures_base / "lexcel_rank_counts_size2.png"
                    if force or not out_png2.exists():
                        generate_kset_rank_occurrence_distribution_heatmap(
                            rankings_csv=canonical,
                            output_dir=figures_base,
                            dpi=int(dpi),
                            out_name="lexcel_rank_counts_size2.png",
                            subset_size=2,
                            x_label=str(occ_size2_xlabel) if occ_size2_xlabel is not None else None,
                            y_label=str(occ_ylabel) if occ_ylabel is not None else None,
                            title=str(occ_title) if occ_title is not None else None,
                            focus_features=(
                                [str(x) for x in occ_size2_focus_features]
                                if isinstance(occ_size2_focus_features, (list, tuple))
                                else None
                            ),
                            require_all_members_in_focus=True,
                        )
                        extra_written += 1
                if occ_size3:
                    out_png3 = figures_base / "lexcel_rank_counts_size3.png"
                    if force or not out_png3.exists():
                        generate_kset_rank_occurrence_distribution_heatmap(
                            rankings_csv=canonical,
                            output_dir=figures_base,
                            dpi=int(dpi),
                            out_name="lexcel_rank_counts_size3.png",
                            subset_size=3,
                        )
                        extra_written += 1
            else:
                out_png = figures_base / "lexcel_rank_counts.png"
                if force or not out_png.exists():
                    generate_lexcel_rank_count_heatmap(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                        out_name="lexcel_rank_counts.png",
                    )
                    extra_written += 1
    except Exception:
        pass

    # Extra figure: Give (引き上げ) top-k table (best-effort; requires rank + singletons).
    try:
        canonical = rankings_root / f"game_{dataset_id}.csv"
        if canonical.exists():
            out_png = figures_base / "give_top10.png"
            if force or not out_png.exists():
                generate_give_topk_table(
                    rankings_csv=canonical,
                    output_dir=figures_base,
                    dpi=int(dpi),
                    top_k=10,
                    out_name="give_top10.png",
                )
                extra_written += 1
    except Exception:
        pass

    # Extra figure (crop): RP Index top-10 size-2 coalitions.
    try:
        if str(dataset_id) == "crop":
            canonical = rankings_root / f"game_{dataset_id}.csv"
            if canonical.exists():
                out_png = figures_base / "rp_index_top_size2_k10.png"
                if force or not out_png.exists():
                    generate_rp_index_top_size2_figure(
                        rankings_csv=canonical,
                        output_dir=figures_base,
                        dpi=int(dpi),
                        top_k=10,
                        coalition_size=2,
                        out_name="rp_index_top_size2_k10.png",
                    )
                    extra_written += 1
    except Exception:
        pass

    suffix = f" (+{extra_written} extra)" if extra_written else ""
    click.echo(f"wrote {written} figure(s){suffix} for dataset={dataset_id}")


__all__ = ["make_figures"]
