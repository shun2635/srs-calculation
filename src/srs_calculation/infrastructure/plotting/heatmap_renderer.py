"""Heatmap rendering adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..datasets import read_feature_labels_yaml


def _coalition_label_from_mask(mask: int, feature_names: list[str]) -> str:
    members = [name for index, name in enumerate(feature_names) if (int(mask) >> index) & 1]
    return "{" + ",".join(members) + "}"


def feature_rule_rank_table(
    *,
    rankings_csv: Path,
    features_yaml: Path,
    max_coalition_size: int = 2,
    rule_labeler: Callable[[str], str] | None = None,
):
    """Return a matrix for the real-data feature-rule heatmap."""

    import pandas as pd

    df = pd.read_csv(rankings_csv)
    player_cols = [str(column) for column in df.columns if str(column).startswith("player")]
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")

    rank_cols = [str(column) for column in df.columns if str(column).startswith("rank_")]
    if not rank_cols:
        raise ValueError("rankings CSV has no rank_* columns")

    items = read_feature_labels_yaml(features_yaml)
    ordered = sorted(items, key=lambda item: int(str(item.player).replace("player", "")))
    feature_names = [item.label or item.column for item in ordered]

    sizes = None
    for column in player_cols:
        values = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
        sizes = values if sizes is None else (sizes + values)
    if sizes is None:
        raise ValueError("rankings CSV missing usable player columns")

    masks = None
    for index, column in enumerate(player_cols):
        values = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
        term = values.astype(int) * (1 << index)
        masks = term if masks is None else (masks + term)
    assert masks is not None

    filtered = df.copy()
    filtered["_size"] = sizes.astype(int)
    filtered["_mask"] = masks.astype(int)
    filtered = filtered[(filtered["_size"] >= 1) & (filtered["_size"] <= int(max_coalition_size))]
    if filtered.empty:
        raise ValueError("no coalitions found for requested max size")

    filtered = filtered.sort_values(["_size", "_mask"], ascending=[True, True], kind="mergesort")
    row_labels = [_coalition_label_from_mask(int(mask), feature_names) for mask in filtered["_mask"].tolist()]
    matrix = filtered[rank_cols].apply(pd.to_numeric, errors="coerce")
    matrix.index = row_labels
    matrix = matrix[~matrix.index.duplicated(keep="first")]

    column_labels = [rule_labeler(column) if rule_labeler is not None else column for column in matrix.columns]
    return matrix, feature_names, column_labels


def normalize_ranks_per_rule(matrix):
    """Normalize each rank column independently to the [0, 1] range."""

    import pandas as pd

    normalized = matrix.copy()
    for column in normalized.columns:
        series = pd.to_numeric(normalized[column], errors="coerce")
        valid = series.dropna()
        if valid.empty:
            continue
        minimum = float(valid.min())
        maximum = float(valid.max())
        if minimum == maximum:
            normalized[column] = series.apply(lambda value: 0.5 if pd.notna(value) else float("nan"))
        else:
            normalized[column] = (series - minimum) / (maximum - minimum)
    return normalized


def render_feature_rule_rank_heatmap(
    *,
    rankings_csv: Path,
    features_yaml: Path,
    out_path: Path,
    dpi: int,
    max_coalition_size: int = 2,
    rule_labeler: Callable[[str], str] | None = None,
) -> None:
    """Render the feature-by-rule rank heatmap PNG."""

    import matplotlib.pyplot as plt
    import pandas as pd

    matrix, _feature_names, column_labels = feature_rule_rank_table(
        rankings_csv=rankings_csv,
        features_yaml=features_yaml,
        max_coalition_size=int(max_coalition_size),
        rule_labeler=rule_labeler,
    )
    normalized = normalize_ranks_per_rule(matrix)

    fig_width = max(6.0, 0.6 * len(column_labels) + 2.0)
    fig_height = max(4.0, 0.35 * len(matrix.index) + 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    ax.set_title(f"Feature sets vs rule ranks (|S| <= {int(max_coalition_size)})")

    values = matrix.to_numpy()
    colors = normalized.to_numpy()
    image = ax.imshow(colors, aspect="auto", interpolation="nearest", cmap="Blues_r", vmin=0.0, vmax=1.0)
    fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02, label="normalized rank within rule (0=best)")

    ax.set_xticks(range(len(column_labels)))
    ax.set_xticklabels(column_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(list(matrix.index))

    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            value = values[row_index, column_index]
            if pd.isna(value):
                continue
            ax.text(column_index, row_index, str(int(value)), ha="center", va="center", fontsize=7, color="black")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


__all__ = [
    "feature_rule_rank_table",
    "normalize_ranks_per_rule",
    "render_feature_rule_rank_heatmap",
]
