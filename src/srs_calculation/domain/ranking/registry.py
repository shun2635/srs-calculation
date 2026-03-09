"""Rule registry for the new domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from .rule import RankingRule
from .rules.banzhaf import BanzhafRule
from .rules.lexcel import LexcelRule
from .rules.ordinal_banzhaf import OrdinalBanzhafRule
from .rules.shapley import ShapleyRule


@dataclass
class RankingRuleRegistry:
    """Simple in-memory registry for ranking rules."""

    _rules: dict[str, RankingRule] = field(default_factory=dict)

    def register(self, rule: RankingRule) -> None:
        self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> RankingRule:
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._rules))
            raise KeyError(f"unknown rule_id '{rule_id}'; known rules: {known}") from exc

    def list_rule_ids(self) -> list[str]:
        return sorted(self._rules)


def build_default_ranking_rule_registry() -> RankingRuleRegistry:
    """Build the first-batch rule registry defined by ADR-0001."""

    registry = RankingRuleRegistry()
    for rule in (ShapleyRule(), BanzhafRule(), LexcelRule(), OrdinalBanzhafRule()):
        registry.register(rule)
    return registry
