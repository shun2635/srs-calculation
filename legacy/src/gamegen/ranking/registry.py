"""Rule registry for ranking column generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, TypeVar

from ..io.game_csv import GameTable
from ..rules import group_lexcel as glex_rules
from ..rules import group_ordinal_banzhaf as gobanz_rules
from ..rules import banzhaf as banzhaf_rules
from ..rules import group_shapley as gshapley_rules
from ..rules import group_sum_shapley as gsumshap_rules
from ..rules import shapley_interaction as si_rules
from ..rules import banzhaf_interaction as bi_rules
from ..rules import rp_index as rp_rules
from ..rules import updown as updown_rules
from ..rules import red_index as red_rules
from ..rules import lexcel as lexcel_rules
from ..rules import ordinal_banzhaf as obanz_rules


class RuleScope(str, Enum):
    PLAYER = "player"
    COALITION = "coalition"


PlayerRanker = Callable[[Mapping[int, float], Mapping[int, int], int], Mapping[int, int]]
CoalitionRanker = Callable[[Mapping[int, float], Mapping[int, int], int], Mapping[int, int]]

K = TypeVar("K")


def _competition_ranks(ranks: Mapping[K, int]) -> dict[K, int]:
    counts: dict[int, int] = {}
    for v in ranks.values():
        r = int(v)
        counts[r] = counts.get(r, 0) + 1

    ordered = sorted(counts.keys())
    comp_by_rank: dict[int, int] = {}
    prefix = 0
    for r in ordered:
        comp_by_rank[r] = prefix + 1
        prefix += counts[r]

    return {k: comp_by_rank[int(v)] for k, v in ranks.items()}


@dataclass(frozen=True)
class RuleSpec:
    name: str
    scope: RuleScope
    ranker: PlayerRanker | CoalitionRanker

    @property
    def column_name(self) -> str:
        return f"rank_{self.name}"


def _singleton_index(mask: int) -> int | None:
    if mask != 0 and (mask & (mask - 1)) == 0:
        return mask.bit_length() - 1
    return None


def compute_rank_column_values(rule: RuleSpec, game: GameTable, *, rank_style: str = "dense") -> dict[int, str]:
    """Return mask -> cell value (string) for the rule's rank column."""
    scores = game.scores_by_mask
    levels = game.levels_by_mask
    n = game.n
    style = str(rank_style).lower()
    if style not in {"dense", "competition"}:
        raise ValueError("rank_style must be 'dense' or 'competition'")

    if rule.scope is RuleScope.PLAYER:
        player_ranks = dict(rule.ranker(scores, levels, n))
        if style == "competition":
            player_ranks = _competition_ranks(player_ranks)
        out: dict[int, str] = {}
        for mask in scores.keys():
            idx = _singleton_index(mask)
            if idx is None:
                out[mask] = ""
            else:
                out[mask] = str(player_ranks.get(idx, ""))
        return out

    coalition_ranks = dict(rule.ranker(scores, levels, n))
    if style == "competition":
        coalition_ranks = _competition_ranks(coalition_ranks)
    out = {}
    for mask in scores.keys():
        if mask == 0:
            out[mask] = ""
        else:
            out[mask] = str(coalition_ranks.get(mask, ""))
    return out


def _rank_shapley(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    from ..rules import shapley as shap_rules

    return shap_rules.rank_by_shapley({int(k): float(v) for k, v in scores.items()}, n)


def _rank_banzhaf(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return banzhaf_rules.rank_by_banzhaf({int(k): float(v) for k, v in scores.items()}, n)


def _rank_g_shapley(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return gshapley_rules.rank_by_group_shapley({int(k): float(v) for k, v in scores.items()}, n)

def _rank_g_sum_shapley(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return gsumshap_rules.rank_by_group_sum_shapley({int(k): float(v) for k, v in scores.items()}, n)

def _rank_shapley_interaction(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return si_rules.rank_by_shapley_interaction({int(k): float(v) for k, v in scores.items()}, n)

def _rank_banzhaf_interaction(scores: Mapping[int, float], _levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return bi_rules.rank_by_banzhaf_interaction({int(k): float(v) for k, v in scores.items()}, n)

def _rank_rp_index(_scores: Mapping[int, float], levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return rp_rules.rank_by_rp_index_from_levels({int(k): int(v) for k, v in levels.items()}, n)


def _rank_ud(_scores: Mapping[int, float], levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return updown_rules.rank_by_ud_from_levels({int(k): int(v) for k, v in levels.items()}, n)


def _rank_du(_scores: Mapping[int, float], levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return updown_rules.rank_by_du_from_levels({int(k): int(v) for k, v in levels.items()}, n)

def _rank_red_index(_scores: Mapping[int, float], levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    return red_rules.rank_by_red_index_from_levels({int(k): int(v) for k, v in levels.items()}, n)

def _rank_g_lexcel(_scores: Mapping[int, float], levels: Mapping[int, int], n: int) -> Mapping[int, int]:
    # Build layers Σ_k from input levels (1..L). Lower rank means stronger.
    max_rank = max(levels.values(), default=0)
    materialized: list[list[int]] = [[] for _ in range(max_rank)]
    for mask, r in levels.items():
        if r <= 0 or r > max_rank:
            continue
        materialized[r - 1].append(int(mask))
    layers: list[set[int]] = [set(layer) for layer in materialized]

    groups = glex_rules.coalition_groups_by_lexcel(layers, n=n)
    coalition_rank: dict[int, int] = {}
    rank_counter = 0
    for group in groups:
        rank_counter += 1
        for mask in group:
            coalition_rank[int(mask)] = rank_counter
    return coalition_rank


_RULES: dict[str, RuleSpec] = {}


def register_rule(rule: RuleSpec) -> None:
    key = str(rule.name).lower()
    if key in _RULES:
        raise ValueError(f"Rule already registered: {rule.name}")
    _RULES[key] = rule


def get_rule(name: str) -> RuleSpec:
    key = str(name).lower()
    try:
        return _RULES[key]
    except KeyError as exc:
        raise KeyError(f"Unknown rule: {name}") from exc


def list_rules() -> tuple[RuleSpec, ...]:
    # Preserve registration order (Python 3.7+ dict order)
    return tuple(_RULES.values())


def _register_builtin_rules() -> None:
    register_rule(RuleSpec(name="shapley", scope=RuleScope.PLAYER, ranker=_rank_shapley))
    register_rule(RuleSpec(name="banzhaf", scope=RuleScope.PLAYER, ranker=_rank_banzhaf))
    register_rule(RuleSpec(name="lexcel", scope=RuleScope.PLAYER, ranker=lambda s, _l, n: lexcel_rules.rank_by_lexcel(dict(s), n)))
    register_rule(
        RuleSpec(
            name="o-banzhaf",
            scope=RuleScope.PLAYER,
            ranker=lambda _s, levels, n: obanz_rules.rank_by_ordinal_banzhaf_from_levels(dict(levels), n),
        )
    )
    register_rule(RuleSpec(name="g-shapley", scope=RuleScope.COALITION, ranker=_rank_g_shapley))
    register_rule(RuleSpec(name="g-sum-shapley", scope=RuleScope.COALITION, ranker=_rank_g_sum_shapley))
    register_rule(
        RuleSpec(
            name="g-o-banzhaf",
            scope=RuleScope.COALITION,
            ranker=lambda _s, levels, n: gobanz_rules.rank_by_group_ordinal_banzhaf_from_levels(dict(levels), n),
        )
    )
    register_rule(RuleSpec(name="g-lexcel", scope=RuleScope.COALITION, ranker=_rank_g_lexcel))
    register_rule(RuleSpec(name="shapley-interaction", scope=RuleScope.COALITION, ranker=_rank_shapley_interaction))
    register_rule(RuleSpec(name="banzhaf-interaction", scope=RuleScope.COALITION, ranker=_rank_banzhaf_interaction))
    register_rule(RuleSpec(name="rp-index", scope=RuleScope.COALITION, ranker=_rank_rp_index))
    register_rule(RuleSpec(name="ud", scope=RuleScope.COALITION, ranker=_rank_ud))
    register_rule(RuleSpec(name="du", scope=RuleScope.COALITION, ranker=_rank_du))
    register_rule(RuleSpec(name="red-index", scope=RuleScope.COALITION, ranker=_rank_red_index))


_register_builtin_rules()
