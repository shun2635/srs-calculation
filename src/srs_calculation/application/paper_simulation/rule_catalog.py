"""Paper-facing ranking-rule catalog: the single source for paper analyses.

This is a thin presentation layer over the domain ranking-rule registry. The
rule *algorithm* (instance) is taken from the domain registry so an
implementation has a single home; the catalog only adds paper-specific metadata:

- the paper label,
- the analysis roles the rule participates in (lens heatmap / rank heatmap /
  focal comparison),
- and the per-heatmap display order.

To add a rule to every paper analysis (evaluation, lens-consistency heatmap,
rank-correlation heatmap) you add ONE :class:`PaperRuleSpec` entry to
``PAPER_RULE_CATALOG``. If the rule appears in a heatmap, also list its id in
that heatmap's display-order tuple so the column/legend order is explicit; an
import-time invariant checks that the order tuples match the role membership, so
the two can never silently diverge.

Behaviour note: the catalog reproduces exactly the historical rule sets and
orders that the previous ``PAPER_LENS_RULE_SPECS`` / ``PAPER_RANK_RULE_SPECS``
tuples defined. This module is structure-only and changes no numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.ranking.registry import build_default_ranking_rule_registry
from ...domain.ranking.rule import RankingRule

# Analysis roles a paper rule can carry.
ROLE_LENS_HEATMAP = "lens_heatmap"
ROLE_RANK_HEATMAP = "rank_heatmap"
ROLE_FOCAL = "focal"


@dataclass(frozen=True)
class PaperRuleSpec:
    """A ranking rule as it appears in the paper analyses."""

    rule_id: str
    label: str
    rule: RankingRule
    roles: frozenset[str] = field(default_factory=frozenset)

    def has_role(self, role: str) -> bool:
        return role in self.roles


_REGISTRY = build_default_ranking_rule_registry()


def _spec(rule_id: str, label: str, roles: set[str]) -> PaperRuleSpec:
    """Build a spec whose rule instance comes from the domain registry."""

    return PaperRuleSpec(rule_id, label, _REGISTRY.get(rule_id), frozenset(roles))


# The single authoritative catalog. Catalog order is the canonical rule order
# (and equals the historical PAPER_RULE_SPECS order).
PAPER_RULE_CATALOG: tuple[PaperRuleSpec, ...] = (
    _spec(
        "group_lexcel",
        "Group Lex-cel",
        {ROLE_LENS_HEATMAP, ROLE_RANK_HEATMAP, ROLE_FOCAL},
    ),
    _spec(
        "rankdiff",
        "Rankdiff",
        {ROLE_LENS_HEATMAP, ROLE_RANK_HEATMAP, ROLE_FOCAL},
    ),
    _spec(
        "group_shapley",
        "Group Shapley Value",
        {ROLE_LENS_HEATMAP, ROLE_RANK_HEATMAP},
    ),
    _spec(
        "shapley_interaction",
        "Shapley Interaction Index",
        {ROLE_LENS_HEATMAP, ROLE_RANK_HEATMAP},
    ),
    _spec(
        "banzhaf_interaction",
        "Banzhaf Interaction Index",
        {ROLE_LENS_HEATMAP, ROLE_RANK_HEATMAP},
    ),
)

_CATALOG_BY_ID = {spec.rule_id: spec for spec in PAPER_RULE_CATALOG}

# Per-heatmap display order. These MUST match the historical column/legend order
# (the lens heatmap and the rank heatmap deliberately order the shared rule set
# differently). The invariant below pins them to the role membership.
_LENS_HEATMAP_ORDER: tuple[str, ...] = (
    "group_lexcel",
    "rankdiff",
    "group_shapley",
    "shapley_interaction",
    "banzhaf_interaction",
)
_RANK_HEATMAP_ORDER: tuple[str, ...] = (
    "group_lexcel",
    "group_shapley",
    "rankdiff",
    "shapley_interaction",
    "banzhaf_interaction",
)


def _ordered_specs(order: tuple[str, ...], role: str) -> tuple[PaperRuleSpec, ...]:
    members = {spec.rule_id for spec in PAPER_RULE_CATALOG if spec.has_role(role)}
    if set(order) != members:
        raise AssertionError(
            f"display order for role {role!r} {set(order)} "
            f"does not match role membership {members}"
        )
    return tuple(_CATALOG_BY_ID[rule_id] for rule_id in order)


# Derived views consumed by the metrics / figure code. Names and contents match
# the previous hard-coded tuples exactly.
PAPER_LENS_RULE_SPECS: tuple[PaperRuleSpec, ...] = _ordered_specs(
    _LENS_HEATMAP_ORDER, ROLE_LENS_HEATMAP
)
PAPER_RANK_RULE_SPECS: tuple[PaperRuleSpec, ...] = _ordered_specs(
    _RANK_HEATMAP_ORDER, ROLE_RANK_HEATMAP
)
PAPER_RULE_SPECS: tuple[PaperRuleSpec, ...] = PAPER_RULE_CATALOG


def focal_rule_specs() -> tuple[PaperRuleSpec, ...]:
    """Return the focal rules (Group Lex-cel and Rankdiff) in catalog order."""

    return tuple(spec for spec in PAPER_RULE_CATALOG if spec.has_role(ROLE_FOCAL))


__all__ = [
    "PAPER_LENS_RULE_SPECS",
    "PAPER_RANK_RULE_SPECS",
    "PAPER_RULE_CATALOG",
    "PAPER_RULE_SPECS",
    "ROLE_FOCAL",
    "ROLE_LENS_HEATMAP",
    "ROLE_RANK_HEATMAP",
    "PaperRuleSpec",
    "focal_rule_specs",
]
