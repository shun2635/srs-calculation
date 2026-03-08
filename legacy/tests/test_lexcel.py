from __future__ import annotations

from gamegen.rules.lexcel import rank_by_lexcel


def test_rank_by_lexcel_orders_players() -> None:
    scores = {
        0b000: 0.0,
        0b001: 10.0,
        0b010: 10.0,
        0b011: 15.0,
        0b100: 8.0,
        0b101: 9.0,
        0b110: 7.0,
        0b111: 20.0,
    }
    ranks = rank_by_lexcel(scores, n=3)
    assert ranks == {0: 1, 1: 2, 2: 3}


def test_rank_by_lexcel_dense_ties() -> None:
    scores = {
        0b00: 0.0,
        0b01: 3.0,
        0b10: 3.0,
        0b11: 4.0,
    }
    ranks = rank_by_lexcel(scores, n=2)
    assert ranks == {0: 1, 1: 1}
