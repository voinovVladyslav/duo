from services.game.engines.battleships import (
    Battleships,
    Cell,
    Move,
    State,
    make_empty_grid,
)


def test_can_make_move_on_boat():
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
    assert engine.is_move_possible(move) is True


def test_does_not_check_own_grid():
    g1 = make_empty_grid()
    g2 = make_empty_grid()
    g1[4][4] = Cell.BOAT
    g2[4][4] = Cell.BOAT
    g1[0][0] = Cell.HIT
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
    assert engine.is_move_possible(move) is True


def test_cannot_hit_same_cell_twice():
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
    assert engine.is_move_possible(move) is False


def test_empty_cell_is_allowed():
    g1 = make_empty_grid()
    g2 = make_empty_grid()
    g1[4][4] = Cell.BOAT
    g2[4][4] = Cell.BOAT

    g1[0][0] = Cell.BOAT
    g2[0][0] = Cell.EMPTY
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
    assert engine.is_move_possible(move) is True
