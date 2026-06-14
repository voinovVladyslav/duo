import enum
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from services.game.engines.base import GameEngine

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
    current_player: Literal[0, 1] = 0
    players: tuple[int, int]
    p1: Grid
    p2: Grid

    @field_validator('p1', 'p2')
    @classmethod
    def validate_grid(cls, value: Grid):
        if len(value) != GRID_SIZE:
            raise ValueError(f'Invalid grid size: {len(value)} != {GRID_SIZE}')

        for row in value:
            if len(row) != GRID_SIZE:
                raise ValueError(
                    f'Invalid grid size: {len(value)} != {GRID_SIZE}'
                )
            for cell in row:
                if cell not in Cell._value2member_map_:
                    raise ValueError(f'Invalid cell value: {cell}')


class PlayerView(BaseModel):
    pass


class Battleships(GameEngine[State, Move, PlayerView]):
    @classmethod
    def new_game(cls, p1: int, p2: int):
        return cls(state=State(players=(p1, p2), p1=[], p2=[]))

    @classmethod
    def load_game(cls, state: dict[str, Any]):
        return cls(state=State.model_validate(state))

    @classmethod
    def load_move(cls, move: str):
        return Move.model_validate_json(move)

    def get_winner(self) -> int | None:
        return None

    def is_draw(self) -> bool:
        return False

    def is_move_possible(self, move: Move) -> bool:
        return False

    def make_move(self, move: Move) -> None:
        return None

    def get_player_view(self, player_id: int) -> PlayerView:
        return PlayerView()

    def get_current_player(self) -> int:
        return 1
