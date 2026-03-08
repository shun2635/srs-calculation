"""Configuration loader for default CLI values.

日本語補足: 既定値を `config.yaml` で一元管理します。存在しない場合は組み込み既定値を使用。
優先順位は (1) コマンド引数 > (2) config.yaml > (3) 組み込み既定 です。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


@dataclass(frozen=True)
class Defaults:
    output_base: str = "outputs"
    theme: str = "light"
    gen_games_count: int = 1
    gen_games_max_score: int | None = None  # if None, use 2^n-1
    gen_games_seed: int | None = None
    # Figures
    figures_png_dpi: int = 150
    # Pipeline
    pipeline_rules: tuple[str, ...] = (
        "shapley",
        "banzhaf",
        "lexcel",
        "o-banzhaf",
        "g-shapley",
        "g-sum-shapley",
        "shapley-interaction",
        "banzhaf-interaction",
        "rp-index",
        "ud",
        "du",
        "red-index",
        "g-lexcel",
        "g-o-banzhaf",
    )
    # Axioms (batch check defaults)
    axiom_rules: tuple[str, ...] = (
        "rp-index",
        "ud",
        "du",
        "red-index",
        "shapley-interaction",
        "banzhaf-interaction",
        "g-shapley",
        "g-sum-shapley",
        "g-lexcel",
        "g-o-banzhaf",
    )


def load_config(path: Path | None) -> Mapping[str, Any]:
    """Load configuration from YAML if present; otherwise return empty mapping.

    日本語補足: 指定パスが None の場合はカレントの `config.yaml` が存在すれば読み込みます。
    フォーマット例はリポジトリ同梱の `config.yaml` を参照してください。
    """
    candidate: Path | None
    if path is not None:
        candidate = path
    else:
        default = Path("config.yaml")
        candidate = default if default.exists() else None

    if candidate is None or not candidate.exists():
        return {}

    data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


__all__ = ["Defaults", "load_config"]
