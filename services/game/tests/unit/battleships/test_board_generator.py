import pytest

from services.game.engines.battleships import (
    Coordinate,
    Direction,
    get_coordinates_around_coordinate,
    is_placement_possible,
)


@pytest.mark.parametrize(
    ('start', 'direction', 'size', 'result'),
    [
        ((0, 0), Direction.RIGHT, 5, True),
        ((0, 0), Direction.BOTTOM, 5, True),
        ((0, 0), Direction.LEFT, 5, False),
        ((0, 0), Direction.TOP, 5, False),
        ((9, 9), Direction.RIGHT, 5, False),
        ((9, 9), Direction.BOTTOM, 5, False),
        ((9, 9), Direction.LEFT, 5, True),
        ((9, 9), Direction.TOP, 5, True),
        ((4, 4), Direction.TOP, 2, True),
        ((4, 4), Direction.LEFT, 2, True),
        ((4, 4), Direction.RIGHT, 2, True),
        ((4, 4), Direction.BOTTOM, 2, True),
        ((1, 1), Direction.BOTTOM, 2, True),
        ((1, 1), Direction.LEFT, 2, True),
        ((1, 1), Direction.RIGHT, 2, True),
        ((1, 1), Direction.TOP, 2, True),
        ((1, 1), Direction.BOTTOM, 3, True),
        ((1, 1), Direction.LEFT, 3, False),
        ((1, 1), Direction.RIGHT, 3, True),
        ((1, 1), Direction.TOP, 3, False),
        ((8, 8), Direction.BOTTOM, 2, True),
        ((8, 8), Direction.LEFT, 2, True),
        ((8, 8), Direction.RIGHT, 2, True),
        ((8, 8), Direction.TOP, 2, True),
        ((8, 8), Direction.BOTTOM, 3, False),
        ((8, 8), Direction.LEFT, 3, True),
        ((8, 8), Direction.RIGHT, 3, False),
        ((8, 8), Direction.TOP, 3, True),
    ],
)
def test_is_placement_possible(
    start: Coordinate, direction: Direction, size: int, result: bool
):
    assert is_placement_possible(start, direction, size) is result


@pytest.mark.parametrize(
    ('coordinate', 'result'),
    [
        ((0, 0), {(0, 1), (1, 0), (1, 1)}),
        (
            (1, 1),
            {
                (0, 0),
                (0, 1),
                (0, 2),
                (1, 0),
                (1, 2),
                (2, 0),
                (2, 1),
                (2, 2),
            },
        ),
        (
            (0, 1),
            {
                (0, 0),
                (0, 2),
                (1, 0),
                (1, 1),
                (1, 2),
            },
        ),
    ],
)
def test_get_coordinates_around_coordinate(
    coordinate: Coordinate,
    result: set[Coordinate],
):
    assert get_coordinates_around_coordinate(coordinate) == result
