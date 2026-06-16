import pytest
from pydantic import ValidationError

from services.game.engines.battleships import State, make_empty_grid


def test_valid_state_ok():
    grids = {
        1: make_empty_grid(),
        2: make_empty_grid(),
    }
    State.model_validate(
        {
            'current_player': 1,
            'players': (1, 2),
            'grids': grids,
        },
    )


def test_invalid_p1_grid_size():
    p1_grid = make_empty_grid()
    p1_grid.append([])
    grids = {
        1: p1_grid,
        2: make_empty_grid(),
    }
    with pytest.raises(ValidationError):
        State.model_validate(
            {'current_player': 1, 'players': (1, 2), 'grids': grids},
        )


def test_invalid_p2_grid_size():
    p2_grid = make_empty_grid()
    p2_grid.append([])
    grids = {
        1: make_empty_grid(),
        2: p2_grid,
    }
    with pytest.raises(ValidationError):
        State.model_validate(
            {'current_player': 1, 'players': (1, 2), 'grids': grids},
        )


def test_invalid_element_inside_grid():
    p1_grid = make_empty_grid()
    p1_grid[0][0] = ' '  # pyright: ignore[]
    grids = {
        1: p1_grid,
        2: make_empty_grid(),
    }
    with pytest.raises(ValidationError):
        State.model_validate(
            {'current_player': 1, 'players': (1, 2), 'grids': grids},
        )
