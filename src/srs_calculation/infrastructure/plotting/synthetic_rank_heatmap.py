"""Synthetic rank-correlation heatmap helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RankingScope = Literal["player", "coalition"]

_RANK_LABEL_FALLBACKS: dict[str, str] = {
    "shapley": "Shapley",
    "banzhaf": "Banzhaf",
    "lexcel": "Lex-cel",
    "o-banzhaf": "Ordinal Banzhaf",
    "g-shapley": "Shapley Group Value",
    "g-sum-shapley": "Sum of Shapley Values",
    "shapley-interaction": "Shapley Interaction Rule",
    "banzhaf-interaction": "Banzhaf Interaction Rule",
    "rp-index": "RP Difference Rule",
    "ud": "UD Rule",
    "du": "DU Rule",
    "red-index": "Redundancy Rule",
    "g-lexcel": "Group Lex-cel",
    "g-o-banzhaf": "Group Ordinal Banzhaf",
}

_PREFERRED_RANK_COLUMN_ORDER: tuple[str, ...] = (
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
)


@dataclass(frozen=True)
class RankPairSummary:
    """Aggregated count matrix for one rank-column pair."""

    matrix: pd.DataFrame
    total_pairs: int
    processed_files: int
    used_files: int


def _player_columns(df: pd.DataFrame) -> list[str]:
    return [str(column) for column in df.columns if str(column).startswith("player")]


def _player_membership_counts(df: pd.DataFrame, player_cols: list[str]) -> pd.Series:
    player_values = df[player_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    return player_values.gt(0).sum(axis=1)


def _subset_for_scope(df: pd.DataFrame, player_cols: list[str], scope: RankingScope) -> pd.Series:
    membership_count = _player_membership_counts(df, player_cols)
    if scope == "player":
        return membership_count == 1
    return membership_count >= 1


def _competition_rank(values: pd.Series) -> pd.Series:
    """Convert rank labels into strictly-better-count + 1 ranks."""

    cleaned = pd.to_numeric(values, errors="coerce").dropna().astype(int)
    if cleaned.empty:
        return pd.Series(dtype=int)
    counts = cleaned.value_counts().to_dict()
    ordered = sorted(int(rank) for rank in counts)
    prefix = 0
    mapping: dict[int, int] = {}
    for rank in ordered:
        mapping[rank] = prefix + 1
        prefix += int(counts[rank])
    return cleaned.map(lambda rank: mapping[int(rank)]).astype(int)


def _rank_column_display_name(column_name: str) -> str:
    normalized = str(column_name)
    if normalized.startswith("rank_") or normalized.startswith("score_"):
        normalized = normalized.split("_", 1)[1]
    return _RANK_LABEL_FALLBACKS.get(normalized, str(column_name))


def _rankings_target_dir(rankings_dir: Path, players: int) -> Path:
    candidate = rankings_dir / f"n{players}"
    if candidate.exists():
        return candidate
    if rankings_dir.exists():
        return rankings_dir
    raise FileNotFoundError(f"Rankings directory not found: {candidate}")


def _ordered_rank_columns(columns: Iterable[str]) -> list[str]:
    remaining = list(dict.fromkeys(str(column) for column in columns))
    ordered = [column for column in _PREFERRED_RANK_COLUMN_ORDER if column in remaining]
    ordered.extend(column for column in remaining if column not in ordered)
    return ordered


def infer_rank_column_scopes(
    rankings_dir: Path,
    players: int,
) -> dict[str, RankingScope]:
    """Infer whether each rank column is player-scope or coalition-scope."""

    target_dir = _rankings_target_dir(rankings_dir, players)
    scopes: dict[str, RankingScope] = {}
    for csv_path in sorted(target_dir.glob("game_*.csv")):
        df = pd.read_csv(csv_path)
        player_cols = _player_columns(df)
        if len(player_cols) != players:
            continue
        membership_count = _player_membership_counts(df, player_cols)
        singleton_mask = membership_count == 1
        non_empty_mask = membership_count >= 1
        for column_name in [str(column) for column in df.columns if str(column).startswith("rank_")]:
            raw = pd.to_numeric(df[column_name], errors="coerce")
            present = raw.notna()
            if not bool(present.any()):
                continue
            if bool((present & ~singleton_mask).any()):
                if bool((present & non_empty_mask).any()):
                    scopes[column_name] = "coalition"
            else:
                scopes.setdefault(column_name, "player")
    return {name: scopes[name] for name in _ordered_rank_columns(scopes)}


def collect_effective_rank_table(
    rankings_dir: Path,
    players: int,
    *,
    rank_cols: list[str],
    scope: RankingScope,
) -> pd.DataFrame:
    """Collect effective ranks across all ranking CSV files for one scope."""

    target_dir = _rankings_target_dir(rankings_dir, players)
    frames: list[pd.DataFrame] = []
    for csv_path in sorted(target_dir.glob("game_*.csv")):
        df = pd.read_csv(csv_path)
        player_cols = _player_columns(df)
        if len(player_cols) != players:
            continue

        subset = _subset_for_scope(df, player_cols, scope)
        if not bool(subset.any()):
            continue

        out = pd.DataFrame(index=df.index)
        for column_name in rank_cols:
            if column_name not in df.columns:
                out[column_name] = np.nan
                continue
            raw = pd.to_numeric(df[column_name], errors="coerce")
            raw_subset = raw.loc[subset & raw.notna()]
            if raw_subset.empty:
                out[column_name] = np.nan
                continue
            effective_subset = _competition_rank(raw_subset)
            full_column = pd.Series(index=df.index, dtype=float)
            full_column.loc[effective_subset.index] = effective_subset.astype(float)
            full_column.loc[~subset] = np.nan
            out[column_name] = full_column

        frames.append(out.loc[subset, rank_cols])

    if not frames:
        return pd.DataFrame(columns=rank_cols)
    return pd.concat(frames, axis=0, ignore_index=True)


def collect_rule_correlation_matrix(
    rankings_dir: Path,
    players: int,
    *,
    rank_cols: list[str],
    scope: RankingScope,
    method: str = "spearman",
) -> pd.DataFrame:
    """Return a rule-by-rule correlation matrix for one scope."""

    table = collect_effective_rank_table(rankings_dir, players, rank_cols=rank_cols, scope=scope)
    if table.empty:
        return pd.DataFrame()
    return table.corr(method=str(method), min_periods=1)


def collect_rank_pairs(
    rankings_dir: Path,
    players: int,
    *,
    x_col: str,
    y_col: str,
    scope: RankingScope,
) -> RankPairSummary:
    """Collect pairwise effective-rank frequencies across ranking CSV files."""

    target_dir = _rankings_target_dir(rankings_dir, players)
    counts: Counter[tuple[int, int]] = Counter()
    processed_files = 0
    used_files = 0
    total_pairs = 0

    for csv_path in sorted(target_dir.glob("game_*.csv")):
        processed_files += 1
        df = pd.read_csv(csv_path)
        player_cols = _player_columns(df)
        if len(player_cols) != players:
            continue
        if x_col not in df.columns or y_col not in df.columns:
            continue

        subset = _subset_for_scope(df, player_cols, scope)
        x_ranks = pd.to_numeric(df[x_col], errors="coerce")
        y_ranks = pd.to_numeric(df[y_col], errors="coerce")
        valid = subset & x_ranks.notna() & y_ranks.notna()
        if not bool(valid.any()):
            continue

        effective_x = _competition_rank(x_ranks.loc[valid])
        effective_y = _competition_rank(y_ranks.loc[valid])

        added = 0
        for x_rank, y_rank in zip((int(value) for value in effective_x), (int(value) for value in effective_y)):
            if x_rank <= 0 or y_rank <= 0:
                continue
            counts[(x_rank, y_rank)] += 1
            total_pairs += 1
            added += 1
        if added > 0:
            used_files += 1

    if not counts:
        return RankPairSummary(
            matrix=pd.DataFrame(),
            total_pairs=0,
            processed_files=processed_files,
            used_files=used_files,
        )

    x_values = sorted({x for x, _ in counts})
    y_values = sorted({y for _, y in counts})
    rows: list[list[int]] = []
    for y_rank in y_values:
        rows.append([counts.get((x_rank, y_rank), 0) for x_rank in x_values])
    matrix = pd.DataFrame(rows, index=y_values, columns=x_values)
    matrix.index.name = y_col
    matrix.columns.name = x_col
    return RankPairSummary(
        matrix=matrix,
        total_pairs=total_pairs,
        processed_files=processed_files,
        used_files=used_files,
    )


def render_rank_pair_heatmap(
    matrix: pd.DataFrame,
    out_path: Path,
    *,
    x_col: str,
    y_col: str,
    dpi: int = 150,
    title: str | None = None,
) -> Path:
    """Render a pairwise effective-rank frequency heatmap."""

    if matrix.empty:
        raise ValueError("Cannot render rank heatmap without data.")

    values = matrix.to_numpy(dtype=float)
    height, width = values.shape
    fig_width = max(6.0, 0.6 * width + 2.5)
    fig_height = max(5.0, 0.6 * height + 2.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(values, origin="lower", cmap=plt.get_cmap("Blues"), aspect="auto")

    ax.set_xticks(np.arange(width), labels=[str(value) for value in matrix.columns])
    ax.set_yticks(np.arange(height), labels=[str(value) for value in matrix.index])
    x_label = _rank_column_display_name(x_col)
    y_label = _rank_column_display_name(y_col)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title or f"Frequency of {y_label} vs {x_label}")

    for row_index in range(height):
        for column_index in range(width):
            count = int(values[row_index, column_index])
            if count > 0:
                ax.text(column_index, row_index, str(count), ha="center", va="center", color="black", fontsize=9)

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="count")
    ax.grid(False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path


def render_correlation_heatmap(
    matrix: pd.DataFrame,
    out_path: Path,
    *,
    dpi: int = 150,
    title: str | None = None,
) -> Path:
    """Render a rule-by-rule correlation heatmap."""

    if matrix.empty:
        raise ValueError("Cannot render correlation heatmap without data.")

    labels = [_rank_column_display_name(str(column)) for column in matrix.columns]
    values = matrix.to_numpy(dtype=float)
    size = len(labels)
    fig_size = max(6.5, 0.55 * size + 2.5)

    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    image = ax.imshow(values, origin="lower", cmap=plt.get_cmap("RdBu_r"), vmin=-1.0, vmax=1.0)
    ticks = np.arange(size)
    ax.set_xticks(ticks, labels=labels, rotation=45, ha="right")
    ax.set_yticks(ticks, labels=labels)
    ax.set_title(title or "Rule Rank Correlation")

    for row_index in range(size):
        for column_index in range(size):
            value = values[row_index, column_index]
            if np.isnan(value):
                continue
            ax.text(column_index, row_index, f"{value:.2f}", ha="center", va="center", color="black", fontsize=8)

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="correlation")
    ax.grid(False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path


__all__ = [
    "RankPairSummary",
    "RankingScope",
    "collect_effective_rank_table",
    "collect_rank_pairs",
    "collect_rule_correlation_matrix",
    "infer_rank_column_scopes",
    "render_correlation_heatmap",
    "render_rank_pair_heatmap",
]
