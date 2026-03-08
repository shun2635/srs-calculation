"""Feature-label mapping for real-data imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


@dataclass(frozen=True)
class FeatureLabel:
    player: str  # e.g. "player1"
    column: str  # original feature column name
    label: str = ""  # preferred display label (e.g. short Japanese)
    description: str = ""


def write_feature_labels_yaml(
    path: Path,
    *,
    feature_columns: list[str],
    feature_descriptions: Mapping[str, str] | None = None,
    feature_labels: Mapping[str, str] | None = None,
) -> None:
    desc = dict(feature_descriptions or {})
    labels = dict(feature_labels or {})
    data = {
        "features": [
            {
                "player": f"player{i+1}",
                "column": str(col),
                "label": str(labels.get(str(col), "")),
                "description": str(desc.get(str(col), "")),
            }
            for i, col in enumerate(feature_columns)
        ]
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def read_feature_labels_yaml(path: Path) -> list[FeatureLabel]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "features" not in raw:
        raise ValueError("Invalid features.yaml: expected mapping with 'features'.")
    items = raw["features"]
    if not isinstance(items, list):
        raise ValueError("Invalid features.yaml: 'features' must be a list.")
    out: list[FeatureLabel] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        player = str(it.get("player", "")).strip()
        column = str(it.get("column", "")).strip()
        label = str(it.get("label", "")).strip()
        description = str(it.get("description", "")).strip()
        if not player or not column:
            continue
        out.append(FeatureLabel(player=player, column=column, label=label, description=description))
    if not out:
        raise ValueError("Invalid features.yaml: no valid feature entries.")
    return out


__all__ = ["FeatureLabel", "read_feature_labels_yaml", "write_feature_labels_yaml"]
