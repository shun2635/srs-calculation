"""Shared type definitions for the game-gen toolkit.

日本語補足: 連合は `frozenset[int]` として表現します。JSON では並び替え済みリスト文字列で
エンコードし、読み込み時に `frozenset` に戻します。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Mapping, NewType, TypedDict

Coalition = FrozenSet[int]
Players = NewType("Players", int)


class CardinalGame(TypedDict):
    """JSON-friendly representation of a cardinal game.

    日本語補足: `v` は JSON 互換のキー (連合の文字列表現) から実数への写像です。
    """

    type: str
    n: int
    v: Mapping[str, float]


class OrdinalGame(TypedDict):
    """JSON-friendly representation of an ordinal game.

    日本語補足: `order` は同値類 (強さが同じ連合の束) のリストです。
    上から強い順に並びます。
    """

    type: str
    n: int
    order: List[List[str]]


@dataclass(frozen=True)
class CoalitionEncoding:
    """Provide helpers to encode and decode coalitions.

    日本語補足: 連合の列挙・エンコード/デコードを担当します。
    """

    n: int

    def all_coalitions(self) -> List[Coalition]:
        """Return all coalitions over N as frozen sets.

        日本語補足: N 上のべき集合 (2^N) をすべて返します。
        """
        return [frozenset(coal) for coal in self.iter_coalitions(range(1, self.n + 1))]

    @staticmethod
    def iter_coalitions(players: Iterable[int]) -> Iterable[Coalition]:
        """Iterate through all coalitions of the provided players.

        日本語補足: 与えられたプレイヤー集合から全ての部分集合を列挙します。
        """
        players_list = list(players)
        total = 1 << len(players_list)
        for mask in range(total):
            members = {players_list[i] for i in range(len(players_list)) if mask & (1 << i)}
            yield frozenset(members)

    @staticmethod
    def encode(coalition: Coalition) -> str:
        """Encode a coalition using sorted JSON-friendly lists.

        日本語補足: 昇順のリストを JSON 文字列化した表現にします (安定なキー化目的)。
        """
        return json_dumps(sorted(coalition))

    @staticmethod
    def decode(key: str) -> Coalition:
        """Decode a coalition string back to a frozenset.

        日本語補足: JSON 文字列の配列を検証し、`frozenset[int]` に戻します。
        """
        data = json_loads(key)
        if not isinstance(data, list) or any(not isinstance(item, int) for item in data):
            raise ValueError("Invalid coalition encoding; expected list of integers.")
        return frozenset(int(member) for member in data)


def json_dumps(value: object) -> str:
    """Local wrapper to avoid dependency cycles in IO helpers."""
    import json

    return json.dumps(value, separators=(",", ":"))


def json_loads(value: str) -> object:
    """Local wrapper to avoid dependency cycles in IO helpers."""
    import json

    return json.loads(value)


__all__ = [
    "CardinalGame",
    "Coalition",
    "CoalitionEncoding",
    "OrdinalGame",
    "Players",
]
