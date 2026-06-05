from datetime import datetime
from typing import Any

from pydantic import BaseModel

from common.types.game import Result, Status, Type


class CreateGameRequest(BaseModel):
    type: Type


class GameResponse(BaseModel):
    id: int
    type: Type
    result: Result
    status: Status
    player1: int
    player2: int | None
    current_player: int
    turn_number: int
    created_at: datetime
    updated_at: datetime


class MoveResponse(BaseModel):
    id: int
    game_id: int
    player_id: int
    turn_number: int
    move_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
