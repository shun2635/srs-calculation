"""Display-name helpers for rules and axioms.

Internal IDs (e.g., 'shapley-interaction', 'gekokujou-2p') are kept stable for
file paths / CSV columns. This module provides formal labels for plots.
"""

from __future__ import annotations

from .label_config import axiom_display_names, rule_display_names


_FALLBACK_RULE_DISPLAY_NAME_BY_ID: dict[str, str] = {
    "g-sum-shapley": "Sum of Shapley Values",
    "g-shapley": "Shapley Group Value",
    "g-o-banzhaf": "Group Ordinal Banzhaf",
    "g-lexcel": "Group Lex-cel",
    "du": "DU Rule",
    "ud": "UD Rule",
    "rp-index": "RP Difference Rule",
    "banzhaf-interaction": "Banzhaf Interaction Rule",
    "shapley-interaction": "Shapley Interaction Rule",
    "red-index": "Redundancy Rule",
}


_FALLBACK_AXIOM_DISPLAY_NAME_BY_ID: dict[str, str] = {
    "gekokujou-2p": "逆転公理",
    "gekokujou-weak-n": "逆転公理（n人版）",
    "give-2p": "引き上げ公理",
    "give-weak-n": "引き上げ公理（n人版）",
    "take-2p": "引き下げ公理",
    "take-weak-n": "引き下げ公理（n人版）",
    "redundancy": "冗長性公理",
}


def _normalize_rule_id(rule_or_column: str) -> str:
    s = str(rule_or_column)
    if s.startswith("rank_") or s.startswith("score_"):
        return s.split("_", 1)[1]
    return s


def rule_display_name(rule_id: str) -> str:
    """Return the formal display name for a rule id (e.g. 'shapley-interaction')."""
    rid = _normalize_rule_id(rule_id)
    return rule_display_names().get(rid, _FALLBACK_RULE_DISPLAY_NAME_BY_ID.get(rid, str(rule_id)))


def rank_column_display_name(column_name: str) -> str:
    """Return the display label for a rank/score column (e.g. 'rank_xxx')."""
    rid = _normalize_rule_id(column_name)
    return rule_display_names().get(rid, _FALLBACK_RULE_DISPLAY_NAME_BY_ID.get(rid, str(column_name)))


def axiom_display_name(axiom_id: str) -> str:
    """Return the formal display name for an axiom id (e.g. 'gekokujou-2p')."""
    key = str(axiom_id)
    return axiom_display_names().get(key, _FALLBACK_AXIOM_DISPLAY_NAME_BY_ID.get(key, key))


__all__ = [
    "axiom_display_name",
    "rank_column_display_name",
    "rule_display_name",
]
