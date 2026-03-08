"""Feature × rule rank heatmap for a real dataset."""

from __future__ import annotations

from pathlib import Path

import click
import yaml

from gamegen.display_names import rank_column_display_name

from ..datasets import resolve_dataset_dir, resolve_dataset_out_base
from ..heatmaps import render_feature_rule_rank_heatmap


def _load_schema_yaml(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items()}


def _default_max_coalition_size(*, dataset_id: str, base_out: Path) -> int:
    default = 2
    schema_out = base_out / "schema.yaml"
    if schema_out.exists():
        try:
            schema = _load_schema_yaml(schema_out)
            heatmaps = schema.get("heatmaps")
            if isinstance(heatmaps, dict) and "feature_rule_max_coalition_size" in heatmaps:
                return int(heatmaps["feature_rule_max_coalition_size"])
        except Exception:
            pass
    try:
        dataset_dir = resolve_dataset_dir(dataset_id, inputs_root=None)
        schema_in = dataset_dir / "schema.yaml"
        if schema_in.exists():
            schema = _load_schema_yaml(schema_in)
            heatmaps = schema.get("heatmaps")
            if isinstance(heatmaps, dict) and "feature_rule_max_coalition_size" in heatmaps:
                return int(heatmaps["feature_rule_max_coalition_size"])
    except Exception:
        pass
    return int(default)


@click.command(name="feature-rule-heatmap")
@click.argument("dataset_id", type=str)
@click.option("--out", "out_root", type=click.Path(path_type=Path), default=None, help="Output root (default: outputs/real/<dataset_id>).")
@click.option("--dpi", type=click.IntRange(72, 600), default=200, show_default=True)
@click.option(
    "--max-coalition-size",
    type=click.IntRange(1, 30),
    default=None,
    help="Show coalitions up to this size (rows). If omitted, use schema heatmaps.feature_rule_max_coalition_size (default: 2).",
)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def feature_rule_heatmap(
    dataset_id: str,
    out_root: Path | None,
    dpi: int,
    max_coalition_size: int | None,
    config_path: Path | None,
) -> None:
    """Render a heatmap (rows=features, cols=rules, cell=rank) for singleton coalitions."""
    base_out = resolve_dataset_out_base(dataset_id, out_root=out_root, config_path=config_path)
    rankings_csv = base_out / "rankings" / f"game_{dataset_id}.csv"
    features_yaml = base_out / "rankings" / f"game_{dataset_id}.features.yaml"
    if not rankings_csv.exists():
        raise click.ClickException(f"rankings CSV not found: {rankings_csv}")
    if not features_yaml.exists():
        raise click.ClickException(f"features mapping not found: {features_yaml}")

    heatmap_dir = base_out / "heatmaps"
    heatmap_dir.mkdir(parents=True, exist_ok=True)
    out_path = heatmap_dir / "feature_rule_rank.png"

    max_size = int(max_coalition_size) if max_coalition_size is not None else _default_max_coalition_size(dataset_id=str(dataset_id), base_out=base_out)
    render_feature_rule_rank_heatmap(
        rankings_csv=rankings_csv,
        features_yaml=features_yaml,
        out_path=out_path,
        dpi=int(dpi),
        max_coalition_size=int(max_size),
        rule_labeler=rank_column_display_name,
    )
    click.echo(f"saved heatmap: {out_path}")


__all__ = ["feature_rule_heatmap"]
