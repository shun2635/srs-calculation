"""Dataset path and metadata adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import yaml


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


__all__ = [
    "default_feature_mask_inputs_root",
    "resolve_feature_mask_dataset_dir",
    "resolve_real_dataset_out_base",
    "write_feature_labels_yaml",
]
