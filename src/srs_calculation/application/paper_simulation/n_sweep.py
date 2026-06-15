"""n-sweep analysis: rule consistency and GL-vs-Rankdiff correlation across n.

This is an *additive* analysis (paper Chapter 5). It runs the existing per-game
metric pipeline for several player counts ``n`` and aggregates across n using the
``group_by_n_and_k_with_overall`` axis added to :mod:`aggregation`. It does not
modify the rules, lenses, reducers, metric calculations, fixed specs, or the
default single-n ``run_paper_simulation`` output.

Each n is run independently with the same fixed ``seed`` (so n=5 reproduces the
canonical numbers exactly). ``count`` (R) is configurable per n because the work
grows with ``2^n``.
"""

from __future__ import annotations

import csv
import json
import random
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.plotting import render_line_series
from .aggregation import OVERALL_KEY, group_by_n_and_k_with_overall
from .config import DEFAULT_SEED
from .full_comparison import (
    PAPER_LENS_RULE_SPECS,
    LensConsistencyObservation,
    evaluate_lens_consistency_observations,
    evaluate_paper_rules,
    summarize_lens_consistency_matrix,
)
from .metrics import (
    LensConsistencyRow,
    RankCorrelationRow,
    _reduce_lens_consistency_group,
    _reduce_rank_correlation_group,
    evaluate_gl_rankdiff_rank_correlation,
    evaluate_reversal_consistency,
)

DEFAULT_SWEEP_STEPS: tuple[tuple[int, int], ...] = (
    (3, 1000),
    (4, 1000),
    (5, 1000),
    (6, 1000),
    (7, 500),
)
DEFAULT_SWEEP_OUT_DIR = Path("outputs/paper/ch5_extensions")
_CORRELATION_METHOD = "spearman"
_RANK_TIE_METHOD = "dense"
_EMPTY_CONSTRAINTS = "exclude"


@dataclass(frozen=True)
class NSweepStep:
    players: int
    count: int


@dataclass(frozen=True)
class NSweepConfig:
    steps: tuple[NSweepStep, ...]
    seed: int
    out_dir: Path

    @property
    def results_dir(self) -> Path:
        return self.out_dir / "results"

    @property
    def figures_dir(self) -> Path:
        return self.out_dir / "figures"


@dataclass(frozen=True)
class NSweepOverviewRow:
    n: int
    count: int
    firing_cases: int
    rankdiff_reversal_macro: float | None
    rankdiff_reversal_micro: float | None
    gl_rankdiff_spearman_overall: float | None


@dataclass(frozen=True)
class NSweepConsistencyRow:
    n: int
    rule_id: str
    rule: str
    reversal_macro: float | None
    reversal_micro: float | None


@dataclass(frozen=True)
class NSweepCorrelationRow:
    n: int
    k: str
    mean_correlation: float | None
    num_valid: int
    num_na: int


@dataclass(frozen=True)
class NSweepResult:
    out_dir: Path
    overview_csv: Path
    consistency_csv: Path
    correlation_csv: Path
    metadata_json: Path
    consistency_figure_pdf: Path
    consistency_figure_png: Path
    correlation_figure_pdf: Path
    correlation_figure_png: Path
    overview_rows: tuple[NSweepOverviewRow, ...]
    consistency_rows: tuple[NSweepConsistencyRow, ...]
    correlation_rows: tuple[NSweepCorrelationRow, ...]


def build_n_sweep_config(
    *,
    steps: tuple[tuple[int, int], ...] = DEFAULT_SWEEP_STEPS,
    seed: int = DEFAULT_SEED,
    out_dir: Path = DEFAULT_SWEEP_OUT_DIR,
) -> NSweepConfig:
    """Validate and build an n-sweep configuration."""

    if not steps:
        raise ValueError("n-sweep needs at least one (players, count) step")
    normalized: list[NSweepStep] = []
    seen: set[int] = set()
    for players, count in steps:
        if int(players) < 2:
            raise ValueError(f"players must be at least 2: {players}")
        if int(count) <= 0:
            raise ValueError(f"count must be positive: {count}")
        if int(players) in seen:
            raise ValueError(f"duplicate players value in sweep: {players}")
        seen.add(int(players))
        normalized.append(NSweepStep(int(players), int(count)))
    normalized.sort(key=lambda step: step.players)
    return NSweepConfig(tuple(normalized), int(seed), Path(out_dir))


def _format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _write_rows(path: Path, header: list[str], rows: Iterable[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: _format_cell(row.get(name)) for name in header})
    return path


def _random_complete_game(n: int, *, max_score: int, rng: random.Random) -> CoalitionGame:
    scores_by_mask = {mask: float(rng.randint(0, int(max_score))) for mask in range(1 << int(n))}
    return CoalitionGame.from_scores_by_mask(int(n), scores_by_mask)


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def run_n_sweep(config: NSweepConfig) -> NSweepResult:
    """Run the n-sweep and write its CSV tables, figures and metadata."""

    all_lens_rows: list[LensConsistencyRow] = []
    all_rank_rows: list[RankCorrelationRow] = []
    consistency_rows: list[NSweepConsistencyRow] = []
    matrix_by_n: dict[int, dict[str, tuple[float | None, float | None]]] = {}

    for step in config.steps:
        n = step.players
        target_sizes = tuple(range(2, n + 1))
        max_score = (1 << n) - 1
        rng = random.Random(int(config.seed))
        lens_observations: list[LensConsistencyObservation] = []
        for index in range(step.count):
            game_id = f"n{n}_game_{index:06d}"
            game = _random_complete_game(n, max_score=max_score, rng=rng)
            rank_sets = evaluate_paper_rules(game)
            gl_ranks = rank_sets["group_lexcel"].ranks_by_coalition
            rankdiff_ranks = rank_sets["rankdiff"].ranks_by_coalition
            lens_observations.extend(
                evaluate_lens_consistency_observations(
                    game_id=game_id,
                    game=game,
                    rank_sets_by_rule=rank_sets,
                    target_sizes=target_sizes,
                )
            )
            all_rank_rows.extend(
                evaluate_gl_rankdiff_rank_correlation(
                    game_id=game_id,
                    player_count=n,
                    gl_rank_by_mask=gl_ranks,
                    rankdiff_rank_by_mask=rankdiff_ranks,
                    target_sizes=target_sizes,
                    correlation_method=_CORRELATION_METHOD,
                    rank_tie_method=_RANK_TIE_METHOD,
                )
            )
            all_lens_rows.extend(
                evaluate_reversal_consistency(
                    game_id=game_id,
                    game=game,
                    rankdiff_rank_by_mask=rankdiff_ranks,
                    target_sizes=target_sizes,
                )
            )

        matrix_cells = summarize_lens_consistency_matrix(lens_observations)
        reversal_by_rule = {
            cell.rule_id: (cell.mean_consistency, cell.micro_consistency)
            for cell in matrix_cells
            if cell.lens_id == "reversal"
        }
        matrix_by_n[n] = reversal_by_rule
        for rule_spec in PAPER_LENS_RULE_SPECS:
            macro, micro = reversal_by_rule.get(rule_spec.rule_id, (None, None))
            consistency_rows.append(
                NSweepConsistencyRow(
                    n=n,
                    rule_id=rule_spec.rule_id,
                    rule=rule_spec.label,
                    reversal_macro=macro,
                    reversal_micro=micro,
                )
            )

    # Cross-n aggregation via the new axis; reducers are reused unchanged.
    lens_groups = group_by_n_and_k_with_overall(
        all_lens_rows, n_of=lambda row: int(row.n), k_of=lambda row: int(row.k)
    )
    lens_summary = [
        _reduce_lens_consistency_group(group, empty_policy=_EMPTY_CONSTRAINTS)
        for group in lens_groups
    ]
    rank_groups = group_by_n_and_k_with_overall(
        all_rank_rows, n_of=lambda row: int(row.n), k_of=lambda row: int(row.k)
    )
    rank_summary = [_reduce_rank_correlation_group(group) for group in rank_groups]

    correlation_rows = tuple(
        NSweepCorrelationRow(
            n=int(row.n),
            k=str(row.k),
            mean_correlation=row.mean_correlation,
            num_valid=row.num_valid_games,
            num_na=row.num_na_games,
        )
        for row in rank_summary
    )

    count_by_n = {step.players: step.count for step in config.steps}
    overview_rows: list[NSweepOverviewRow] = []
    for step in config.steps:
        n = step.players
        lens_overall = next(
            row for row in lens_summary if int(row.n) == n and row.k == OVERALL_KEY
        )
        rank_overall = next(
            (row for row in rank_summary if int(row.n) == n and row.k == OVERALL_KEY),
            None,
        )
        overview_rows.append(
            NSweepOverviewRow(
                n=n,
                count=count_by_n[n],
                firing_cases=lens_overall.num_constraints,
                rankdiff_reversal_macro=lens_overall.mean_consistency,
                rankdiff_reversal_micro=lens_overall.micro_consistency,
                gl_rankdiff_spearman_overall=(
                    None if rank_overall is None else rank_overall.mean_correlation
                ),
            )
        )

    return _write_outputs(config, tuple(overview_rows), tuple(consistency_rows), correlation_rows)


def _write_outputs(
    config: NSweepConfig,
    overview_rows: tuple[NSweepOverviewRow, ...],
    consistency_rows: tuple[NSweepConsistencyRow, ...],
    correlation_rows: tuple[NSweepCorrelationRow, ...],
) -> NSweepResult:
    config.results_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)

    overview_csv = config.results_dir / "n_sweep_overview.csv"
    consistency_csv = config.results_dir / "n_sweep_consistency.csv"
    correlation_csv = config.results_dir / "n_sweep_correlation.csv"
    metadata_json = config.results_dir / "experiment_metadata.json"
    consistency_figure_pdf = config.figures_dir / "n_sweep_consistency.pdf"
    consistency_figure_png = config.figures_dir / "n_sweep_consistency.png"
    correlation_figure_pdf = config.figures_dir / "n_sweep_correlation.pdf"
    correlation_figure_png = config.figures_dir / "n_sweep_correlation.png"

    _write_rows(
        overview_csv,
        [
            "n",
            "count",
            "firing_cases",
            "rankdiff_reversal_macro",
            "rankdiff_reversal_micro",
            "gl_rankdiff_spearman_overall",
        ],
        (asdict(row) for row in overview_rows),
    )
    _write_rows(
        consistency_csv,
        ["n", "rule_id", "rule", "reversal_macro", "reversal_micro"],
        (asdict(row) for row in consistency_rows),
    )
    _write_rows(
        correlation_csv,
        ["n", "k", "mean_correlation", "num_valid", "num_na"],
        (asdict(row) for row in correlation_rows),
    )

    ns = [row.n for row in overview_rows]
    consistency_series = [
        (
            rule_spec.label,
            [
                next(
                    (
                        row.reversal_macro
                        for row in consistency_rows
                        if row.n == n and row.rule_id == rule_spec.rule_id
                    ),
                    None,
                )
                for n in ns
            ],
        )
        for rule_spec in PAPER_LENS_RULE_SPECS
    ]
    render_line_series(
        x_values=ns,
        series=consistency_series,
        title="Reversal consistency (macro) vs n",
        xlabel="players n",
        ylabel="mean consistency",
        pdf_path=consistency_figure_pdf,
        png_path=consistency_figure_png,
    )
    render_line_series(
        x_values=ns,
        series=[
            (
                "Group Lex-cel vs Rankdiff",
                [row.gl_rankdiff_spearman_overall for row in overview_rows],
            )
        ],
        title="Group Lex-cel vs Rankdiff Spearman (overall) vs n",
        xlabel="players n",
        ylabel="Spearman correlation",
        ylim=(-1.0, 1.0),
        pdf_path=correlation_figure_pdf,
        png_path=correlation_figure_png,
    )

    metadata_json.write_text(
        json.dumps(
            {
                "workflow": "srs-game-gen paper-n-sweep",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "git_commit": _git_commit(),
                "seed": config.seed,
                "correlation_method": _CORRELATION_METHOD,
                "rank_tie_method": _RANK_TIE_METHOD,
                "empty_constraints": _EMPTY_CONSTRAINTS,
                "steps": [
                    {"players": step.players, "count": step.count} for step in config.steps
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return NSweepResult(
        out_dir=config.out_dir,
        overview_csv=overview_csv,
        consistency_csv=consistency_csv,
        correlation_csv=correlation_csv,
        metadata_json=metadata_json,
        consistency_figure_pdf=consistency_figure_pdf,
        consistency_figure_png=consistency_figure_png,
        correlation_figure_pdf=correlation_figure_pdf,
        correlation_figure_png=correlation_figure_png,
        overview_rows=overview_rows,
        consistency_rows=consistency_rows,
        correlation_rows=correlation_rows,
    )


__all__ = [
    "DEFAULT_SWEEP_OUT_DIR",
    "DEFAULT_SWEEP_STEPS",
    "NSweepConfig",
    "NSweepConsistencyRow",
    "NSweepCorrelationRow",
    "NSweepOverviewRow",
    "NSweepResult",
    "NSweepStep",
    "build_n_sweep_config",
    "run_n_sweep",
]
