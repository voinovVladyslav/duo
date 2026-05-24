import asyncio
import json
import logging
from typing import Any, MutableMapping, cast

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
from redis.asyncio.client import PubSub

from generated import game_pb2, game_pb2_grpc
from services.api.routers.websockets.types import (
    AuthenticatedMessage,
    AuthenticatedMessageBody,
    ConnectedMessage,
    ConnectedMessageBody,
    DisconnectedMessage,
    DisconnectedMessageBody,
    GameMessageAdapter,
    GameStateMessage,
    GameStateMessageBody,
    InvalidMoveMessage,
    InvalidMoveMessageBody,
    MessageType,
)
from services.api.token import get_user_from_token

router = APIRouter(tags=['websocket'])

_logger = logging.getLogger('duo.api.websockets')


class GameLoggingAdapter(logging.LoggerAdapter[logging.Logger]):
    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        if self.extra is None:
            return msg, kwargs

        game = self.extra.get('game', '-')
        user = self.extra.get('user', '-')
        return f'({game} : {user}) {msg}', kwargs


def get_opponent(game: game_pb2.Game, user: int) -> int | None:
    if game.player1 == user:
        return game.player2
    if game.player2 == user:
        return game.player1
    return None


async def handle_authentication(
    *,
    websocket: WebSocket,
    logger: GameLoggingAdapter,
) -> int | None:
    await websocket.accept()
    logger.debug('connection accepted')

    message = GameMessageAdapter.validate_python(await websocket.receive_json())

    if message.type != MessageType.TOKEN:
        logger.debug('received message is not token, rejecting')
        await websocket.close(code=1008, reason='not authenticated')
        return None

    user = get_user_from_token(message.body.token)
    if user is None:
        logger.debug('token is not valid, rejecting')
        await websocket.close(code=1008, reason='not authenticated')
        return None

    return user


async def _game_loop(  # noqa: PLR0913
    *,
    logger: GameLoggingAdapter,
    game_service: game_pb2_grpc.GameServiceAsyncStub,
    cache: redis.Redis,
    websocket: WebSocket,
    user: int,
    game_id: int,
) -> None:
    while True:
        logger.debug('waiting for message from user')
        message = GameMessageAdapter.validate_python(
            await websocket.receive_json()
        )
        logger.debug('message received: %s', message)
        if message.type != MessageType.GAME_MOVE:
            await websocket.send_text(
                InvalidMoveMessage(
                    body=InvalidMoveMessageBody(message='invalid move')
                ).model_dump_json()
            )
            continue
        try:
            move_response = await game_service.MakeMove(
                game_pb2.MakeMoveRequest(
                    game_id=game_id,
                    player_id=user,
                    move_data=json.dumps(message.body.game_move),
                )
            )
        except Exception:
            await websocket.send_text(
                InvalidMoveMessage(
                    body=InvalidMoveMessageBody(message='invalid move')
                ).model_dump_json()
            )
            continue

        game = move_response.game
        if game.player1 == user:
            ws_payload = move_response.player1_view
            cache_payload = move_response.player2_view
        else:
            ws_payload = move_response.player2_view
            cache_payload = move_response.player1_view

        await websocket.send_text(
            GameStateMessage(
                body=GameStateMessageBody(game_state=json.loads(ws_payload))
            ).model_dump_json()
        )
        opponent = get_opponent(game, user)
        await cache.publish(  # pyright: ignore
            f'game:{game_id}:{opponent}',
            GameStateMessage(
                body=GameStateMessageBody(game_state=json.loads(cache_payload))
            ).model_dump_json(),
        )


async def _wait_for_messages(
    *,
    logger: GameLoggingAdapter,
    websocket: WebSocket,
    channel: PubSub,
) -> None:
    logger.debug('waiting for message for user')
    async for message in channel.listen():  # pyright: ignore
        if message['type'] == 'message':
            message = cast(dict[str, Any], message)
            logger.debug('received message for user: %s', message)
            await websocket.send_text(message['data'].decode())


async def _fetch_game(
    *,
    game_service: game_pb2_grpc.GameServiceAsyncStub,
    game_id: int,
) -> game_pb2.Game | None:
    try:
        return await game_service.GetGameById(
            game_pb2.GetGameByIdRequest(game_id=game_id)
        )
    except Exception:
        return None


async def _handle_second_player_join(  # noqa: PLR0913
    *,
    game_service: game_pb2_grpc.GameServiceAsyncStub,
    game: game_pb2.Game,
    user: int,
    websocket: WebSocket,
    cache: redis.Redis,
    logger: GameLoggingAdapter,
) -> game_pb2.Game:
    response = await game_service.JoinGame(
        game_pb2.JoinGameRequest(game_id=game.id, player_id=user),
    )
    game = response.game
    logger.debug('accepted game as user %s', user)
    logger.debug('sending to ws for user: %s', game.player2)
    await websocket.send_text(
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(response.player2_view)
            )
        ).model_dump_json()
    )
    logger.debug('publishing to redis for user: %s', game.player1)
    await cache.publish(  # pyright: ignore
        f'game:{game.id}:{game.player1}',
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(response.player1_view)
            )
        ).model_dump_json(),
    )
    return game


async def _handle_player_reconnected(  # noqa: PLR0913
    *,
    game_service: game_pb2_grpc.GameServiceAsyncStub,
    game: game_pb2.Game,
    user: int,
    logger: GameLoggingAdapter,
    websocket: WebSocket,
    cache: redis.Redis,
) -> None:
    player_view = await game_service.GetPlayerView(
        game_pb2.GetPlayerViewRequest(game_id=game.id, player_id=user)
    )
    await websocket.send_text(
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(player_view.game_state)
            )
        ).model_dump_json()
    )
    logger.debug('user reconnected')
    opponent = get_opponent(game=game, user=user)
    await cache.publish(  # pyright: ignore
        f'game:{game.id}:{opponent}',
        ConnectedMessage(
            body=ConnectedMessageBody(message=f'Opponent {user} connected'),
        ).model_dump_json(),
    )


@router.websocket('/games/{game_id}/')
async def play_game(
    websocket: WebSocket,
    game_id: int,
) -> None:
    user: int | None = None
    logger = GameLoggingAdapter(logger=_logger)
    logger.extra = {'game': game_id}

    game_service: game_pb2_grpc.GameServiceAsyncStub = (  # pyright: ignore
        game_pb2_grpc.GameServiceStub(websocket.app.state.game_channel)
    )
    game = await _fetch_game(game_service=game_service, game_id=game_id)
    if not game:
        await websocket.close()
        return

    cache: redis.Redis = websocket.app.state.cache
    channel: PubSub = cache.pubsub()  # pyright: ignore

    try:
        user = await handle_authentication(websocket=websocket, logger=logger)
        if not user:
            return

        logger.extra['user'] = user
        logger.debug('user verified')
        await channel.subscribe(f'game:{game_id}:{user}')  # pyright: ignore

        is_first_player_connects = game.player1 == user and game.player2 == 0
        is_second_player_joins = game.player1 != user and game.player2 == 0
        is_player_reconnected = user in [game.player1, game.player2]

        if not any(
            [
                is_first_player_connects,
                is_second_player_joins,
                is_player_reconnected,
            ]
        ):
            logger.debug('player does not belong to a game')
            await websocket.close()
            return

        await websocket.send_text(
            data=AuthenticatedMessage(
                body=AuthenticatedMessageBody(
                    success=True,
                    message='Successfully authenticated',
                ),
            ).model_dump_json(),
        )

        if is_first_player_connects:
            logger.debug('first player connected, waiting for second player')

        elif is_second_player_joins:
            logger.debug('second player joins game')
            game = await _handle_second_player_join(
                game_service=game_service,
                game=game,
                user=user,
                websocket=websocket,
                cache=cache,
                logger=logger,
            )

        elif is_player_reconnected:
            logger.debug('second player is reconnected, can safely play a game')
            await _handle_player_reconnected(
                game_service=game_service,
                game=game,
                user=user,
                logger=logger,
                websocket=websocket,
                cache=cache,
            )

        await asyncio.gather(
            _game_loop(
                logger=logger,
                user=user,
                websocket=websocket,
                game_id=game_id,
                game_service=game_service,
                cache=cache,
            ),
            _wait_for_messages(
                logger=logger,
                websocket=websocket,
                channel=channel,
            ),
        )
    except WebSocketDisconnect:
        logger.debug('user disconnected')
    except Exception:
        logger.exception('Unexpected exception')
    finally:
        if user:
            opponent = get_opponent(game=game, user=user)
            await cache.publish(  # pyright: ignore
                f'game:{game_id}:{opponent}',
                DisconnectedMessage(
                    body=DisconnectedMessageBody(
                        message='Opponent disconnected'
                    ),
                ).model_dump_json(),
            )
        await channel.unsubscribe()  # pyright: ignore
