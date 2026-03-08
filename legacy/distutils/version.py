"""Minimal `distutils.version` shim (Python 3.12+ compatibility).

Provides `LooseVersion` with basic comparison semantics sufficient for
`japanize_matplotlib`.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any


def _split_version(s: str) -> list[int | str]:
    parts = re.split(r"[\\._\\-]+", str(s))
    out: list[int | str] = []
    for part in parts:
        if not part:
            continue
        for token in re.findall(r"\\d+|[A-Za-z]+|[^A-Za-z\\d]+", part):
            if not token or token == ".":
                continue
            if token.isdigit():
                out.append(int(token))
            else:
                out.append(token)
    return out


@total_ordering
class LooseVersion:
    """A very small subset of the original `distutils.version.LooseVersion`."""

    vstring: str
    version: list[int | str]

    def __init__(self, vstring: str = "") -> None:
        self.vstring = str(vstring)
        self.version = _split_version(self.vstring)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"LooseVersion({self.vstring!r})"

    def _coerce(self, other: Any) -> "LooseVersion":
        if isinstance(other, LooseVersion):
            return other
        return LooseVersion(str(other))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (LooseVersion, str)):
            return NotImplemented  # type: ignore[return-value]
        rhs = self._coerce(other)
        return self.version == rhs.version

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (LooseVersion, str)):
            return NotImplemented  # type: ignore[return-value]
        rhs = self._coerce(other)
        return self.version < rhs.version


__all__ = ["LooseVersion"]

