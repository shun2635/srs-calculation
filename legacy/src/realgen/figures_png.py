"""Lightweight PNG figure generator for real-data rankings.

Unlike gamegen.figures_png, this module:
- does not depend on japanize_matplotlib
- can label coalitions by original feature column names via *.features.yaml
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import matplotlib.pyplot as plt
import pandas as pd

from gamegen.io.rankings_csv import RANK_COLUMN_ALIASES
from gamegen.rules.ordinal_banzhaf import ordinal_banzhaf_detail

from .io.feature_labels import read_feature_labels_yaml
from .viz.fonts import set_japanese_font_if_available


@dataclass(frozen=True)
class TableSpec:
    col_labels: Sequence[str]
    rows: Sequence[Sequence[str]]


def _players_columns(df: pd.DataFrame) -> List[str]:
    cols: List[str] = []
    for c in df.columns:
        if str(c).startswith("player"):
            cols.append(str(c))
        else:
            break
    return cols


def _filter_by_coalition_size(df: pd.DataFrame, player_cols: Sequence[str], *, max_size: int) -> pd.DataFrame:
    if max_size <= 0:
        return df.iloc[0:0].copy()
    dfx = df.copy()
    sizes = None
    for col in player_cols:
        v = pd.to_numeric(dfx[col], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=1)
        sizes = v if sizes is None else (sizes + v)
    if sizes is None:
        return dfx
    dfx["_coalition_size"] = sizes
    dfx = dfx[dfx["_coalition_size"] <= int(max_size)].drop(columns=["_coalition_size"])
    return dfx


def _coalition_label(row: pd.Series, player_cols: Sequence[str], player_names: Sequence[str] | None) -> str:
    members: List[str] = []
    for idx, col in enumerate(player_cols, start=1):
        try:
            v = int(row[col])
        except Exception:
            v = 0
        if v != 0:
            if player_names is not None and 0 <= (idx - 1) < len(player_names):
                members.append(str(player_names[idx - 1]))
            else:
                members.append(str(idx))
    return "{" + ",".join(members) + "}"


def _max_cell_len(tables: Sequence[TableSpec], *, col_index: int = 0) -> int:
    m = 0
    for t in tables:
        for row in t.rows:
            if col_index < len(row):
                m = max(m, len(str(row[col_index])))
    return m


def _format_score_cell(value: object) -> str:
    try:
        x = float(value)  # type: ignore[arg-type]
    except Exception:
        return ""
    if x.is_integer():
        return str(int(x))
    return f"{x:.10g}"


def _team_table(df: pd.DataFrame, player_cols: Sequence[str], player_names: Sequence[str] | None, limit: int | None) -> TableSpec:
    dfx = df.copy()
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx["score"] = pd.to_numeric(dfx["score"], errors="coerce")
    dfx = dfx.sort_values(["rank", "score"], ascending=[True, False], kind="mergesort")
    if limit is not None:
        dfx = dfx.head(limit)
    rows: List[List[str]] = []
    for _, r in dfx.iterrows():
        rows.append(
            [
                _coalition_label(r, player_cols, player_names),
                str(int(r["rank"])) if pd.notna(r["rank"]) else "",
                _format_score_cell(r["score"]) if pd.notna(r["score"]) else "",
            ]
        )
    return TableSpec(col_labels=["coalition", "rank", "score"], rows=rows)


def _contrib_table(df: pd.DataFrame, player_cols: Sequence[str], player_names: Sequence[str] | None, rank_col: str, limit: int | None) -> TableSpec | None:
    if rank_col not in df.columns:
        return None
    dfx = df.copy()
    dfx[rank_col] = pd.to_numeric(dfx[rank_col], errors="coerce")
    dfx = dfx[pd.notna(dfx[rank_col])]
    if dfx.empty:
        return None
    dfx = dfx.sort_values([rank_col], ascending=[True], kind="mergesort")
    rows: List[List[str]] = []
    for _, r in dfx.iterrows():
        rows.append([_coalition_label(r, player_cols, player_names), str(int(r[rank_col]))])
    if limit is not None:
        rows = rows[:limit]
    return TableSpec(col_labels=["coalition", rank_col], rows=rows)


def generate_real_ranking_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 150,
    max_coalition_size: int = 3,
) -> None:
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        player_names = [it.label or it.column for it in ordered]

    # Visualization-only filter: keep only coalitions up to max size (interpretability).
    df = _filter_by_coalition_size(df, player_cols, max_size=int(max_coalition_size))

    rank_cols = [c for c in df.columns if str(c).startswith("rank_")]
    # prefer compact set (personal then group)
    preferred = [
        "rank_shapley",
        "rank_banzhaf",
        "rank_lexcel",
        "rank_o-banzhaf",
        "rank_g-shapley",
        "rank_g-sum-shapley",
        "rank_shapley-interaction",
        "rank_banzhaf-interaction",
        "rank_rp-index",
        "rank_ud",
        "rank_du",
        "rank_red-index",
        "rank_g-lexcel",
        "rank_g-o-banzhaf",
    ]
    ordered_rank_cols = [c for c in preferred if c in rank_cols] + [c for c in rank_cols if c not in preferred]

    row_limit = 30 if len(player_cols) >= 8 else None
    tables: list[TableSpec] = [_team_table(df, player_cols, player_names, limit=row_limit)]
    for col in ordered_rank_cols:
        t = _contrib_table(df, player_cols, player_names, col, limit=row_limit)
        if t is not None:
            tables.append(t)

    n_tables = len(tables)
    max_rows = max((len(t.rows) for t in tables), default=0)
    max_coalition_len = _max_cell_len(tables, col_index=0)

    # Size heuristics:
    # - height: scale with row count to avoid vertical clipping
    # - width: widen per-table and additionally by maximum coalition-label length
    width = max(6.0, 5.2 * n_tables)
    width *= min(3.0, 1.0 + max(0.0, (max_coalition_len - 24) / 70.0))
    height = max(3.0, 0.28 * (max_rows + 1))
    fig, axes = plt.subplots(1, n_tables, figsize=(width, height), constrained_layout=True)
    if n_tables == 1:
        axes = [axes]  # type: ignore[assignment]

    for ax, spec in zip(axes, tables):
        ax.axis("off")
        table = ax.table(
            cellText=spec.rows,
            colLabels=list(spec.col_labels),
            loc="center",
            cellLoc="center",
            colLoc="center",
        )
        table.auto_set_font_size(False)
        fs = 8 if max_rows <= 80 else 7
        table.set_fontsize(fs)
        y_scale = 1.15 if max_rows <= 40 else 1.0
        # Widen the table horizontally so the coalition label fits without wrapping.
        x_scale = min(3.0, 1.0 + max(0.0, (_max_cell_len([spec], col_index=0) - 24) / 55.0))
        table.scale(x_scale, y_scale)
        # Also allocate more column width to the first (coalition) column.
        try:
            n_rows = len(spec.rows)
            n_cols = len(spec.col_labels)
            if n_rows >= 0 and n_cols >= 2:
                coalition_w = 0.75
                rest_w = (1.0 - coalition_w) / float(n_cols - 1)
                for r in range(0, n_rows + 1):  # include header row
                    table[(r, 0)].set_width(coalition_w)
                    for c in range(1, n_cols):
                        table[(r, c)].set_width(rest_w)
        except Exception:
            pass

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (rankings_csv.stem + ".png")
    fig.savefig(target, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _mask_from_row(row: pd.Series, player_cols: Sequence[str]) -> int:
    mask = 0
    for i, col in enumerate(player_cols):
        try:
            v = int(row[col])
        except Exception:
            v = 0
        if v != 0:
            mask |= 1 << i
    return int(mask)


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
) -> None:
    """Write interaction index top-k coalition tables into interaction_index.png.

    Uses ALL coalitions (no coalition-size filter).
    """
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        player_names = [it.label or it.column for it in ordered]

    specs = [
        ("shapley-interaction", "Shapley Interaction", "rank_shapley-interaction", "score_shapley-interaction"),
        ("banzhaf-interaction", "Banzhaf Interaction", "rank_banzhaf-interaction", "score_banzhaf-interaction"),
        ("rp-index", "RP Index", "rank_rp-index", "score_rp-index"),
    ]

    available = [(key, title, rank_col, score_col) for (key, title, rank_col, score_col) in specs if rank_col in df.columns]
    if not available:
        raise ValueError("No interaction index rank columns found in rankings CSV.")

    fig_w = max(12.0, 6.5 * len(available))
    fig_h = max(8.0, 0.25 * (int(top_k) + 2))
    fig, axes = plt.subplots(1, len(available), figsize=(fig_w, fig_h), constrained_layout=True)
    if len(available) == 1:
        axes = [axes]  # type: ignore[assignment]

    for ax, (_key, title, rank_col, score_col) in zip(axes, available):
        ax.axis("off")

        dfx = df.copy()
        dfx[rank_col] = pd.to_numeric(dfx[rank_col], errors="coerce")
        dfx = dfx[pd.notna(dfx[rank_col])]
        if dfx.empty:
            ax.set_title(f"{title} (no data)")
            continue
        if include_game_score and "score" in dfx.columns:
            dfx["score"] = pd.to_numeric(dfx["score"], errors="coerce")
        if include_game_rank and "rank" in dfx.columns:
            dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
        dfx["_mask"] = dfx.apply(lambda r: _mask_from_row(r, player_cols), axis=1)
        dfx = dfx[dfx["_mask"] != 0]
        if max_coalition_size is not None:
            dfx["_size"] = dfx["_mask"].apply(lambda m: int(m).bit_count())
            dfx = dfx[dfx["_size"] <= int(max_coalition_size)]
        if exclude_feature_substrings and player_names is not None:
            banned = [s for s in (str(x) for x in exclude_feature_substrings) if s]
            if banned:
                banned_idx = [i for i, name in enumerate(player_names) if any(b in str(name) for b in banned)]
                if banned_idx:
                    banned_mask = 0
                    for i in banned_idx:
                        banned_mask |= 1 << int(i)
                    dfx = dfx[(dfx["_mask"].astype(int) & int(banned_mask)) == 0]
        dfx = dfx.sort_values([rank_col, "_mask"], ascending=[True, True], kind="mergesort").head(int(top_k))

        rows: list[list[str]] = []
        for _, r in dfx.iterrows():
            coalition = _coalition_label(r, player_cols, player_names)
            rank_cell = str(int(r[rank_col])) if pd.notna(r[rank_col]) else ""
            game_score_cell = ""
            if include_game_score and "score" in dfx.columns:
                game_score_cell = _format_score_cell(r.get("score"))
            game_rank_cell = ""
            if include_game_rank and "rank" in dfx.columns:
                v = r.get("rank")
                game_rank_cell = str(int(float(v))) if v is not None and pd.notna(v) else ""
            score_cell = ""
            if score_col in dfx.columns:
                score_cell = _format_score_cell(r.get(score_col))
            if include_game_score and include_game_rank:
                rows.append([coalition, game_score_cell, game_rank_cell, score_cell, rank_cell])
            elif include_game_score:
                rows.append([coalition, game_score_cell, score_cell, rank_cell])
            elif include_game_rank:
                rows.append([coalition, game_rank_cell, score_cell, rank_cell])
            else:
                rows.append([coalition, score_cell, rank_cell])

        col_labels = ["coalition"]
        if include_game_score:
            col_labels.append("score")
        if include_game_rank:
            col_labels.append("rank")
        col_labels.append(score_col if score_col in df.columns else "score")
        col_labels.append(rank_col)
        table = ax.table(
            cellText=rows,
            colLabels=col_labels,
            loc="center",
            cellLoc="left",
            colLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.35, 1.15)
        # Favor coalition column width.
        try:
            n_rows = len(rows)
            for rr in range(0, n_rows + 1):
                if include_game_score and include_game_rank:
                    table[(rr, 0)].set_width(0.56)
                    table[(rr, 1)].set_width(0.14)
                    table[(rr, 2)].set_width(0.08)
                    table[(rr, 3)].set_width(0.14)
                    table[(rr, 4)].set_width(0.08)
                elif include_game_score:
                    table[(rr, 0)].set_width(0.62)
                    table[(rr, 1)].set_width(0.14)
                    table[(rr, 2)].set_width(0.14)
                    table[(rr, 3)].set_width(0.10)
                elif include_game_rank:
                    table[(rr, 0)].set_width(0.64)
                    table[(rr, 1)].set_width(0.10)
                    table[(rr, 2)].set_width(0.16)
                    table[(rr, 3)].set_width(0.10)
                else:
                    table[(rr, 0)].set_width(0.72)
                    table[(rr, 1)].set_width(0.16)
                    table[(rr, 2)].set_width(0.12)
        except Exception:
            pass
        ax.set_title(f"{title} top-{int(top_k)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / str(out_name)
    fig.savefig(target, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)


def generate_red_index_topk_by_size_figures(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 30,
) -> list[Path]:
    """Write per-coalition-size red-index top-k tables as PNGs.

    Output files are named: red_index_top<size>_k<top_k>.png (size is 2-digit).
    Uses ALL coalitions (no coalition-size filter during input).
    """
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "score_red-index" not in df.columns:
        raise ValueError("score_red-index column not found (apply red-index rule first).")

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    n = len(player_cols)

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        player_names = [it.label or it.column for it in ordered]

    dfx = df.copy()
    dfx["score_red-index"] = pd.to_numeric(dfx["score_red-index"], errors="coerce")
    dfx = dfx[pd.notna(dfx["score_red-index"])]
    if dfx.empty:
        raise ValueError("no non-empty score_red-index values found")

    dfx["_mask"] = dfx.apply(lambda r: _mask_from_row(r, player_cols), axis=1)
    dfx = dfx[dfx["_mask"] != 0]
    if dfx.empty:
        raise ValueError("no non-empty coalitions found")

    # Coalition size and canonical tie-break ordering.
    dfx["_size"] = dfx["_mask"].apply(lambda m: int(m).bit_count())
    dfx = dfx.sort_values(["_size", "score_red-index", "_mask"], ascending=[True, False, True], kind="mergesort")

    written: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for size in range(1, n + 1):
        sub = dfx[dfx["_size"] == int(size)].head(int(top_k))
        if sub.empty:
            continue

        rows: list[list[str]] = []
        for _, r in sub.iterrows():
            coalition = _coalition_label(r, player_cols, player_names)
            acc = _format_score_cell(r.get("score"))
            rows.append([coalition, str(int(r["score_red-index"])), acc])

        # Size heuristics: widen by coalition label length (no wrapping).
        max_len = max((len(r[0]) for r in rows), default=0)
        fig_w = max(10.0, 10.0 * min(2.8, 1.0 + max(0.0, (max_len - 24) / 70.0)))
        fig_h = max(6.0, 0.28 * (len(rows) + 2))
        fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
        ax.axis("off")
        ax.set_title(f"Redundancy Index top-{int(top_k)} (|S|={int(size)})")

        table = ax.table(
            cellText=rows,
            colLabels=["予測因子の組", "Red Index", "正解率"],
            loc="center",
            cellLoc="left",
            colLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.25, 1.1)
        try:
            n_rows = len(rows)
            for rr in range(0, n_rows + 1):
                table[(rr, 0)].set_width(0.72)
                table[(rr, 1)].set_width(0.14)
                table[(rr, 2)].set_width(0.14)
        except Exception:
            pass

        out_path = output_dir / f"red_index_top{int(size):02d}_k{int(top_k)}.png"
        fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
        plt.close(fig)
        written.append(out_path)

    return written


def generate_red_index_scatter_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a scatter plot (x=|S|, y=score_red-index) as red_index_scatter.png."""
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "score_red-index" not in df.columns:
        raise ValueError("score_red-index column not found (apply red-index rule first).")

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    n = len(player_cols)

    dfx = df.copy()
    for c in player_cols:
        dfx[c] = pd.to_numeric(dfx[c], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=1)
    dfx["score_red-index"] = pd.to_numeric(dfx["score_red-index"], errors="coerce")
    dfx = dfx[pd.notna(dfx["score_red-index"])]

    dfx["_mask"] = dfx.apply(lambda r: _mask_from_row(r, player_cols), axis=1)
    dfx = dfx[dfx["_mask"] != 0]
    if dfx.empty:
        raise ValueError("no non-empty coalitions with score_red-index found")

    sizes = dfx[player_cols].sum(axis=1).astype(int)
    scores = dfx["score_red-index"].astype(float)

    dataset_id = rankings_csv.stem
    if dataset_id.startswith("game_"):
        dataset_id = dataset_id[len("game_") :]

    fig_w = max(7.0, 0.6 * n + 2.0)
    fig_h = 5.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    ax.scatter(sizes.to_numpy(), scores.to_numpy(), s=10, alpha=0.25, edgecolors="none")
    ax.set_xlabel("提携サイズ |S|")
    ax.set_ylabel("Redundancy Index")
    ax.set_title(f"{dataset_id}データセット：提携サイズごとのRedundancy Index推移プロット（n={n}, points={len(dfx)}）")
    ax.set_xticks(list(range(1, n + 1)))
    ax.grid(True, axis="y", alpha=0.2)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "red_index_scatter.png"
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_shapley_values_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a feature × Shapley value bar plot as shapley_values.png."""
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "score_shapley" not in df.columns:
        raise ValueError("score_shapley column not found (apply shapley rule first).")

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    n = len(player_cols)

    dataset_id = rankings_csv.stem
    if dataset_id.startswith("game_"):
        dataset_id = dataset_id[len("game_") :]

    feature_names = [f"player{i+1}" for i in range(n)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        feature_names = [it.label or it.column for it in ordered]

    dfx = df.copy()
    for c in player_cols:
        dfx[c] = pd.to_numeric(dfx[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["score_shapley"] = pd.to_numeric(dfx["score_shapley"], errors="coerce")
    dfx = dfx[pd.notna(dfx["score_shapley"])]
    if dfx.empty:
        raise ValueError("no score_shapley values found")

    # Keep singleton rows only.
    sizes = dfx[player_cols].sum(axis=1).astype(int)
    dfx = dfx[sizes == 1]
    if dfx.empty:
        raise ValueError("no singleton rows with score_shapley found")

    # Map singleton coalition to player index.
    values = [0.0] * n
    seen = [False] * n
    for _, r in dfx.iterrows():
        idx = None
        for i, c in enumerate(player_cols):
            if int(r[c]) != 0:
                idx = i
                break
        if idx is None:
            continue
        values[idx] = float(r["score_shapley"])
        seen[idx] = True
    if not any(seen):
        raise ValueError("no singleton player mapping found for score_shapley")

    max_label_len = max((len(str(x)) for x in feature_names), default=0)
    fig_w = max(8.0, 0.55 * n + max(0.0, (max_label_len - 8) * 0.08))
    fig_h = 5.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    xs = list(range(n))
    ax.bar(xs, values, color="#4C78A8")
    ax.set_xticks(xs)
    ax.set_xticklabels(feature_names, rotation=45 if max_label_len >= 10 else 0, ha="right")
    ax.set_ylabel("Shapley value")
    ax.set_title(f"{dataset_id}データセット：特徴量ごとのShapley値（n={n}）")
    ax.grid(True, axis="y", alpha=0.2)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "shapley_values.png"
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_ordinal_banzhaf_values_plot(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
) -> Path:
    """Write a feature × Ordinal Banzhaf score bar plot as ordinal_banzhaf_values.png."""
    set_japanese_font_if_available()
    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "rank" not in df.columns:
        raise ValueError("rank column not found (need coalition ordinal levels).")

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    n = len(player_cols)

    dataset_id = rankings_csv.stem
    if dataset_id.startswith("game_"):
        dataset_id = dataset_id[len("game_") :]

    feature_names = [f"player{i+1}" for i in range(n)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        feature_names = [it.label or it.column for it in ordered]

    dfx = df.copy()
    for c in player_cols:
        dfx[c] = pd.to_numeric(dfx[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank"])]
    if dfx.empty:
        raise ValueError("no rank values found")

    # Use the given coalition rank as ordinal information, but break ties deterministically by mask.
    # This avoids degenerate cases where coarse pre-binned ranks (e.g., class_id) create many ties
    # and can yield s_i=0 for some features.
    rank_by_mask: dict[int, int] = {}
    for _, r in dfx.iterrows():
        m = _mask_from_row(r, player_cols)
        rank_by_mask[m] = int(float(r["rank"]))
    ordered = sorted(rank_by_mask.items(), key=lambda kv: (kv[1], kv[0]))
    level_of_mask: dict[int, int] = {m: i + 1 for i, (m, _rank) in enumerate(ordered)}

    detail = ordinal_banzhaf_detail(level_of_mask, n)
    values = [int(detail[i]["s"]) for i in range(n)]

    max_label_len = max((len(str(x)) for x in feature_names), default=0)
    fig_w = max(8.0, 0.55 * n + max(0.0, (max_label_len - 8) * 0.08))
    fig_h = 5.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    xs = list(range(n))
    ax.bar(xs, values, color="#F58518")
    ax.set_xticks(xs)
    ax.set_xticklabels(feature_names, rotation=45 if max_label_len >= 10 else 0, ha="right")
    ax.set_xlabel("特徴量")
    ax.set_ylabel("序数的Banzhafスコア")
    ax.set_title(f"{dataset_id}データセット：特徴量ごとの序数的Banzhafスコア（n={n}）")
    ax.grid(True, axis="y", alpha=0.2)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "ordinal_banzhaf_values.png"
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_rp_index_top_size2_figure(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 10,
    coalition_size: int = 2,
    out_name: str = "rp_index_top_size2_k10.png",
) -> Path:
    """Write a PNG table of top-k size=2 coalitions by RP Index (rank_rp-index)."""
    set_japanese_font_if_available()
    k = int(top_k)
    if k <= 0:
        raise ValueError("top_k must be >= 1")
    target_size = int(coalition_size)
    if target_size <= 0:
        raise ValueError("coalition_size must be >= 1")

    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "rank_rp-index" not in df.columns:
        raise ValueError("rank_rp-index column not found (apply rp-index rule first).")

    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        player_names = [it.label or it.column for it in ordered]

    dfx = df.copy()
    dfx["rank_rp-index"] = pd.to_numeric(dfx["rank_rp-index"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank_rp-index"])]
    if dfx.empty:
        raise ValueError("no rank_rp-index values found")

    dfx["_mask"] = dfx.apply(lambda r: _mask_from_row(r, player_cols), axis=1)
    dfx = dfx[dfx["_mask"] != 0]
    dfx["_size"] = dfx["_mask"].apply(lambda m: int(m).bit_count())
    dfx = dfx[dfx["_size"] == target_size]
    if dfx.empty:
        raise ValueError(f"no coalitions found for |S|={target_size}")

    dfx = dfx.sort_values(["rank_rp-index", "_mask"], ascending=[True, True], kind="mergesort").head(k)

    rows: list[list[str]] = []
    for _, r in dfx.iterrows():
        coalition = _coalition_label(r, player_cols, player_names)
        score_cell = _format_score_cell(r.get("score_rp-index")) if "score_rp-index" in dfx.columns else ""
        rank_cell = str(int(float(r["rank_rp-index"])))
        rows.append([coalition, score_cell, rank_cell])

    max_len = max((len(r[0]) for r in rows), default=0)
    fig_w = max(10.0, 10.0 * min(2.4, 1.0 + max(0.0, (max_len - 24) / 70.0)))
    fig_h = max(5.0, 0.32 * (len(rows) + 2))
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
    ax.axis("off")

    dataset_id = rankings_csv.stem
    if dataset_id.startswith("game_"):
        dataset_id = dataset_id[len("game_") :]
    ax.set_title(f"{dataset_id}：RP Index 上位{len(rows)}（|S|={target_size}）")

    table = ax.table(
        cellText=rows,
        colLabels=["予測因子の組", "RP Index", "rank_rp-index"],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.15)
    try:
        n_rows = len(rows)
        for rr in range(0, n_rows + 1):
            table[(rr, 0)].set_width(0.70)
            table[(rr, 1)].set_width(0.18)
            table[(rr, 2)].set_width(0.12)
    except Exception:
        pass

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / str(out_name)
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_give_topk_table(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    top_k: int = 10,
    out_name: str = "give_top10.png",
) -> Path:
    """Write a PNG table of top-k coalitions by give(T)=|{i in T | T ≻ {i}}|."""
    set_japanese_font_if_available()
    k = int(top_k)
    if k <= 0:
        raise ValueError("top_k must be >= 1")

    df = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])

    if "rank" not in df.columns:
        raise ValueError("rank column not found")
    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")
    n = len(player_cols)

    player_names: list[str] | None = None
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        player_names = [it.label or it.column for it in ordered]

    dfx = df.copy()
    for c in player_cols:
        dfx[c] = pd.to_numeric(dfx[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx = dfx[pd.notna(dfx["rank"])]
    if dfx.empty:
        raise ValueError("no rank values found")

    # Map singleton ranks: idx -> rank({i})
    singleton_rank: dict[int, int] = {}
    for _, r in dfx.iterrows():
        mask = _mask_from_row(r, player_cols)
        if mask != 0 and (mask & (mask - 1)) == 0:
            idx = int(mask).bit_length() - 1
            singleton_rank[idx] = int(float(r["rank"]))
    if len(singleton_rank) != n:
        # Best-effort: still proceed, but missing singleton ranks reduce give counts.
        pass

    rows_scored: list[tuple[int, int, int, str]] = []  # (give, mask, size, label)
    for _, r in dfx.iterrows():
        mask = _mask_from_row(r, player_cols)
        if mask == 0:
            continue
        size = int(mask).bit_count()
        if size < 2:
            continue
        r_t = int(float(r["rank"]))
        give = 0
        for i in range(n):
            if (mask >> i) & 1:
                r_i = singleton_rank.get(i)
                if r_i is not None and r_t < int(r_i):
                    give += 1
        label = _coalition_label(r, player_cols, player_names)
        rows_scored.append((int(give), int(mask), int(size), label))

    rows_scored.sort(key=lambda t: (-t[0], t[1]))
    top = rows_scored[:k]

    out_rows: list[list[str]] = []
    for give, _mask, size, label in top:
        out_rows.append([label, str(int(give)), str(int(size))])

    max_len = max((len(r[0]) for r in out_rows), default=0)
    fig_w = max(10.0, 10.0 * min(2.4, 1.0 + max(0.0, (max_len - 24) / 70.0)))
    fig_h = max(4.5, 0.34 * (len(out_rows) + 2))
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
    ax.axis("off")

    dataset_id = rankings_csv.stem
    if dataset_id.startswith("game_"):
        dataset_id = dataset_id[len("game_") :]
    ax.set_title(f"{dataset_id}：引き上げ(give)上位{len(out_rows)}提携")

    table = ax.table(
        cellText=out_rows,
        colLabels=["予測因子の組", "引き上げ数(give)", "提携サイズ"],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.15)
    try:
        n_rows = len(out_rows)
        for rr in range(0, n_rows + 1):
            table[(rr, 0)].set_width(0.74)
            table[(rr, 1)].set_width(0.16)
            table[(rr, 2)].set_width(0.10)
    except Exception:
        pass

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / str(out_name)
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_lexcel_rank_count_heatmap(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    out_name: str = "lexcel_rank_counts.png",
) -> Path:
    """Write Lexcel θ-vector heatmap (x=feature, y=level index, cell=θ_i(j))."""
    set_japanese_font_if_available()
    rankings_csv = Path(rankings_csv)
    if not rankings_csv.exists():
        raise ValueError(f"rankings CSV not found: {rankings_csv}")

    df0 = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df0.columns and new not in df0.columns:
            df0 = df0.rename(columns={old: new})
        elif old in df0.columns and new in df0.columns:
            df0 = df0.drop(columns=[old])
    player_cols = _players_columns(df0)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")
    if "rank" not in df0.columns:
        raise ValueError("rankings CSV missing rank column")
    n = len(player_cols)

    # Feature names from features.yaml next to the CSV (if present).
    feature_names = [f"player{i+1}" for i in range(n)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        feature_names = [it.label or it.column for it in ordered]

    # Build rank layers from rankings CSV and compute θ vectors.
    df = df0.copy()
    for c in player_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df[pd.notna(df["rank"])]
    if df.empty:
        raise ValueError("no rank values found")

    level_of_mask: dict[int, int] = {}
    for _, r in df.iterrows():
        mask = _mask_from_row(r, player_cols)
        level_of_mask[int(mask)] = int(float(r["rank"]))
    if not level_of_mask:
        raise ValueError("no coalitions found")

    from gamegen.rules.lexcel import theta_vectors

    level_count = max(level_of_mask.values(), default=0)
    if level_count <= 0:
        raise ValueError("no levels found")
    theta = theta_vectors({int(k): int(v) for k, v in level_of_mask.items()}, n, level_count)
    # theta[player][level_index]
    mat = [[int(theta[player][level]) for player in range(n)] for level in range(level_count)]

    # Figure sizing heuristics
    max_label_len = max((len(str(x)) for x in feature_names), default=0)
    fig_w = max(8.0, 0.6 * n + max(0.0, (max_label_len - 8) * 0.08))
    fig_h = max(4.0, 0.35 * level_count + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)

    # Show rank 1 at the top.
    im = ax.imshow(mat, aspect="auto", interpolation="nearest", cmap="Blues", origin="upper")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="count")

    ax.set_xticks(list(range(n)))
    ax.set_xticklabels(feature_names, rotation=45 if max_label_len >= 10 else 0, ha="right")
    # Limit y tick density for large level counts.
    if level_count <= 30:
        yticks = list(range(level_count))
    else:
        step = 5 if level_count <= 120 else 10
        yticks = list(range(0, level_count, step))
        if (level_count - 1) not in yticks:
            yticks.append(level_count - 1)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(i + 1) for i in yticks])
    ax.set_xlabel("特徴量")
    ax.set_ylabel("ランク層（上が1）")

    title_dataset = rankings_csv.stem
    if title_dataset.startswith("game_"):
        title_dataset = title_dataset[len("game_") :]
    if title_dataset == "crop_policy":
        ax.set_title("cropデータセット：施策ごとの収穫量ランク出現回数")
        ax.set_ylabel("トウモロコシ収穫量ランク")
    else:
        ax.set_title(f"{title_dataset}データセット：特徴量ごとのランク出現回数")

    # Annotate counts
    if level_count <= 40 and n <= 20:
        for y in range(level_count):
            for x in range(n):
                v = mat[y][x]
                if v == 0:
                    continue
                ax.text(x, y, str(int(v)), ha="center", va="center", fontsize=7, color="black")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / str(out_name)
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


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
    """Write rank-occurrence distribution heatmap (x=feature, y=rank, cell=proportion).

    Proportion is normalized per feature (column sums to 1.0 over the selected coalitions).
    If coalition_size is set, uses only coalitions of that size (observed subset).
    """
    set_japanese_font_if_available()
    rankings_csv = Path(rankings_csv)
    if not rankings_csv.exists():
        raise ValueError(f"rankings CSV not found: {rankings_csv}")

    df0 = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df0.columns and new not in df0.columns:
            df0 = df0.rename(columns={old: new})
        elif old in df0.columns and new in df0.columns:
            df0 = df0.drop(columns=[old])
    player_cols = _players_columns(df0)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")
    if "rank" not in df0.columns:
        raise ValueError("rankings CSV missing rank column")
    n_all = len(player_cols)

    feature_names = [f"player{i+1}" for i in range(n_all)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        feature_names = [it.label or it.column for it in ordered]

    df = df0.copy()
    for c in player_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df[pd.notna(df["rank"])]
    if df.empty:
        raise ValueError("no rank values found")

    if coalition_size is not None:
        sizes = None
        for c in player_cols:
            v = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
            sizes = v if sizes is None else (sizes + v)
        if sizes is None:
            df = df.iloc[0:0].copy()
        else:
            df = df[sizes == int(coalition_size)]
        if df.empty:
            raise ValueError(f"no coalitions found for coalition_size={coalition_size}")

    level_of_mask: dict[int, int] = {}
    for _, r in df.iterrows():
        mask = _mask_from_row(r, player_cols)
        level_of_mask[int(mask)] = int(float(r["rank"]))
    if not level_of_mask:
        raise ValueError("no coalitions found")

    from gamegen.rules.lexcel import theta_vectors

    level_count = max(level_of_mask.values(), default=0)
    if level_count <= 0:
        raise ValueError("no levels found")
    theta = theta_vectors({int(k): int(v) for k, v in level_of_mask.items()}, n_all, level_count)

    # Normalize per feature.
    totals = [sum(theta[p]) for p in range(n_all)]
    keep_players = [p for p in range(n_all) if totals[p] > 0]
    if not keep_players:
        raise ValueError("no non-empty features found")

    mat: list[list[float]] = []
    for level in range(level_count):
        row: list[float] = []
        for p in keep_players:
            denom = float(totals[p])
            row.append(float(theta[p][level]) / denom if denom > 0 else 0.0)
        mat.append(row)

    # Drop all-zero levels (e.g., missing ranks in subset).
    keep_levels = [i for i, row in enumerate(mat) if any(v > 0 for v in row)]
    if not keep_levels:
        raise ValueError("no non-empty levels found")
    mat = [mat[i] for i in keep_levels]
    level_labels = [str(i + 1) for i in keep_levels]

    feature_names_kept = [feature_names[p] for p in keep_players]
    n = len(feature_names_kept)
    level_n = len(mat)

    max_label_len = max((len(str(x)) for x in feature_names_kept), default=0)
    fig_w = max(8.0, 0.6 * n + max(0.0, (max_label_len - 8) * 0.08))
    fig_h = max(4.0, 0.35 * level_n + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)

    im = ax.imshow(mat, aspect="auto", interpolation="nearest", cmap="Blues", origin="upper")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="出現割合")

    ax.set_xticks(list(range(n)))
    ax.set_xticklabels(feature_names_kept, rotation=45 if max_label_len >= 10 else 0, ha="right")
    ax.set_yticks(list(range(level_n)))
    ax.set_yticklabels(level_labels)
    ax.set_xlabel(str(x_label) if x_label is not None else "特徴量")
    ax.set_ylabel(str(y_label) if y_label is not None else "ランク層（上が1）")

    title_dataset = rankings_csv.stem
    if title_dataset.startswith("game_"):
        title_dataset = title_dataset[len("game_") :]
    suffix = f"（|S|={int(coalition_size)}のみ）" if coalition_size is not None else ""
    if title is not None:
        ax.set_title(str(title) + str(suffix))
    else:
        ax.set_title(f"{title_dataset}：ランク出現分布（規格化）{suffix}")

    if level_n <= 40 and n <= 20:
        for y in range(level_n):
            for x in range(n):
                v = float(mat[y][x])
                if v <= 0.0:
                    continue
                ax.text(x, y, f"{v:.2f}", ha="center", va="center", fontsize=7, color="black")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / str(out_name)
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_pair_rank_occurrence_distribution_heatmap(
    *,
    rankings_csv: Path,
    output_dir: Path,
    dpi: int = 200,
    out_name: str = "lexcel_rank_counts_size2.png",
) -> Path:
    """Write pair-coalition (|S|=2) rank-occurrence distribution heatmap.

    Deprecated: kept for compatibility; use generate_kset_rank_occurrence_distribution_heatmap(subset_size=2).
    """
    return generate_kset_rank_occurrence_distribution_heatmap(
        rankings_csv=rankings_csv,
        output_dir=output_dir,
        dpi=dpi,
        out_name=out_name,
        subset_size=2,
    )


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
    """Write k-set (|S|=k) rank-occurrence distribution heatmap.

    X-axis: observed k-sets (count>0), where a k-set is counted if a coalition includes all its members.
    Y-axis: rank level (1 at top).
    Cell: normalized proportion per k-set (column sums to 1.0 over levels).
    """
    set_japanese_font_if_available()
    rankings_csv = Path(rankings_csv)
    if not rankings_csv.exists():
        raise ValueError(f"rankings CSV not found: {rankings_csv}")

    df0 = pd.read_csv(rankings_csv)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df0.columns and new not in df0.columns:
            df0 = df0.rename(columns={old: new})
        elif old in df0.columns and new in df0.columns:
            df0 = df0.drop(columns=[old])
    player_cols = _players_columns(df0)
    if not player_cols:
        raise ValueError("rankings CSV missing player columns")
    if "rank" not in df0.columns:
        raise ValueError("rankings CSV missing rank column")
    n = len(player_cols)
    k = int(subset_size)
    if k <= 0:
        raise ValueError("subset_size must be >= 1")
    if k > n:
        raise ValueError("subset_size must be <= number of players")

    feature_names = [f"player{i+1}" for i in range(n)]
    features_path = rankings_csv.with_suffix(".features.yaml")
    if features_path.exists():
        items = read_feature_labels_yaml(features_path)
        ordered = sorted(items, key=lambda it: int(str(it.player).replace("player", "")))
        feature_names = [it.label or it.column for it in ordered]

    df = df0.copy()
    for c in player_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int).clip(0, 1)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df[pd.notna(df["rank"])]
    if df.empty:
        raise ValueError("no rank values found")

    level_count = int(df["rank"].max()) if pd.notna(df["rank"].max()) else 0
    if level_count <= 0:
        raise ValueError("no levels found")

    # Count occurrences: for each coalition, increment all contained k-sets at its rank level.
    # Key is a sorted tuple of member indices.
    counts: dict[tuple[int, ...], list[int]] = {}
    for _, r in df.iterrows():
        try:
            level = int(float(r["rank"]))
        except Exception:
            continue
        if level <= 0:
            continue
        members: list[int] = []
        for i, col in enumerate(player_cols):
            try:
                v = int(r[col])
            except Exception:
                v = 0
            if v != 0:
                members.append(i)
        if len(members) < k:
            continue
        members = sorted(set(int(x) for x in members))
        # Avoid importing itertools at module level; keep local.
        import itertools

        for comb in itertools.combinations(members, k):
            key = tuple(int(x) for x in comb)
            vec = counts.get(key)
            if vec is None:
                vec = [0] * level_count
                counts[key] = vec
            vec[level - 1] += 1

    if not counts:
        raise ValueError("no k-set occurrences found")

    focus_set = {str(x) for x in (focus_features or []) if str(x)}

    # Keep only observed k-sets (total>0), normalize per k-set.
    items = []
    for key, vec in counts.items():
        total = int(sum(vec))
        if total <= 0:
            continue
        if focus_set:
            member_names = [str(feature_names[i]) for i in key]
            if require_all_members_in_focus:
                if not all(n in focus_set for n in member_names):
                    continue
            else:
                if not any(n in focus_set for n in member_names):
                    continue
        label = "{" + ",".join([str(feature_names[i]) for i in key]) + "}"
        items.append((key, label, vec, total))
    if not items:
        raise ValueError("no non-empty k-sets found after filtering")

    # Sort by total desc then label for stable output.
    items.sort(key=lambda t: (-int(t[3]), str(t[1])))

    labels = [t[1] for t in items]
    mat: list[list[float]] = []
    for level in range(level_count):
        row: list[float] = []
        for _, _label, vec, total in items:
            row.append(float(vec[level]) / float(total) if total > 0 else 0.0)
        mat.append(row)

    # Drop all-zero levels (unlikely but possible if ranks are sparse).
    keep_levels = [idx for idx, row in enumerate(mat) if any(v > 0 for v in row)]
    if not keep_levels:
        raise ValueError("no non-empty levels found")
    mat = [mat[idx] for idx in keep_levels]
    level_labels = [str(idx + 1) for idx in keep_levels]

    max_label_len = max((len(str(x)) for x in labels), default=0)
    fig_w = max(10.0, 0.22 * len(labels) + max(0.0, (max_label_len - 12) * 0.03))
    fig_h = max(4.0, 0.35 * len(mat) + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)

    im = ax.imshow(mat, aspect="auto", interpolation="nearest", cmap="Blues", origin="upper")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="出現割合")

    ax.set_xticks(list(range(len(labels))))
    ax.set_xticklabels(labels, rotation=45 if max_label_len >= 10 else 0, ha="right")
    ax.set_yticks(list(range(len(mat))))
    ax.set_yticklabels(level_labels)
    ax.set_xlabel(str(x_label) if x_label is not None else f"提携（|S|={k}）")
    ax.set_ylabel(str(y_label) if y_label is not None else "ランク層（上が1）")

    title_dataset = rankings_csv.stem
    if title_dataset.startswith("game_"):
        title_dataset = title_dataset[len("game_") :]
    if title is not None:
        ax.set_title(str(title))
    else:
        kind = "ペア" if k == 2 else (f"|S|={k}")
        ax.set_title(f"{title_dataset}：{kind}提携のランク出現分布（規格化）")

    # annotate lightly for readability
    if len(mat) <= 30 and len(labels) <= 60:
        for y in range(len(mat)):
            for x in range(len(labels)):
                v = float(mat[y][x])
                if v <= 0.0:
                    continue
                ax.text(x, y, f"{v:.2f}", ha="center", va="center", fontsize=6, color="black")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / str(out_name)
    fig.savefig(out_path, dpi=int(dpi), bbox_inches="tight")
    plt.close(fig)
    return out_path


__all__ = [
    "_filter_by_coalition_size",
    "generate_interaction_index_figure",
    "generate_real_ranking_figure",
    "generate_red_index_topk_by_size_figures",
    "generate_red_index_scatter_plot",
    "generate_shapley_values_plot",
    "generate_ordinal_banzhaf_values_plot",
    "generate_rp_index_top_size2_figure",
    "generate_give_topk_table",
    "generate_lexcel_rank_count_heatmap",
    "generate_rank_occurrence_distribution_heatmap",
    "generate_pair_rank_occurrence_distribution_heatmap",
    "generate_kset_rank_occurrence_distribution_heatmap",
]
