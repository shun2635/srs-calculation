"""Orchestration for the paper simulation workflow."""

from __future__ import annotations

import csv
import json
import random
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from ...domain.games.coalition_game import CoalitionGame
from ...infrastructure.plotting import (
    render_paper_heatmap,
    render_rank_correlation_figure,
    render_reversal_consistency_figure,
)
from .config import PaperSimulationConfig
from .full_comparison import (
    PAPER_LENS_RULE_SPECS,
    PAPER_LENS_SPECS,
    PAPER_RANK_RULE_SPECS,
    LensConsistencyMatrixCell,
    RankCorrelationMatrixCell,
    evaluate_lens_consistency_observations,
    evaluate_paper_rules,
    evaluate_rank_correlation_observations,
    summarize_lens_consistency_matrix,
    summarize_rank_correlation_matrix,
)
from .metrics import (
    LensConsistencyRow,
    LensConsistencySummaryRow,
    RankCorrelationRow,
    RankCorrelationSummaryRow,
    evaluate_gl_rankdiff_rank_correlation,
    evaluate_reversal_consistency,
    summarize_lens_consistency,
    summarize_rank_correlation,
)


@dataclass(frozen=True)
class PaperSimulationResult:
    """Materialized paper simulation artifacts."""

    out_dir: Path
    results_dir: Path
    figures_dir: Path
    docs_dir: Path
    lens_consistency_csv: Path
    lens_consistency_summary_csv: Path
    rank_correlation_csv: Path
    rank_correlation_summary_csv: Path
    lens_consistency_matrix_csv: Path
    lens_consistency_long_csv: Path
    rank_correlation_matrix_csv: Path
    rank_correlation_long_csv: Path
    simulation_summary_csv: Path
    metadata_json: Path
    reversal_consistency_pdf: Path
    reversal_consistency_png: Path
    rank_correlation_pdf: Path
    rank_correlation_png: Path
    lens_consistency_heatmap_pdf: Path
    lens_consistency_heatmap_png: Path
    rank_correlation_heatmap_pdf: Path
    rank_correlation_heatmap_png: Path
    result_summary_md: Path
    lens_summary_rows: tuple[LensConsistencySummaryRow, ...]
    rank_summary_rows: tuple[RankCorrelationSummaryRow, ...]
    lens_matrix_cells: tuple[LensConsistencyMatrixCell, ...]
    rank_matrix_cells: tuple[RankCorrelationMatrixCell, ...]


def _random_complete_game(
    player_count: int,
    *,
    max_score: int,
    rng: random.Random,
) -> CoalitionGame:
    scores_by_mask = {
        int(mask): float(rng.randint(0, int(max_score)))
        for mask in range(1 << int(player_count))
    }
    return CoalitionGame.from_scores_by_mask(int(player_count), scores_by_mask)


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
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: _format_cell(row.get(name)) for name in header})
    return path


def _lens_row_dict(row: LensConsistencyRow) -> dict[str, object]:
    return asdict(row)


def _lens_summary_dict(row: LensConsistencySummaryRow) -> dict[str, object]:
    return asdict(row)


def _rank_row_dict(row: RankCorrelationRow) -> dict[str, object]:
    return asdict(row)


def _rank_summary_dict(row: RankCorrelationSummaryRow) -> dict[str, object]:
    return asdict(row)


def _lens_matrix_cell_dict(row: LensConsistencyMatrixCell) -> dict[str, object]:
    return asdict(row)


def _rank_matrix_cell_dict(row: RankCorrelationMatrixCell) -> dict[str, object]:
    return asdict(row)


def _lens_matrix_rows(
    cells: Iterable[LensConsistencyMatrixCell],
) -> list[dict[str, object]]:
    cell_by_key = {(cell.rule_id, cell.lens_id): cell for cell in cells}
    rows: list[dict[str, object]] = []
    for rule_spec in PAPER_LENS_RULE_SPECS:
        row: dict[str, object] = {"rule": rule_spec.label}
        for lens_spec in PAPER_LENS_SPECS:
            cell = cell_by_key[(rule_spec.rule_id, lens_spec.lens_id)]
            row[lens_spec.label] = cell.mean_consistency
        rows.append(row)
    return rows


def _rank_matrix_rows(
    cells: Iterable[RankCorrelationMatrixCell],
) -> list[dict[str, object]]:
    cell_by_key = {(cell.rule_a_id, cell.rule_b_id): cell for cell in cells}
    rows: list[dict[str, object]] = []
    for row_rule in PAPER_RANK_RULE_SPECS:
        row: dict[str, object] = {"rule": row_rule.label}
        for col_rule in PAPER_RANK_RULE_SPECS:
            cell = cell_by_key[(row_rule.rule_id, col_rule.rule_id)]
            row[col_rule.label] = cell.mean_correlation
        rows.append(row)
    return rows


def _lens_heatmap_values(
    cells: Iterable[LensConsistencyMatrixCell],
) -> list[list[float | None]]:
    cell_by_key = {(cell.rule_id, cell.lens_id): cell for cell in cells}
    return [
        [
            cell_by_key[(rule_spec.rule_id, lens_spec.lens_id)].mean_consistency
            for lens_spec in PAPER_LENS_SPECS
        ]
        for rule_spec in PAPER_LENS_RULE_SPECS
    ]


def _rank_heatmap_values(
    cells: Iterable[RankCorrelationMatrixCell],
) -> list[list[float | None]]:
    cell_by_key = {(cell.rule_a_id, cell.rule_b_id): cell for cell in cells}
    return [
        [
            cell_by_key[(row_rule.rule_id, col_rule.rule_id)].mean_correlation
            for col_rule in PAPER_RANK_RULE_SPECS
        ]
        for row_rule in PAPER_RANK_RULE_SPECS
    ]


def _simulation_summary_rows(
    lens_summary_rows: Iterable[LensConsistencySummaryRow],
    rank_summary_rows: Iterable[RankCorrelationSummaryRow],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in lens_summary_rows:
        rows.append(
            {
                "metric": "reversal_consistency",
                "n": row.n,
                "k": row.k,
                "num_games": row.num_games,
                "num_valid": row.num_valid_games,
                "num_excluded": row.num_empty_constraint_games,
                "mean": row.mean_consistency,
                "std": row.std_consistency,
                "min": row.min_consistency,
                "max": row.max_consistency,
                "micro": row.micro_consistency,
            }
        )
    for row in rank_summary_rows:
        rows.append(
            {
                "metric": "gl_rankdiff_rank_correlation",
                "n": row.n,
                "k": row.k,
                "num_games": row.num_games,
                "num_valid": row.num_valid_games,
                "num_excluded": row.num_na_games,
                "mean": row.mean_correlation,
                "std": row.std_correlation,
                "min": row.min_correlation,
                "max": row.max_correlation,
                "micro": None,
            }
        )
    return rows


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _write_metadata(
    path: Path,
    config: PaperSimulationConfig,
    output_paths: dict[str, Path],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflow": "srs-game-gen paper-simulation",
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "config": {
            "players": config.players,
            "count": config.count,
            "seed": config.seed,
            "max_score": config.max_score,
            "out_dir": str(config.out_dir),
            "target_sizes": list(config.target_sizes),
            "correlation_method": config.correlation_method,
            "rank_tie_method": config.rank_tie_method,
            "empty_constraints": config.empty_constraints,
        },
        "command_options": {
            "--players": config.players,
            "--count": config.count,
            "--seed": config.seed,
            "--max-score": config.max_score,
            "--out": str(config.out_dir),
            "--target-sizes": ",".join(str(value) for value in config.target_sizes),
            "--correlation-method": config.correlation_method,
            "--rank-tie-method": config.rank_tie_method,
            "--empty-constraints": config.empty_constraints,
        },
        "generation_assumptions": {
            "coalition_values": "iid integers",
            "value_range": [0, config.max_score],
            "coalition_size_monotonicity": False,
            "empty_coalition_generated": True,
            "singletons_included": True,
            "tie_handling": "ties are preserved as ordinal equivalence classes",
        },
        "paper_heatmaps": {
            "lens_consistency_rules": [
                rule_spec.label for rule_spec in PAPER_LENS_RULE_SPECS
            ],
            "rank_correlation_rules": [
                rule_spec.label for rule_spec in PAPER_RANK_RULE_SPECS
            ],
            "lenses": [lens_spec.label for lens_spec in PAPER_LENS_SPECS],
            "diagnostic_lenses": ["Up", "Down", "Redundancy"],
        },
        "outputs": {name: str(path_value) for name, path_value in output_paths.items()},
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _summary_value(rows: Iterable[object], attr: str) -> float | None:
    for row in rows:
        if str(getattr(row, "k")) == "overall":
            value = getattr(row, attr)
            return None if value is None else float(value)
    return None


def _format_float(value: float | None) -> str:
    return "NA" if value is None else f"{float(value):.4f}"


def _lens_cell_value(
    cells: Iterable[LensConsistencyMatrixCell],
    *,
    rule: str,
    lens: str,
) -> float | None:
    for cell in cells:
        if cell.rule == rule and cell.lens == lens:
            return cell.mean_consistency
    return None


def _rank_cell_value(
    cells: Iterable[RankCorrelationMatrixCell],
    *,
    rule_a: str,
    rule_b: str,
) -> float | None:
    for cell in cells:
        if cell.rule_a == rule_a and cell.rule_b == rule_b:
            return cell.mean_correlation
    return None


def _off_diagonal_rank_cells(
    cells: Iterable[RankCorrelationMatrixCell],
) -> list[RankCorrelationMatrixCell]:
    selected: list[RankCorrelationMatrixCell] = []
    seen: set[tuple[str, str]] = set()
    for cell in cells:
        if cell.rule_a_id == cell.rule_b_id or cell.mean_correlation is None:
            continue
        key = tuple(sorted((cell.rule_a_id, cell.rule_b_id)))
        if key in seen:
            continue
        selected.append(cell)
        seen.add(key)
    return selected


def _heatmap_tendency_text(
    rank_matrix_cells: Iterable[RankCorrelationMatrixCell],
) -> str:
    off_diagonal = _off_diagonal_rank_cells(rank_matrix_cells)
    if not off_diagonal:
        return "The full rank-correlation heatmap has no valid off-diagonal cells."

    strongest = max(off_diagonal, key=lambda cell: float(cell.mean_correlation))
    weakest = min(off_diagonal, key=lambda cell: float(cell.mean_correlation))
    return (
        "In the full rule-correlation heatmap, the strongest off-diagonal "
        f"mean correlation is {strongest.rule_a} vs {strongest.rule_b} "
        f"({_format_float(strongest.mean_correlation)}), while the lowest is "
        f"{weakest.rule_a} vs {weakest.rule_b} "
        f"({_format_float(weakest.mean_correlation)})."
    )


def _lens_summary_text(cells: Iterable[LensConsistencyMatrixCell]) -> str:
    gl_reversal = _lens_cell_value(cells, rule="Group Lex-cel", lens="Reversal")
    rp_reversal = _lens_cell_value(cells, rule="Rankdiff", lens="Reversal")
    group_shapley_reversal = _lens_cell_value(
        cells,
        rule="Group Shapley Value",
        lens="Reversal",
    )
    shapley_interaction_reversal = _lens_cell_value(
        cells,
        rule="Shapley Interaction Index",
        lens="Reversal",
    )
    banzhaf_interaction_reversal = _lens_cell_value(
        cells,
        rule="Banzhaf Interaction Index",
        lens="Reversal",
    )
    return (
        "Rankdiff is fully consistent with Reversal in this run "
        f"({_format_float(rp_reversal)}). Group Lex-cel has lower Reversal "
        f"consistency ({_format_float(gl_reversal)}). The cardinal benchmarks "
        "show Reversal consistency of "
        f"{_format_float(group_shapley_reversal)} for Group Shapley Value, "
        f"{_format_float(shapley_interaction_reversal)} for Shapley "
        "Interaction Index, and "
        f"{_format_float(banzhaf_interaction_reversal)} for Banzhaf "
        "Interaction Index. Up, Down, and Redundancy are diagnostic lenses "
        "for the simulation only, not full axiomatic foundations in the main "
        "text."
    )


def _rank_summary_text(cells: Iterable[RankCorrelationMatrixCell]) -> str:
    gl_group_shapley = _rank_cell_value(
        cells,
        rule_a="Group Lex-cel",
        rule_b="Group Shapley Value",
    )
    rp_shapley_interaction = _rank_cell_value(
        cells,
        rule_a="Rankdiff",
        rule_b="Shapley Interaction Index",
    )
    rp_banzhaf_interaction = _rank_cell_value(
        cells,
        rule_a="Rankdiff",
        rule_b="Banzhaf Interaction Index",
    )
    gl_rp = _rank_cell_value(
        cells,
        rule_a="Group Lex-cel",
        rule_b="Rankdiff",
    )
    return (
        "Group Lex-cel and Group Shapley Value have mean rank correlation "
        f"{_format_float(gl_group_shapley)}. Rankdiff is correlated with "
        f"the Shapley and Banzhaf interaction indices at "
        f"{_format_float(rp_shapley_interaction)} and "
        f"{_format_float(rp_banzhaf_interaction)}, respectively. The "
        "Group Lex-cel vs Rankdiff correlation is "
        f"{_format_float(gl_rp)}, suggesting a visible separation between "
        "group-level value and formation/interaction perspectives."
    )


def _write_markdown_summary(
    path: Path,
    *,
    config: PaperSimulationConfig,
    lens_summary_rows: tuple[LensConsistencySummaryRow, ...],
    rank_summary_rows: tuple[RankCorrelationSummaryRow, ...],
    lens_matrix_cells: tuple[LensConsistencyMatrixCell, ...],
    rank_matrix_cells: tuple[RankCorrelationMatrixCell, ...],
    output_paths: dict[str, Path],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall_consistency = _summary_value(lens_summary_rows, "mean_consistency")
    overall_consistency_micro = _summary_value(lens_summary_rows, "micro_consistency")
    overall_correlation = _summary_value(rank_summary_rows, "mean_correlation")
    rp_reversal = _lens_cell_value(
        lens_matrix_cells,
        rule="Rankdiff",
        lens="Reversal",
    )
    gl_rp_correlation = _rank_cell_value(
        rank_matrix_cells,
        rule_a="Group Lex-cel",
        rule_b="Rankdiff",
    )
    heatmap_tendency = _heatmap_tendency_text(rank_matrix_cells)
    lens_heatmap_summary = _lens_summary_text(lens_matrix_cells)
    rank_heatmap_summary = _rank_summary_text(rank_matrix_cells)
    rq1_summary = (
        f"The overall mean {config.correlation_method} rank correlation between "
        "Group Lex-cel and Rankdiff is "
        f"{_format_float(overall_correlation)} over valid game-size rows. "
        "Rows with undefined correlation are excluded from this average."
    )
    rq2_summary = (
        "The overall Reversal lens consistency for Rankdiff is "
        f"{_format_float(overall_consistency)} (macro, per-game equal-weight mean "
        "over valid game-size rows) and "
        f"{_format_float(overall_consistency_micro)} (micro, pooled over all "
        "firing cases). Empty constraint sets are handled with policy "
        f"`{config.empty_constraints}` for the macro average; the micro average "
        "pools constraints directly and is unaffected by that policy."
    )
    draft_text = (
        f"In the main simulation with n={config.players} and R={config.count}, "
        "coalition values were sampled independently and uniformly from the "
        f"integers 0 to {config.max_score}, without imposing monotonicity with "
        f"respect to coalition size. The mean {config.correlation_method} rank "
        "correlation between Group Lex-cel and Rankdiff was "
        f"{_format_float(gl_rp_correlation)}, while Rankdiff's mean "
        "Reversal lens consistency rate was "
        f"{_format_float(rp_reversal)}. The focused comparison indicates "
        "that the two rules do not simply reproduce the same ranking. The "
        "heatmap analysis places this comparison in a broader rule space by "
        "using cardinal group-value and interaction-index benchmarks, while "
        "Up, Down, and Redundancy are included only as diagnostic lenses."
    )
    text = f"""# Simulation Result Summary

## Experiment Settings

- players: {config.players}
- games: {config.count}
- seed: {config.seed}
- max_score: {config.max_score}
- target group sizes: {', '.join(str(value) for value in config.target_sizes)}
- coalition values: iid integers from 0 to max_score
- coalition size monotonicity: not assumed
- correlation method: {config.correlation_method}
- rank tie method: {config.rank_tie_method}
- empty Reversal constraints: {config.empty_constraints}

## RQ1: Group Lex-cel vs Rankdiff

{rq1_summary}

## RQ2: Reversal Consistency of Rankdiff

{rq2_summary}

## Main Figures

- lens consistency heatmap: `{output_paths["lens_consistency_heatmap_pdf"]}`
- rank correlation heatmap: `{output_paths["rank_correlation_heatmap_pdf"]}`
- Reversal consistency bar chart: `{output_paths["reversal_consistency_pdf"]}`
- GL vs Rankdiff rank correlation bar chart: `{output_paths["rank_correlation_pdf"]}`

## Main Numerical Summary

- Rankdiff Reversal consistency: {_format_float(rp_reversal)}
- Group Lex-cel vs Rankdiff rank correlation: {_format_float(gl_rp_correlation)}
- {heatmap_tendency}

## Lens Consistency Summary

{lens_heatmap_summary}

Reversal is the main formation-value lens discussed in the paper. Up, Down,
and Redundancy are included as diagnostic lenses for the simulation only; they
are not treated as full axiomatic foundations in the main text.

## Rank Correlation Summary

{rank_heatmap_summary}

## Outputs

- lens consistency CSV: `{output_paths["lens_consistency_csv"]}`
- lens consistency summary CSV: `{output_paths["lens_consistency_summary_csv"]}`
- lens consistency matrix CSV: `{output_paths["lens_consistency_matrix_csv"]}`
- lens consistency long CSV: `{output_paths["lens_consistency_long_csv"]}`
- rank correlation CSV: `{output_paths["rank_correlation_csv"]}`
- rank correlation summary CSV: `{output_paths["rank_correlation_summary_csv"]}`
- rank correlation matrix CSV: `{output_paths["rank_correlation_matrix_csv"]}`
- rank correlation long CSV: `{output_paths["rank_correlation_long_csv"]}`
- simulation summary CSV: `{output_paths["simulation_summary_csv"]}`
- metadata JSON: `{output_paths["metadata_json"]}`
- lens consistency heatmap: `{output_paths["lens_consistency_heatmap_pdf"]}`
- rule rank correlation heatmap: `{output_paths["rank_correlation_heatmap_pdf"]}`
- Reversal consistency figure: `{output_paths["reversal_consistency_pdf"]}`
- GL vs Rankdiff rank correlation figure: `{output_paths["rank_correlation_pdf"]}`

## Draft Text for Paper

{draft_text}

## Notes

- The reported values are generated from this run and should not be copied across
  different seeds or settings.
- Reversal satisfaction requires a strict Rankdiff ranking improvement; ties
  are not counted as satisfied.
- Undefined correlations and empty constraint sets are excluded from the default averages.
"""
    path.write_text(text, encoding="utf-8")
    return path


def run_paper_simulation(config: PaperSimulationConfig) -> PaperSimulationResult:
    """Run the paper simulation workflow and write all paper-facing artifacts."""

    config.results_dir.mkdir(parents=True, exist_ok=True)
    config.figures_dir.mkdir(parents=True, exist_ok=True)
    config.docs_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(int(config.seed))
    lens_rows: list[LensConsistencyRow] = []
    rank_rows: list[RankCorrelationRow] = []
    lens_heatmap_observations = []
    rank_heatmap_observations = []

    for index in range(1, int(config.count) + 1):
        game_id = f"game_{index:06d}"
        game = _random_complete_game(config.players, max_score=config.max_score, rng=rng)
        rank_sets_by_rule = evaluate_paper_rules(game)
        gl_rank_by_mask = rank_sets_by_rule["group_lexcel"].ranks_by_coalition
        rankdiff_rank_by_mask = rank_sets_by_rule["rankdiff"].ranks_by_coalition

        lens_rows.extend(
            evaluate_reversal_consistency(
                game_id=game_id,
                game=game,
                rankdiff_rank_by_mask=rankdiff_rank_by_mask,
                target_sizes=config.target_sizes,
            )
        )
        rank_rows.extend(
            evaluate_gl_rankdiff_rank_correlation(
                game_id=game_id,
                player_count=config.players,
                gl_rank_by_mask=gl_rank_by_mask,
                rankdiff_rank_by_mask=rankdiff_rank_by_mask,
                target_sizes=config.target_sizes,
                correlation_method=config.correlation_method,
                rank_tie_method=config.rank_tie_method,
            )
        )
        lens_heatmap_observations.extend(
            evaluate_lens_consistency_observations(
                game_id=game_id,
                game=game,
                rank_sets_by_rule=rank_sets_by_rule,
                target_sizes=config.target_sizes,
            )
        )
        rank_heatmap_observations.extend(
            evaluate_rank_correlation_observations(
                game_id=game_id,
                player_count=config.players,
                rank_sets_by_rule=rank_sets_by_rule,
                target_sizes=config.target_sizes,
                correlation_method=config.correlation_method,
                rank_tie_method=config.rank_tie_method,
            )
        )

    lens_summary_rows = summarize_lens_consistency(
        lens_rows,
        empty_policy=config.empty_constraints,
    )
    rank_summary_rows = summarize_rank_correlation(rank_rows)
    lens_matrix_cells = summarize_lens_consistency_matrix(lens_heatmap_observations)
    rank_matrix_cells = summarize_rank_correlation_matrix(
        rank_heatmap_observations,
        num_game_size_rows=int(config.count) * len(config.target_sizes),
    )

    lens_consistency_csv = config.results_dir / "lens_consistency.csv"
    lens_consistency_summary_csv = config.results_dir / "lens_consistency_summary.csv"
    rank_correlation_csv = config.results_dir / "rank_correlation.csv"
    rank_correlation_summary_csv = config.results_dir / "rank_correlation_summary.csv"
    lens_consistency_matrix_csv = config.results_dir / "lens_consistency_matrix.csv"
    lens_consistency_long_csv = config.results_dir / "lens_consistency_long.csv"
    rank_correlation_matrix_csv = config.results_dir / "rank_correlation_matrix.csv"
    rank_correlation_long_csv = config.results_dir / "rank_correlation_long.csv"
    simulation_summary_csv = config.results_dir / "simulation_summary.csv"
    metadata_json = config.results_dir / "experiment_metadata.json"
    reversal_consistency_pdf = config.figures_dir / "reversal_consistency.pdf"
    reversal_consistency_png = config.figures_dir / "reversal_consistency.png"
    rank_correlation_pdf = config.figures_dir / "rank_correlation_glc_rp.pdf"
    rank_correlation_png = config.figures_dir / "rank_correlation_glc_rp.png"
    lens_consistency_heatmap_pdf = config.figures_dir / "lens_consistency_heatmap.pdf"
    lens_consistency_heatmap_png = config.figures_dir / "lens_consistency_heatmap.png"
    rank_correlation_heatmap_pdf = config.figures_dir / "rank_correlation_heatmap.pdf"
    rank_correlation_heatmap_png = config.figures_dir / "rank_correlation_heatmap.png"
    result_summary_md = config.docs_dir / "simulation_result_summary.md"

    _write_rows(
        lens_consistency_csv,
        [
            "game_id",
            "n",
            "k",
            "num_constraints",
            "num_satisfied",
            "consistency_rate",
            "is_empty_constraints",
        ],
        (_lens_row_dict(row) for row in lens_rows),
    )
    _write_rows(
        lens_consistency_summary_csv,
        [
            "n",
            "k",
            "num_games",
            "num_valid_games",
            "num_empty_constraint_games",
            "num_constraints",
            "num_satisfied",
            "mean_consistency",
            "std_consistency",
            "min_consistency",
            "max_consistency",
            "micro_consistency",
        ],
        (_lens_summary_dict(row) for row in lens_summary_rows),
    )
    _write_rows(
        rank_correlation_csv,
        [
            "game_id",
            "n",
            "k",
            "correlation_method",
            "rank_tie_method",
            "correlation",
            "is_na",
            "reason_if_na",
        ],
        (_rank_row_dict(row) for row in rank_rows),
    )
    _write_rows(
        rank_correlation_summary_csv,
        [
            "n",
            "k",
            "num_games",
            "num_valid_games",
            "num_na_games",
            "mean_correlation",
            "std_correlation",
            "min_correlation",
            "max_correlation",
        ],
        (_rank_summary_dict(row) for row in rank_summary_rows),
    )
    _write_rows(
        lens_consistency_matrix_csv,
        ["rule", *[lens_spec.label for lens_spec in PAPER_LENS_SPECS]],
        _lens_matrix_rows(lens_matrix_cells),
    )
    _write_rows(
        lens_consistency_long_csv,
        ["rule", "lens", "mean_consistency", "micro_consistency", "num_valid", "num_empty_or_na"],
        (_lens_matrix_cell_dict(row) for row in lens_matrix_cells),
    )
    _write_rows(
        rank_correlation_matrix_csv,
        ["rule", *[rule_spec.label for rule_spec in PAPER_RANK_RULE_SPECS]],
        _rank_matrix_rows(rank_matrix_cells),
    )
    _write_rows(
        rank_correlation_long_csv,
        ["rule_a", "rule_b", "mean_correlation", "num_valid", "num_na"],
        (_rank_matrix_cell_dict(row) for row in rank_matrix_cells),
    )
    _write_rows(
        simulation_summary_csv,
        [
            "metric",
            "n",
            "k",
            "num_games",
            "num_valid",
            "num_excluded",
            "mean",
            "std",
            "min",
            "max",
            "micro",
        ],
        _simulation_summary_rows(lens_summary_rows, rank_summary_rows),
    )

    output_paths = {
        "lens_consistency_csv": lens_consistency_csv,
        "lens_consistency_summary_csv": lens_consistency_summary_csv,
        "lens_consistency_matrix_csv": lens_consistency_matrix_csv,
        "lens_consistency_long_csv": lens_consistency_long_csv,
        "rank_correlation_csv": rank_correlation_csv,
        "rank_correlation_summary_csv": rank_correlation_summary_csv,
        "rank_correlation_matrix_csv": rank_correlation_matrix_csv,
        "rank_correlation_long_csv": rank_correlation_long_csv,
        "simulation_summary_csv": simulation_summary_csv,
        "metadata_json": metadata_json,
        "reversal_consistency_pdf": reversal_consistency_pdf,
        "reversal_consistency_png": reversal_consistency_png,
        "rank_correlation_pdf": rank_correlation_pdf,
        "rank_correlation_png": rank_correlation_png,
        "lens_consistency_heatmap_pdf": lens_consistency_heatmap_pdf,
        "lens_consistency_heatmap_png": lens_consistency_heatmap_png,
        "rank_correlation_heatmap_pdf": rank_correlation_heatmap_pdf,
        "rank_correlation_heatmap_png": rank_correlation_heatmap_png,
        "result_summary_md": result_summary_md,
    }

    render_reversal_consistency_figure(
        lens_summary_rows,
        pdf_path=reversal_consistency_pdf,
        png_path=reversal_consistency_png,
    )
    render_rank_correlation_figure(
        rank_summary_rows,
        pdf_path=rank_correlation_pdf,
        png_path=rank_correlation_png,
    )
    render_paper_heatmap(
        row_labels=[rule_spec.label for rule_spec in PAPER_LENS_RULE_SPECS],
        column_labels=[lens_spec.label for lens_spec in PAPER_LENS_SPECS],
        values=_lens_heatmap_values(lens_matrix_cells),
        vmin=0.0,
        vmax=1.0,
        cmap_name="Blues",
        colorbar_label="Mean consistency",
        figsize=(7.0, 4.0),
        pdf_path=lens_consistency_heatmap_pdf,
        png_path=lens_consistency_heatmap_png,
    )
    render_paper_heatmap(
        row_labels=[rule_spec.label for rule_spec in PAPER_RANK_RULE_SPECS],
        column_labels=[rule_spec.label for rule_spec in PAPER_RANK_RULE_SPECS],
        values=_rank_heatmap_values(rank_matrix_cells),
        vmin=-1.0,
        vmax=1.0,
        cmap_name="coolwarm",
        colorbar_label=f"Mean {config.correlation_method.capitalize()} correlation",
        figsize=(6.5, 5.0),
        pdf_path=rank_correlation_heatmap_pdf,
        png_path=rank_correlation_heatmap_png,
    )
    _write_metadata(metadata_json, config, output_paths)
    _write_markdown_summary(
        result_summary_md,
        config=config,
        lens_summary_rows=lens_summary_rows,
        rank_summary_rows=rank_summary_rows,
        lens_matrix_cells=tuple(lens_matrix_cells),
        rank_matrix_cells=tuple(rank_matrix_cells),
        output_paths=output_paths,
    )

    return PaperSimulationResult(
        out_dir=config.out_dir,
        results_dir=config.results_dir,
        figures_dir=config.figures_dir,
        docs_dir=config.docs_dir,
        lens_consistency_csv=lens_consistency_csv,
        lens_consistency_summary_csv=lens_consistency_summary_csv,
        rank_correlation_csv=rank_correlation_csv,
        rank_correlation_summary_csv=rank_correlation_summary_csv,
        lens_consistency_matrix_csv=lens_consistency_matrix_csv,
        lens_consistency_long_csv=lens_consistency_long_csv,
        rank_correlation_matrix_csv=rank_correlation_matrix_csv,
        rank_correlation_long_csv=rank_correlation_long_csv,
        simulation_summary_csv=simulation_summary_csv,
        metadata_json=metadata_json,
        reversal_consistency_pdf=reversal_consistency_pdf,
        reversal_consistency_png=reversal_consistency_png,
        rank_correlation_pdf=rank_correlation_pdf,
        rank_correlation_png=rank_correlation_png,
        lens_consistency_heatmap_pdf=lens_consistency_heatmap_pdf,
        lens_consistency_heatmap_png=lens_consistency_heatmap_png,
        rank_correlation_heatmap_pdf=rank_correlation_heatmap_pdf,
        rank_correlation_heatmap_png=rank_correlation_heatmap_png,
        result_summary_md=result_summary_md,
        lens_summary_rows=tuple(lens_summary_rows),
        rank_summary_rows=tuple(rank_summary_rows),
        lens_matrix_cells=tuple(lens_matrix_cells),
        rank_matrix_cells=tuple(rank_matrix_cells),
    )


__all__ = ["PaperSimulationResult", "run_paper_simulation"]
