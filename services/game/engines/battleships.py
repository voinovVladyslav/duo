from typing import Any

from pydantic import BaseModel

from services.game.engines.base import GameEngine


class Move(BaseModel):
    pass


class State(BaseModel):
    pass


class PlayerView(BaseModel):
    pass


class Battleships(GameEngine[State, Move, PlayerView]):
    @classmethod
    def new_game(cls, p1: int, p2: int):
        return cls(state=State())

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
