"""Heatmap renderers for realgen."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from .io.feature_labels import read_feature_labels_yaml
from .viz.fonts import set_japanese_font_if_available


def _coalition_sizes(df: pd.DataFrame, player_cols: list[str]) -> pd.Series:
    sizes = None
    for col in player_cols:
        v = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=1)
        sizes = v if sizes is None else (sizes + v)
    if sizes is None:
        return pd.Series([], dtype="int64")
    return sizes.astype(int)


def _mask_series(df: pd.DataFrame, player_cols: list[str]) -> pd.Series:
    bits = []
    for col in player_cols:
        bits.append(pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int).clip(0, 1))
    if not bits:
        return pd.Series([], dtype="int64")
    mask = None
    for i, b in enumerate(bits):
        term = b.astype(int) * (1 << i)
        mask = term if mask is None else (mask + term)
    assert mask is not None
    return mask.astype(int)


def _coalition_label_from_mask(mask: int, feature_names: list[str]) -> str:
    members = []
    for i, name in enumerate(feature_names):
        if (int(mask) >> i) & 1:
            members.append(str(name))
    return "{" + ",".join(members) + "}"


def feature_rule_rank_table(
    *,
    rankings_csv: Path,
    features_yaml: Path,
    max_coalition_size: int = 2,
    rule_labeler: Callable[[str], str] | None = None,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Return (table, feature_names, rule_labels) for the heatmap.

    Rows are all coalitions of size 1..max_coalition_size (excluding empty).
    Columns are all rank_* columns in the rankings CSV.
    """
    df = pd.read_csv(rankings_csv)
    player_cols = [c for c in df.columns if str(c).startswith("player")]
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")

    rank_cols = [c for c in df.columns if str(c).startswith("rank_")]
    if not rank_cols:
        raise ValueError("rankings CSV has no rank_* columns")

    items = read_feature_labels_yaml(features_yaml)
    ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
    feature_names = [it.label or it.description.split("（", 1)[0] or it.column for it in ordered]

    sizes = _coalition_sizes(df, player_cols)
    masks = _mask_series(df, player_cols)
    df2 = df.copy()
    df2["_size"] = sizes
    df2["_mask"] = masks
    df2 = df2[(df2["_size"] >= 1) & (df2["_size"] <= int(max_coalition_size))]
    if df2.empty:
        raise ValueError("no coalitions found for requested max size")

    # Deterministic row ordering: size asc, then mask asc.
    df2 = df2.sort_values(["_size", "_mask"], ascending=[True, True], kind="mergesort")
    row_labels = [_coalition_label_from_mask(int(m), feature_names) for m in df2["_mask"].tolist()]

    mat = df2[rank_cols].apply(pd.to_numeric, errors="coerce")
    mat.index = row_labels
    mat = mat[~mat.index.duplicated(keep="first")]

    col_labels = [rule_labeler(c) if rule_labeler is not None else c for c in mat.columns]
    return mat, feature_names, col_labels


def normalize_ranks_per_rule(mat: pd.DataFrame) -> pd.DataFrame:
    """Normalize ranks per column to [0,1] using that column's min..max.

    - Lower rank is better, so min(rank)=0 and max(rank)=1 after normalization.
    - Columns with constant non-null values are set to 0.5.
    - NaNs are preserved.
    """
    out = mat.copy()
    for col in out.columns:
        s = pd.to_numeric(out[col], errors="coerce")
        valid = s.dropna()
        if valid.empty:
            continue
        vmin = float(valid.min())
        vmax = float(valid.max())
        if vmax == vmin:
            out[col] = s.apply(lambda x: 0.5 if pd.notna(x) else float("nan"))
        else:
            out[col] = (s - vmin) / (vmax - vmin)
    return out


def render_feature_rule_rank_heatmap(
    *,
    rankings_csv: Path,
    features_yaml: Path,
    out_path: Path,
    dpi: int,
    max_coalition_size: int = 2,
    rule_labeler: Callable[[str], str] | None = None,
) -> None:
    import matplotlib.pyplot as plt

    set_japanese_font_if_available()

    mat, _feature_names, col_labels = feature_rule_rank_table(
        rankings_csv=rankings_csv,
        features_yaml=features_yaml,
        max_coalition_size=int(max_coalition_size),
        rule_labeler=rule_labeler,
    )
    norm = normalize_ranks_per_rule(mat)

    fig_w = max(6.0, 0.6 * len(col_labels) + 2.0)
    fig_h = max(4.0, 0.35 * len(mat.index) + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.set_title(f"特徴量セット×ルール順位（|S|<= {int(max_coalition_size)}）")

    # Per-rule (per-column) normalized colors so the scale adapts to each rule's rank range.
    data = mat.to_numpy()
    data_norm = norm.to_numpy()
    im = ax.imshow(data_norm, aspect="auto", interpolation="nearest", cmap="Blues_r", vmin=0.0, vmax=1.0)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="normalized rank within rule (0=best)")

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(mat.index)))
    ax.set_yticklabels(list(mat.index))

    # Annotate cells
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if pd.isna(v):
                continue
            ax.text(j, i, str(int(v)), ha="center", va="center", fontsize=7, color="black")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


__all__ = ["feature_rule_rank_table", "normalize_ranks_per_rule", "render_feature_rule_rank_heatmap"]
