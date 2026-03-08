r"""Lex-cel ranking applied to coalition layers.

日本語補足:
商順序の層 \(\Sigma_1, \Sigma_2, \dots, \Sigma_\ell\) から、
各提携 \(T\) について \(\Theta(T) = (T_1, \dots, T_\ell)\) を
上向きゼータ変換で計算し、辞書式降順で比較します。
"""

from __future__ import annotations

from typing import Callable, Iterable, MutableMapping, Sequence

Coalition = int
Layer = Iterable[Coalition]


def _infer_player_count(layers: Sequence[Sequence[int]], n: int | None) -> int:
    """Infer player count from layers or validate provided n."""

    if n is None:
        max_mask = 0
        for layer in layers:
            for mask in layer:
                if mask < 0:
                    raise ValueError("Coalition mask must be non-negative.")
                if mask > max_mask:
                    max_mask = mask
        n = max_mask.bit_length()
    if n < 0:
        raise ValueError("Player count cannot be negative.")
    return n


def _validate_layers(layers: Sequence[Sequence[int]], n: int) -> list[frozenset[int]]:
    """Validate layer structure and normalise to frozensets."""

    normalised: list[frozenset[int]] = []
    seen: set[int] = set()
    max_mask = 1 << n if n >= 0 else 0
    for idx, layer in enumerate(layers):
        collected = list(layer)
        current = frozenset(collected)
        if len(current) != len(collected):
            raise ValueError(f"Layer {idx} contains duplicate coalitions.")
        for mask in current:
            if mask < 0:
                raise ValueError("Coalition mask must be non-negative.")
            if n >= 0 and mask >= max_mask:
                raise ValueError(
                    f"Coalition mask {mask} exceeds player count n={n}."
                )
            if mask in seen:
                raise ValueError(
                    f"Coalition mask {mask} appears in multiple layers (up to index {idx})."
                )
        seen.update(current)
        normalised.append(current)
    return normalised


def _superset_zeta_transform(values: list[int], n: int) -> list[int]:
    """Perform the superset zeta transform in-place and return values."""

    transformed = values[:]
    size = 1 << n
    for bit in range(n):
        step = 1 << bit
        for mask in range(size):
            if (mask & step) == 0:
                transformed[mask] += transformed[mask | step]
    return transformed


def _theta_vectors(layers: Sequence[frozenset[int]], n: int) -> dict[int, tuple[int, ...]]:
    """Compute Theta(T) vectors for all non-empty coalitions."""

    if n <= 0:
        return {}
    size = 1 << n
    theta: dict[int, tuple[int, ...]] = {}
    accum: list[list[int]] = []
    for layer in layers:
        indicator = [0] * size
        for mask in layer:
            indicator[mask] = 1
        accum.append(_superset_zeta_transform(indicator, n))
    for mask in range(1, size):
        theta[mask] = tuple(values[mask] for values in accum)
    return theta


def coalition_groups_by_lexcel(
    layers: Sequence[Layer],
    *,
    n: int | None = None,
) -> list[set[int]]:
    """Return lexicographically ordered coalition groups."""

    materialised = [list(layer) for layer in layers]
    player_count = _infer_player_count(materialised, n)
    normalised = _validate_layers(materialised, player_count)
    theta = _theta_vectors(normalised, player_count)
    if not theta:
        return []
    grouped: MutableMapping[tuple[int, ...], set[int]] = {}
    for mask, vec in theta.items():
        grouped.setdefault(vec, set()).add(mask)
    ordered_keys = sorted(grouped.keys(), key=lambda vec: tuple(-v for v in vec))
    return [grouped[key] for key in ordered_keys]


def coalition_comparator_by_lexcel(
    layers: Sequence[Layer],
    *,
    n: int | None = None,
) -> Callable[[Coalition, Coalition], int]:
    """Return a comparator consistent with the lex-cel ranking."""

    materialised = [list(layer) for layer in layers]
    player_count = _infer_player_count(materialised, n)
    normalised = _validate_layers(materialised, player_count)
    theta = _theta_vectors(normalised, player_count)
    size = 1 << player_count

    def _ensure_mask(mask: int) -> tuple[int, ...]:
        if mask <= 0:
            raise ValueError("Comparator requires non-empty coalitions (mask > 0).")
        if mask >= size:
            raise ValueError(
                f"Coalition mask {mask} exceeds player count n={player_count}."
            )
        try:
            return theta[mask]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Coalition mask {mask} is not representable for n={player_count}."
            ) from exc

    def compare(left: Coalition, right: Coalition) -> int:
        left_vec = _ensure_mask(left)
        right_vec = _ensure_mask(right)
        for l_val, r_val in zip(left_vec, right_vec):
            if l_val > r_val:
                return -1
            if l_val < r_val:
                return 1
        return 0

    return compare


def sort_coalitions_by_lexcel(
    coalitions: Iterable[Coalition],
    layers: Sequence[Layer],
    *,
    n: int | None = None,
) -> list[Coalition]:
    """Sort coalitions according to the lex-cel ranking."""

    materialised = [list(layer) for layer in layers]
    player_count = _infer_player_count(materialised, n)
    normalised = _validate_layers(materialised, player_count)
    theta = _theta_vectors(normalised, player_count)
    if player_count <= 0:
        return []
    size = 1 << player_count

    def ensure_mask(mask: int) -> tuple[int, ...]:
        if mask <= 0:
            raise ValueError("Sorting requires non-empty coalitions (mask > 0).")
        if mask >= size:
            raise ValueError(
                f"Coalition mask {mask} exceeds player count n={player_count}."
            )
        try:
            return theta[mask]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Coalition mask {mask} is not representable for n={player_count}."
            ) from exc

    def sort_key(mask: Coalition) -> tuple[int, ...]:
        vec = ensure_mask(mask)
        negated = tuple(-value for value in vec)
        return negated + (mask,)

    return sorted(coalitions, key=sort_key)


__all__ = [
    "coalition_groups_by_lexcel",
    "coalition_comparator_by_lexcel",
    "sort_coalitions_by_lexcel",
]
