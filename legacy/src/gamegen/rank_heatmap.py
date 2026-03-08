"""Utilities for building and rendering rank correlation heatmaps.

This module aggregates singleton player ranks across ranking CSV files and
renders frequency heatmaps for rank_lexcel vs rank_shapley pairs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Tuple

try:
    import matplotlib  # type: ignore[import-untyped]
    matplotlib.use("Agg")  # type: ignore[union-attr]
    import matplotlib.pyplot as plt  # type: ignore[import-untyped]
    import japanize_matplotlib  # type: ignore[import-untyped]  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    plt = None  # type: ignore[assignment]
import numpy as np
import pandas as pd

from .display_names import rank_column_display_name


@dataclass(frozen=True)
class RankPairSummary:
    """Aggregated counts and metadata for rank pairs."""

    matrix: pd.DataFrame
    total_pairs: int
    processed_files: int
    used_files: int
    skipped_files: Tuple[Tuple[Path, str], ...]


def _player_columns(df: pd.DataFrame) -> List[str]:
    cols: List[str] = []
    for col in df.columns:
        label = str(col)
        if label.startswith("player"):
            cols.append(label)
        else:
            break
    return cols


def _competition_rank(values: pd.Series) -> pd.Series:
    """Convert dense/competition ranks to 'strictly-better count + 1' ranks.

    For a ranking where smaller is better:
      eff(x) = 1 + |{y : rank(y) < rank(x)}|

    This is equivalent to converting dense ranks to competition ranks.
    """
    cleaned = pd.to_numeric(values, errors="coerce").dropna().astype(int)
    if cleaned.empty:
        return pd.Series(dtype=int)
    counts = cleaned.value_counts().to_dict()
    ordered = sorted(counts.keys())
    prefix = 0
    mapping: dict[int, int] = {}
    for r in ordered:
        mapping[int(r)] = int(prefix + 1)
        prefix += int(counts[int(r)])
    return cleaned.map(lambda x: mapping.get(int(x), 0)).astype(int)


def _effective_rank_series(raw: pd.Series) -> pd.Series:
    """Return 'strictly-better count + 1' ranks for a series of ranks (smaller is better)."""
    return _competition_rank(raw)


def _subset_singletons(df: pd.DataFrame, player_cols: list[str]) -> pd.Series:
    player_values = df[player_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    membership_count = player_values.gt(0).sum(axis=1)
    return membership_count == 1


def _subset_non_empty(df: pd.DataFrame, player_cols: list[str]) -> pd.Series:
    player_values = df[player_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    membership_count = player_values.gt(0).sum(axis=1)
    return membership_count >= 1


def collect_effective_rank_table(
    rankings_dir: Path,
    players: int,
    *,
    rank_cols: list[str],
    mode: str,
) -> pd.DataFrame:
    """Collect effective ranks for multiple rule columns across all ranking CSVs.

    Effective rank = (number of strictly better coalitions/players) + 1, computed
    per-file and per-column over the compared set.

    mode:
      - "player": singleton rows only
      - "coalition": non-empty coalition rows
    """
    target_dir = rankings_dir / f"n{players}"
    if not target_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {target_dir}")

    frames: list[pd.DataFrame] = []
    for csv_path in sorted(target_dir.glob("game_*.csv")):
        df = pd.read_csv(csv_path)
        player_cols = _player_columns(df)
        if len(player_cols) != players:
            continue

        if mode == "player":
            subset = _subset_singletons(df, player_cols)
        elif mode == "coalition":
            subset = _subset_non_empty(df, player_cols)
        else:
            raise ValueError("mode must be 'player' or 'coalition'")

        if not bool(subset.any()):
            continue

        out = pd.DataFrame(index=df.index)
        for col in rank_cols:
            if col not in df.columns:
                out[col] = np.nan
                continue
            raw = pd.to_numeric(df[col], errors="coerce")
            raw_sub = raw.loc[subset & raw.notna()]
            if raw_sub.empty:
                out[col] = np.nan
                continue
            eff_sub = _effective_rank_series(raw_sub)
            col_full = pd.Series(index=df.index, dtype=float)
            col_full.loc[eff_sub.index] = eff_sub.astype(float)
            col_full.loc[~subset] = np.nan
            out[col] = col_full

        frames.append(out.loc[subset, rank_cols])

    if not frames:
        return pd.DataFrame(columns=rank_cols)
    return pd.concat(frames, axis=0, ignore_index=True)


def collect_rule_correlation_matrix(
    rankings_dir: Path,
    players: int,
    *,
    rank_cols: list[str],
    mode: str,
    method: str = "spearman",
) -> pd.DataFrame:
    """Return a rule×rule correlation matrix for the given scope."""
    table = collect_effective_rank_table(rankings_dir, players, rank_cols=rank_cols, mode=mode)
    if table.empty:
        return pd.DataFrame()
    corr = table.corr(method=str(method), min_periods=1)
    return corr

def collect_rank_pairs(
    rankings_dir: Path,
    players: int,
    lex_col: str = "rank_lexcel",
    shap_col: str = "rank_shapley",
) -> RankPairSummary:
    """Collect singleton rank pairs from ranking CSV files."""

    target_dir = rankings_dir / f"n{players}"
    if not target_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {target_dir}")

    counts: Counter[tuple[int, int]] = Counter()
    processed_files = 0
    used_files = 0
    total_pairs = 0
    skipped: List[Tuple[Path, str]] = []

    # Only consider ranking CSVs that follow the expected naming
    # convention (game_XXXXXX.csv). This also ignores macOS resource
    # fork files like ._game_XXXXXX.csv.
    for csv_path in sorted(target_dir.glob("game_*.csv")):
        processed_files += 1
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:  # pragma: no cover - defensive
            skipped.append((csv_path, f"read error: {exc}"))
            continue

        player_cols = _player_columns(df)
        if len(player_cols) != players:
            skipped.append(
                (
                    csv_path,
                    f"expected {players} player columns, found {len(player_cols)}",
                )
            )
            continue

        if lex_col not in df.columns or shap_col not in df.columns:
            skipped.append(
                (
                    csv_path,
                    f"missing required column(s): {lex_col}/{shap_col}",
                )
            )
            continue

        player_values = (
            df[player_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
        )
        membership_count = player_values.gt(0).sum(axis=1)
        singletons = membership_count == 1

        lex_ranks = pd.to_numeric(df[lex_col], errors="coerce")
        shap_ranks = pd.to_numeric(df[shap_col], errors="coerce")
        valid = singletons & lex_ranks.notna() & shap_ranks.notna()
        if not bool(valid.any()):
            continue

        # Use "strictly better count + 1" ranks within the compared set to reduce tie distortion.
        eff_lex = _competition_rank(lex_ranks.loc[valid])
        eff_shap = _competition_rank(shap_ranks.loc[valid])

        pairs: Iterable[Tuple[int, int]] = zip(
            (int(x) for x in eff_lex),
            (int(y) for y in eff_shap),
        )
        added = 0
        for lex_rank, shap_rank in pairs:
            if lex_rank <= 0 or shap_rank <= 0:
                continue
            counts[(lex_rank, shap_rank)] += 1
            total_pairs += 1
            added += 1
        if added > 0:
            used_files += 1

    if not counts:
        empty = pd.DataFrame()
        return RankPairSummary(
            matrix=empty,
            total_pairs=0,
            processed_files=processed_files,
            used_files=0,
            skipped_files=tuple(skipped),
        )

    lex_values = sorted({lex for lex, _ in counts})
    shap_values = sorted({shap for _, shap in counts})
    data = []
    for shap_rank in shap_values:
        row = []
        for lex_rank in lex_values:
            row.append(counts.get((lex_rank, shap_rank), 0))
        data.append(row)
    matrix = pd.DataFrame(data, index=shap_values, columns=lex_values)
    matrix.index.name = shap_col
    matrix.columns.name = lex_col

    return RankPairSummary(
        matrix=matrix,
        total_pairs=total_pairs,
        processed_files=processed_files,
        used_files=used_files,
        skipped_files=tuple(skipped),
    )


def render_heatmap(
    matrix: pd.DataFrame,
    out_path: Path,
    lex_label: str = "rank_lexcel",
    shap_label: str = "rank_shapley",
    dpi: int = 150,
    title: str | None = None,
) -> None:
    """Render and save a heatmap for the provided rank matrix."""

    if plt is None:
        raise RuntimeError(
            "matplotlib is required to render heatmaps. Install the 'matplotlib' package."
        )
    if matrix.empty:
        raise ValueError("Cannot render heatmap without data.")

    values = matrix.to_numpy(dtype=float)
    height, width = values.shape
    fig_width = max(6.0, 0.6 * width + 2.5)
    fig_height = max(5.0, 0.6 * height + 2.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    cmap = plt.get_cmap("Blues")
    image = ax.imshow(values, origin="lower", cmap=cmap, aspect="auto")

    x_ticks = np.arange(width)
    y_ticks = np.arange(height)
    ax.set_xticks(x_ticks, labels=[str(v) for v in matrix.columns])
    ax.set_yticks(y_ticks, labels=[str(v) for v in matrix.index])
    x_label = rank_column_display_name(lex_label)
    y_label = rank_column_display_name(shap_label)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title or f"Frequency of {y_label} vs {x_label}")

    for y_idx, shap_val in enumerate(matrix.index):
        for x_idx, lex_val in enumerate(matrix.columns):
            count = int(values[y_idx, x_idx])
            if count > 0:
                ax.text(
                    x_idx,
                    y_idx,
                    str(count),
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=9,
                )

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="count")
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    # No grid lines per spec change
    ax.grid(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


def render_correlation_heatmap(
    matrix: pd.DataFrame,
    out_path: Path,
    *,
    dpi: int = 150,
    title: str | None = None,
) -> None:
    """Render a rule×rule correlation heatmap (values in [-1, 1])."""
    if plt is None:
        raise RuntimeError("matplotlib is required to render heatmaps. Install the 'matplotlib' package.")
    if matrix.empty:
        raise ValueError("Cannot render heatmap without data.")

    labels = [rank_column_display_name(str(c)) for c in matrix.columns]
    values = matrix.to_numpy(dtype=float)
    n = len(labels)
    fig_size = max(6.5, 0.55 * n + 2.5)

    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    cmap = plt.get_cmap("RdBu_r")
    image = ax.imshow(values, origin="lower", cmap=cmap, vmin=-1.0, vmax=1.0)

    ticks = np.arange(n)
    ax.set_xticks(ticks, labels=labels, rotation=45, ha="right")
    ax.set_yticks(ticks, labels=labels)
    ax.set_title(title or "Rule Rank Correlation")

    for y in range(n):
        for x in range(n):
            v = values[y, x]
            if np.isnan(v):
                continue
            ax.text(x, y, f"{v:.2f}", ha="center", va="center", color="black", fontsize=8)

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="correlation")
    ax.grid(False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)

__all__ = [
    "RankPairSummary",
    "collect_rank_pairs",
    "render_heatmap",
    "collect_effective_rank_table",
    "collect_rule_correlation_matrix",
    "render_correlation_heatmap",
]


def collect_group_rank_pairs(
    rankings_dir: Path,
    players: int,
    lex_col: str = "rank_g-lexcel",
    banz_col: str = "rank_g-o-banzhaf",
) -> RankPairSummary:
    """Collect coalition (non-empty) rank pairs from ranking CSV files.

    Aggregates pairs (lex_col, banz_col) over every non-empty coalition row
    across all ranking CSVs under rankings_dir/n{players}.
    """

    target_dir = rankings_dir / f"n{players}"
    if not target_dir.exists():
        raise FileNotFoundError(f"Rankings directory not found: {target_dir}")

    counts: Counter[tuple[int, int]] = Counter()
    processed_files = 0
    used_files = 0
    total_pairs = 0
    skipped: List[Tuple[Path, str]] = []

    for csv_path in sorted(target_dir.glob("game_*.csv")):
        processed_files += 1
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:  # pragma: no cover - defensive
            skipped.append((csv_path, f"read error: {exc}"))
            continue

        player_cols = _player_columns(df)
        if len(player_cols) != players:
            skipped.append(
                (
                    csv_path,
                    f"expected {players} player columns, found {len(player_cols)}",
                )
            )
            continue

        if lex_col not in df.columns or banz_col not in df.columns:
            skipped.append(
                (
                    csv_path,
                    f"missing required column(s): {lex_col}/{banz_col}",
                )
            )
            continue

        # non-empty coalitions only
        membership_count = (
            df[player_cols].apply(pd.to_numeric, errors="coerce").fillna(0).gt(0).sum(axis=1)
        )
        non_empty = membership_count >= 1

        lex_ranks = pd.to_numeric(df[lex_col], errors="coerce")
        banz_ranks = pd.to_numeric(df[banz_col], errors="coerce")
        valid = non_empty & lex_ranks.notna() & banz_ranks.notna()
        if not bool(valid.any()):
            continue

        eff_lex = _competition_rank(lex_ranks.loc[valid])
        eff_banz = _competition_rank(banz_ranks.loc[valid])

        added = 0
        for lx_i, bz_i in zip(eff_lex, eff_banz):
            lx_i = int(lx_i)
            bz_i = int(bz_i)
            if lx_i <= 0 or bz_i <= 0:
                continue
            counts[(lx_i, bz_i)] += 1
            total_pairs += 1
            added += 1
        if added > 0:
            used_files += 1

    if not counts:
        empty = pd.DataFrame()
        return RankPairSummary(
            matrix=empty,
            total_pairs=0,
            processed_files=processed_files,
            used_files=0,
            skipped_files=tuple(skipped),
        )

    lex_values = sorted({lex for lex, _ in counts})
    banz_values = sorted({b for _, b in counts})
    data = []
    for b in banz_values:  # y-axis = banzhaf
        row = []
        for l in lex_values:  # x-axis = g-lexcel
            row.append(counts.get((l, b), 0))
        data.append(row)
    matrix = pd.DataFrame(data, index=banz_values, columns=lex_values)
    matrix.index.name = banz_col
    matrix.columns.name = lex_col

    return RankPairSummary(
        matrix=matrix,
        total_pairs=total_pairs,
        processed_files=processed_files,
        used_files=used_files,
        skipped_files=tuple(skipped),
    )


__all__.extend(["collect_group_rank_pairs"])
