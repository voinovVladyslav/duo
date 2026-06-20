import json
import logging
from typing import Any, override

from grpc import StatusCode
from grpc.aio import ServicerContext

from common.proto import datetime_to_timestamp
from generated import game_pb2, game_pb2_grpc
from services.game.db.crud import get_game_move_by_id, get_game_moves
from services.game.db.models import GameMove

logger = logging.getLogger('duo.game.grpc')


def _game_move_to_proto(move: GameMove) -> game_pb2.GameMove:
    assert move.id is not None
    return game_pb2.GameMove(
        id=move.id,
        game_id=move.game_id,
        player_id=move.player_id,
        turn_number=move.turn_number,
        move_data=json.dumps(move.move_data),
        created_at=datetime_to_timestamp(move.created_at),
        updated_at=datetime_to_timestamp(move.updated_at),
    )


class GameMoveService(game_pb2_grpc.GameMoveServiceServicer):
    @override
    async def GetMoveById(
        self,
        request: game_pb2.GetMoveByIdRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.GameMove:
        move = await get_game_move_by_id(id=request.move_id)
        if move is None:
            logger.info('move not found', extra={'move_id': request.move_id})
            await context.abort(code=StatusCode.NOT_FOUND)
        return _game_move_to_proto(move)

    @override
    async def GetMovesForGame(
        self,
        request: game_pb2.GetMovesForGameRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.ListMoveResponse:
        moves = await get_game_moves(game_id=request.game_id)
        return game_pb2.ListMoveResponse(
            moves=(_game_move_to_proto(m) for m in moves)
        )
