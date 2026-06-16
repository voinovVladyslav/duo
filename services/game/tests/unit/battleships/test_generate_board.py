from services.game.engines.battleships import Cell, init_grid


def test_generates_all_ships():
    expected = sum([5, 4, 3, 3, 2])
    grid = init_grid()

    total = 0
    for row in grid:
        for cell in row:
            if cell == Cell.BOAT:
                total += 1

    assert expected == total
