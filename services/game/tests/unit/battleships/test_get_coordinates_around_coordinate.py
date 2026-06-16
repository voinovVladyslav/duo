import pytest

from services.game.engines.battleships import (
    Coordinate,
    get_coordinates_around_coordinate,
)


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
