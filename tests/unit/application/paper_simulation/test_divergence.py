"""Tests for the divergence condition analysis (#22, part 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from srs_calculation.application.paper_simulation.divergence import (
    build_divergence_config,
    run_divergence_analysis,
)


def test_divergence_config_validates() -> None:
    with pytest.raises(ValueError):
        build_divergence_config(players=1)
    with pytest.raises(ValueError):
        build_divergence_config(count=0)


def test_divergence_writes_records_and_feature_table(tmp_path: Path) -> None:
    config = build_divergence_config(players=4, count=50, out_dir=tmp_path / "div")
    result = run_divergence_analysis(config)

    assert result.records_csv.exists()
    assert result.feature_correlation_csv.exists()
    assert result.metadata_json.exists()
    assert result.scatter_pdf.exists()

    # n=4 has size-2 and size-3 coalition sizes with >= 2 coalitions.
    assert {record.k for record in result.records} == {2, 3}
    for record in result.records:
        assert 0.0 <= record.disagreement_rate <= 1.0
        assert 0 <= record.num_discordant_pairs <= record.num_pairs
        assert record.num_reversal_pairs >= 0

    # Feature rows cover both targets, an "all" pooled segment and per-k segments.
    segments = {row.k_segment for row in result.feature_rows}
    assert "all" in segments and "2" in segments and "3" in segments
    targets = {row.target for row in result.feature_rows}
    assert targets == {"disagreement_rate", "one_minus_spearman"}
