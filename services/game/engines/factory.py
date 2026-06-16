from typing import Any

from common.types.game import Type
from services.game.engines.base import GameEngine
from services.game.engines.battleships import Battleships
from services.game.engines.tic_tac_toe import TicTacToe


def get_game_engine_class(game_type: Type) -> type[GameEngine[Any, Any, Any]]:
    if game_type == Type.TIC_TAC_TOE:
        return TicTacToe
    if game_type == Type.BATTLESHIPS:
        return Battleships
