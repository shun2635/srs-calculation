"""Regression safety net pinning the confirmed paper-simulation numbers.

This test is the guard required by the refactor mandate: it runs the full
``run_paper_simulation`` orchestrator at the canonical settings
(``n=5, R=1000, seed=42``) and pins the numbers that the previous, paper-aligned
refactor established. Any structural refactor that changes behaviour will move
one of these values and turn this test red.

Confirmed baseline (seed=42, n=5, R=1000):
- Rankdiff Reversal consistency: macro = 1.0000, micro = 1.0000 (exact)
- Reversal firing cases (total constraints over all games/sizes): 43071 (exact)
- Group Lex-cel Reversal consistency: macro = 0.7073, micro = 0.7171
- Group Lex-cel vs Rankdiff Spearman correlation (overall): 0.5568

Floating-point values use abs tolerance 1e-4; the exact theorem values
(Rankdiff = 1.0) and the integer firing count are pinned exactly.

Do NOT edit the expected numbers to make a refactor pass. If a refactor moves a
value, stop and investigate -- the numbers are the source of truth (see
CLAUDE.md).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srs_calculation.application.paper_simulation import (
    build_paper_simulation_config,
    run_paper_simulation,
)
from srs_calculation.application.paper_simulation.full_comparison import (
    LensConsistencyMatrixCell,
)

# Canonical, paper-confirmed baseline numbers.
RANKDIFF_REVERSAL_MACRO = 1.0
RANKDIFF_REVERSAL_MICRO = 1.0
REVERSAL_FIRING_CASES = 43071
GROUP_LEXCEL_REVERSAL_MACRO = 0.7073
GROUP_LEXCEL_REVERSAL_MICRO = 0.7171
GL_RANKDIFF_SPEARMAN_OVERALL = 0.5568
ABS_TOL = 1e-4


def _reversal_cell(
    cells: tuple[LensConsistencyMatrixCell, ...], rule: str
) -> LensConsistencyMatrixCell:
    return next(cell for cell in cells if cell.rule == rule and cell.lens == "Reversal")


@pytest.mark.slow
def test_paper_simulation_baseline_numbers(tmp_path: Path) -> None:
    config = build_paper_simulation_config(
        players=5,
        count=1000,
        seed=42,
        out_dir=tmp_path / "paper",
        correlation_method="spearman",
        rank_tie_method="dense",
        empty_constraints="exclude",
    )
    result = run_paper_simulation(config)

    rankdiff_cell = _reversal_cell(result.lens_matrix_cells, "Rankdiff")
    group_lexcel_cell = _reversal_cell(result.lens_matrix_cells, "Group Lex-cel")
    lens_overall = next(row for row in result.lens_summary_rows if row.k == "overall")
    rank_overall = next(row for row in result.rank_summary_rows if row.k == "overall")

    # Rankdiff Reversal consistency is the proven theorem value: pin it exactly.
    assert rankdiff_cell.mean_consistency == RANKDIFF_REVERSAL_MACRO
    assert rankdiff_cell.micro_consistency == RANKDIFF_REVERSAL_MICRO
    # The focal Rankdiff path summary must agree (macro and micro both 1.0).
    assert lens_overall.mean_consistency == RANKDIFF_REVERSAL_MACRO
    assert lens_overall.micro_consistency == RANKDIFF_REVERSAL_MICRO

    # Firing-case count (strict < group ordering). Pinning this isolates whether a
    # consistency drift comes from the constraint set or from the rule output.
    assert lens_overall.num_constraints == REVERSAL_FIRING_CASES

    # Group Lex-cel Reversal consistency: macro and micro both pinned.
    assert group_lexcel_cell.mean_consistency == pytest.approx(
        GROUP_LEXCEL_REVERSAL_MACRO, abs=ABS_TOL
    )
    assert group_lexcel_cell.micro_consistency == pytest.approx(
        GROUP_LEXCEL_REVERSAL_MICRO, abs=ABS_TOL
    )

    # Group Lex-cel vs Rankdiff Spearman correlation (overall, the main-text value).
    assert rank_overall.mean_correlation == pytest.approx(
        GL_RANKDIFF_SPEARMAN_OVERALL, abs=ABS_TOL
    )
