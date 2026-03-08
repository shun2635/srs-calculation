"""IO helpers for reading and writing game specifications.

日本語補足: ゲーム定義の JSON/YAML 読み書きとスキーマ検証を提供します。
ファイル拡張子で自動判別します (.json / .yaml / .yml)。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping

import yaml

from .types import CardinalGame, Coalition, CoalitionEncoding, OrdinalGame

_JSON_EXT = {".json"}
_YAML_EXT = {".yaml", ".yml"}


class GameIOError(ValueError):
    """Raised when a game file cannot be decoded or validated.

    日本語補足: 入出力や検証で失敗した場合に投げます。
    """


def _normalise_path(path: Path) -> Path:
    if not path.suffix:
        raise GameIOError("File extension required to choose JSON or YAML serialization.")
    return path


def _encode_cardinal(game: Mapping[str, Any]) -> CardinalGame:
    if game.get("type") != "cardinal":
        raise GameIOError("Expected a cardinal game for encoding.")
    n = int(game["n"])
    encoding = CoalitionEncoding(n)
    serialisable: Dict[str, float] = {}
    values: Mapping[Coalition, float] = game["v"]
    for coalition, value in values.items():
        serialisable[encoding.encode(coalition)] = float(value)
    return {"type": "cardinal", "n": n, "v": serialisable}


def _encode_ordinal(game: Mapping[str, Any]) -> OrdinalGame:
    if game.get("type") != "ordinal":
        raise GameIOError("Expected an ordinal game for encoding.")
    n = int(game["n"])
    encoding = CoalitionEncoding(n)
    order: Iterable[Iterable[Coalition]] = game["order"]
    serialisable = [[encoding.encode(coal) for coal in tier] for tier in order]
    return {"type": "ordinal", "n": n, "order": serialisable}


def _decode_cardinal(data: Mapping[str, Any]) -> Dict[str, Any]:
    if data.get("type") != "cardinal":
        raise GameIOError("Not a cardinal game payload.")
    n = int(data["n"])
    encoding = CoalitionEncoding(n)
    raw_v = data.get("v")
    if not isinstance(raw_v, Mapping):
        raise GameIOError("Cardinal game payload requires mapping field 'v'.")
    result: MutableMapping[Coalition, float] = {}
    for key, value in raw_v.items():
        coalition = encoding.decode(str(key))
        result[coalition] = float(value)
    _validate_cardinal_payload(n, result)
    return {"type": "cardinal", "n": n, "v": dict(result)}


def _decode_ordinal(data: Mapping[str, Any]) -> Dict[str, Any]:
    if data.get("type") != "ordinal":
        raise GameIOError("Not an ordinal game payload.")
    n = int(data["n"])
    encoding = CoalitionEncoding(n)
    raw_order = data.get("order")
    if not isinstance(raw_order, Iterable):
        raise GameIOError("Ordinal game payload requires iterable 'order'.")
    tiers: list[list[Coalition]] = []
    seen: set[Coalition] = set()
    for raw_tier in raw_order:
        if not isinstance(raw_tier, Iterable):
            raise GameIOError("Ordinal order tiers must be iterable.")
        tier: list[Coalition] = []
        for item in raw_tier:
            coalition = encoding.decode(str(item))
            tier.append(coalition)
            seen.add(coalition)
        tiers.append(tier)
    _validate_ordinal_payload(n, tiers)
    return {"type": "ordinal", "n": n, "order": tiers}


def save_game(game: Mapping[str, Any], path: Path) -> None:
    """Persist a game as JSON or YAML based on the file extension.

    日本語補足: `type` に応じて内部表現を JSON 互換形式へ変換して保存します。
    """
    target = _normalise_path(path)
    payload: Mapping[str, Any]
    if game.get("type") == "cardinal":
        payload = _encode_cardinal(game)
    elif game.get("type") == "ordinal":
        payload = _encode_ordinal(game)
    else:
        raise GameIOError("Game payload must declare type 'ordinal' or 'cardinal'.")

    if target.suffix.lower() in _JSON_EXT:
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return
    if target.suffix.lower() in _YAML_EXT:
        target.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
        return
    raise GameIOError("Unsupported file extension; use .json, .yaml, or .yml.")


def load_game(path: Path) -> Dict[str, Any]:
    """Load and validate a game definition from JSON or YAML.

    日本語補足: ファイルを解析し、型安全な内部表現に復元してから検証を行います。
    """
    source = _normalise_path(path)
    suffix = source.suffix.lower()
    if suffix in _JSON_EXT:
        data = json.loads(source.read_text(encoding="utf-8"))
    elif suffix in _YAML_EXT:
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
    else:
        raise GameIOError("Unsupported file extension; use .json, .yaml, or .yml.")

    if not isinstance(data, Mapping):
        raise GameIOError("Game file must decode to a mapping.")

    game_type = data.get("type")
    if game_type == "cardinal":
        return _decode_cardinal(data)
    if game_type == "ordinal":
        return _decode_ordinal(data)
    raise GameIOError("Game payload missing type 'ordinal' or 'cardinal'.")


def _validate_cardinal_payload(n: int, values: Mapping[Coalition, float]) -> None:
    encoding = CoalitionEncoding(n)
    universe = {coal for coal in encoding.iter_coalitions(range(1, n + 1))}
    if frozenset() not in values:
        raise GameIOError("Cardinal games must include value for empty coalition.")
    if values[frozenset()] != 0.0:
        raise GameIOError("Cardinal games require v(empty set) = 0.")
    if any(coal not in universe for coal in values):
        raise GameIOError("Cardinal games may only reference coalitions within 2^N.")


def _validate_ordinal_payload(n: int, tiers: Iterable[Iterable[Coalition]]) -> None:
    encoding = CoalitionEncoding(n)
    universe = {coal for coal in encoding.iter_coalitions(range(1, n + 1))}
    seen: set[Coalition] = set()
    for tier in tiers:
        tier_set = set(tier)
        if not tier_set:
            raise GameIOError("Ordinal tiers must not be empty.")
        seen.update(tier_set)
    if seen != universe:
        raise GameIOError("Ordinal games must totally order all coalitions without repetition.")


__all__ = ["load_game", "save_game", "GameIOError"]
