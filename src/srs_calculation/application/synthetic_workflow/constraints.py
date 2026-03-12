"""Constraint-set helpers for synthetic workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.config import load_yaml_config

_CANONICAL_CONSTRAINT_ORDER: tuple[str, ...] = (
    "empty_zero",
    "monotone",
    "superadditive",
)

_PROFILE_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "tu": ("empty_zero", "monotone", "superadditive"),
    "unconstrained": (),
}

_KNOWN_CONSTRAINTS = set(_CANONICAL_CONSTRAINT_ORDER) | {"unconstrained"}


@dataclass(frozen=True)
class SyntheticConstraintSelection:
    """Normalized constraint selection for synthetic workflows."""

    constraints: tuple[str, ...]
    constraint_set_id: str
    profile: str | None = None

    @property
    def is_unconstrained(self) -> bool:
        return not self.constraints


def _normalize_constraints(raw_constraints: Iterable[str]) -> tuple[str, ...]:
    items = [str(item) for item in raw_constraints]
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in items:
        value = str(raw).strip().lower().replace("-", "_")
        if not value:
            continue
        if value not in _KNOWN_CONSTRAINTS:
            known = ", ".join(sorted(_KNOWN_CONSTRAINTS))
            raise ValueError(f"unknown synthetic constraint '{raw}'; known constraints: {known}")
        if value == "unconstrained":
            if len(items) > 1:
                raise ValueError("'unconstrained' cannot be combined with other constraints")
            return ()
        if value not in seen:
            normalized.append(value)
            seen.add(value)

    ordered = [name for name in _CANONICAL_CONSTRAINT_ORDER if name in seen]
    ordered.extend(sorted(name for name in seen if name not in set(_CANONICAL_CONSTRAINT_ORDER)))
    return tuple(ordered)


def _constraints_from_config(config_path: Path | None) -> tuple[tuple[str, ...], str | None]:
    config = load_yaml_config(config_path)
    synthetic = config.get("synthetic")
    gen_games = config.get("gen_games")

    preferred: dict[str, object] = {}
    if isinstance(gen_games, dict):
        preferred.update(gen_games)
    if isinstance(synthetic, dict):
        preferred.update(synthetic)

    raw_constraints = preferred.get("constraints")
    constraints: tuple[str, ...] = ()
    if isinstance(raw_constraints, (list, tuple)):
        constraints = tuple(str(item) for item in raw_constraints)
    elif raw_constraints is not None:
        constraints = (str(raw_constraints),)

    raw_profile = preferred.get("profile")
    profile = None if raw_profile is None else str(raw_profile).strip().lower()
    return constraints, profile


def normalize_constraint_selection(
    *,
    constraints: Iterable[str] = (),
    profile: str | None = None,
) -> SyntheticConstraintSelection:
    """Normalize explicit CLI or config constraint selection."""

    effective_constraints = tuple(str(item) for item in constraints)
    effective_profile = None if profile is None else str(profile).strip().lower()
    expanded: list[str] = list(effective_constraints)

    if effective_profile:
        try:
            expanded.extend(_PROFILE_EXPANSIONS[effective_profile])
        except KeyError as exc:
            known = ", ".join(sorted(_PROFILE_EXPANSIONS))
            raise ValueError(f"unknown synthetic profile '{profile}'; known profiles: {known}") from exc

    ordered = _normalize_constraints(expanded)
    if not ordered:
        return SyntheticConstraintSelection(
            constraints=(),
            constraint_set_id="unconstrained",
            profile="unconstrained" if effective_profile == "unconstrained" else None,
        )
    if ordered == _PROFILE_EXPANSIONS["tu"]:
        return SyntheticConstraintSelection(
            constraints=ordered,
            constraint_set_id="tu",
            profile="tu",
        )
    return SyntheticConstraintSelection(
        constraints=ordered,
        constraint_set_id="+".join(ordered),
        profile=effective_profile,
    )


def resolve_constraint_selection(
    *,
    constraints: Iterable[str] = (),
    profile: str | None = None,
    config_path: Path | None = None,
) -> SyntheticConstraintSelection:
    """Resolve synthetic constraints from explicit input and config."""

    explicit_constraints = tuple(str(item) for item in constraints)
    explicit_profile = None if profile is None else str(profile).strip().lower()
    if explicit_constraints or explicit_profile:
        return normalize_constraint_selection(
            constraints=explicit_constraints,
            profile=explicit_profile,
        )

    config_constraints, config_profile = _constraints_from_config(config_path)
    return normalize_constraint_selection(
        constraints=config_constraints,
        profile=config_profile,
    )


def game_satisfies_constraints(game: CoalitionGame, constraints: Iterable[str]) -> bool:
    """Return whether a coalition game satisfies the normalized constraint set."""

    normalized = normalize_constraint_selection(constraints=constraints).constraints
    if "empty_zero" in normalized and float(game.coalition_value_or(0, 0.0)) != 0.0:
        return False

    masks = list(game.coalition_masks())
    mask_set = set(masks)
    if "monotone" in normalized:
        for smaller in masks:
            for larger in masks:
                if int(smaller) == int(larger):
                    continue
                if int(smaller) & ~int(larger):
                    continue
                if game.coalition_value(int(smaller)) > game.coalition_value(int(larger)):
                    return False

    if "superadditive" in normalized:
        for left in masks:
            if int(left) == 0:
                continue
            for right in masks:
                if int(right) == 0:
                    continue
                if int(left) & int(right):
                    continue
                union = int(left) | int(right)
                if union not in mask_set:
                    continue
                if game.coalition_value(union) < game.coalition_value(int(left)) + game.coalition_value(int(right)):
                    return False

    return True


__all__ = [
    "SyntheticConstraintSelection",
    "game_satisfies_constraints",
    "normalize_constraint_selection",
    "resolve_constraint_selection",
]
