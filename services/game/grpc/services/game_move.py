import json
from typing import Any, override

from grpc import StatusCode
from grpc.aio import ServicerContext

from common.proto import datetime_to_timestamp
from generated import game_pb2, game_pb2_grpc
from services.game.db.crud import (
    get_game_by_id,
    get_game_move_by_id,
    get_game_moves,
)
from services.game.db.models import GameMove
from services.game.grpc.interceptors import get_current_user_id


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
        user = get_current_user_id()
        if user is None:
            return await context.abort(code=StatusCode.UNAUTHENTICATED)

        move = await get_game_move_by_id(id=request.move_id)
        if move is None:
            return await context.abort(code=StatusCode.NOT_FOUND)

        game = await get_game_by_id(id=move.game_id)
        if game is None:
            return await context.abort(code=StatusCode.NOT_FOUND)

        if user not in (game.player1, game.player2):
            return await context.abort(code=StatusCode.PERMISSION_DENIED)
        return _game_move_to_proto(move)

    @override
    async def GetMovesForGame(
        self,
        request: game_pb2.GetMovesForGameRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.ListMoveResponse:
        user = get_current_user_id()
        if user is None:
            return await context.abort(code=StatusCode.UNAUTHENTICATED)

        game = await get_game_by_id(id=request.game_id)
        if game is None:
            return await context.abort(code=StatusCode.NOT_FOUND)

        if user not in (game.player1, game.player2):
            return await context.abort(code=StatusCode.PERMISSION_DENIED)

        moves = await get_game_moves(game_id=request.game_id)
        return game_pb2.ListMoveResponse(
            moves=(_game_move_to_proto(m) for m in moves)
        )
