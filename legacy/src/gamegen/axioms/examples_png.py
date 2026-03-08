"""Render PNG examples for axiom violations."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg", force=True)
import japanize_matplotlib  # type: ignore[import-untyped]  # noqa: E402,F401
import matplotlib.pyplot as plt  # noqa: E402

from ..display_names import axiom_display_name, rule_display_name  # noqa: E402


def _player_column_count(header: list[str]) -> int:
    count = 0
    for name in header:
        if str(name).startswith("player"):
            count += 1
        else:
            break
    return count


def _mask_from_row_prefix(row: list[str], n: int) -> int:
    mask = 0
    for i in range(n):
        try:
            v = int(row[i])
        except Exception:
            v = 0
        if v != 0:
            mask |= 1 << i
    return mask


def _bits(mask: int, n: int) -> str:
    return "".join("1" if (int(mask) >> i) & 1 else "0" for i in range(n))


def _coalition_set(mask: int, n: int) -> str:
    if int(mask) == 0:
        return "∅"
    members = [str(i + 1) for i in range(int(n)) if (int(mask) >> i) & 1]
    return "{" + ",".join(members) + "}"


def _score_by_mask_from_rows(rows: list[list[str]], n: int, header: list[str]) -> dict[int, float]:
    try:
        idx_score = header.index("score")
    except ValueError:
        return {}
    out: dict[int, float] = {}
    for row in rows:
        mask = _mask_from_row_prefix(row, n)
        try:
            out[int(mask)] = float(row[idx_score])
        except Exception:
            continue
    return out


def _base_rank_by_mask_from_rows(rows: list[list[str]], n: int, header: list[str]) -> dict[int, int]:
    try:
        idx_rank = header.index("rank")
    except ValueError:
        return {}
    out: dict[int, int] = {}
    for row in rows:
        mask = _mask_from_row_prefix(row, n)
        try:
            out[int(mask)] = int(row[idx_rank])
        except Exception:
            continue
    return out


def _theta_lexcel_vectors(scores_by_mask: dict[int, float], n: int) -> dict[int, str]:
    """Return a string vector per player index (0-based)."""
    if n <= 0 or not scores_by_mask:
        return {}
    try:
        from ..rules import lexcel as lexcel_rules
    except Exception:
        return {}
    _, level_of_mask = lexcel_rules.build_levels({int(k): float(v) for k, v in scores_by_mask.items()})
    level_count = max(level_of_mask.values(), default=0)
    theta = lexcel_rules.theta_vectors(level_of_mask, n, level_count)
    return {i: "(" + ",".join(str(x) for x in theta[i]) + ")" for i in range(n)}


def _theta_g_lexcel_vectors(base_rank_by_mask: dict[int, int], n: int) -> dict[int, str]:
    """Return Theta(T) vectors per coalition mask for group lex-cel."""
    if n <= 0 or not base_rank_by_mask:
        return {}
    # Build layers Σ_1..Σ_l from base dense ranks: same rank -> same layer (excluding empty coalition).
    layers: dict[int, list[int]] = {}
    for mask, level in base_rank_by_mask.items():
        if int(mask) == 0:
            continue
        layers.setdefault(int(level), []).append(int(mask))
    if not layers:
        return {}
    ordered_levels = sorted(layers.keys())
    layer_list = [layers[lvl] for lvl in ordered_levels]

    size = 1 << int(n)
    accum: list[list[int]] = []
    for layer in layer_list:
        indicator = [0] * size
        for mask in layer:
            indicator[int(mask)] = 1
        transformed = indicator[:]
        for bit in range(int(n)):
            step = 1 << bit
            for mask in range(size):
                if (mask & step) == 0:
                    transformed[mask] += transformed[mask | step]
        accum.append(transformed)

    theta: dict[int, str] = {}
    for mask in range(1, size):
        vec = tuple(values[mask] for values in accum)
        theta[int(mask)] = "(" + ",".join(str(x) for x in vec) + ")"
    return theta


def render_violation_example_png(
    *,
    rankings_csv: Path,
    rule_name: str,
    axiom_id: str,
    left_mask: int,
    right_mask: int,
    out_path: Path,
    extra_masks: Iterable[int] = (),
) -> None:
    """Render a small table highlighting two coalitions involved in a violation."""
    with rankings_csv.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if r]

    header_s = [str(x) for x in header]
    n = _player_column_count(header_s)
    if n <= 0:
        raise ValueError("ranking csv has no player columns")
    idx_score = header_s.index("score") if "score" in header_s else None
    idx_rank = header_s.index("rank") if "rank" in header_s else None
    col_rule = f"rank_{rule_name}"
    idx_rule = header_s.index(col_rule) if col_rule in header_s else None

    scores_by_mask = _score_by_mask_from_rows([[str(x) for x in r] for r in rows], n, header_s)
    theta_lexcel = _theta_lexcel_vectors(scores_by_mask, n) if rule_name == "lexcel" else {}
    base_rank_by_mask = _base_rank_by_mask_from_rows([[str(x) for x in r] for r in rows], n, header_s)
    theta_g_lexcel = _theta_g_lexcel_vectors(base_rank_by_mask, n) if rule_name == "g-lexcel" else {}

    col_metric = f"score_{rule_name}"
    idx_metric = header_s.index(col_metric) if col_metric in header_s else None

    mask_to_row: dict[int, list[str]] = {}
    for row in rows:
        mask = _mask_from_row_prefix([str(x) for x in row], n)
        mask_to_row[int(mask)] = [str(x) for x in row]

    masks = [int(left_mask), int(right_mask), *[int(m) for m in extra_masks]]
    seen: set[int] = set()
    selected: list[int] = []
    for m in masks:
        if m in seen:
            continue
        if m in mask_to_row:
            selected.append(m)
            seen.add(m)

    # Order rows by base score descending (then by mask ascending for stability).
    def _score_key(mask: int) -> float:
        try:
            return float(scores_by_mask.get(int(mask), float("-inf")))
        except Exception:
            return float("-inf")

    selected = sorted(selected, key=lambda m: (-_score_key(m), int(m)))

    show_metric = idx_metric is not None
    show_indicator = bool(theta_lexcel or theta_g_lexcel)

    def row_values(mask: int) -> list[str]:
        r = mask_to_row[int(mask)]
        score = r[idx_score] if idx_score is not None and idx_score < len(r) else ""
        rank = r[idx_rank] if idx_rank is not None and idx_rank < len(r) else ""
        metric = r[idx_metric] if idx_metric is not None and idx_metric < len(r) else ""
        rule_rank = r[idx_rule] if idx_rule is not None and idx_rule < len(r) else ""
        theta = ""
        if theta_lexcel:
            if int(mask) != 0 and (int(mask) & (int(mask) - 1)) == 0:
                idx = int(mask).bit_length() - 1
                theta = theta_lexcel.get(idx, "")
        if theta_g_lexcel:
            theta = theta_g_lexcel.get(int(mask), "")
        values: list[str] = [_coalition_set(mask, n), score, rank]
        if show_metric:
            values.append(metric)
        if show_indicator:
            values.append(theta)
        values.append(rule_rank)
        return values

    table_rows = [row_values(m) for m in selected]
    col_labels: list[str] = ["coalition", "score", "rank"]
    if show_metric:
        col_labels.append(col_metric)
    if show_indicator:
        col_labels.append("indicator")
    col_labels.append(f"rank ({rule_display_name(rule_name)})")

    fig, ax = plt.subplots(figsize=(9, max(2.0, 0.6 + 0.4 * len(table_rows))))
    ax.axis("off")
    axiom_label = axiom_display_name(axiom_id)
    rule_label = rule_display_name(rule_name)
    ax.set_title(
        f"{axiom_label} violation example ({rule_label})\n"
        f"{rankings_csv.name}: {_coalition_set(left_mask,n)} vs {_coalition_set(right_mask,n)}"
    )

    cell_colours = [["white"] * len(col_labels) for _ in table_rows]
    for i, m in enumerate(selected):
        if int(m) == int(left_mask):
            cell_colours[i] = ["#ffe5e5"] * len(col_labels)
        elif int(m) == int(right_mask):
            cell_colours[i] = ["#e5f0ff"] * len(col_labels)

    tab = ax.table(
        cellText=table_rows,
        colLabels=col_labels,
        cellColours=cell_colours,
        cellLoc="center",
        loc="center",
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(10)
    tab.scale(1.0, 1.4)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


__all__ = ["render_violation_example_png"]
