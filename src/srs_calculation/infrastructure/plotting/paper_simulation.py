"""Paper simulation figures."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _wrapped_label(value: object) -> str:
    text = str(value)
    if len(text) <= 14:
        return text
    return "\n".join(textwrap.wrap(text, width=14, break_long_words=False))


def _render_bar_chart(
    *,
    labels: list[str],
    values: list[float | None],
    title: str,
    ylabel: str,
    pdf_path: Path,
    png_path: Path,
) -> tuple[Path, Path]:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_values = [np.nan if value is None else float(value) for value in values]
    x_positions = np.arange(len(labels))
    fig_width = max(6.0, 0.8 * len(labels) + 2.0)
    fig, ax = plt.subplots(figsize=(fig_width, 4.2))
    ax.bar(x_positions, numeric_values, color="#4c78a8", width=0.65)
    ax.set_xticks(x_positions, labels=labels)
    ax.set_ylim(-1.0 if any((value is not None and value < 0) for value in values) else 0.0, 1.0)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)

    if all(value is None for value in values):
        ax.text(0.5, 0.5, "No valid values", transform=ax.transAxes, ha="center", va="center")
    else:
        for x_pos, value in zip(x_positions, values, strict=True):
            if value is None:
                continue
            ax.text(
                x_pos,
                float(value),
                f"{float(value):.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    return pdf_path, png_path


def render_reversal_consistency_figure(
    summary_rows: Iterable[object],
    *,
    pdf_path: Path,
    png_path: Path,
) -> tuple[Path, Path]:
    """Render Reversal consistency by k plus overall."""

    rows = list(summary_rows)
    labels = [f"k={row.k}" if str(row.k) != "overall" else "overall" for row in rows]
    values = [row.mean_consistency for row in rows]
    return _render_bar_chart(
        labels=labels,
        values=values,
        title="Reversal Consistency of Rankdiff",
        ylabel="mean consistency",
        pdf_path=pdf_path,
        png_path=png_path,
    )


def render_rank_correlation_figure(
    summary_rows: Iterable[object],
    *,
    pdf_path: Path,
    png_path: Path,
) -> tuple[Path, Path]:
    """Render GL vs Rankdiff rank correlation by k plus overall."""

    rows = list(summary_rows)
    labels = [f"k={row.k}" if str(row.k) != "overall" else "overall" for row in rows]
    values = [row.mean_correlation for row in rows]
    return _render_bar_chart(
        labels=labels,
        values=values,
        title="Group Lex-cel vs Rankdiff Rank Correlation",
        ylabel="mean correlation",
        pdf_path=pdf_path,
        png_path=png_path,
    )


def render_line_series(
    *,
    x_values: list[int],
    series: list[tuple[str, list[float | None]]],
    title: str,
    xlabel: str,
    ylabel: str,
    pdf_path: Path,
    png_path: Path,
    ylim: tuple[float, float] | None = (0.0, 1.0),
) -> tuple[Path, Path]:
    """Render one or more value-vs-x line series (e.g. a metric over n)."""

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(max(6.0, 0.9 * len(x_values) + 2.5), 4.4))
    for label, values in series:
        y_values = [np.nan if value is None else float(value) for value in values]
        ax.plot(x_values, y_values, marker="o", label=label)
    ax.set_xticks(list(x_values))
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.25)
    if len(series) > 1:
        ax.legend(fontsize=8, loc="best")

    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    return pdf_path, png_path


def render_paper_heatmap(
    *,
    row_labels: list[str],
    column_labels: list[str],
    values: list[list[float | None]],
    vmin: float,
    vmax: float,
    cmap_name: str,
    colorbar_label: str,
    figsize: tuple[float, float] | None = None,
    title: str | None = None,
    pdf_path: Path,
    png_path: Path,
) -> tuple[Path, Path]:
    """Render a paper-ready matrix heatmap with numeric cell annotations."""

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    data = np.array(
        [[np.nan if value is None else float(value) for value in row] for row in values],
        dtype=float,
    )
    masked_data = np.ma.masked_invalid(data)
    cmap = plt.get_cmap(cmap_name).copy()
    cmap.set_bad(color="#f2f2f2")

    fig_width = max(5.8, 0.78 * len(column_labels) + 3.0)
    fig_height = max(4.4, 0.58 * len(row_labels) + 1.6)
    if figsize is not None:
        fig_width, fig_height = figsize
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(masked_data, vmin=float(vmin), vmax=float(vmax), cmap=cmap)
    if title:
        ax.set_title(title, fontsize=9, pad=8)

    ax.set_xticks(np.arange(len(column_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels([_wrapped_label(label) for label in column_labels])
    ax.set_yticklabels([_wrapped_label(label) for label in row_labels])
    ax.tick_params(axis="x", labelrotation=35, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)

    ax.set_xticks(np.arange(len(column_labels) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(row_labels) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row_index, row in enumerate(values):
        for col_index, value in enumerate(row):
            if value is None:
                label = "N/A"
                color = "#555555"
            else:
                label = f"{float(value):.2f}"
                normalized = (float(value) - float(vmin)) / (float(vmax) - float(vmin))
                red, green, blue, _ = cmap(float(np.clip(normalized, 0.0, 1.0)))
                luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                color = "white" if luminance < 0.45 else "black"
            ax.text(
                col_index,
                row_index,
                label,
                ha="center",
                va="center",
                fontsize=7.5,
                color=color,
            )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label(colorbar_label, fontsize=8)
    colorbar.ax.tick_params(labelsize=8)

    fig.tight_layout()
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


__all__ = [
    "render_line_series",
    "render_paper_heatmap",
    "render_rank_correlation_figure",
    "render_reversal_consistency_figure",
]
