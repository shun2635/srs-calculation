"""Render heatmaps from axiom summary.csv."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import japanize_matplotlib  # type: ignore[import-untyped]  # noqa: E402,F401
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ..display_names import axiom_display_name, rule_display_name  # noqa: E402
from ..label_config import apply_order, axiom_order, rule_order  # noqa: E402


def order_axiom_labels(labels: list[str]) -> list[str]:
    return apply_order([str(x) for x in labels], axiom_order())


def order_rule_labels(labels: list[str]) -> list[str]:
    return apply_order([str(x) for x in labels], rule_order())


def render_axiom_summary_heatmap(
    summary_csv: Path,
    out_path: Path,
    *,
    dpi: int = 150,
    title: str | None = None,
) -> None:
    """Render a heatmap with rows=rules, cols=axioms, value=satisfied_rate."""
    df = pd.read_csv(summary_csv)
    required = {"rule", "axiom", "satisfied_rate"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"summary.csv missing required columns: {sorted(required)}")

    df = df.copy()
    df["satisfied_rate"] = pd.to_numeric(df["satisfied_rate"], errors="coerce")

    pivot = df.pivot(index="rule", columns="axiom", values="satisfied_rate")
    if pivot.empty:
        raise ValueError("summary.csv has no data to plot")

    pivot = pivot.reindex(index=order_rule_labels([str(x) for x in pivot.index]))
    preferred_axioms = axiom_order()
    if preferred_axioms:
        available = {str(c) for c in pivot.columns}
        desired = [a for a in preferred_axioms if a in available]
        if desired:
            pivot = pivot.reindex(columns=desired)
    else:
        pivot = pivot.reindex(columns=order_axiom_labels([str(c) for c in pivot.columns]))

    values = pivot.to_numpy(dtype=float)
    n_rules, n_axioms = values.shape
    fig_w = max(8.0, 0.55 * n_axioms + 3.0)
    fig_h = max(6.0, 0.45 * n_rules + 3.0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = plt.get_cmap("Blues")
    image = ax.imshow(values, origin="lower", cmap=cmap, vmin=0.0, vmax=1.0, aspect="auto")

    axiom_labels = [axiom_display_name(str(x)) for x in pivot.columns]
    rule_labels = [rule_display_name(str(x)) for x in pivot.index]
    ax.set_xticks(np.arange(n_axioms), labels=axiom_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(n_rules), labels=rule_labels)
    ax.set_xlabel("axiom")
    ax.set_ylabel("rule")
    ax.set_title(title or f"Axiom satisfied_rate heatmap ({summary_csv.parent.name})")

    for y in range(n_rules):
        for x in range(n_axioms):
            v = values[y, x]
            if np.isnan(v):
                continue
            ax.text(x, y, f"{v:.2f}", ha="center", va="center", color="black", fontsize=8)

    fig.colorbar(image, ax=ax, fraction=0.050, pad=0.04, label="整合率")
    ax.grid(False)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


__all__ = ["order_axiom_labels", "order_rule_labels", "render_axiom_summary_heatmap"]
