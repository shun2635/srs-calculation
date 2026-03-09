"""Dataset path and metadata adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


@dataclass(frozen=True)
class FeatureLabel:
    """Player-to-feature metadata entry."""

    player: str
    column: str
    label: str = ""
    description: str = ""


def default_feature_mask_inputs_root() -> Path:
    """Return the default root for feature-mask datasets."""

    return Path("inputs") / "feature_mask_tables"


def resolve_feature_mask_dataset_dir(dataset_id: str, *, inputs_root: Path | None = None) -> Path:
    """Resolve one feature-mask dataset directory."""

    root = default_feature_mask_inputs_root() if inputs_root is None else Path(inputs_root)
    return root / str(dataset_id)


def resolve_real_dataset_out_base(dataset_id: str, *, out_root: Path | None = None) -> Path:
    """Resolve the dataset-scoped output directory for real-data workflows."""

    root = Path("outputs") / "real" if out_root is None else Path(out_root)
    return root if root.name == str(dataset_id) else root / str(dataset_id)


def write_feature_labels_yaml(
    path: Path,
    *,
    feature_columns: list[str],
    feature_descriptions: Mapping[str, str] | None = None,
    feature_labels: Mapping[str, str] | None = None,
) -> None:
    """Write player-to-feature metadata used by real-data workflows."""

    descriptions = dict(feature_descriptions or {})
    labels = dict(feature_labels or {})
    data = {
        "features": [
            {
                "player": f"player{index + 1}",
                "column": str(column),
                "label": str(labels.get(str(column), "")),
                "description": str(descriptions.get(str(column), "")),
            }
            for index, column in enumerate(feature_columns)
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def read_feature_labels_yaml(path: Path) -> list[FeatureLabel]:
    """Read player-to-feature metadata from a features.yaml file."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "features" not in raw:
        raise ValueError("Invalid features.yaml: expected mapping with 'features'.")
    items = raw["features"]
    if not isinstance(items, list):
        raise ValueError("Invalid features.yaml: 'features' must be a list.")

    labels: list[FeatureLabel] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        player = str(item.get("player", "")).strip()
        column = str(item.get("column", "")).strip()
        label = str(item.get("label", "")).strip()
        description = str(item.get("description", "")).strip()
        if not player or not column:
            continue
        labels.append(
            FeatureLabel(
                player=player,
                column=column,
                label=label,
                description=description,
            )
        )
    if not labels:
        raise ValueError("Invalid features.yaml: no valid feature entries.")
    return labels


__all__ = [
    "FeatureLabel",
    "default_feature_mask_inputs_root",
    "read_feature_labels_yaml",
    "resolve_feature_mask_dataset_dir",
    "resolve_real_dataset_out_base",
    "write_feature_labels_yaml",
]
