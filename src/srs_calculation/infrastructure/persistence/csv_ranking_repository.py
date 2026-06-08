"""CSV persistence adapter for compatibility-format ranking outputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from ...domain.games.coalition_game import CoalitionGame
from ...domain.ranking.result import RankingResult

RankingScope = Literal["player", "coalition"]


@dataclass(frozen=True)
class CompatibleRankingRuleSpec:
    """Mapping from internal rule identifiers to compatibility-format CSV columns."""

    internal_rule_id: str
    compatible_rule_id: str
    scope: RankingScope
    score_column_names: tuple[str, ...] = ()
    write_rank_column: bool = True

    @property
    def rank_column_name(self) -> str:
        return f"rank_{self.compatible_rule_id}"

    @property
    def score_column_name(self) -> str:
        if not self.score_column_names:
            return f"score_{self.compatible_rule_id}"
        return self.score_column_names[0]


_COMPATIBILITY_RULE_SPECS: dict[str, CompatibleRankingRuleSpec] = {
    "shapley": CompatibleRankingRuleSpec(
        internal_rule_id="shapley",
        compatible_rule_id="shapley",
        scope="player",
        score_column_names=("score_shapley",),
    ),
    "banzhaf": CompatibleRankingRuleSpec(
        internal_rule_id="banzhaf",
        compatible_rule_id="banzhaf",
        scope="player",
        score_column_names=("score_banzhaf",),
    ),
    "lexcel": CompatibleRankingRuleSpec(
        internal_rule_id="lexcel",
        compatible_rule_id="lexcel",
        scope="player",
    ),
    "ordinal_banzhaf": CompatibleRankingRuleSpec(
        internal_rule_id="ordinal_banzhaf",
        compatible_rule_id="o-banzhaf",
        scope="player",
    ),
    "group_shapley": CompatibleRankingRuleSpec(
        internal_rule_id="group_shapley",
        compatible_rule_id="g-shapley",
        scope="coalition",
        score_column_names=("score_g-shapley",),
    ),
    "group_sum_shapley": CompatibleRankingRuleSpec(
        internal_rule_id="group_sum_shapley",
        compatible_rule_id="g-sum-shapley",
        scope="coalition",
        score_column_names=("score_g-sum-shapley",),
    ),
    "group_ordinal_banzhaf": CompatibleRankingRuleSpec(
        internal_rule_id="group_ordinal_banzhaf",
        compatible_rule_id="g-o-banzhaf",
        scope="coalition",
    ),
    "group_lexcel": CompatibleRankingRuleSpec(
        internal_rule_id="group_lexcel",
        compatible_rule_id="g-lexcel",
        scope="coalition",
    ),
    "shapley_interaction": CompatibleRankingRuleSpec(
        internal_rule_id="shapley_interaction",
        compatible_rule_id="shapley-interaction",
        scope="coalition",
        score_column_names=("score_shapley-interaction",),
    ),
    "banzhaf_interaction": CompatibleRankingRuleSpec(
        internal_rule_id="banzhaf_interaction",
        compatible_rule_id="banzhaf-interaction",
        scope="coalition",
        score_column_names=("score_banzhaf-interaction",),
    ),
    "rankdiff": CompatibleRankingRuleSpec(
        internal_rule_id="rankdiff",
        compatible_rule_id="rankdiff",
        scope="coalition",
        score_column_names=("score_rankdiff",),
    ),
    "ud": CompatibleRankingRuleSpec(
        internal_rule_id="ud",
        compatible_rule_id="ud",
        scope="coalition",
        score_column_names=("score_ud_up", "score_ud_down"),
    ),
    "du": CompatibleRankingRuleSpec(
        internal_rule_id="du",
        compatible_rule_id="du",
        scope="coalition",
        score_column_names=("score_du_up", "score_du_down"),
    ),
    "red_index": CompatibleRankingRuleSpec(
        internal_rule_id="red_index",
        compatible_rule_id="red-index",
        scope="coalition",
        score_column_names=("score_red-index",),
    ),
}


_CANONICAL_DERIVED_COLUMN_ORDER: tuple[str, ...] = (
    "score_shapley",
    "score_banzhaf",
    "score_g-shapley",
    "score_g-sum-shapley",
    "score_shapley-interaction",
    "score_banzhaf-interaction",
    "score_rankdiff",
    "score_ud_up",
    "score_ud_down",
    "score_du_up",
    "score_du_down",
    "score_red-index",
    "rank_shapley",
    "rank_banzhaf",
    "rank_lexcel",
    "rank_o-banzhaf",
    "rank_g-shapley",
    "rank_g-sum-shapley",
    "rank_shapley-interaction",
    "rank_banzhaf-interaction",
    "rank_rankdiff",
    "rank_ud",
    "rank_du",
    "rank_red-index",
    "rank_g-lexcel",
    "rank_g-o-banzhaf",
)


def get_compatible_ranking_rule_spec(rule_id: str) -> CompatibleRankingRuleSpec:
    """Return the compatibility-format CSV mapping for a supported ranking rule."""

    try:
        return _COMPATIBILITY_RULE_SPECS[str(rule_id)]
    except KeyError as exc:
        known = ", ".join(sorted(_COMPATIBILITY_RULE_SPECS))
        raise KeyError(f"no compatibility CSV mapping for rule_id '{rule_id}'; known rules: {known}") from exc


def ordered_compatible_derived_columns(column_names: Iterable[str]) -> list[str]:
    """Return derived columns in the compatibility-format display order."""

    remaining = list(dict.fromkeys(str(name) for name in column_names))
    ordered: list[str] = []
    for name in _CANONICAL_DERIVED_COLUMN_ORDER:
        if name in remaining:
            ordered.append(name)
            remaining.remove(name)
    ordered.extend(remaining)
    return ordered


def _format_base_score(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(float(value))


def _format_derived_score(value: float) -> str:
    return f"{float(value):.10g}"


def _is_singleton_mask(mask: int) -> bool:
    return mask != 0 and (mask & (mask - 1)) == 0


def _singleton_player_index(mask: int) -> int | None:
    if not _is_singleton_mask(mask):
        return None
    return int(mask).bit_length() - 1


def _ordered_masks_for_output(game: CoalitionGame) -> list[int]:
    return sorted(game.coalition_masks(), key=lambda mask: (-game.coalition_value(mask), int(mask)))


def _dense_base_ranks_by_mask(game: CoalitionGame) -> dict[int, int]:
    ranks: dict[int, int] = {}
    current_rank = 0
    last_score: float | None = None
    for mask in _ordered_masks_for_output(game):
        score = game.coalition_value(mask)
        if last_score is None or score != last_score:
            current_rank += 1
            last_score = score
        ranks[int(mask)] = current_rank
    return ranks


def _competition_ranks(ranks_by_key: dict[int, int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for rank in ranks_by_key.values():
        normalized = int(rank)
        counts[normalized] = counts.get(normalized, 0) + 1

    competition_by_dense_rank: dict[int, int] = {}
    prefix = 0
    for rank in sorted(counts):
        competition_by_dense_rank[rank] = prefix + 1
        prefix += counts[rank]

    return {
        int(key): competition_by_dense_rank[int(rank)]
        for key, rank in ranks_by_key.items()
    }


def _serialize_player_score_column(
    game: CoalitionGame,
    values_by_player: dict[int, float],
) -> dict[int, str]:
    column: dict[int, str] = {}
    for mask in game.coalition_masks():
        player_index = _singleton_player_index(mask)
        if player_index is None:
            column[int(mask)] = ""
            continue
        value = values_by_player.get(player_index)
        column[int(mask)] = "" if value is None else _format_derived_score(value)
    return column


def _serialize_player_rank_column(
    game: CoalitionGame,
    ranks_by_player: dict[int, int],
    *,
    rank_style: str,
) -> dict[int, str]:
    if rank_style not in {"dense", "competition"}:
        raise ValueError("rank_style must be 'dense' or 'competition'")

    normalized_ranks = (
        _competition_ranks(ranks_by_player) if rank_style == "competition" else {int(k): int(v) for k, v in ranks_by_player.items()}
    )

    column: dict[int, str] = {}
    for mask in game.coalition_masks():
        player_index = _singleton_player_index(mask)
        if player_index is None:
            column[int(mask)] = ""
            continue
        rank = normalized_ranks.get(player_index)
        column[int(mask)] = "" if rank is None else str(int(rank))
    return column


def _serialize_coalition_score_column(
    game: CoalitionGame,
    values_by_coalition: dict[int, float],
) -> dict[int, str]:
    column: dict[int, str] = {}
    for mask in game.coalition_masks():
        if int(mask) == 0:
            column[int(mask)] = ""
            continue
        value = values_by_coalition.get(int(mask))
        column[int(mask)] = "" if value is None else _format_derived_score(value)
    return column


def _serialize_coalition_rank_column(
    game: CoalitionGame,
    ranks_by_coalition: dict[int, int],
    *,
    rank_style: str,
) -> dict[int, str]:
    if rank_style not in {"dense", "competition"}:
        raise ValueError("rank_style must be 'dense' or 'competition'")
    normalized_ranks = (
        _competition_ranks(ranks_by_coalition)
        if rank_style == "competition"
        else {int(k): int(v) for k, v in ranks_by_coalition.items()}
    )
    column: dict[int, str] = {}
    for mask in game.coalition_masks():
        if int(mask) == 0:
            column[int(mask)] = ""
            continue
        rank = normalized_ranks.get(int(mask))
        column[int(mask)] = "" if rank is None else str(int(rank))
    return column


def serialize_compatible_ranking_columns(
    game: CoalitionGame,
    result: RankingResult,
    *,
    rank_style: str = "dense",
) -> dict[str, dict[int, str]]:
    """Serialize one ranking result into compatibility-format derived columns."""

    spec = get_compatible_ranking_rule_spec(result.rule_id)
    columns: dict[str, dict[int, str]] = {}
    if spec.scope == "player":
        if spec.score_column_names and result.score_set is not None:
            columns[spec.score_column_name] = _serialize_player_score_column(
                game,
                result.score_set.values_by_player,
            )
        if spec.write_rank_column and result.rank_set is not None:
            columns[spec.rank_column_name] = _serialize_player_rank_column(
                game,
                result.rank_set.ranks_by_player,
                rank_style=rank_style,
            )
    else:
        if spec.score_column_names and result.score_set is not None and len(spec.score_column_names) == 1:
            columns[spec.score_column_name] = _serialize_coalition_score_column(
                game,
                result.score_set.values_by_coalition,
            )
        if spec.score_column_names and len(spec.score_column_names) > 1:
            for column_name in spec.score_column_names:
                score_set = result.auxiliary_score_sets.get(column_name)
                if score_set is None:
                    continue
                columns[column_name] = _serialize_coalition_score_column(
                    game,
                    score_set.values_by_coalition,
                )
        if spec.write_rank_column and result.rank_set is not None:
            columns[spec.rank_column_name] = _serialize_coalition_rank_column(
                game,
                result.rank_set.ranks_by_coalition,
                rank_style=rank_style,
            )
    return columns


def write_compatible_rankings_csv(
    rankings_path: Path,
    game: CoalitionGame,
    results: Iterable[RankingResult],
    *,
    rank_style: str = "dense",
) -> tuple[str, ...]:
    """Write a full compatibility-format rankings CSV from domain results."""

    derived_columns_by_name: dict[str, dict[int, str]] = {}
    for result in results:
        serialized = serialize_compatible_ranking_columns(game, result, rank_style=rank_style)
        for column_name, values_by_mask in serialized.items():
            if column_name in derived_columns_by_name:
                raise ValueError(f"duplicate derived column generated: {column_name}")
            derived_columns_by_name[column_name] = values_by_mask

    ordered_columns = tuple(ordered_compatible_derived_columns(derived_columns_by_name))
    base_ranks_by_mask = _dense_base_ranks_by_mask(game)
    masks_in_output_order = _ordered_masks_for_output(game)

    header = [f"player{i + 1}" for i in range(game.player_count)] + ["score", "rank", *ordered_columns]
    rankings_path.parent.mkdir(parents=True, exist_ok=True)
    with rankings_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for mask in masks_in_output_order:
            membership = ["1" if (int(mask) >> i) & 1 else "0" for i in range(game.player_count)]
            row = membership + [
                _format_base_score(game.coalition_value(mask)),
                str(int(base_ranks_by_mask[int(mask)])),
            ]
            for column_name in ordered_columns:
                row.append(derived_columns_by_name[column_name].get(int(mask), ""))
            writer.writerow(row)

    return ordered_columns

LegacyRankingRuleSpec = CompatibleRankingRuleSpec
get_legacy_ranking_rule_spec = get_compatible_ranking_rule_spec
ordered_legacy_derived_columns = ordered_compatible_derived_columns
serialize_legacy_ranking_columns = serialize_compatible_ranking_columns
write_legacy_rankings_csv = write_compatible_rankings_csv


__all__ = [
    "CompatibleRankingRuleSpec",
    "get_compatible_ranking_rule_spec",
    "ordered_compatible_derived_columns",
    "serialize_compatible_ranking_columns",
    "write_compatible_rankings_csv",
    "LegacyRankingRuleSpec",
    "get_legacy_ranking_rule_spec",
    "ordered_legacy_derived_columns",
    "serialize_legacy_ranking_columns",
    "write_legacy_rankings_csv",
]
