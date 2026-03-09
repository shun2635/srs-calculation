"""YAML-backed configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(path: Path | None) -> dict[str, Any]:
    """Load a YAML config file as a mapping, or return an empty mapping."""

    if path is None:
        return {}
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


def get_realgen_import_rank_bins(path: Path | None, *, default: int = 5) -> int:
    """Read realgen.import_rank_bins from a config file when present."""

    config = load_yaml_config(path)
    realgen = config.get("realgen")
    if not isinstance(realgen, dict):
        return int(default)
    raw = realgen.get("import_rank_bins", default)
    try:
        return int(raw)
    except Exception:
        return int(default)


__all__ = ["get_realgen_import_rank_bins", "load_yaml_config"]
