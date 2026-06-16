import pytest

from services.game.engines.battleships import (
    Battleships,
    Cell,
    Move,
    State,
    make_empty_grid,
)
from services.game.exceptions import InvalidMoveError


def test_if_hit_continue_making_move():
    g1 = make_empty_grid()
    g2 = make_empty_grid()

    g1[4][4] = Cell.BOAT
    g2[4][4] = Cell.BOAT

    g1[0][0] = Cell.BOAT
    g2[0][0] = Cell.BOAT

    engine = Battleships(
        state=State(
            current_player=1,
            players=(1, 2),
            grids={
                1: g1,
                2: g2,
            },
        )
    )
    move = Move(coordinate=(0, 0))
    engine.make_move(move)
    assert engine.state.current_player == 1
    assert engine.state.grids[2][0][0] == Cell.HIT


def test_if_miss_opponent_moves_next():
    g1 = make_empty_grid()
    g2 = make_empty_grid()

    g1[4][4] = Cell.BOAT
    g2[4][4] = Cell.BOAT

    g1[0][0] = Cell.BOAT
    g2[0][0] = Cell.BOAT

    engine = Battleships(
        state=State(
            current_player=1,
            players=(1, 2),
            grids={
                1: g1,
                2: g2,
            },
        )
    )
    move = Move(coordinate=(1, 1))
    engine.make_move(move)
    assert engine.state.current_player == 2  # noqa
    assert engine.state.grids[2][1][1] == Cell.MISS


def test_making_invalid_move_raises():
    g1 = make_empty_grid()
    g2 = make_empty_grid()

    g1[4][4] = Cell.BOAT
    g2[4][4] = Cell.BOAT

    g1[0][0] = Cell.BOAT
    g2[0][0] = Cell.HIT

    engine = Battleships(
        state=State(
            current_player=1,
            players=(1, 2),
            grids={
                1: g1,
                2: g2,
            },
        )
    )
    move = Move(coordinate=(0, 0))
    with pytest.raises(InvalidMoveError):
        engine.make_move(move)
