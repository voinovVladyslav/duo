from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from grpc import StatusCode, aio

from common.types.game import (
    RESULT_FROM_PROTO_MAP,
    STATUS_FROM_PROTO_MAP,
    TYPE_FROM_PROTO_MAP,
    TYPE_TO_PROTO_MAP,
)
from generated import game_pb2
from services.api.dependencies import GameServiceDep
from services.api.schemas.games import CreateGameRequest, GameResponse
from services.api.security import Credentials
from services.api.token import get_user_from_token

router = APIRouter(tags=['games'])


def _game_proto_to_response(game: game_pb2.Game) -> GameResponse:
    return GameResponse(
        id=game.id,
        type=TYPE_FROM_PROTO_MAP[game.type],
        result=RESULT_FROM_PROTO_MAP[game.result],
        status=STATUS_FROM_PROTO_MAP[game.status],
        player1=game.player1,
        player2=game.player2,
        current_player=game.current_player,
        turn_number=game.turn_number,
        created_at=game.created_at.ToDatetime(),
        updated_at=game.updated_at.ToDatetime(),
    )


@router.post('/create/')
async def game_create(
    credentials: Credentials,
    game_stub: GameServiceDep,
    data: CreateGameRequest,
) -> GameResponse:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    meta = (('authorization', credentials.credentials),)
    try:
        game = await game_stub.CreateGame(
            game_pb2.CreateGameRequest(type=TYPE_TO_PROTO_MAP[data.type]),
            timeout=2,
            metadata=meta,
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
            )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Unexpected error',
        )

    return _game_proto_to_response(game)


@router.get('/{game_id}/')
async def game_detail(
    credentials: Credentials,
    game_stub: GameServiceDep,
    game_id: int,
) -> GameResponse:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    meta = (('authorization', credentials.credentials),)
    try:
        game = await game_stub.GetGameById(
            game_pb2.GetGameByIdRequest(game_id=game_id),
            timeout=2,
            metadata=meta,
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
            )

        if exc.code() == StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Not found'
            )

        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to authorize you',
        )

    return _game_proto_to_response(game)
