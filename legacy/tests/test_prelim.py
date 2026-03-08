from __future__ import annotations

import json
from pathlib import Path

import pytest

from gamegen.prelim.io import GameIOError, load_game, save_game


def _cardinal_example() -> dict[str, object]:
    return {
        "type": "cardinal",
        "n": 3,
        "v": {
            frozenset(): 0.0,
            frozenset({1}): 1.0,
            frozenset({2}): 1.5,
            frozenset({1, 2}): 2.5,
        },
    }


def _ordinal_example() -> dict[str, object]:
    return {
        "type": "ordinal",
        "n": 3,
        "order": [
            [frozenset({1, 2})],
            [frozenset({1}), frozenset({2})],
            [frozenset({1, 3}), frozenset({2, 3})],
            [frozenset({3})],
            [frozenset({1, 2, 3})],
            [frozenset()],
        ],
    }


def test_cardinal_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "cardinal.json"
    save_game(_cardinal_example(), path)
    loaded = load_game(path)
    assert loaded["type"] == "cardinal"
    assert loaded["v"][frozenset({1})] == pytest.approx(1.0)


def test_ordinal_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "ordinal.yaml"
    save_game(_ordinal_example(), path)
    loaded = load_game(path)
    assert loaded["type"] == "ordinal"
    assert frozenset({1, 2}) in loaded["order"][0]


def test_invalid_cardinal_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"type": "cardinal", "n": 3, "v": {}}), encoding="utf-8")
    with pytest.raises(GameIOError):
        load_game(path)


def test_invalid_extension(tmp_path: Path) -> None:
    path = tmp_path / "game.dat"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(GameIOError):
        load_game(path)
