from services.game.engines.battleships import (
    Battleships,
    Cell,
    State,
    make_empty_grid,
)


def test_get_winner_return_none_if_both_have_ships():
    g1 = make_empty_grid()
    g2 = make_empty_grid()
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
    assert engine.get_winner() is None


def test_get_winner_return_opponent_if_no_boats():
    g1 = make_empty_grid()
    g2 = make_empty_grid()
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
    assert engine.get_winner() == 2  # noqa


def test_get_winner_return_opponent_if_no_boats_vice_versa():
    g1 = make_empty_grid()
    g2 = make_empty_grid()
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
    assert engine.get_winner() == 1
