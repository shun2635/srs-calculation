"""General figure rendering adapter."""

from __future__ import annotations

from pathlib import Path

from ..datasets import read_feature_labels_yaml


def _player_columns(columns) -> list[str]:
    return [str(column) for column in columns if str(column).startswith("player")]


def _filter_by_coalition_size(df, player_cols: list[str], *, max_size: int):
    if max_size <= 0:
        return df.iloc[0:0].copy()
    filtered = df.copy()
    sizes = None
    for column in player_cols:
        values = filtered[column].fillna(0).astype(int).clip(lower=0, upper=1)
        sizes = values if sizes is None else (sizes + values)
    if sizes is None:
        return filtered
    filtered["_coalition_size"] = sizes
    return filtered[filtered["_coalition_size"] <= int(max_size)].drop(columns=["_coalition_size"])


def _coalition_label(row, player_cols: list[str], player_names: list[str] | None) -> str:
    members: list[str] = []
    for index, column in enumerate(player_cols, start=1):
        try:
            value = int(row[column])
        except Exception:
            value = 0
        if value != 0:
            if player_names is not None and 0 <= index - 1 < len(player_names):
                members.append(player_names[index - 1])
            else:
                members.append(str(index))
    return "{" + ",".join(members) + "}"


def _format_score_cell(value: object) -> str:
    try:
        numeric = float(value)
    except Exception:
        return ""
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.10g}"


def _canonical_rank_column_order(columns: list[str]) -> list[str]:
    preferred = [
        "rank_shapley",
        "rank_banzhaf",
        "rank_lexcel",
        "rank_o-banzhaf",
    ]
    ordered = [column for column in preferred if column in columns]
    ordered.extend(column for column in columns if column not in ordered)
    return ordered


def generate_real_ranking_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 150,
    max_coalition_size: int = 3,
) -> Path:
    """Render one table-style overview figure from a rankings CSV."""

    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.read_csv(rankings_csv)
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda item: int(str(item.player).replace("player", "")))
        player_names = [item.label or item.column for item in ordered]

    filtered = _filter_by_coalition_size(df, player_cols, max_size=int(max_coalition_size))
    rank_cols = _canonical_rank_column_order([str(column) for column in filtered.columns if str(column).startswith("rank_")])

    rows: list[list[str]] = []
    for _, row in filtered.iterrows():
        coalition = _coalition_label(row, player_cols, player_names)
        base_rank = "" if pd.isna(row.get("rank")) else str(int(float(row["rank"])))
        base_score = _format_score_cell(row.get("score"))
        derived = []
        for column in rank_cols:
            value = row.get(column)
            derived.append("" if pd.isna(value) else str(int(float(value))))
        rows.append([coalition, base_rank, base_score, *derived])

    if not rows:
        raise ValueError("no rows available for figure rendering")

    rows = rows[:30]
    column_labels = ["coalition", "rank", "score", *rank_cols]
    fig_width = max(8.0, 1.5 * len(column_labels))
    fig_height = max(3.5, 0.35 * (len(rows) + 1))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    ax.axis("off")
    ax.set_title(rankings_csv.stem)
    table = ax.table(
        cellText=rows,
        colLabels=column_labels,
        loc="center",
        cellLoc="center",
        colLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.15)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{rankings_csv.stem}.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


__all__ = ["generate_real_ranking_figure"]
