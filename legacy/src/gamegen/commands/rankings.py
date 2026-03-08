"""Ranking (decision rule) commands."""

from __future__ import annotations

from pathlib import Path

import click

from ..config import Defaults, load_config
from ..io.game_csv import GameTable, read_game_csv
from ..io.paths import OutputPaths
from ..io.rankings_csv import write_rankings_with_columns, write_rankings_with_rank_column
from ..ranking.registry import compute_rank_column_values, get_rule, list_rules


def available_rule_names() -> list[str]:
    return [r.name for r in list_rules()]


def update_rankings_for_game(
    *,
    game_path: Path,
    rule: str,
    base_out: Path,
    rank_style: str = "dense",
) -> tuple[Path, bool, GameTable]:
    """Apply a rule to one game CSV and write/update its rankings CSV.

    Returns (rankings_path, already_exists, game_table).
    """
    game = read_game_csv(game_path)
    paths = OutputPaths(base_out)
    rankings_dir = paths.rankings_dir(game.n)
    rankings_dir.mkdir(parents=True, exist_ok=True)
    rankings_path = rankings_dir / game_path.name

    rule_spec = get_rule(rule)
    values_by_mask = compute_rank_column_values(rule_spec, game, rank_style=rank_style)

    if rule_spec.name == "shapley":
        from ..rules import shapley as shap_rules  # lazy optional dependency

        phi = shap_rules.player_shapley_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask != 0 and (mask & (mask - 1)) == 0:
                idx = mask.bit_length() - 1
                score_by_mask[mask] = _score_cell(phi[idx] if 0 <= idx < len(phi) else 0.0)
            else:
                score_by_mask[mask] = ""

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_shapley": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "banzhaf":
        from ..rules import banzhaf as banzhaf_rules

        phi = banzhaf_rules.player_banzhaf_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask != 0 and (mask & (mask - 1)) == 0:
                idx = mask.bit_length() - 1
                score_by_mask[mask] = _score_cell(phi[idx] if 0 <= idx < len(phi) else 0.0)
            else:
                score_by_mask[mask] = ""

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_banzhaf": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "g-shapley":
        from ..rules import group_shapley as gshapley_rules

        values = gshapley_rules.group_shapley_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = _score_cell(values.get(int(mask), 0.0))

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_g-shapley": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "g-sum-shapley":
        from ..rules import group_sum_shapley as gsumshap_rules

        values = gsumshap_rules.group_sum_shapley_values(
            {int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n
        )

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = _score_cell(values.get(int(mask), 0.0))

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_g-sum-shapley": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "shapley-interaction":
        from ..rules import shapley_interaction as si_rules

        values = si_rules.shapley_interaction_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = _score_cell(values.get(int(mask), 0.0))

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_shapley-interaction": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "banzhaf-interaction":
        from ..rules import banzhaf_interaction as bi_rules

        values = bi_rules.banzhaf_interaction_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = _score_cell(values.get(int(mask), 0.0))

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_banzhaf-interaction": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "rp-index":
        from ..rules import rp_index as rp_rules

        values = rp_rules.rp_index_values_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)

        def _score_cell(value: float) -> str:
            return f"{float(value):.10g}"

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = _score_cell(values.get(int(mask), 0.0)) if mask in values else ""

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_rp-index": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name in {"ud", "du"}:
        from ..rules import updown as updown_rules

        counts = updown_rules.updown_counts_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)

        up_by_mask: dict[int, str] = {}
        down_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                up_by_mask[mask] = ""
                down_by_mask[mask] = ""
            else:
                if int(mask) in counts:
                    up, down = counts[int(mask)]
                    up_by_mask[mask] = str(int(up))
                    down_by_mask[mask] = str(int(down))
                else:
                    up_by_mask[mask] = ""
                    down_by_mask[mask] = ""

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                f"score_{rule_spec.name}_up": up_by_mask,
                f"score_{rule_spec.name}_down": down_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    elif rule_spec.name == "red-index":
        from ..rules import red_index as red_rules

        values = red_rules.red_index_values_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)

        score_by_mask: dict[int, str] = {}
        for mask in game.scores_by_mask.keys():
            if mask == 0:
                score_by_mask[mask] = ""
            else:
                score_by_mask[mask] = str(values.get(int(mask), ""))

        already_exists, _ = write_rankings_with_columns(
            rankings_path=rankings_path,
            game=game,
            new_columns={
                "score_red-index": score_by_mask,
                rule_spec.column_name: values_by_mask,
            },
            primary_column=rule_spec.column_name,
        )
    else:
        already_exists, _ = write_rankings_with_rank_column(
            rankings_path=rankings_path,
            game=game,
            new_col_name=rule_spec.column_name,
            new_values_by_mask=values_by_mask,
        )
    return rankings_path, already_exists, game


@click.command(name="rank-game")
@click.option(
    "--game",
    "game_path",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Path to a generated game CSV.",
)
@click.option(
    "--rule",
    "rule",
    type=click.Choice(available_rule_names(), case_sensitive=False),
    required=True,
    help="Decision rule to apply.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output base directory (default from config or 'outputs').",
)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def rank_game(
    game_path: Path,
    rule: str,
    out_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Apply a decision rule to a game CSV and write/update a rankings CSV."""
    try:
        game = read_game_csv(game_path)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))

    try:
        rankings_path, already_exists, _game = update_rankings_for_game(
            game_path=game_path,
            rule=rule,
            base_out=base_out,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if already_exists:
        click.echo(f"reordered rank columns in {rankings_path} (no new 'rank_{rule}' added)")
    click.echo(f"wrote rankings to {rankings_path}")


__all__ = ["rank_game", "available_rule_names", "update_rankings_for_game"]
