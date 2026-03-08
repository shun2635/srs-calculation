"""Axiom checking commands.

Output layout (new):
  outputs/axiom/nN/<axiom_id>/<rule>.csv
  outputs/axiom/nN/<axiom_id>/examples/<rule>/*.png (up to 3)
  outputs/axiom/nN/summary.csv

Legacy layout (<axiom_id>__<rule>.csv) is supported by the summarizer.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import click

from ..axioms import (
    count_gekokujou_2p,
    count_gekokujou_weak_n,
    count_give_2p,
    count_take_2p,
    count_give_weak_n,
    count_take_weak_n,
    collect_redundancy_violations,
    count_redundancy,
    render_axiom_summary_heatmap,
    render_violation_example_png,
)
from ..config import Defaults, load_config
from ..io.paths import OutputPaths
from ..io.rankings_csv import read_rankings_table
from .rankings import available_rule_names


@dataclass(frozen=True)
class AxiomCounts:
    constraints: int
    satisfied: int


def _parse_interaction_rank_column(
    *,
    table: object,
    column_name: str,
) -> dict[int, int]:
    if not hasattr(table, "values_by_mask") or not hasattr(table, "rank_columns"):
        raise TypeError("unexpected rankings table type")
    rank_columns = getattr(table, "rank_columns")
    if column_name not in set(rank_columns):
        raise ValueError(f"required column not found: {column_name}")
    values_by_mask = getattr(table, "values_by_mask")
    out: dict[int, int] = {}
    for mask, cols in values_by_mask.items():
        cell = cols.get(column_name, "")
        if str(cell).strip() == "":
            continue
        out[int(mask)] = int(cell)
    return out


def _write_rule_axiom_csv(path: Path, rows: list[tuple[str, int, int, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["game", "constraints", "satisfied", "satisfied_rate"])
        for game_name, constraints, satisfied, rate in rows:
            writer.writerow([game_name, int(constraints), int(satisfied), str(rate)])


def _read_counts_csv(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"axiom counts CSV is empty: {path}") from exc
        header_s = [str(h) for h in header]
        if header_s not in (["game", "constraints", "satisfied"], ["game", "constraints", "satisfied", "satisfied_rate"]):
            raise ValueError(f"unexpected header in {path}: {header}")
        constraints = 0
        satisfied = 0
        for row in reader:
            if not row:
                continue
            try:
                constraints += int(row[1])
                satisfied += int(row[2])
            except Exception as exc:
                raise ValueError(f"invalid row in {path}: {row}") from exc
    return int(constraints), int(satisfied)


def _write_summary_csv(path: Path, rows: list[tuple[str, str, int, int, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["rule", "axiom", "constraints", "satisfied", "satisfied_rate"])
        for rule, axiom, constraints, satisfied, rate in rows:
            writer.writerow([rule, axiom, int(constraints), int(satisfied), str(rate)])

def _summarize_axioms_dir(axioms_dir: Path) -> Path | None:
    rows: list[tuple[str, str, int, int, str]] = []
    # New layout: <axiom_id>/<rule>.csv
    any_new = False
    for axiom_subdir in sorted(p for p in axioms_dir.iterdir() if p.is_dir()):
        if axiom_subdir.name == "examples":
            continue
        for path in sorted(axiom_subdir.glob("*.csv")):
            any_new = True
            rule_name = path.stem
            constraints, satisfied = _read_counts_csv(path)
            rate = "0" if constraints <= 0 else f"{(satisfied / constraints):.10g}"
            rows.append((rule_name, axiom_subdir.name, constraints, satisfied, rate))

    # Legacy layout fallback: <axiom_id>__<rule>.csv directly under nN
    if not any_new:
        for path in sorted(axioms_dir.glob("*.csv")):
            if path.name == "summary.csv":
                continue
            if "__" not in path.stem:
                continue
            axiom_id, rule_name = path.stem.split("__", 1)
            constraints, satisfied = _read_counts_csv(path)
            rate = "0" if constraints <= 0 else f"{(satisfied / constraints):.10g}"
            rows.append((rule_name, axiom_id, constraints, satisfied, rate))

    if not rows:
        return None
    out_path = axioms_dir / "summary.csv"
    _write_summary_csv(out_path, rows)
    return out_path


def _popcount(x: int) -> int:
    return int(x).bit_count()


def _pair_masks(n_players: int) -> list[int]:
    full = 1 << int(n_players)
    return [m for m in range(1, full) if _popcount(m) == 2]


def _singletons_from_mask(mask: int, n_players: int) -> list[int]:
    return [1 << i for i in range(int(n_players)) if (int(mask) >> i) & 1]


def _give_take_for_pair(mask: int, base_rank_by_mask: dict[int, int], n_players: int) -> tuple[int, int]:
    r_t = int(base_rank_by_mask[int(mask)])
    give = 0
    take = 0
    for i in range(int(n_players)):
        if not ((int(mask) >> i) & 1):
            continue
        s_mask = int(mask) & ~(1 << i)
        if s_mask == 0:
            continue
        r_s = int(base_rank_by_mask[int(s_mask)])
        if r_t < r_s:
            give += 1
        elif r_s < r_t:
            take += 1
    return int(give), int(take)


def _collect_violation_pairs_give_take_2p(
    *,
    axiom_id: str,
    n_players: int,
    base_rank_by_mask: dict[int, int],
    interaction_rank_by_mask: dict[int, int],
    max_examples: int,
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    if max_examples <= 0:
        return out
    pairs = _pair_masks(n_players)
    give_by: dict[int, int] = {}
    take_by: dict[int, int] = {}
    for m in pairs:
        g, t = _give_take_for_pair(int(m), base_rank_by_mask, n_players)
        give_by[int(m)] = g
        take_by[int(m)] = t

    for t in pairs:
        r_it = interaction_rank_by_mask.get(int(t))
        for u in pairs:
            if u == t:
                continue
            r_iu = interaction_rank_by_mask.get(int(u))
            if axiom_id == "give-2p":
                constrained = give_by[int(t)] > give_by[int(u)]
                satisfied = r_it is not None and r_iu is not None and int(r_it) < int(r_iu)
            else:
                constrained = take_by[int(t)] > take_by[int(u)]
                satisfied = r_it is not None and r_iu is not None and int(r_iu) < int(r_it)
            if constrained and not satisfied:
                out.append((int(t), int(u)))
                if len(out) >= max_examples:
                    return out
    return out


def _sorted_singleton_ranks(mask: int, base_rank_by_mask: dict[int, int], n_players: int) -> list[int]:
    ranks: list[int] = []
    for i in range(int(n_players)):
        if (int(mask) >> i) & 1:
            ranks.append(int(base_rank_by_mask[1 << i]))
    ranks.sort()
    return ranks


def _matching_exists_and_has_strict(rs: list[int], rt: list[int]) -> tuple[bool, bool]:
    if len(rs) != len(rt):
        return False, False
    strict = False
    for a, b in zip(rs, rt, strict=True):
        if int(a) > int(b):
            return False, False
        if int(a) < int(b):
            strict = True
    return True, strict


def _collect_violation_pairs_gekokujou(
    *,
    n_players: int,
    base_rank_by_mask: dict[int, int],
    interaction_rank_by_mask: dict[int, int],
    coalition_sizes: list[int],
    max_examples: int,
) -> list[tuple[int, int]]:
    """Return up to max_examples violating ordered pairs (S,T) for gekokujou axioms."""
    out: list[tuple[int, int]] = []
    if max_examples <= 0:
        return out

    full = 1 << int(n_players)
    for size in coalition_sizes:
        if size < 2 or size > n_players:
            continue
        masks = [m for m in range(1, full) if _popcount(m) == int(size)]
        if len(masks) <= 1:
            continue
        singleton_ranks_cache = {m: _sorted_singleton_ranks(m, base_rank_by_mask, n_players) for m in masks}

        for s in masks:
            r_s = int(base_rank_by_mask[int(s)])
            r_is = interaction_rank_by_mask.get(int(s))
            for t in masks:
                if t == s:
                    continue
                r_t = int(base_rank_by_mask[int(t)])
                # S ≼ T  <=>  rank(S) >= rank(T)
                if r_s < r_t:
                    continue
                ok, strict_singleton = _matching_exists_and_has_strict(singleton_ranks_cache[int(s)], singleton_ranks_cache[int(t)])
                if not ok:
                    continue
                strict_group = r_s > r_t  # S ≺ T
                if not (strict_singleton or strict_group):
                    continue

                r_it = interaction_rank_by_mask.get(int(t))
                satisfied = r_is is not None and r_it is not None and int(r_it) < int(r_is)  # T P^I S
                if not satisfied:
                    out.append((int(s), int(t)))
                    if len(out) >= max_examples:
                        return out
    return out


def _collect_violation_pairs_give_take_weak_n(
    *,
    axiom_id: str,
    n_players: int,
    base_rank_by_mask: dict[int, int],
    interaction_rank_by_mask: dict[int, int],
    min_coalition_size: int,
    max_examples: int,
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    if max_examples <= 0:
        return out
    full = 1 << int(n_players)

    for k in range(int(min_coalition_size), int(n_players) + 1):
        masks = [m for m in range(1, full) if _popcount(m) == int(k)]
        if len(masks) <= 1:
            continue
        give_by: dict[int, int] = {}
        take_by: dict[int, int] = {}
        for m in masks:
            r_m = int(base_rank_by_mask[int(m)])
            g = 0
            t = 0
            for i in range(int(n_players)):
                if (int(m) >> i) & 1:
                    r_i = int(base_rank_by_mask[1 << i])
                    if r_m < r_i:
                        g += 1
                    elif r_i < r_m:
                        t += 1
            give_by[int(m)] = int(g)
            take_by[int(m)] = int(t)

        for s in masks:
            r_is = interaction_rank_by_mask.get(int(s))
            for t_mask in masks:
                if t_mask == s:
                    continue
                r_it = interaction_rank_by_mask.get(int(t_mask))
                if axiom_id == "give-weak-n":
                    constrained = give_by[int(s)] > give_by[int(t_mask)]
                    satisfied = r_is is not None and r_it is not None and int(r_is) < int(r_it)
                else:
                    constrained = take_by[int(s)] > take_by[int(t_mask)]
                    satisfied = r_is is not None and r_it is not None and int(r_it) < int(r_is)
                if constrained and not satisfied:
                    out.append((int(s), int(t_mask)))
                    if len(out) >= max_examples:
                        return out
    return out


@click.command(name="check-axioms")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True)
@click.option(
    "--rules",
    "rules",
    type=click.Choice(available_rule_names(), case_sensitive=False),
    multiple=True,
    default=(),
    help="Interaction rules to check against axioms (repeatable).",
)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--min-coalition-size",
    type=click.IntRange(2, 12),
    default=2,
    help="Minimum coalition size for the weak n-person axiom aggregation.",
)
def check_axioms(
    players: int,
    rules: tuple[str, ...],
    out_dir: Path | None,
    config_path: Path | None,
    min_coalition_size: int,
) -> None:
    """Batch-check axioms on rankings CSVs under outputs/rankings/nN.

    For each rankings CSV, count:
      - how many comparisons are constrained by each axiom
      - how many constrained comparisons satisfy the axiom under each interaction rule

    Outputs are written under outputs/axiom/nN as CSV files.
    """
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    paths = OutputPaths(base_out)

    rankings_dir = paths.rankings_dir(players)
    if not rankings_dir.exists():
        raise click.ClickException(f"Rankings directory not found: {rankings_dir}")

    rules_list: list[str]
    if rules:
        rules_list = [str(r).lower() for r in rules]
    else:
        rules_cfg = cfg.get("axioms", {}).get("rules", defaults.axiom_rules) if isinstance(cfg, dict) else defaults.axiom_rules
        if isinstance(rules_cfg, (list, tuple)) and rules_cfg:
            rules_list = [str(x).lower() for x in rules_cfg]
        else:
            rules_list = [s.strip() for s in str(rules_cfg).split(",") if s.strip()]

    if not rules_list:
        raise click.ClickException("no rules specified (use --rules, or set axioms.rules in config.yaml)")

    axioms_dir = paths.axioms_dir(players)
    axioms_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(rankings_dir.glob("game_*.csv"))
    if not files:
        click.echo("no rankings CSV found; nothing to do")
        return

    axiom_ids = (
        "gekokujou-2p",
        "gekokujou-weak-n",
        "give-2p",
        "take-2p",
        "give-weak-n",
        "take-weak-n",
        "redundancy",
    )
    output_rows: dict[tuple[str, str], list[tuple[str, int, int]]] = {}
    for rule_name in rules_list:
        for axiom_id in axiom_ids:
            output_rows[(axiom_id, rule_name)] = []

    # (axiom_id, rule_name) -> list[(game_name, left_mask, right_mask)]
    examples: dict[tuple[str, str], list[tuple[str, int, int]]] = {}
    for rule_name in rules_list:
        for axiom_id in (
            "gekokujou-2p",
            "gekokujou-weak-n",
            "give-2p",
            "take-2p",
            "give-weak-n",
            "take-weak-n",
            "redundancy",
        ):
            examples[(axiom_id, rule_name)] = []

    for rankings_csv in files:
        table = read_rankings_table(rankings_csv)
        if table.n != players:
            raise click.ClickException(f"unexpected player count in {rankings_csv}: {table.n}")

        for rule_name in rules_list:
            col = f"rank_{rule_name}"
            interaction_rank_by_mask = _parse_interaction_rank_column(table=table, column_name=col)

            c2, s2 = count_gekokujou_2p(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
            )
            cw, sw = count_gekokujou_weak_n(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
                min_coalition_size=min_coalition_size,
            )
            cg, sg = count_give_2p(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
            )
            ct, st = count_take_2p(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
            )
            cgw, sgw = count_give_weak_n(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
                min_coalition_size=min_coalition_size,
            )
            ctw, stw = count_take_weak_n(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
                min_coalition_size=min_coalition_size,
            )
            cr, sr = count_redundancy(
                n_players=players,
                base_rank_by_mask=table.base_level_by_mask,
                interaction_rank_by_mask=interaction_rank_by_mask,
            )
            output_rows[("gekokujou-2p", rule_name)].append((rankings_csv.name, c2, s2))
            output_rows[("gekokujou-weak-n", rule_name)].append((rankings_csv.name, cw, sw))
            output_rows[("give-2p", rule_name)].append((rankings_csv.name, cg, sg))
            output_rows[("take-2p", rule_name)].append((rankings_csv.name, ct, st))
            output_rows[("give-weak-n", rule_name)].append((rankings_csv.name, cgw, sgw))
            output_rows[("take-weak-n", rule_name)].append((rankings_csv.name, ctw, stw))
            output_rows[("redundancy", rule_name)].append((rankings_csv.name, cr, sr))

            # Collect up to 3 violation examples per (axiom, rule) across games.
            for axiom_id in ("give-2p", "take-2p"):
                key = (axiom_id, rule_name)
                if key not in examples or len(examples[key]) >= 3:
                    continue
                needed = 3 - len(examples[key])
                viol_pairs = _collect_violation_pairs_give_take_2p(
                    axiom_id=axiom_id,
                    n_players=players,
                    base_rank_by_mask=dict(table.base_level_by_mask),
                    interaction_rank_by_mask=interaction_rank_by_mask,
                    max_examples=needed,
                )
                for left, right in viol_pairs:
                    examples[key].append((rankings_csv.name, int(left), int(right)))
                    if len(examples[key]) >= 3:
                        break

            for axiom_id in ("gekokujou-2p", "gekokujou-weak-n"):
                key = (axiom_id, rule_name)
                if key not in examples or len(examples[key]) >= 3:
                    continue
                needed = 3 - len(examples[key])
                if axiom_id == "gekokujou-2p":
                    sizes = [2]
                else:
                    sizes = list(range(int(min_coalition_size), int(players) + 1))
                viol_pairs = _collect_violation_pairs_gekokujou(
                    n_players=players,
                    base_rank_by_mask=dict(table.base_level_by_mask),
                    interaction_rank_by_mask=interaction_rank_by_mask,
                    coalition_sizes=sizes,
                    max_examples=needed,
                )
                for left, right in viol_pairs:
                    examples[key].append((rankings_csv.name, int(left), int(right)))
                    if len(examples[key]) >= 3:
                        break

            for axiom_id in ("give-weak-n", "take-weak-n"):
                key = (axiom_id, rule_name)
                if key not in examples or len(examples[key]) >= 3:
                    continue
                needed = 3 - len(examples[key])
                viol_pairs = _collect_violation_pairs_give_take_weak_n(
                    axiom_id=axiom_id,
                    n_players=players,
                    base_rank_by_mask=dict(table.base_level_by_mask),
                    interaction_rank_by_mask=interaction_rank_by_mask,
                    min_coalition_size=min_coalition_size,
                    max_examples=needed,
                )
                for left, right in viol_pairs:
                    examples[key].append((rankings_csv.name, int(left), int(right)))
                    if len(examples[key]) >= 3:
                        break

            key = ("redundancy", rule_name)
            if key in examples and len(examples[key]) < 3:
                needed = 3 - len(examples[key])
                viol_pairs = collect_redundancy_violations(
                    n_players=players,
                    base_rank_by_mask=table.base_level_by_mask,
                    interaction_rank_by_mask=interaction_rank_by_mask,
                    max_examples=needed,
                )
                for left, right in viol_pairs:
                    examples[key].append((rankings_csv.name, int(left), int(right)))
                    if len(examples[key]) >= 3:
                        break

    # Write per-axiom/per-rule CSVs with per-game rate.
    for (axiom_id, rule_name), rows in output_rows.items():
        rows_with_rate: list[tuple[str, int, int, str]] = []
        for game_name, constraints, satisfied in rows:
            rate = "0" if int(constraints) <= 0 else f"{(int(satisfied) / int(constraints)):.10g}"
            rows_with_rate.append((game_name, int(constraints), int(satisfied), rate))
        out_path = axioms_dir / axiom_id / f"{rule_name}.csv"
        _write_rule_axiom_csv(out_path, rows_with_rate)

    # Cleanup legacy count files for the same (axiom, rule) pairs to reduce confusion.
    for rule_name in rules_list:
        for axiom_id in axiom_ids:
            legacy = axioms_dir / f"{axiom_id}__{rule_name}.csv"
            if legacy.exists():
                try:
                    legacy.unlink()
                except Exception:
                    pass

    # Write example PNGs (best-effort).
    for (axiom_id, rule_name), items in examples.items():
        if not items:
            continue
        examples_dir = axioms_dir / axiom_id / "examples" / rule_name
        for i, (game_name, left, right) in enumerate(items[:3], start=1):
            rankings_csv = rankings_dir / game_name
            extra_masks = [
                *_singletons_from_mask(int(left), players),
                *_singletons_from_mask(int(right), players),
            ]
            out_png = examples_dir / f"example_{i:02d}__{Path(game_name).stem}__{left}_vs_{right}.png"
            try:
                render_violation_example_png(
                    rankings_csv=rankings_csv,
                    rule_name=rule_name,
                    axiom_id=axiom_id,
                    left_mask=int(left),
                    right_mask=int(right),
                    out_path=out_png,
                    extra_masks=extra_masks,
                )
            except Exception:
                pass

    summary_path = _summarize_axioms_dir(axioms_dir)
    if summary_path is not None:
        click.echo(f"axiom summary written: {summary_path}")
    click.echo(f"axiom check completed: n={players}, {len(files)} file(s)")

@click.command(name="summarize-axioms")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
def summarize_axioms(
    players: int,
    out_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Summarize axiom count CSVs under outputs/axiom/nN into one file.

    Input files: outputs/axiom/nN/<axiom_id>/<rule>.csv (1 row per game).
    Output file: outputs/axiom/nN/summary.csv
    """
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    paths = OutputPaths(base_out)

    axioms_dir = paths.axioms_dir(players)
    if not axioms_dir.exists():
        raise click.ClickException(f"Axioms directory not found: {axioms_dir}")

    out_path = _summarize_axioms_dir(axioms_dir)
    if out_path is None:
        click.echo("no axiom counts CSV found; nothing to do")
        return

    click.echo(f"axiom summary written: {out_path}")


@click.command(name="axiom-summary-heatmap")
@click.option("--players", "players", "-p", type=click.IntRange(1, 12), required=True)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
@click.option("--dpi", type=click.IntRange(72, 600), default=None)
def axiom_summary_heatmap(
    players: int,
    out_dir: Path | None,
    config_path: Path | None,
    dpi: int | None,
) -> None:
    """Render a heatmap from outputs/axiom/nN/summary.csv."""
    cfg = load_config(config_path)
    defaults = Defaults()
    base_out = Path(out_dir) if out_dir is not None else Path(str(cfg.get("output_base", defaults.output_base)))
    paths = OutputPaths(base_out)

    axioms_dir = paths.axioms_dir(players)
    summary_csv = axioms_dir / "summary.csv"
    if not summary_csv.exists():
        raise click.ClickException(f"summary.csv not found: {summary_csv}")

    effective_dpi = dpi if dpi is not None else int(cfg.get("figures", {}).get("png_dpi", defaults.figures_png_dpi)) if isinstance(cfg, dict) else defaults.figures_png_dpi
    out_path = axioms_dir / "summary_heatmap.png"
    render_axiom_summary_heatmap(summary_csv, out_path, dpi=effective_dpi, title="各ルールの公理整合率")
    click.echo(f"saved heatmap: {out_path}")


__all__ = ["check_axioms", "summarize_axioms", "axiom_summary_heatmap"]
