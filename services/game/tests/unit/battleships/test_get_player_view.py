from services.game.engines.battleships import (
    Battleships,
    Cell,
    State,
    init_grid,
)


def test_if_hit_continue_making_move():
    g1 = init_grid()
    g2 = init_grid()

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
    view = engine.get_player_view(1)
    for row in view.opponent_grid:
        assert Cell.BOAT not in row
