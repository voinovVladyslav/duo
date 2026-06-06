import json
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Query
from grpc import StatusCode, aio

from generated import game_pb2
from services.api.dependencies import GameMoveServiceDep
from services.api.schemas.games import MoveResponse
from services.api.security import Credentials
from services.api.token import get_user_from_token

router = APIRouter(tags=['game-moves'])


def _require_authenticated_user(token_raw: str) -> int:
    user = get_user_from_token(token_raw)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    return user


def _rpc_error_to_http_exception(exc: aio.AioRpcError) -> HTTPException:
    if exc.code() == StatusCode.UNAUTHENTICATED:
        return HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    if exc.code() == StatusCode.PERMISSION_DENIED:
        return HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Forbidden'
        )
    if exc.code() == StatusCode.NOT_FOUND:
        return HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Not found'
        )
    return HTTPException(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail='Unexpected error',
    )


@router.get('/', response_model=list[MoveResponse])
async def list_game_moves(
    credentials: Credentials,
    game_move_stub: GameMoveServiceDep,
    game: int = Query(
        ..., title='Game ID', description='ID of the game to list moves for'
    ),
) -> list[MoveResponse]:
    _require_authenticated_user(credentials.credentials)
    meta = (('authorization', credentials.credentials),)
    try:
        resp = await game_move_stub.get_moves_for_game(
            game_pb2.GetMovesForGameRequest(game_id=game),
            timeout=2,
            metadata=meta,
        )
    except aio.AioRpcError as exc:
        raise _rpc_error_to_http_exception(exc)

    moves = [
        MoveResponse(
            id=m.id,
            game_id=m.game_id,
            player_id=m.player_id,
            turn_number=m.turn_number,
            move_data=json.loads(m.move_data),
            created_at=m.created_at.ToDatetime(),
            updated_at=m.updated_at.ToDatetime(),
        )
        for m in resp.moves
    ]

    return moves
