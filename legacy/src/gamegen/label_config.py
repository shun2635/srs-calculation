"""Load rule/axiom labels and ordering from repo-root config files.

This project keeps human-facing labels and preferred ordering in versioned YAML
files under the repository root `config/` directory so they can be updated
without touching Python source.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml


def _repo_root() -> Path:
    # src/gamegen/<this_file>.py -> src -> <repo root>
    return Path(__file__).resolve().parents[2]


def _labels_yaml_path() -> Path:
    return _repo_root() / "config" / "labels.yaml"


def _as_dict(x: object) -> dict[str, Any]:
    return dict(x) if isinstance(x, dict) else {}


@lru_cache(maxsize=1)
def load_labels() -> dict[str, Any]:
    """Return merged labels configuration from `config/labels.yaml` if present."""
    path = _labels_yaml_path()
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _section(kind: str) -> Mapping[str, Any]:
    cfg = load_labels()
    return _as_dict(cfg.get(kind))


def rule_display_names() -> dict[str, str]:
    section = _section("rules")
    raw = section.get("display_names")
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def axiom_display_names() -> dict[str, str]:
    section = _section("axioms")
    raw = section.get("display_names")
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def rule_order() -> list[str]:
    section = _section("rules")
    raw = section.get("order")
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]


def axiom_order() -> list[str]:
    section = _section("axioms")
    raw = section.get("order")
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]


def apply_order(items: list[str], preferred: list[str]) -> list[str]:
    """Return items reordered by preferred list, appending unknowns in original order."""
    if not preferred:
        return list(items)
    present = set(str(x) for x in items)
    out: list[str] = []
    seen: set[str] = set()
    for x in preferred:
        key = str(x)
        if key in present and key not in seen:
            out.append(key)
            seen.add(key)
    for x in items:
        key = str(x)
        if key in seen:
            continue
        out.append(key)
        seen.add(key)
    return out


__all__ = [
    "apply_order",
    "axiom_display_names",
    "axiom_order",
    "load_labels",
    "rule_display_names",
    "rule_order",
]

