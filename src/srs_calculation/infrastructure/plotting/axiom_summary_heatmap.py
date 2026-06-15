"""Synthetic axiom-summary heatmap helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_RULE_LABELS: dict[str, str] = {
    "shapley": "Shapley",
    "banzhaf": "Banzhaf",
    "lexcel": "Lex-cel",
    "ordinal_banzhaf": "Ordinal Banzhaf",
    "group_shapley": "Shapley Group Value",
    "group_sum_shapley": "Sum of Shapley Values",
    "group_ordinal_banzhaf": "Group Ordinal Banzhaf",
    "group_lexcel": "Group Lex-cel",
    "shapley_interaction": "Shapley Interaction",
    "banzhaf_interaction": "Banzhaf Interaction",
    "rankdiff": "Rankdiff",
    "ud": "UD",
    "du": "DU",
    "red_index": "Redundancy",
}

_AXIOM_LABELS: dict[str, str] = {
    "reversal-2p": "Reversal 2p",
    "reversal-weak-n": "Reversal Weak n",
    "give-2p": "Give 2p",
    "take-2p": "Take 2p",
    "give-weak-n": "Give Weak n",
    "take-weak-n": "Take Weak n",
    "redundancy": "Redundancy",
}


def render_axiom_summary_heatmap(
    summary_csv: Path,
    out_path: Path,
    *,
    dpi: int = 150,
    title: str | None = None,
) -> Path:
    """Render a heatmap from one axiom summary CSV."""

    df = pd.read_csv(summary_csv)
    required = {"rule", "axiom", "satisfied_rate"}
    if not required.issubset(df.columns):
        missing = sorted(required - set(df.columns))
        raise ValueError(f"summary CSV missing required columns: {missing}")

    table = df.pivot(index="rule", columns="axiom", values="satisfied_rate")
    if table.empty:
        raise ValueError("summary CSV has no data")

    values = table.to_numpy(dtype=float)
    fig_width = max(7.0, 0.6 * len(table.columns) + 2.5)
    fig_height = max(5.0, 0.5 * len(table.index) + 2.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(values, origin="lower", cmap=plt.get_cmap("Blues"), vmin=0.0, vmax=1.0, aspect="auto")

    x_labels = [_AXIOM_LABELS.get(str(value), str(value)) for value in table.columns]
    y_labels = [_RULE_LABELS.get(str(value), str(value)) for value in table.index]
    ax.set_xticks(np.arange(len(x_labels)), labels=x_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(y_labels)), labels=y_labels)
    ax.set_xlabel("axiom")
    ax.set_ylabel("rule")
    ax.set_title(title or "Axiom Satisfaction Rate")

    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            value = values[row_index, column_index]
            if np.isnan(value):
                continue
            ax.text(column_index, row_index, f"{value:.2f}", ha="center", va="center", color="black", fontsize=8)

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="satisfied_rate")
    ax.grid(False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    return out_path


__all__ = ["render_axiom_summary_heatmap"]
