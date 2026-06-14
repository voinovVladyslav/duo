import pytest
from pydantic import ValidationError

from services.game.engines.battleships import GRID_SIZE, Cell, Grid, State


def _make_empty_grid() -> Grid:
    return [[Cell.EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def test_valid_state_ok():
    State.model_validate(
        {
            'players': (1, 2),
            'p1': _make_empty_grid(),
            'p2': _make_empty_grid(),
        },
    )


def test_invalid_p1_grid_size():
    p1_grid = _make_empty_grid()
    p1_grid.append([])
    with pytest.raises(ValidationError):
        State.model_validate(
            {
                'players': (1, 2),
                'p1': p1_grid,
                'p2': _make_empty_grid(),
            },
        )


def test_invalid_p2_grid_size():
    p2_grid = _make_empty_grid()
    p2_grid.append([])
    with pytest.raises(ValidationError):
        State.model_validate(
            {
                'players': (1, 2),
                'p1': _make_empty_grid(),
                'p2': p2_grid,
            },
        )


def test_invalid_element_inside_grid():
    p1_grid = _make_empty_grid()
    p1_grid[0][0] = ' '  # pyright: ignore[]
    with pytest.raises(ValidationError):
        State.model_validate(
            {
                'players': (1, 2),
                'p1': p1_grid,
                'p2': _make_empty_grid(),
            },
        )
