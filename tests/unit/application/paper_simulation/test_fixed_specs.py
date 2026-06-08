"""Guards for the fixed (non-configurable) specifications (Step4).

These pin the paper-critical specs and assert they are NOT exposed as
configuration, so they cannot be flipped by a CLI flag or config field.
"""

from __future__ import annotations

import dataclasses

from srs_calculation.application.paper_simulation import fixed_specs
from srs_calculation.application.paper_simulation.config import PaperSimulationConfig


def test_fixed_spec_values() -> None:
    assert fixed_specs.REVERSAL_STRICT_GROUP_ORDERING is True
    assert fixed_specs.OUTPUT_TIES_COUNT_AS_UNSATISFIED is True
    assert fixed_specs.RANK_VALUE_TIES_NOT_COUNTED is True
    assert fixed_specs.MAIN_TEXT_ADEQUACY_AVERAGE == "macro"
    assert fixed_specs.RANKDIFF_DEFINITION == (
        "Rankdiff(S) = (1/|S|) * sum_{i in S} r({i}) - r(S)"
    )


def test_fixed_specs_are_not_configurable() -> None:
    config_fields = {field.name for field in dataclasses.fields(PaperSimulationConfig)}
    # None of the fixed-spec concepts may appear as a configurable field.
    forbidden = {
        "reversal_strict_group_ordering",
        "output_ties_count_as_unsatisfied",
        "rank_value_ties_not_counted",
        "rankdiff_definition",
        "adequacy_average",
        "tie_satisfaction",
    }
    assert config_fields.isdisjoint(forbidden)
