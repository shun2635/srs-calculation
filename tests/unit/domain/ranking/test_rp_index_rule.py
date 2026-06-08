"""Unit tests for the Rankdiff (rp_index) rule.

These tests pin the paper definition

    Rankdiff(S) = (1 / |S|) * sum_{i in S} r({i})  -  r(S)

with ``r(C) = |{C' : C' > C}|`` (number of strictly-better coalitions, ties not
counted, smallest rank value = most preferred). The key property exercised here
is that ties at both the individual and the coalition level are handled exactly
as in the hand calculation, i.e. tied coalitions do not contribute to each
other's rank value.
"""

from __future__ import annotations

from srs_calculation.domain.games.coalition_game import CoalitionGame
from srs_calculation.domain.ranking.rules.rp_index import RpIndexRule


def _rank_value(level: int, levels: dict[int, int]) -> int:
    """Reference r(C): count non-empty coalitions on strictly smaller levels."""

    return sum(
        1
        for mask, other_level in levels.items()
        if int(mask) != 0 and int(other_level) < int(level)
    )


def test_rankdiff_matches_paper_with_individual_and_team_ties() -> None:
    """§4.3-style example with S={3,4}, T={1,2}, mixing individual/team ties.

    Players 1..4 map to bit indices 0..3, so T={1,2}=0b0011=3 and
    S={3,4}=0b1100=12. T's singletons individually dominate S's singletons
    (and are tied with each other), while S forms the stronger group. Several
    other coalitions are deliberately tied so that the ``ties not counted``
    rule materially affects every rank value.
    """

    scores_by_mask = {
        0b0000: 0,  # empty set (excluded from the pool)
        0b0001: 10,  # {1}  tie with {2}
        0b0010: 10,  # {2}
        0b0011: 5,  # {1,2} = T
        0b0100: 6,  # {3}  tie with {4}
        0b0101: 7,  # {1,3} tie with {2,3}
        0b0110: 7,  # {2,3}
        0b0111: 12,  # {1,2,3}
        0b1000: 6,  # {4}
        0b1001: 4,  # {1,4} tie with {2,4}
        0b1010: 4,  # {2,4}
        0b1011: 11,  # {1,2,4}
        0b1100: 9,  # {3,4} = S
        0b1101: 13,  # {1,3,4}
        0b1110: 3,  # {2,3,4}
        0b1111: 15,  # grand coalition
    }
    game = CoalitionGame.from_scores_by_mask(4, {m: float(v) for m, v in scores_by_mask.items()})

    result = RpIndexRule().evaluate(game)
    assert result.score_set is not None
    values = result.score_set.values_by_coalition

    # Rank values r(C) computed independently from the induced levels.
    levels = game.coalition_levels()
    r = {mask: _rank_value(levels[mask], levels) for mask in scores_by_mask if mask != 0}

    # Hand-computed rank values for the coalitions of interest.
    assert r[0b0001] == 4 and r[0b0010] == 4  # T's members (tied, high)
    assert r[0b0100] == 9 and r[0b1000] == 9  # S's members (tied, lower)
    assert r[0b1100] == 6  # S as a group
    assert r[0b0011] == 11  # T as a group

    # Rankdiff(S) = avg(9, 9) - 6 = 3 ; Rankdiff(T) = avg(4, 4) - 11 = -7.
    s_mask, t_mask = 0b1100, 0b0011
    assert values[s_mask] == 3.0
    assert values[t_mask] == -7.0

    # Every size>=2 coalition must equal the paper formula exactly.
    for mask, value in values.items():
        members = game.coalition_members(mask)
        expected = sum(r[1 << p] for p in members) / len(members) - r[mask]
        assert value == expected

    # S has strictly more synergy than T, so the induced ranking puts S above T.
    ranks = result.rank_set.ranks_by_coalition
    assert ranks[s_mask] < ranks[t_mask]
