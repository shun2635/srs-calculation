"""Figure rendering adapters for synthetic and real-data workflows."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Sequence

from ..datasets import read_feature_labels_yaml


def _player_columns(columns) -> list[str]:
    return [str(column) for column in columns if str(column).startswith("player")]


def _feature_names(rankings_csv: Path, player_count: int) -> list[str]:
    feature_names = [f"player{index + 1}" for index in range(player_count)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if not features_path.exists():
        return feature_names
    items = read_feature_labels_yaml(features_path)
    ordered = sorted(items, key=lambda item: int(str(item.player).replace("player", "")))
    return [item.label or item.column for item in ordered]


def _read_rankings_df(rankings_csv: Path):
    import pandas as pd

    return pd.read_csv(rankings_csv)


def _mask_from_row(row, player_cols: list[str]) -> int:
    mask = 0
    for index, column in enumerate(player_cols):
        try:
            value = int(row[column])
        except Exception:
            value = 0
        if value != 0:
            mask |= 1 << index
    return int(mask)


def _coalition_label(row, player_cols: list[str], player_names: list[str]) -> str:
    members: list[str] = []
    for index, column in enumerate(player_cols):
        try:
            value = int(row[column])
        except Exception:
            value = 0
        if value != 0:
            members.append(player_names[index])
    return "{" + ",".join(members) + "}"


def _mask_label(mask: int, player_names: list[str]) -> str:
    members = [player_names[index] for index in range(len(player_names)) if (int(mask) >> index) & 1]
    return "{" + ",".join(members) + "}"


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
        "rank_g-shapley",
        "rank_g-sum-shapley",
        "rank_shapley-interaction",
        "rank_banzhaf-interaction",
        "rank_rankdiff",
        "rank_ud",
        "rank_du",
        "rank_red-index",
        "rank_g-lexcel",
        "rank_g-o-banzhaf",
    ]
    ordered = [column for column in preferred if column in columns]
    ordered.extend(column for column in columns if column not in ordered)
    return ordered


@dataclass(frozen=True)
class _SyntheticTableSpec:
    title: str
    col_labels: list[str]
    rows: list[list[str]]


def _synthetic_coalition_label(row, player_cols: list[str]) -> str:
    members: list[str] = []
    for index, column in enumerate(player_cols, start=1):
        try:
            value = int(row[column])
        except Exception:
            value = 0
        if value != 0:
            members.append(str(index))
    return "{" + ",".join(members) + "}"


def _synthetic_table_col_widths(spec: _SyntheticTableSpec) -> list[float]:
    widths: list[float] = []
    for column_index, label in enumerate(spec.col_labels):
        max_len = len(str(label))
        for row in spec.rows:
            if column_index < len(row):
                max_len = max(max_len, len(str(row[column_index])))
        if str(label) in {"team", "player(s)"}:
            widths.append(max(4.0, float(max_len) * 0.75))
        elif str(label) in {"rank", "score"}:
            widths.append(max(2.8, float(max_len) * 0.6))
        else:
            widths.append(max(5.0, float(max_len)))
    total = sum(widths) or 1.0
    return [width / total for width in widths]


def _render_horizontal_tables(
    *,
    out_path: Path,
    tables: list[_SyntheticTableSpec],
    dpi: int,
) -> Path:
    import matplotlib.pyplot as plt

    if not tables:
        raise ValueError("no tables available for rendering")

    table_count = len(tables)
    max_rows = max((len(spec.rows) for spec in tables), default=1)
    fig_width = max(4.0, 4.2 * table_count)
    fig_height = max(3.0, min(max_rows, 50) * 0.6 + 0.6)
    fig, axes = plt.subplots(1, table_count, figsize=(fig_width, fig_height), constrained_layout=True)
    if table_count == 1:
        axes = [axes]

    for ax, spec in zip(axes, tables):
        ax.axis("off")
        table = ax.table(
            cellText=spec.rows,
            colLabels=spec.col_labels,
            loc="center",
            cellLoc="center",
            colLoc="center",
            colWidths=_synthetic_table_col_widths(spec),
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, 1.25)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _synthetic_team_performance_table(df, player_cols: list[str], *, limit: int | None) -> _SyntheticTableSpec:
    import pandas as pd

    dfx = df.copy()
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx["score"] = pd.to_numeric(dfx["score"], errors="coerce")
    dfx = dfx.sort_values(["rank", "score"], ascending=[True, False], kind="mergesort")
    if limit is not None:
        dfx = dfx.head(limit)

    rows: list[list[str]] = []
    for _, row in dfx.iterrows():
        rows.append(
            [
                _synthetic_coalition_label(row, player_cols),
                "" if pd.isna(row["rank"]) else str(int(float(row["rank"]))),
                _format_score_cell(row["score"]),
            ]
        )
    return _SyntheticTableSpec(
        title="team ranking",
        col_labels=["team", "rank", "score"],
        rows=rows,
    )


def _synthetic_contribution_table(
    df,
    player_cols: list[str],
    *,
    rank_column: str,
    limit: int | None,
) -> _SyntheticTableSpec | None:
    import pandas as pd

    if rank_column not in df.columns:
        return None
    dfx = df.copy()
    dfx[rank_column] = pd.to_numeric(dfx[rank_column], errors="coerce")
    dfx = dfx[pd.notna(dfx[rank_column])]
    if dfx.empty:
        return None

    def _sort_key(record: dict[str, object]) -> tuple[int, int, list[int]]:
        members: list[int] = []
        for index, column in enumerate(player_cols, start=1):
            try:
                value = int(record[column])  # type: ignore[arg-type]
            except Exception:
                value = 0
            if value != 0:
                members.append(index)
        return (int(float(record[rank_column])), len(members), members)

    records = sorted(dfx.to_dict("records"), key=_sort_key)
    rows: list[list[str]] = []
    for record in records[:limit]:
        series = pd.Series(record)
        rows.append(
            [
                _synthetic_coalition_label(series, player_cols),
                str(int(float(record[rank_column]))),
            ]
        )
    return _SyntheticTableSpec(
        title=rank_column,
        col_labels=["player(s)", rank_column],
        rows=rows,
    )


def _render_table_figure(
    *,
    out_path: Path,
    title: str,
    column_labels: list[str],
    rows: list[list[str]],
    dpi: int,
) -> Path:
    import matplotlib.pyplot as plt

    if not rows:
        raise ValueError("no rows available for table rendering")

    fig_width = max(7.0, 1.5 * len(column_labels))
    fig_height = max(3.5, 0.35 * (len(rows) + 1))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    ax.axis("off")
    ax.set_title(title)
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _render_bar_chart(
    *,
    out_path: Path,
    title: str,
    x_labels: list[str],
    values: list[float],
    y_label: str,
    dpi: int,
) -> Path:
    import matplotlib.pyplot as plt

    fig_width = max(6.0, 0.7 * len(x_labels) + 2.0)
    fig_height = 4.5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    ax.bar(range(len(x_labels)), values)
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _render_heatmap(
    *,
    out_path: Path,
    title: str,
    matrix,
    row_labels: list[str],
    column_labels: list[str],
    dpi: int,
    colorbar_label: str,
) -> Path:
    import matplotlib.pyplot as plt

    fig_width = max(6.0, 0.7 * len(column_labels) + 2.0)
    fig_height = max(4.0, 0.35 * len(row_labels) + 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.03, pad=0.02, label=colorbar_label)
    ax.set_title(title)
    ax.set_xticks(range(len(column_labels)))
    ax.set_xticklabels(column_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels)

    for row_index in range(len(row_labels)):
        for column_index in range(len(column_labels)):
            value = matrix[row_index][column_index]
            ax.text(column_index, row_index, f"{float(value):.2g}", ha="center", va="center", fontsize=7, color="black")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _singleton_values_from_column(df, player_cols: list[str], value_column: str) -> list[float]:
    import pandas as pd

    filtered = df.copy()
    for column in player_cols:
        filtered[column] = pd.to_numeric(filtered[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    filtered[value_column] = pd.to_numeric(filtered[value_column], errors="coerce")
    filtered = filtered[pd.notna(filtered[value_column])]
    sizes = filtered[player_cols].sum(axis=1).astype(int)
    filtered = filtered[sizes == 1]
    values = [0.0] * len(player_cols)
    for _, row in filtered.iterrows():
        for index, column in enumerate(player_cols):
            if int(row[column]) != 0:
                values[index] = float(row[value_column])
                break
    return values


def _level_of_mask_from_rank(df, player_cols: list[str]) -> dict[int, int]:
    import pandas as pd

    filtered = df.copy()
    for column in player_cols:
        filtered[column] = pd.to_numeric(filtered[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    filtered["rank"] = pd.to_numeric(filtered["rank"], errors="coerce")
    filtered = filtered[pd.notna(filtered["rank"])]
    rank_by_mask: dict[int, int] = {}
    for _, row in filtered.iterrows():
        rank_by_mask[_mask_from_row(row, player_cols)] = int(float(row["rank"]))
    ordered = sorted(rank_by_mask.items(), key=lambda item: (item[1], item[0]))
    return {mask: index + 1 for index, (mask, _rank) in enumerate(ordered)}


def _ordinal_banzhaf_scores_from_level_map(level_of_mask: dict[int, int], player_count: int) -> list[float]:
    scores = [0.0] * player_count
    coalition_count = 1 << player_count
    for base_mask in range(coalition_count):
        if base_mask not in level_of_mask:
            continue
        base_level = level_of_mask[base_mask]
        for player in range(player_count):
            if (base_mask >> player) & 1:
                continue
            with_player = base_mask | (1 << player)
            if with_player not in level_of_mask:
                continue
            candidate = level_of_mask[with_player]
            if candidate < base_level:
                scores[player] += 1.0
            elif candidate > base_level:
                scores[player] -= 1.0
    return scores


def _theta_vectors(level_of_mask: dict[int, int], player_count: int) -> list[list[int]]:
    level_count = max(level_of_mask.values(), default=0)
    theta = [[0 for _ in range(level_count)] for _ in range(player_count)]
    for mask, level in level_of_mask.items():
        if mask == 0:
            continue
        level_index = int(level) - 1
        for player in range(player_count):
            if (int(mask) >> player) & 1:
                theta[player][level_index] += 1
    return theta


def generate_synthetic_ranking_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 150,
) -> Path:
    """Render one compatibility-format synthetic ranking PNG from a rankings CSV."""

    df = _read_rankings_df(rankings_csv)
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    row_limit = 30 if len(player_cols) >= 8 else None
    rank_columns = _canonical_rank_column_order(
        [str(column) for column in df.columns if str(column).startswith("rank_")]
    )

    tables: list[_SyntheticTableSpec] = [
        _synthetic_team_performance_table(df, player_cols, limit=row_limit)
    ]
    for rank_column in rank_columns:
        table = _synthetic_contribution_table(
            df,
            player_cols,
            rank_column=rank_column,
            limit=row_limit,
        )
        if table is not None:
            tables.append(table)

    return _render_horizontal_tables(
        out_path=output_dir / f"{rankings_csv.stem}.png",
        tables=tables,
        dpi=dpi,
    )


def generate_real_ranking_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 150,
    max_coalition_size: int = 3,
) -> Path:
    """Render one table-style overview figure from a rankings CSV."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    player_names = _feature_names(rankings_csv, len(player_cols))
    filtered = _filter_by_coalition_size(df, player_cols, max_size=int(max_coalition_size))
    rank_cols = _canonical_rank_column_order(
        [str(column) for column in filtered.columns if str(column).startswith("rank_")]
    )

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

    return _render_table_figure(
        out_path=output_dir / f"{rankings_csv.stem}.png",
        title=rankings_csv.stem,
        column_labels=["coalition", "rank", "score", *rank_cols],
        rows=rows[:30],
        dpi=dpi,
    )


def generate_interaction_index_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 30,
    max_coalition_size: int | None = None,
    exclude_feature_substrings: Sequence[str] = (),
    out_name: str = "interaction_index.png",
    include_game_score: bool = False,
    include_game_rank: bool = False,
) -> Path:
    """Write interaction-index top-k coalition tables as one PNG."""

    import matplotlib.pyplot as plt
    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    player_names = _feature_names(rankings_csv, len(player_cols))
    specs = [
        ("Shapley Interaction", "rank_shapley-interaction", "score_shapley-interaction"),
        ("Banzhaf Interaction", "rank_banzhaf-interaction", "score_banzhaf-interaction"),
        ("Rankdiff", "rank_rankdiff", "score_rankdiff"),
    ]
    available = [(title, rank_col, score_col) for title, rank_col, score_col in specs if rank_col in df.columns]
    if not available:
        raise ValueError("No interaction index rank columns found in rankings CSV.")

    fig, axes = plt.subplots(1, len(available), figsize=(max(12.0, 6.5 * len(available)), max(6.0, 0.25 * (int(top_k) + 4))), constrained_layout=True)
    if len(available) == 1:
        axes = [axes]

    for ax, (title, rank_col, score_col) in zip(axes, available):
        dfx = df.copy()
        dfx[rank_col] = pd.to_numeric(dfx[rank_col], errors="coerce")
        dfx = dfx[pd.notna(dfx[rank_col])]
        dfx["_mask"] = dfx.apply(lambda row: _mask_from_row(row, player_cols), axis=1)
        dfx = dfx[dfx["_mask"] != 0]
        if max_coalition_size is not None:
            dfx["_size"] = dfx["_mask"].apply(lambda mask: int(mask).bit_count())
            dfx = dfx[dfx["_size"] <= int(max_coalition_size)]
        if exclude_feature_substrings:
            banned_mask = 0
            for index, name in enumerate(player_names):
                if any(fragment in str(name) for fragment in exclude_feature_substrings):
                    banned_mask |= 1 << index
            if banned_mask:
                dfx = dfx[(dfx["_mask"].astype(int) & int(banned_mask)) == 0]
        dfx = dfx.sort_values([rank_col, "_mask"], ascending=[True, True], kind="mergesort").head(int(top_k))

        rows: list[list[str]] = []
        for _, row in dfx.iterrows():
            cells = [_coalition_label(row, player_cols, player_names), str(int(float(row[rank_col])))]
            if score_col in dfx.columns and not pd.isna(row.get(score_col)):
                cells.append(_format_score_cell(row.get(score_col)))
            if include_game_score and "score" in dfx.columns and not pd.isna(row.get("score")):
                cells.append(_format_score_cell(row.get("score")))
            if include_game_rank and "rank" in dfx.columns and not pd.isna(row.get("rank")):
                cells.append(str(int(float(row["rank"]))))
            rows.append(cells)

        ax.axis("off")
        if not rows:
            ax.set_title(f"{title} (no data)")
            continue
        labels = ["coalition", "rank"]
        if score_col in dfx.columns:
            labels.append("score")
        if include_game_score:
            labels.append("game_score")
        if include_game_rank:
            labels.append("game_rank")
        table = ax.table(cellText=rows, colLabels=labels, loc="center", cellLoc="center", colLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.12)
        ax.set_title(title)

    out_path = output_dir / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_red_index_topk_by_size_figures(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 30,
) -> list[Path]:
    """Write per-coalition-size red-index top-k tables."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "score_red-index" not in df.columns:
        raise ValueError("score_red-index column not found (apply red-index rule first).")

    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    player_names = _feature_names(rankings_csv, len(player_cols))

    dfx = df.copy()
    dfx["score_red-index"] = pd.to_numeric(dfx["score_red-index"], errors="coerce")
    dfx = dfx[pd.notna(dfx["score_red-index"])]
    dfx["_mask"] = dfx.apply(lambda row: _mask_from_row(row, player_cols), axis=1)
    dfx = dfx[dfx["_mask"] != 0]
    dfx["_size"] = dfx["_mask"].apply(lambda mask: int(mask).bit_count())
    written: list[Path] = []
    for size in range(1, len(player_cols) + 1):
        subset = dfx[dfx["_size"] == size].sort_values(["score_red-index", "_mask"], ascending=[False, True], kind="mergesort").head(int(top_k))
        if subset.empty:
            continue
        rows = [
            [_coalition_label(row, player_cols, player_names), _format_score_cell(row["score_red-index"])]
            for _, row in subset.iterrows()
        ]
        written.append(
            _render_table_figure(
                out_path=output_dir / f"red_index_top{size:02d}_k{int(top_k)}.png",
                title=f"Red Index top-{int(top_k)} (|S|={size})",
                column_labels=["coalition", "score_red-index"],
                rows=rows,
                dpi=dpi,
            )
        )
    return written


def generate_red_index_scatter_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a scatter plot for coalition size versus red-index score."""

    import matplotlib.pyplot as plt
    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "score_red-index" not in df.columns:
        raise ValueError("score_red-index column not found (apply red-index rule first).")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    dfx = df.copy()
    for column in player_cols:
        dfx[column] = pd.to_numeric(dfx[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["score_red-index"] = pd.to_numeric(dfx["score_red-index"], errors="coerce")
    dfx = dfx[pd.notna(dfx["score_red-index"])]
    dfx["_mask"] = dfx.apply(lambda row: _mask_from_row(row, player_cols), axis=1)
    dfx = dfx[dfx["_mask"] != 0]
    if dfx.empty:
        raise ValueError("no non-empty coalitions with score_red-index found")

    sizes = dfx[player_cols].sum(axis=1).astype(int)
    fig, ax = plt.subplots(figsize=(7.0, 5.0), constrained_layout=True)
    ax.scatter(sizes.to_numpy(), dfx["score_red-index"].astype(float).to_numpy(), s=12, alpha=0.3, edgecolors="none")
    ax.set_xlabel("coalition size")
    ax.set_ylabel("score_red-index")
    ax.set_title("Red Index scatter")
    ax.grid(True, axis="y", alpha=0.2)

    out_path = output_dir / "red_index_scatter.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_shapley_values_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a feature-by-Shapley-value bar plot."""

    df = _read_rankings_df(rankings_csv)
    if "score_shapley" not in df.columns:
        raise ValueError("score_shapley column not found (apply shapley rule first).")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    values = _singleton_values_from_column(df, player_cols, "score_shapley")
    return _render_bar_chart(
        out_path=output_dir / "shapley_values.png",
        title="Shapley values",
        x_labels=_feature_names(rankings_csv, len(player_cols)),
        values=values,
        y_label="score_shapley",
        dpi=dpi,
    )


def generate_ordinal_banzhaf_values_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a feature-by-ordinal-Banzhaf-score bar plot."""

    df = _read_rankings_df(rankings_csv)
    if "rank" not in df.columns:
        raise ValueError("rank column not found (need coalition ordinal levels).")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    level_of_mask = _level_of_mask_from_rank(df, player_cols)
    scores = _ordinal_banzhaf_scores_from_level_map(level_of_mask, len(player_cols))
    return _render_bar_chart(
        out_path=output_dir / "ordinal_banzhaf_values.png",
        title="Ordinal Banzhaf values",
        x_labels=_feature_names(rankings_csv, len(player_cols)),
        values=scores,
        y_label="ordinal_banzhaf",
        dpi=dpi,
    )


def generate_lexcel_rank_count_heatmap(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    out_name: str = "lexcel_rank_counts.png",
) -> Path:
    """Write Lexcel theta-vector heatmap."""

    df = _read_rankings_df(rankings_csv)
    if "rank" not in df.columns:
        raise ValueError("rankings CSV missing rank column")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")
    level_of_mask = _level_of_mask_from_rank(df, player_cols)
    theta = _theta_vectors(level_of_mask, len(player_cols))
    if not theta or not theta[0]:
        raise ValueError("no levels found")
    level_labels = [f"L{index + 1}" for index in range(len(theta[0]))]
    matrix = list(map(list, zip(*theta)))
    return _render_heatmap(
        out_path=output_dir / out_name,
        title="Lexcel rank counts",
        matrix=matrix,
        row_labels=level_labels,
        column_labels=_feature_names(rankings_csv, len(player_cols)),
        dpi=dpi,
        colorbar_label="count",
    )


def generate_rankdiff_top_size2_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 10,
    coalition_size: int = 2,
    out_name: str = "rankdiff_top_size2_k10.png",
) -> Path:
    """Write a top-k table of coalitions ranked by Rankdiff."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "rank_rankdiff" not in df.columns:
        raise ValueError("rank_rankdiff column not found (apply rankdiff rule first).")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    player_names = _feature_names(rankings_csv, len(player_cols))

    dfx = df.copy()
    dfx["rank_rankdiff"] = pd.to_numeric(dfx["rank_rankdiff"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank_rankdiff"])]
    dfx["_mask"] = dfx.apply(lambda row: _mask_from_row(row, player_cols), axis=1)
    dfx["_size"] = dfx["_mask"].apply(lambda mask: int(mask).bit_count())
    dfx = dfx[(dfx["_mask"] != 0) & (dfx["_size"] == int(coalition_size))]
    if dfx.empty:
        raise ValueError(f"no coalitions found for |S|={int(coalition_size)}")
    dfx = dfx.sort_values(["rank_rankdiff", "_mask"], ascending=[True, True], kind="mergesort").head(int(top_k))

    rows = []
    for _, row in dfx.iterrows():
        cells = [_coalition_label(row, player_cols, player_names), str(int(float(row["rank_rankdiff"])))]
        if "score_rankdiff" in dfx.columns:
            cells.append(_format_score_cell(row.get("score_rankdiff")))
        rows.append(cells)

    labels = ["coalition", "rank_rankdiff"]
    if "score_rankdiff" in dfx.columns:
        labels.append("score_rankdiff")
    return _render_table_figure(
        out_path=output_dir / out_name,
        title=f"Rankdiff top-{int(top_k)} (|S|={int(coalition_size)})",
        column_labels=labels,
        rows=rows,
        dpi=dpi,
    )


def generate_give_topk_table(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 10,
    out_name: str = "give_top10.png",
) -> Path:
    """Write a top-k table ordered by give(T)."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "rank" not in df.columns:
        raise ValueError("rank column not found")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    player_names = _feature_names(rankings_csv, len(player_cols))

    dfx = df.copy()
    for column in player_cols:
        dfx[column] = pd.to_numeric(dfx[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank"])]

    singleton_rank: dict[int, int] = {}
    for _, row in dfx.iterrows():
        mask = _mask_from_row(row, player_cols)
        if mask != 0 and (mask & (mask - 1)) == 0:
            singleton_rank[int(mask).bit_length() - 1] = int(float(row["rank"]))

    scored_rows: list[tuple[int, int, str, int]] = []
    for _, row in dfx.iterrows():
        mask = _mask_from_row(row, player_cols)
        if mask == 0:
            continue
        rank = int(float(row["rank"]))
        give = 0
        for player in range(len(player_cols)):
            if (mask >> player) & 1 and rank < singleton_rank.get(player, 10**9):
                give += 1
        scored_rows.append((give, mask, _coalition_label(row, player_cols, player_names), rank))
    scored_rows.sort(key=lambda item: (-item[0], item[1]))

    rows = [[label, str(give), str(rank)] for give, _mask, label, rank in scored_rows[: int(top_k)]]
    return _render_table_figure(
        out_path=output_dir / out_name,
        title=f"Give top-{int(top_k)}",
        column_labels=["coalition", "give", "rank"],
        rows=rows,
        dpi=dpi,
    )


def generate_rank_occurrence_distribution_heatmap(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    out_name: str = "rank_occurrence_distribution.png",
    coalition_size: int | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    title: str | None = None,
) -> Path:
    """Write per-feature rank-occurrence distribution heatmap."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "rank" not in df.columns:
        raise ValueError("rankings CSV missing rank column")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")

    dfx = df.copy()
    for column in player_cols:
        dfx[column] = pd.to_numeric(dfx[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank"])]
    if coalition_size is not None:
        dfx["_size"] = dfx[player_cols].sum(axis=1).astype(int)
        dfx = dfx[dfx["_size"] == int(coalition_size)]

    rank_levels = sorted({int(float(value)) for value in dfx["rank"].tolist()})
    feature_names = _feature_names(rankings_csv, len(player_cols))
    matrix = []
    for rank_level in rank_levels:
        row = []
        subset = dfx[dfx["rank"] == int(rank_level)]
        for column in player_cols:
            denominator = int(dfx[column].sum())
            numerator = int(subset[column].sum())
            row.append(0.0 if denominator <= 0 else numerator / float(denominator))
        matrix.append(row)

    out_path = _render_heatmap(
        out_path=output_dir / out_name,
        title=title or "Rank occurrence distribution",
        matrix=matrix,
        row_labels=[str(level) for level in rank_levels],
        column_labels=feature_names,
        dpi=dpi,
        colorbar_label="proportion",
    )
    return out_path


def generate_kset_rank_occurrence_distribution_heatmap(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    out_name: str,
    subset_size: int,
    x_label: str | None = None,
    y_label: str | None = None,
    title: str | None = None,
    focus_features: Sequence[str] | None = None,
    require_all_members_in_focus: bool = False,
) -> Path:
    """Write rank-occurrence distribution heatmap for k-sets."""

    import pandas as pd

    df = _read_rankings_df(rankings_csv)
    if "rank" not in df.columns:
        raise ValueError("rankings CSV missing rank column")
    player_cols = _player_columns(df.columns)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")
    feature_names = _feature_names(rankings_csv, len(player_cols))

    dfx = df.copy()
    for column in player_cols:
        dfx[column] = pd.to_numeric(dfx[column], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank"])]

    focus = {str(item) for item in focus_features or []}
    subset_masks: list[tuple[int, str]] = []
    for combo in combinations(range(len(player_cols)), int(subset_size)):
        combo_names = [feature_names[index] for index in combo]
        if focus:
            in_focus = [name in focus for name in combo_names]
            if require_all_members_in_focus and not all(in_focus):
                continue
            if not require_all_members_in_focus and not any(in_focus):
                continue
        mask = 0
        for index in combo:
            mask |= 1 << index
        subset_masks.append((mask, "{" + ",".join(combo_names) + "}"))
    if not subset_masks:
        raise ValueError("no k-sets available for the requested focus")

    rank_levels = sorted({int(float(value)) for value in dfx["rank"].tolist()})
    matrix = []
    for rank_level in rank_levels:
        row = []
        rank_subset = dfx[dfx["rank"] == int(rank_level)]
        for mask, _label in subset_masks:
            count_all = 0
            count_rank = 0
            for _, item in dfx.iterrows():
                coalition_mask = _mask_from_row(item, player_cols)
                if coalition_mask & mask == mask:
                    count_all += 1
            for _, item in rank_subset.iterrows():
                coalition_mask = _mask_from_row(item, player_cols)
                if coalition_mask & mask == mask:
                    count_rank += 1
            row.append(0.0 if count_all <= 0 else count_rank / float(count_all))
        matrix.append(row)

    return _render_heatmap(
        out_path=output_dir / out_name,
        title=title or f"Rank occurrence distribution for |S|={int(subset_size)}",
        matrix=matrix,
        row_labels=[str(level) for level in rank_levels],
        column_labels=[label for _mask, label in subset_masks],
        dpi=dpi,
        colorbar_label="proportion",
    )


__all__ = [
    "generate_give_topk_table",
    "generate_interaction_index_figure",
    "generate_kset_rank_occurrence_distribution_heatmap",
    "generate_lexcel_rank_count_heatmap",
    "generate_rank_occurrence_distribution_heatmap",
    "generate_real_ranking_figure",
    "generate_red_index_scatter_plot",
    "generate_red_index_topk_by_size_figures",
    "generate_rankdiff_top_size2_figure",
    "generate_shapley_values_plot",
    "generate_ordinal_banzhaf_values_plot",
    "generate_synthetic_ranking_figure",
]
