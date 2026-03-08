"""PNG figure generator for rankings CSV.

This module reads a rankings CSV and renders horizontally arranged tables:
- Left: team performance ranking (team | rank | score)
- Right: contribution rankings for non-empty columns among
  [rank_shapley, rank_banzhaf, rank_lexcel, rank_o-banzhaf, rank_g-shapley, rank_g-sum-shapley, rank_shapley-interaction, rank_banzhaf-interaction, rank_rp-index, rank_ud, rank_du, rank_red-index, rank_g-lexcel, rank_g-o-banzhaf]

Outputs a single PNG per CSV under `<output_dir>/nX/{csv_filename}.png`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
import japanize_matplotlib  # type: ignore[import-untyped]  # noqa: F401
import pandas as pd

from .display_names import rank_column_display_name
from .io.rankings_csv import RANK_COLUMN_ALIASES

PlayerTuple = Tuple[int, ...]


@dataclass(frozen=True)
class TableSpec:
    title: str
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


def _coalition_label(row: pd.Series, player_cols: Sequence[str]) -> str:
    members: List[str] = []
    for idx, col in enumerate(player_cols, start=1):
        try:
            v = int(row[col])
        except Exception:
            v = 0
        if v != 0:
            members.append(str(idx))
    return "{" + ",".join(members) + "}"

def _team_performance_table(
    df: pd.DataFrame,
    player_cols: Sequence[str],
    limit: int | None = None,
) -> TableSpec:
    # Sort by numeric rank asc, stable
    dfx = df.copy()
    dfx["rank"] = pd.to_numeric(dfx["rank"], errors="coerce")
    dfx["score"] = pd.to_numeric(dfx["score"], errors="coerce")
    dfx = dfx.sort_values(["rank", "score"], ascending=[True, False], kind="mergesort")

    if limit is not None:
        dfx = dfx.head(limit)

    rows: List[List[str]] = []
    for _, r in dfx.iterrows():
        rows.append([
            _coalition_label(r, player_cols),
            str(int(r["rank"])) if pd.notna(r["rank"]) else "",
            str(int(r["score"])) if pd.notna(r["score"]) else "",
        ])
    return TableSpec(
        title="team ranking",
        col_labels=["team", "rank", "score"],
        rows=rows,
    )


def _contrib_table(
    df: pd.DataFrame,
    player_cols: Sequence[str],
    rank_col: str,
    limit: int | None = None,
) -> TableSpec | None:
    if rank_col not in df.columns:
        return None
    dfx = df.copy()
    dfx[rank_col] = pd.to_numeric(dfx[rank_col], errors="coerce")
    dfx = dfx[pd.notna(dfx[rank_col])]
    if dfx.empty:
        return None

    # Sort by rank asc, then by team size and lexicographic membership
    def sort_key(row: pd.Series) -> Tuple[int, int, List[int]]:
        label_members = []
        for i, col in enumerate(player_cols, start=1):
            try:
                v = int(row[col])
            except Exception:
                v = 0
            if v != 0:
                label_members.append(i)
        size = len(label_members)
        rank_val = int(row[rank_col])
        return (rank_val, size, label_members)

    dfx = dfx.sort_values(
        by=list(player_cols) + [rank_col],  # provide deterministic order first
        key=None,
        kind="mergesort",
    )
    # Apply custom sort using Python since pandas doesn't support complex tuple keys directly
    dfx = pd.DataFrame(list(sorted(dfx.to_dict("records"), key=lambda rec: sort_key(pd.Series(rec)))), columns=dfx.columns)

    rows: List[List[str]] = []
    for _, r in dfx.iterrows():
        rows.append([
            _coalition_label(r, player_cols),
            str(int(r[rank_col])) if pd.notna(r[rank_col]) else "",
        ])
    if limit is not None:
        rows = rows[:limit]

    return TableSpec(
        title=rank_col,
        col_labels=["player(s)", rank_column_display_name(rank_col)],
        rows=rows,
    )


def _is_numeric_rank_col(label: str) -> bool:
    lbl = str(label)
    return lbl in {"rank", "score"} or lbl.startswith("rank_")


def _is_narrow_label_col(label: str) -> bool:
    lbl = str(label).lower()
    return lbl in {"team", "player(s)"}


def _col_widths_for_spec(spec: TableSpec) -> List[float]:
    # Estimate width by max character length per column; shrink numeric rank columns.
    ncols = len(spec.col_labels)
    if ncols == 0:
        return []
    lens: List[float] = []
    for j, lbl in enumerate(spec.col_labels):
        max_len = float(len(str(lbl)))
        for row in spec.rows:
            if j < len(row):
                max_len = max(max_len, float(len(str(row[j]))))
        if _is_numeric_rank_col(str(lbl)):
            # Numeric rank/score columns: keep tight
            weight = max(2.8, max_len * 0.6)
        elif _is_narrow_label_col(str(lbl)):
            # team / player(s): prefer narrower but allow slightly more room
            weight = max(4.0, max_len * 0.75)
        else:
            weight = max(5.0, max_len * 1.0)
        lens.append(weight)
    total = sum(lens) or 1.0
    return [w / total for w in lens]


def _render_tables_horizontal(
    tables: Sequence[TableSpec],
    title: str,
    figsize_per_table: Tuple[float, float] = (4.2, 0.6),
    max_rows_for_height: int = 50,
) -> plt.Figure:
    # Compute figure size proportional to table count and rows
    n_tables = max(1, len(tables))
    max_rows = max((len(t.rows) for t in tables), default=1)
    # width: per table; height: scale with rows and add margins for titles
    width = max(4.0, figsize_per_table[0] * n_tables)
    row_height = max(0.6, figsize_per_table[1])
    visible_rows = min(max_rows_for_height, max_rows)
    height = max(3.0, visible_rows * row_height + 0.6)  # minimal headroom (no titles)
    fig, axes = plt.subplots(1, n_tables, figsize=(width, height), constrained_layout=True)
    if n_tables == 1:
        axes = [axes]  # type: ignore[assignment]

    for ax, spec in zip(axes, tables):
        ax.axis("off")
        col_widths = _col_widths_for_spec(spec)
        table = ax.table(
            cellText=spec.rows,
            colLabels=list(spec.col_labels),
            loc="center",
            cellLoc="center",
            colLoc="center",
            colWidths=col_widths if col_widths else None,
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.0, 1.25)

    # With constrained_layout, avoid tight_layout to prevent warnings
    # No overall figure title; only column headers in tables are shown
    return fig


def generate_team_ranking_figure(csv_path: Path, output_dir: Path, dpi: int = 150) -> None:
    """Read the CSV, create ranking tables, and save a PNG figure.

    - Left table: team performance ranking (team | rank | score)
    - Right tables: contribution rankings for rank_shapley, rank_banzhaf, rank_lexcel, rank_o-banzhaf, rank_g-shapley, rank_g-sum-shapley, rank_shapley-interaction, rank_banzhaf-interaction, rank_rp-index, rank_ud, rank_du, rank_red-index, rank_g-lexcel, rank_g-o-banzhaf
    - Output: `<output_dir>/nX/{csv_filename}.png`
    """
    # Read CSV via pandas
    df = pd.read_csv(csv_path)
    for old, new in RANK_COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
        elif old in df.columns and new in df.columns:
            df = df.drop(columns=[old])
    player_cols = _players_columns(df)
    if not player_cols:
        raise ValueError("CSV missing player columns (player1, ...)")

    row_limit = 30 if len(player_cols) >= 8 else None

    # Compose tables
    tables: List[TableSpec] = []
    tables.append(_team_performance_table(df, player_cols, limit=row_limit))

    # Order: personal -> group
    for col in [
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
    ]:
        t = _contrib_table(df, player_cols, col, limit=row_limit)
        if t is not None:
            tables.append(t)

    # Build figure title
    title = f"{csv_path.name}"

    # Render figure and save
    fig = _render_tables_horizontal(tables, title)
    try:
        n = len(player_cols)
        target_dir = output_dir / f"n{n}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / (csv_path.stem + ".png")
        fig.savefig(target_path, dpi=dpi)
    finally:
        plt.close(fig)


__all__ = [
    "generate_team_ranking_figure",
]
