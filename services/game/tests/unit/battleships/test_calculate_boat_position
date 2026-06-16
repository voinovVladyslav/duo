import pytest

from services.game.engines.battleships import (
    Coordinate,
    Direction,
    calculate_boat_position,
)


@pytest.mark.parametrize(
    ('start', 'direction', 'size', 'result'),
    [
        ((0, 0), Direction.RIGHT, 2, [(0, 0), (0, 1)]),
        ((0, 0), Direction.BOTTOM, 2, [(0, 0), (1, 0)]),
        ((0, 0), Direction.RIGHT, 5, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]),
        ((0, 0), Direction.BOTTOM, 5, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]),
        ((9, 9), Direction.TOP, 2, [(9, 9), (8, 9)]),
        ((9, 9), Direction.LEFT, 2, [(9, 9), (9, 8)]),
        ((9, 9), Direction.TOP, 5, [(9, 9), (8, 9), (7, 9), (6, 9), (5, 9)]),
        ((9, 9), Direction.LEFT, 5, [(9, 9), (9, 8), (9, 7), (9, 6), (9, 5)]),
    ],
)
def test_calculate_boat_position(
    start: Coordinate,
    direction: Direction,
    size: int,
    result: list[Coordinate],
):
    assert calculate_boat_position(start, direction, size) == result
