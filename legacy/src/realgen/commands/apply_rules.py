"""Apply gamegen ranking rules to real-data game CSVs.

Note: realgen uses a dataset-scoped output layout without `nN` subdirectories.
"""

from __future__ import annotations

import csv
from math import factorial
from pathlib import Path

import click
import yaml

from gamegen.commands.rankings import available_rule_names
from gamegen.config import Defaults, load_config

from gamegen.io.game_csv import GameTable
from gamegen.io.rankings_csv import write_rankings_with_columns, write_rankings_with_rank_column
from gamegen.ranking.registry import compute_rank_column_values, get_rule

from ..datasets import resolve_dataset_out_base
from ..rules import observed_rank_rules as obs_rules


def _load_schema_yaml(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items()}


def _competition_ranks_from_dense(dense: dict[int, int]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for v in dense.values():
        r = int(v)
        counts[r] = counts.get(r, 0) + 1

    ordered = sorted(counts.keys())
    comp_by_rank: dict[int, int] = {}
    prefix = 0
    for r in ordered:
        comp_by_rank[r] = prefix + 1
        prefix += counts[r]

    return {k: comp_by_rank[int(v)] for k, v in dense.items()}


def _group_shapley_values_default0(scores_by_mask: dict[int, float], n: int) -> dict[int, float]:
    """Group Shapley values treating missing v(S) as 0.0."""
    if n <= 0:
        return {}
    full = 1 << n
    all_players_mask = full - 1

    out: dict[int, float] = {}
    for c_mask in range(1, full):
        k = int(c_mask).bit_count()
        m = n - k + 1
        m_fact = factorial(m)

        max_t = n - k
        weights = [0.0] * (max_t + 1)
        for t in range(max_t + 1):
            weights[t] = (factorial(t) * factorial(m - t - 1)) / float(m_fact)

        complement = all_players_mask ^ c_mask
        total = 0.0
        sub = complement
        while True:
            t = int(sub).bit_count()
            diff = float(scores_by_mask.get(int(sub | c_mask), 0.0)) - float(scores_by_mask.get(int(sub), 0.0))
            total += weights[t] * diff
            if sub == 0:
                break
            sub = (sub - 1) & complement

        out[int(c_mask)] = float(total)
    return out


@click.command(name="apply-rules")
@click.argument("dataset_id", type=str)
@click.option(
    "--rules",
    "rules",
    type=click.Choice(available_rule_names(), case_sensitive=False),
    multiple=True,
    help="Decision rules to apply for rankings (repeatable). If omitted, use outputs/real/<dataset_id>/schema.yaml rules or config pipeline.rules.",
)
@click.option("--out", "out_root", type=click.Path(path_type=Path), default=None, help="Output root (default: outputs/real/<dataset_id>).")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def apply_rules(dataset_id: str, rules: tuple[str, ...], out_root: Path | None, config_path: Path | None) -> None:
    """Apply rank_* rules to the dataset under outputs/real/<dataset_id>/."""
    base_out = resolve_dataset_out_base(dataset_id, out_root=out_root, config_path=config_path)
    games_dir = base_out / "games"
    if not games_dir.exists():
        raise click.ClickException(f"Games directory not found: {games_dir}")

    # Resolve default rule set.
    cfg = load_config(config_path)
    defaults = Defaults()
    rules_list = list(rules)
    if not rules_list:
        schema_path = base_out / "schema.yaml"
        schema_rules: list[str] = []
        if schema_path.exists():
            try:
                schema = _load_schema_yaml(schema_path)
                rules_raw = schema.get("rules")
                if isinstance(rules_raw, (list, tuple)):
                    schema_rules = [str(x) for x in rules_raw]
                elif rules_raw is not None:
                    schema_rules = [s.strip() for s in str(rules_raw).split(",") if s.strip()]
            except Exception:
                schema_rules = []

        if schema_rules:
            rules_list = schema_rules
        else:
            rules_cfg = cfg.get("pipeline", {}).get("rules", defaults.pipeline_rules) if isinstance(cfg, dict) else defaults.pipeline_rules
            if isinstance(rules_cfg, (list, tuple)):
                rules_list = [str(x) for x in rules_cfg]
            else:
                rules_list = [s.strip() for s in str(rules_cfg).split(",") if s.strip()]

    allowed = set(available_rule_names())
    rules_list = [str(r).lower() for r in rules_list if str(r).lower() in allowed]
    if not rules_list:
        click.echo("no valid rules to apply; nothing to do")
        return

    processed = 0
    for game_csv in sorted(games_dir.glob("game_*.csv")):
        # Read game CSV without requiring a full 2^N coalition set (some real datasets are incomplete).
        with game_csv.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            rows = [r for r in reader if r]

        n = 0
        for name in header:
            if str(name).startswith("player"):
                n += 1
            else:
                break
        if n <= 0:
            raise click.ClickException(f"Invalid game CSV (no player columns): {game_csv}")
        try:
            score_idx = header.index("score")
            rank_idx = header.index("rank")
        except ValueError as exc:
            raise click.ClickException(f"Invalid game CSV (missing score/rank): {game_csv}") from exc

        scores_by_mask: dict[int, float] = {}
        levels_by_mask: dict[int, int] = {}
        for row in rows:
            mask = 0
            for i in range(n):
                try:
                    v = int(row[i])
                except Exception:
                    v = 0
                if v != 0:
                    mask |= 1 << i
            try:
                score = float(row[score_idx])
                level = int(row[rank_idx])
            except Exception as exc:
                raise click.ClickException(f"Invalid score/rank cell in {game_csv}: {row}") from exc
            scores_by_mask[int(mask)] = float(score)
            levels_by_mask[int(mask)] = int(level)
        masks_in_order = tuple(sorted(scores_by_mask.keys(), key=lambda m: (-scores_by_mask[m], m)))
        game = GameTable(n=n, scores_by_mask=scores_by_mask, levels_by_mask=levels_by_mask, masks_in_canonical_order=masks_in_order)

        expected = 1 << n
        is_complete = len(scores_by_mask) == expected
        rules_for_game = list(rules_list)
        if not is_complete:
            click.echo(f"warning: incomplete game table ({game_csv.name}); missing masks treated as 0.0 where applicable")

        # Hard guard: some rules are intractable for large n regardless of table completeness.
        # (e.g., interaction indices and group Shapley are O(3^n)).
        if n >= 16:
            intractable = {"shapley-interaction", "banzhaf-interaction", "g-shapley"}
            if any(r in intractable for r in rules_for_game):
                click.echo(f"warning: n={n} too large for {sorted(intractable)}; skipping those rules")
                rules_for_game = [r for r in rules_for_game if r not in intractable]
        rankings_dir = base_out / "rankings"
        rankings_dir.mkdir(parents=True, exist_ok=True)
        rankings_path = rankings_dir / game_csv.name

        for rule_name in rules_for_game:
            rule_spec = get_rule(rule_name)
            # For incomplete games, some rules require observed-set implementations.
            if not is_complete and rule_spec.name in {"o-banzhaf", "g-o-banzhaf", "rp-index", "ud", "du", "red-index"}:
                masks = list(game.scores_by_mask.keys())
                if rule_spec.name == "o-banzhaf":
                    player_ranks = obs_rules.rank_by_ordinal_banzhaf_observed(game.levels_by_mask, masks, game.n)
                    values_by_mask = {}
                    for mask in game.scores_by_mask.keys():
                        if mask != 0 and (mask & (mask - 1)) == 0:
                            idx = mask.bit_length() - 1
                            values_by_mask[int(mask)] = str(player_ranks.get(idx, ""))
                        else:
                            values_by_mask[int(mask)] = ""
                    write_rankings_with_rank_column(
                        rankings_path=rankings_path,
                        game=game,
                        new_col_name=rule_spec.column_name,
                        new_values_by_mask=values_by_mask,
                    )
                    continue
                if rule_spec.name == "g-o-banzhaf":
                    ranks = obs_rules.rank_by_group_ordinal_banzhaf_observed(game.levels_by_mask, masks)
                    values_by_mask = {int(mask): ("" if mask == 0 else str(ranks.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                    write_rankings_with_rank_column(
                        rankings_path=rankings_path,
                        game=game,
                        new_col_name=rule_spec.column_name,
                        new_values_by_mask=values_by_mask,
                    )
                    continue
                if rule_spec.name == "rp-index":
                    values = obs_rules.rp_index_values_observed(game.levels_by_mask, masks, game.n)
                    ranks = obs_rules.rank_by_rp_index_observed(game.levels_by_mask, masks, game.n)
                    score_by_mask = {int(mask): ("" if mask == 0 else (f"{float(values.get(int(mask), 0.0)):.10g}" if int(mask) in values else "")) for mask in game.scores_by_mask.keys()}
                    values_by_mask = {int(mask): ("" if mask == 0 else str(ranks.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                    write_rankings_with_columns(
                        rankings_path=rankings_path,
                        game=game,
                        new_columns={"score_rp-index": score_by_mask, rule_spec.column_name: values_by_mask},
                        primary_column=rule_spec.column_name,
                    )
                    continue
                if rule_spec.name in {"ud", "du"}:
                    counts = obs_rules.updown_counts_observed(game.levels_by_mask, masks, game.n)
                    if rule_spec.name == "ud":
                        ranks = obs_rules.rank_by_ud_observed(game.levels_by_mask, masks, game.n)
                    else:
                        ranks = obs_rules.rank_by_du_observed(game.levels_by_mask, masks, game.n)
                    up_by_mask: dict[int, str] = {}
                    down_by_mask: dict[int, str] = {}
                    for mask in game.scores_by_mask.keys():
                        if mask == 0:
                            up_by_mask[int(mask)] = ""
                            down_by_mask[int(mask)] = ""
                            continue
                        if int(mask) in counts:
                            up, down = counts[int(mask)]
                            up_by_mask[int(mask)] = str(int(up))
                            down_by_mask[int(mask)] = str(int(down))
                        else:
                            up_by_mask[int(mask)] = ""
                            down_by_mask[int(mask)] = ""
                    values_by_mask = {int(mask): ("" if mask == 0 else str(ranks.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                    write_rankings_with_columns(
                        rankings_path=rankings_path,
                        game=game,
                        new_columns={
                            f"score_{rule_spec.name}_up": up_by_mask,
                            f"score_{rule_spec.name}_down": down_by_mask,
                            rule_spec.column_name: values_by_mask,
                        },
                        primary_column=rule_spec.column_name,
                    )
                    continue
                if rule_spec.name == "red-index":
                    values = obs_rules.red_index_values_observed(game.levels_by_mask, masks)
                    ranks = obs_rules.rank_by_red_index_observed(game.levels_by_mask, masks)
                    score_by_mask = {int(mask): ("" if mask == 0 else str(values.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                    values_by_mask = {int(mask): ("" if mask == 0 else str(ranks.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                    write_rankings_with_columns(
                        rankings_path=rankings_path,
                        game=game,
                        new_columns={"score_red-index": score_by_mask, rule_spec.column_name: values_by_mask},
                        primary_column=rule_spec.column_name,
                    )
                    continue
            if not is_complete and rule_spec.name == "g-shapley":
                values = _group_shapley_values_default0(
                    {int(k): float(v) for k, v in game.scores_by_mask.items()},
                    game.n,
                )
                order = sorted(values.keys(), key=lambda m: (-values[m], int(m)))
                dense: dict[int, int] = {}
                current = 0
                last: float | None = None
                for m in order:
                    v = float(values[m])
                    if last is None or v != last:
                        current += 1
                        last = v
                    dense[int(m)] = int(current)
                comp = _competition_ranks_from_dense(dense)
                rank_by_mask = {int(mask): ("" if mask == 0 else str(comp.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                score_by_mask = {int(mask): ("" if mask == 0 else f"{float(values.get(int(mask), 0.0)):.10g}") for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_g-shapley": score_by_mask, rule_spec.column_name: rank_by_mask},
                    primary_column=rule_spec.column_name,
                )
                continue

            values_by_mask = compute_rank_column_values(rule_spec, game, rank_style="competition")

            if rule_spec.name == "shapley":
                from gamegen.rules import shapley as shap_rules

                phi = shap_rules.player_shapley_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask: dict[int, str] = {}
                for mask in game.scores_by_mask.keys():
                    if mask != 0 and (mask & (mask - 1)) == 0:
                        idx = mask.bit_length() - 1
                        score_by_mask[mask] = f"{float(phi[idx] if 0 <= idx < len(phi) else 0.0):.10g}"
                    else:
                        score_by_mask[mask] = ""
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_shapley": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "banzhaf":
                from gamegen.rules import banzhaf as banzhaf_rules

                phi = banzhaf_rules.player_banzhaf_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask: dict[int, str] = {}
                for mask in game.scores_by_mask.keys():
                    if mask != 0 and (mask & (mask - 1)) == 0:
                        idx = mask.bit_length() - 1
                        score_by_mask[mask] = f"{float(phi[idx] if 0 <= idx < len(phi) else 0.0):.10g}"
                    else:
                        score_by_mask[mask] = ""
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_banzhaf": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "g-shapley":
                from gamegen.rules import group_shapley as gshapley_rules

                values = gshapley_rules.group_shapley_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else f"{float(values.get(int(mask), 0.0)):.10g}") for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_g-shapley": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "g-sum-shapley":
                from gamegen.rules import group_sum_shapley as gsum_rules

                values = gsum_rules.group_sum_shapley_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else f"{float(values.get(int(mask), 0.0)):.10g}") for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_g-sum-shapley": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "shapley-interaction":
                from gamegen.rules import shapley_interaction as si_rules

                values = si_rules.shapley_interaction_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else f"{float(values.get(int(mask), 0.0)):.10g}") for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_shapley-interaction": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "banzhaf-interaction":
                from gamegen.rules import banzhaf_interaction as bi_rules

                values = bi_rules.banzhaf_interaction_values({int(k): float(v) for k, v in game.scores_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else f"{float(values.get(int(mask), 0.0)):.10g}") for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_banzhaf-interaction": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name == "rp-index":
                from gamegen.rules import rp_index as rp_rules

                values = rp_rules.rp_index_values_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else (f"{float(values.get(int(mask), 0.0)):.10g}" if int(mask) in values else "")) for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_rp-index": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            elif rule_spec.name in {"ud", "du"}:
                from gamegen.rules import updown as updown_rules

                counts = updown_rules.updown_counts_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)
                up_by_mask: dict[int, str] = {}
                down_by_mask: dict[int, str] = {}
                for mask in game.scores_by_mask.keys():
                    if mask == 0:
                        up_by_mask[int(mask)] = ""
                        down_by_mask[int(mask)] = ""
                        continue
                    if int(mask) in counts:
                        up, down = counts[int(mask)]
                        up_by_mask[int(mask)] = str(int(up))
                        down_by_mask[int(mask)] = str(int(down))
                    else:
                        up_by_mask[int(mask)] = ""
                        down_by_mask[int(mask)] = ""
                write_rankings_with_columns(
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
                from gamegen.rules import red_index as red_rules

                values = red_rules.red_index_values_from_levels({int(k): int(v) for k, v in game.levels_by_mask.items()}, game.n)
                score_by_mask = {int(mask): ("" if mask == 0 else str(values.get(int(mask), ""))) for mask in game.scores_by_mask.keys()}
                write_rankings_with_columns(
                    rankings_path=rankings_path,
                    game=game,
                    new_columns={"score_red-index": score_by_mask, rule_spec.column_name: values_by_mask},
                    primary_column=rule_spec.column_name,
                )
            else:
                write_rankings_with_rank_column(
                    rankings_path=rankings_path,
                    game=game,
                    new_col_name=rule_spec.column_name,
                    new_values_by_mask=values_by_mask,
                )

        # Copy feature mapping alongside rankings (best-effort).
        src = game_csv.with_suffix(".features.yaml")
        dst = rankings_path.with_suffix(".features.yaml")
        if src.exists() and not dst.exists():
            try:
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        processed += 1

    click.echo(f"applied rules to {processed} real game(s) for dataset={dataset_id}")


__all__ = ["apply_rules"]
