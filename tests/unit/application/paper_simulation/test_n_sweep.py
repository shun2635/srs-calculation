"""Tests for the n-sweep analysis (#22, part 1).

The slow test pins that the n=5 step of the sweep reproduces the canonical
single-n baseline numbers exactly -- i.e. the additive analysis does not perturb
the protected results.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srs_calculation.application.paper_simulation.n_sweep import (
    DEFAULT_SWEEP_STEPS,
    build_n_sweep_config,
    run_n_sweep,
)


def test_build_n_sweep_config_sorts_and_validates() -> None:
    config = build_n_sweep_config(steps=((5, 100), (3, 200)))
    assert [(step.players, step.count) for step in config.steps] == [(3, 200), (5, 100)]

    with pytest.raises(ValueError):
        build_n_sweep_config(steps=((3, 100), (3, 200)))  # duplicate n
    with pytest.raises(ValueError):
        build_n_sweep_config(steps=())


def test_default_sweep_steps_are_3_to_7() -> None:
    assert DEFAULT_SWEEP_STEPS == ((3, 1000), (4, 1000), (5, 1000), (6, 1000), (7, 500))


def test_n_sweep_writes_outputs_for_small_sweep(tmp_path: Path) -> None:
    config = build_n_sweep_config(steps=((3, 50), (4, 50)), out_dir=tmp_path / "sweep")
    result = run_n_sweep(config)

    assert result.overview_csv.exists()
    assert result.consistency_csv.exists()
    assert result.correlation_csv.exists()
    assert result.metadata_json.exists()
    assert result.consistency_figure_pdf.exists()
    assert result.correlation_figure_pdf.exists()

    assert [row.n for row in result.overview_rows] == [3, 4]
    # Rankdiff stays fully Reversal-consistent at every n (the theorem holds).
    for row in result.overview_rows:
        assert row.rankdiff_reversal_macro == 1.0
        assert row.rankdiff_reversal_micro == 1.0
    # Five rules per n in the per-rule consistency table.
    assert len(result.consistency_rows) == 2 * 5


@pytest.mark.slow
def test_n_sweep_n5_reproduces_canonical_numbers(tmp_path: Path) -> None:
    config = build_n_sweep_config(steps=((5, 1000),), out_dir=tmp_path / "sweep")
    result = run_n_sweep(config)

    overview = next(row for row in result.overview_rows if row.n == 5)
    assert overview.firing_cases == 43071
    assert overview.rankdiff_reversal_macro == 1.0
    assert overview.rankdiff_reversal_micro == 1.0
    assert overview.gl_rankdiff_spearman_overall == pytest.approx(0.5568, abs=1e-4)
