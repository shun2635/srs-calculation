"""Divergence condition analysis: when do GL and Rankdiff disagree?

Additive analysis (paper Chapter 5). For a fixed player count ``n`` it measures,
per game and coalition size ``k``, how much Group Lex-cel and Rankdiff disagree,
and relates that divergence to structural features of the input -- in particular
the number of Reverse-Axiom firing pairs (the synergy / individual-vs-group
reversal structure the theory predicts should drive divergence).

This module reuses the existing rule evaluation, the reversal constraint
generator and the correlation helper; it does not modify rules, lenses,
reducers, metric calculations or fixed specs, and does not touch the default
single-n output. Numbers are reported, not interpreted.
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
from ...domain.lenses import generate_reversal_constraints
from ...infrastructure.plotting import render_scatter
from .config import DEFAULT_SEED
from .full_comparison import evaluate_paper_rules
from .metrics import _correlation, _masks_of_size, correlation_for_method

DEFAULT_DIVERGENCE_OUT_DIR = Path("outputs/paper/ch5_extensions")


@dataclass(frozen=True)
class DivergenceConfig:
    players: int
    count: int
    seed: int
    out_dir: Path

    @property
    def results_dir(self) -> Path:
        return self.out_dir / "results"

    @property
    def figures_dir(self) -> Path:
        return self.out_dir / "figures"


@dataclass(frozen=True)
class DivergenceRecord:
    game_id: str
    n: int
    k: int
    num_coalitions: int
    num_pairs: int
    num_discordant_pairs: int
    disagreement_rate: float
    one_minus_spearman: float | None
    num_reversal_pairs: int
    num_distinct_levels: int
    max_level_class_size: int
    score_variance: float
    score_range: float


@dataclass(frozen=True)
class FeatureCorrelationRow:
    feature: str
    target: str
    k_segment: str
    pearson: float | None
    spearman: float | None
    num_points: int


@dataclass(frozen=True)
class DivergenceResult:
    out_dir: Path
    records_csv: Path
    feature_correlation_csv: Path
    metadata_json: Path
    scatter_pdf: Path
    scatter_png: Path
    records: tuple[DivergenceRecord, ...]
    feature_rows: tuple[FeatureCorrelationRow, ...]


def build_divergence_config(
    *,
    players: int = 5,
    count: int = 1000,
    seed: int = DEFAULT_SEED,
    out_dir: Path = DEFAULT_DIVERGENCE_OUT_DIR,
) -> DivergenceConfig:
    if int(players) < 2:
        raise ValueError("players must be at least 2")
    if int(count) <= 0:
        raise ValueError("count must be positive")
    return DivergenceConfig(int(players), int(count), int(seed), Path(out_dir))


def _random_complete_game(n: int, *, max_score: int, rng: random.Random) -> CoalitionGame:
    scores_by_mask = {mask: float(rng.randint(0, int(max_score))) for mask in range(1 << int(n))}
    return CoalitionGame.from_scores_by_mask(int(n), scores_by_mask)


def _discordant_pairs(
    gl_ranks: dict[int, int],
    rankdiff_ranks: dict[int, int],
    masks: list[int],
) -> tuple[int, int]:
    """Return (discordant, total) coalition pairs (smaller rank = more preferred)."""

    total = 0
    discordant = 0
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            a, b = masks[i], masks[j]
            gl_diff = gl_ranks[a] - gl_ranks[b]
            rd_diff = rankdiff_ranks[a] - rankdiff_ranks[b]
            total += 1
            if (gl_diff < 0 and rd_diff > 0) or (gl_diff > 0 and rd_diff < 0):
                discordant += 1
    return discordant, total


def _level_tie_features(levels: dict[int, int], masks: list[int]) -> tuple[int, int]:
    classes: dict[int, int] = {}
    for mask in masks:
        level = int(levels[mask])
        classes[level] = classes.get(level, 0) + 1
    return len(classes), (max(classes.values()) if classes else 0)


def _score_dispersion(game: CoalitionGame, masks: list[int]) -> tuple[float, float]:
    scores = [float(game.coalition_value(mask)) for mask in masks]
    if not scores:
        return 0.0, 0.0
    mean = sum(scores) / len(scores)
    variance = sum((value - mean) ** 2 for value in scores) / len(scores)
    return variance, max(scores) - min(scores)


def _rank_transform(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index
        while end + 1 < len(order) and values[order[end + 1]] == values[order[index]]:
            end += 1
        average_rank = (index + end) / 2.0 + 1.0
        for position in range(index, end + 1):
            ranks[order[position]] = average_rank
        index = end + 1
    return ranks


def _pearson_and_spearman(
    feature_values: list[float],
    target_values: list[float],
) -> tuple[float | None, float | None]:
    pearson, _ = _correlation(feature_values, target_values)
    spearman, _ = _correlation(
        _rank_transform(feature_values), _rank_transform(target_values)
    )
    return pearson, spearman


_FEATURES: tuple[str, ...] = (
    "num_reversal_pairs",
    "num_distinct_levels",
    "max_level_class_size",
    "score_variance",
    "score_range",
    "k",
)


def run_divergence_analysis(config: DivergenceConfig) -> DivergenceResult:
    """Run the divergence condition analysis and write its tables and scatter."""

    n = config.players
    target_sizes = tuple(range(2, n + 1))
    max_score = (1 << n) - 1
    rng = random.Random(int(config.seed))
    records: list[DivergenceRecord] = []

    for index in range(config.count):
        game_id = f"n{n}_game_{index:06d}"
        game = _random_complete_game(n, max_score=max_score, rng=rng)
        rank_sets = evaluate_paper_rules(game)
        gl_ranks = rank_sets["group_lexcel"].ranks_by_coalition
        rankdiff_ranks = rank_sets["rankdiff"].ranks_by_coalition
        levels = game.coalition_levels()

        for k in target_sizes:
            masks = _masks_of_size(n, k)
            if len(masks) < 2:
                continue
            discordant, total = _discordant_pairs(gl_ranks, rankdiff_ranks, masks)
            spearman, _ = correlation_for_method(
                gl_ranks, rankdiff_ranks, masks, method="spearman", tie_method="dense"
            )
            distinct_levels, max_class = _level_tie_features(levels, masks)
            variance, value_range = _score_dispersion(game, masks)
            records.append(
                DivergenceRecord(
                    game_id=game_id,
                    n=n,
                    k=k,
                    num_coalitions=len(masks),
                    num_pairs=total,
                    num_discordant_pairs=discordant,
                    disagreement_rate=(discordant / total) if total else 0.0,
                    one_minus_spearman=(None if spearman is None else 1.0 - float(spearman)),
                    num_reversal_pairs=len(generate_reversal_constraints(game, k)),
                    num_distinct_levels=distinct_levels,
                    max_level_class_size=max_class,
                    score_variance=variance,
                    score_range=value_range,
                )
            )

    feature_rows = _feature_correlations(records)
    return _write_outputs(config, tuple(records), feature_rows)


def _feature_correlations(
    records: list[DivergenceRecord],
) -> tuple[FeatureCorrelationRow, ...]:
    rows: list[FeatureCorrelationRow] = []
    # "all" pools every k; the per-k segments control for the k confounder.
    segments: list[str] = ["all"] + [str(k) for k in sorted({record.k for record in records})]
    for target in ("disagreement_rate", "one_minus_spearman"):
        for segment in segments:
            usable = [
                record
                for record in records
                if (segment == "all" or record.k == int(segment))
                and (target != "one_minus_spearman" or record.one_minus_spearman is not None)
            ]
            target_values = [float(getattr(record, target)) for record in usable]
            for feature in _FEATURES:
                feature_values = [float(getattr(record, feature)) for record in usable]
                pearson, spearman = _pearson_and_spearman(feature_values, target_values)
                rows.append(
                    FeatureCorrelationRow(
                        feature=feature,
                        target=target,
                        k_segment=segment,
                        pearson=pearson,
                        spearman=spearman,
                        num_points=len(usable),
                    )
                )
    return tuple(rows)


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


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def _write_outputs(
    config: DivergenceConfig,
    records: tuple[DivergenceRecord, ...],
    feature_rows: tuple[FeatureCorrelationRow, ...],
) -> DivergenceResult:
    config.results_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)

    records_csv = config.results_dir / "divergence_records.csv"
    feature_correlation_csv = config.results_dir / "divergence_feature_correlation.csv"
    metadata_json = config.results_dir / "divergence_metadata.json"
    scatter_pdf = config.figures_dir / "divergence_scatter.pdf"
    scatter_png = config.figures_dir / "divergence_scatter.png"

    _write_rows(
        records_csv,
        [
            "game_id",
            "n",
            "k",
            "num_coalitions",
            "num_pairs",
            "num_discordant_pairs",
            "disagreement_rate",
            "one_minus_spearman",
            "num_reversal_pairs",
            "num_distinct_levels",
            "max_level_class_size",
            "score_variance",
            "score_range",
        ],
        (asdict(record) for record in records),
    )
    _write_rows(
        feature_correlation_csv,
        ["feature", "target", "k_segment", "pearson", "spearman", "num_points"],
        (asdict(row) for row in feature_rows),
    )

    render_scatter(
        x_values=[float(record.num_reversal_pairs) for record in records],
        y_values=[float(record.disagreement_rate) for record in records],
        title=f"GL-Rankdiff divergence vs reversal pairs (n={config.players})",
        xlabel="number of Reverse-Axiom firing pairs",
        ylabel="GL-Rankdiff disagreement rate",
        pdf_path=scatter_pdf,
        png_path=scatter_png,
    )

    metadata_json.write_text(
        json.dumps(
            {
                "workflow": "srs-game-gen paper-divergence",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "git_commit": _git_commit(),
                "players": config.players,
                "count": config.count,
                "seed": config.seed,
                "features": list(_FEATURES),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return DivergenceResult(
        out_dir=config.out_dir,
        records_csv=records_csv,
        feature_correlation_csv=feature_correlation_csv,
        metadata_json=metadata_json,
        scatter_pdf=scatter_pdf,
        scatter_png=scatter_png,
        records=records,
        feature_rows=feature_rows,
    )


__all__ = [
    "DEFAULT_DIVERGENCE_OUT_DIR",
    "DivergenceConfig",
    "DivergenceRecord",
    "DivergenceResult",
    "FeatureCorrelationRow",
    "build_divergence_config",
    "run_divergence_analysis",
]
