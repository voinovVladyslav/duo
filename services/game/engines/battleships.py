import enum
import random
from typing import Any

from pydantic import BaseModel, field_validator

from services.game.engines.base import GameEngine
from services.game.exceptions import InvalidMoveError

GRID_SIZE = 10


class Cell(str, enum.Enum):
    EMPTY = ''
    BOAT = 'b'
    HIT = 'x'
    MISS = 'm'


type Grid = list[list[Cell]]
type Coordinate = tuple[int, int]


class Move(BaseModel):
    coordinate: Coordinate


class State(BaseModel):
    current_player: int
    players: tuple[int, int]
    grids: dict[int, Grid]

    @field_validator('grids')
    @classmethod
    def validate_grids(cls, value: dict[int, Grid]):
        for grid in value.values():
            if len(grid) != GRID_SIZE:
                raise ValueError(
                    f'Invalid grid size: {len(grid)} != {GRID_SIZE}'
                )

            for row in grid:
                if len(row) != GRID_SIZE:
                    raise ValueError(
                        f'Invalid grid size: {len(grid)} != {GRID_SIZE}'
                    )
                for cell in row:
                    if cell not in Cell._value2member_map_:
                        raise ValueError(f'Invalid cell v: {cell}')
        return value


class PlayerView(BaseModel):
    your_turn: bool
    your_grid: Grid
    opponent_grid: Grid
    winner: int | None
    is_draw: bool


class Direction(str, enum.Enum):
    TOP = 'top'
    BOTTOM = 'bottom'
    LEFT = 'left'
    RIGHT = 'right'


def make_empty_grid() -> Grid:
    return [[Cell.EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def _get_random_coordinate() -> Coordinate:
    x = random.randint(0, 9)
    y = random.randint(0, 9)
    return x, y


def _generate_directions() -> list[Direction]:
    result = [Direction.TOP, Direction.BOTTOM, Direction.LEFT, Direction.RIGHT]
    random.shuffle(result)
    return result


def is_placement_possible(
    start: Coordinate,
    direction: Direction,
    size: int,
) -> bool:
    size = size - 1
    if direction == Direction.TOP:
        return (start[0] - size) >= 0

    if direction == Direction.BOTTOM:
        return (start[0] + size) < GRID_SIZE

    if direction == Direction.LEFT:
        return (start[1] - size) >= 0

    if direction == Direction.RIGHT:
        return (start[1] + size) < GRID_SIZE


def calculate_boat_position(
    start: Coordinate,
    direction: Direction,
    size: int,
) -> list[Coordinate]:
    result: list[Coordinate] = []
    if direction == Direction.BOTTOM:
        for i in range(size):
            result.append((start[0] + i, start[1]))
        return result
    if direction == Direction.TOP:
        for i in range(size):
            result.append((start[0] - i, start[1]))
        return result
    if direction == Direction.LEFT:
        for i in range(size):
            result.append((start[0], start[1] - i))
        return result
    if direction == Direction.RIGHT:
        for i in range(size):
            result.append((start[0], start[1] + i))
        return result


def get_coordinates_around_coordinate(position: Coordinate) -> set[Coordinate]:
    coords: set[Coordinate] = {
        (position[0] - 1, position[1] - 1),  # top left
        (position[0] - 1, position[1] + 0),  # top top
        (position[0] - 1, position[1] + 1),  # top right
        (position[0] + 0, position[1] + 1),  # right right
        (position[0] + 1, position[1] + 1),  # bottom right
        (position[0] + 1, position[1] + 0),  # bottom bottom
        (position[0] + 1, position[1] - 1),  # bottom left
        (position[0] + 0, position[1] - 1),  # left left
    }
    res: set[Coordinate] = set()
    for c in coords:
        if c[0] == -1 or c[0] == GRID_SIZE or c[1] == -1 or c[1] == GRID_SIZE:
            continue
        res.add(c)
    return res


def has_ship_around(position: Coordinate, grid: Grid) -> bool:
    coords_to_check = get_coordinates_around_coordinate(position)
    for coord in coords_to_check:
        if grid[coord[0]][coord[1]] == Cell.BOAT:
            return True
    return False


def is_placement_allowed(positions: list[Coordinate], grid: Grid) -> bool:
    for pos in positions:
        if has_ship_around(pos, grid):
            return False
    return True


def fill_grid(grid: Grid) -> None:
    """Fills grid in place"""
    for size in (5, 4, 3, 3, 2):
        is_boat_placed: bool = False
        while is_boat_placed is False:
            start = _get_random_coordinate()
            directions = _generate_directions()
            for direction in directions:
                if not is_placement_possible(start, direction, size):
                    continue

                position = calculate_boat_position(start, direction, size)
                if not is_placement_allowed(position, grid):
                    continue

                for coord in position:
                    grid[coord[0]][coord[1]] = Cell.BOAT

                is_boat_placed = True


def init_grid() -> Grid:
    grid = make_empty_grid()
    fill_grid(grid)
    return grid


class Battleships(GameEngine[State, Move, PlayerView]):
    @classmethod
    def new_game(cls, p1: int, p2: int):
        grids = {p1: init_grid(), p2: init_grid()}
        return cls(
            state=State(
                current_player=p1,
                players=(p1, p2),
                grids=grids,
            ),
        )

    @classmethod
    def load_game(cls, state: dict[str, Any]):
        return cls(state=State.model_validate(state))

    @classmethod
    def load_move(cls, move: str):
        return Move.model_validate_json(move)

    def get_winner(self) -> int | None:
        for player, grid in self.state.grids.items():
            has_ships = False
            for row in grid:
                if Cell.BOAT in row:
                    has_ships = True
                    break

            if not has_ships:
                return self._get_opponent(player)
        return None

    def _get_opponent(self, player: int) -> int:
        if self.state.players[0] == player:
            return self.state.players[1]
        return self.state.players[0]

    def is_draw(self) -> bool:
        """Draw is impossible in battleships"""
        return False

    def is_move_possible(self, move: Move) -> bool:
        if self.is_game_over():
            return False

        opponent = self._get_opponent(self.state.current_player)
        grid = self.state.grids[opponent]
        cell = grid[move.coordinate[0]][move.coordinate[1]]
        return cell in [Cell.EMPTY, Cell.BOAT]

    def make_move(self, move: Move) -> None:
        if not self.is_move_possible(move):
            raise InvalidMoveError('Move is invalid')

        opponent = self._get_opponent(self.state.current_player)
        grid = self.state.grids[opponent]
        x, y = move.coordinate
        assert grid[x][y] not in [Cell.HIT, Cell.MISS]
        if grid[x][y] == Cell.BOAT:
            grid[x][y] = Cell.HIT

        if grid[x][y] == Cell.EMPTY:
            grid[x][y] = Cell.MISS
            self.state.current_player = opponent

    @staticmethod
    def _get_masked_grid(grid: Grid) -> Grid:
        result: Grid = make_empty_grid()
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if cell == Cell.BOAT:
                    result[i][j] = Cell.EMPTY
                else:
                    result[i][j] = cell
        return result

    def _get_opponent_grid(self, player_id: int) -> Grid:
        opp = self._get_opponent(player_id)
        return self._get_masked_grid(self.state.grids[opp])

    def get_player_view(self, player_id: int) -> PlayerView:
        your_turn = self.state.current_player == player_id
        winner = self.get_winner()
        if winner:
            your_turn = False
        return PlayerView(
            your_turn=your_turn,
            your_grid=self.state.grids[player_id],
            opponent_grid=self._get_opponent_grid(player_id),
            winner=winner,
            is_draw=self.is_draw(),
        )

    def get_current_player(self) -> int:
        return self.state.current_player
