"""Rule registry for the new domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from .rule import RankingRule
from .rules.banzhaf import BanzhafRule
from .rules.banzhaf_interaction import BanzhafInteractionRule
from .rules.group_lexcel import GroupLexcelRule
from .rules.group_ordinal_banzhaf import GroupOrdinalBanzhafRule
from .rules.group_shapley import GroupShapleyRule
from .rules.group_sum_shapley import GroupSumShapleyRule
from .rules.lexcel import LexcelRule
from .rules.ordinal_banzhaf import OrdinalBanzhafRule
from .rules.rankdiff import RankdiffRule
from .rules.red_index import RedIndexRule
from .rules.shapley import ShapleyRule
from .rules.shapley_interaction import ShapleyInteractionRule
from .rules.updown import DuRule, UdRule


@dataclass
class RankingRuleRegistry:
    """Simple in-memory registry for ranking rules."""

    _rules: dict[str, RankingRule] = field(default_factory=dict)
    _aliases: dict[str, str] = field(default_factory=dict)

    def register(self, rule: RankingRule) -> None:
        self._rules[rule.rule_id] = rule

    def register_alias(self, alias: str, canonical_rule_id: str) -> None:
        self._aliases[str(alias)] = str(canonical_rule_id)

    def get(self, rule_id: str) -> RankingRule:
        resolved_rule_id = self._aliases.get(str(rule_id), str(rule_id))
        try:
            return self._rules[resolved_rule_id]
        except KeyError as exc:
            known = ", ".join(sorted(set(self._rules) | set(self._aliases)))
            raise KeyError(f"unknown rule_id '{rule_id}'; known rules: {known}") from exc

    def list_rule_ids(self) -> list[str]:
        return sorted(self._rules)


def build_default_ranking_rule_registry() -> RankingRuleRegistry:
    """Build the first-batch rule registry defined by ADR-0001."""

    registry = RankingRuleRegistry()
    for rule in (
        ShapleyRule(),
        BanzhafRule(),
        LexcelRule(),
        OrdinalBanzhafRule(),
        GroupShapleyRule(),
        GroupSumShapleyRule(),
        GroupOrdinalBanzhafRule(),
        GroupLexcelRule(),
        ShapleyInteractionRule(),
        BanzhafInteractionRule(),
        RankdiffRule(),
        UdRule(),
        DuRule(),
        RedIndexRule(),
    ):
        registry.register(rule)
    registry.register_alias("o-banzhaf", "ordinal_banzhaf")
    registry.register_alias("g-shapley", "group_shapley")
    registry.register_alias("g-sum-shapley", "group_sum_shapley")
    registry.register_alias("g-o-banzhaf", "group_ordinal_banzhaf")
    registry.register_alias("g-lexcel", "group_lexcel")
    registry.register_alias("shapley-interaction", "shapley_interaction")
    registry.register_alias("banzhaf-interaction", "banzhaf_interaction")
    registry.register_alias("red-index", "red_index")
    return registry
