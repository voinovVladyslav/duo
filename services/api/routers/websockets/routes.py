import asyncio
import json
import logging
from contextlib import suppress
from dataclasses import dataclass
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


@dataclass
class _GameContext:
    websocket: WebSocket
    cache: redis.Redis
    game_service: game_pb2_grpc.GameServiceAsyncStub
    logger: GameLoggingAdapter


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


async def _game_loop(
    *,
    ctx: _GameContext,
    user: int,
    game_id: int,
) -> bool:
    while True:
        ctx.logger.debug('waiting for message from user')
        message = GameMessageAdapter.validate_python(
            await ctx.websocket.receive_json()
        )
        ctx.logger.debug('message received: %s', message)
        if message.type != MessageType.GAME_MOVE:
            await ctx.websocket.send_text(
                InvalidMoveMessage(
                    body=InvalidMoveMessageBody(message='invalid move')
                ).model_dump_json()
            )
            continue
        try:
            move_response = await ctx.game_service.MakeMove(
                game_pb2.MakeMoveRequest(
                    game_id=game_id,
                    player_id=user,
                    move_data=json.dumps(message.body.game_move),
                )
            )
        except Exception:
            await ctx.websocket.send_text(
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

        await ctx.websocket.send_text(
            GameStateMessage(
                body=GameStateMessageBody(game_state=json.loads(ws_payload))
            ).model_dump_json()
        )
        opponent = get_opponent(game, user)
        if opponent:
            await ctx.cache.publish(  # pyright: ignore
                f'game:{game_id}:{opponent}',
                GameStateMessage(
                    body=GameStateMessageBody(
                        game_state=json.loads(cache_payload)
                    )
                ).model_dump_json(),
            )

        if game.status == game_pb2.FINISHED:
            ctx.logger.debug('game finished, closing websocket loop')
            return True


async def _wait_for_messages(
    *,
    ctx: _GameContext,
    channel: PubSub,
) -> None:
    ctx.logger.debug('waiting for message for user')
    async for message in channel.listen():  # pyright: ignore
        if message['type'] == 'message':
            message = cast(dict[str, Any], message)
            ctx.logger.debug('received message for user: %s', message)
            await ctx.websocket.send_text(message['data'].decode())


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


async def _handle_second_player_join(
    *,
    ctx: _GameContext,
    game: game_pb2.Game,
    user: int,
) -> game_pb2.Game:
    response = await ctx.game_service.JoinGame(
        game_pb2.JoinGameRequest(game_id=game.id, player_id=user),
    )
    game = response.game
    ctx.logger.debug('accepted game as user %s', user)
    ctx.logger.debug('sending to ws for user: %s', game.player2)
    await ctx.websocket.send_text(
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(response.player2_view)
            )
        ).model_dump_json()
    )
    ctx.logger.debug('publishing to redis for user: %s', game.player1)
    await ctx.cache.publish(  # pyright: ignore
        f'game:{game.id}:{game.player1}',
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(response.player1_view)
            )
        ).model_dump_json(),
    )
    return game


async def _handle_player_reconnected(
    *,
    ctx: _GameContext,
    game: game_pb2.Game,
    user: int,
) -> None:
    player_view = await ctx.game_service.GetPlayerView(
        game_pb2.GetPlayerViewRequest(game_id=game.id, player_id=user)
    )
    await ctx.websocket.send_text(
        GameStateMessage(
            body=GameStateMessageBody(
                game_state=json.loads(player_view.game_state)
            )
        ).model_dump_json()
    )
    ctx.logger.debug('user reconnected')
    opponent = get_opponent(game=game, user=user)
    if opponent:
        await ctx.cache.publish(  # pyright: ignore
            f'game:{game.id}:{opponent}',
            ConnectedMessage(
                body=ConnectedMessageBody(message=f'Opponent {user} connected'),
            ).model_dump_json(),
        )


def _determine_player_state(game: game_pb2.Game, user: int) -> str:
    """Return a short tag describing player's relationship to the game.

    Possible return values:
    - 'first_connects'
    - 'second_joins'
    - 'reconnected'
    - 'invalid'
    """
    is_first_player_connects = game.player1 == user and game.player2 == 0
    is_second_player_joins = game.player1 != user and game.player2 == 0
    is_player_reconnected = user in [game.player1, game.player2]

    if is_first_player_connects:
        return 'first_connects'
    if is_second_player_joins:
        return 'second_joins'
    if is_player_reconnected:
        return 'reconnected'
    return 'invalid'


async def _start_game_tasks(
    *, ctx: _GameContext, user: int, game_id: int, channel: PubSub
) -> bool:
    """Start game loop and message listener, await first completed.

    Returns True if game finished, otherwise False.
    """
    game_task = asyncio.create_task(
        _game_loop(
            ctx=ctx,
            user=user,
            game_id=game_id,
        )
    )
    messages_task = asyncio.create_task(
        _wait_for_messages(
            ctx=ctx,
            channel=channel,
        )
    )
    done, pending = await asyncio.wait(
        {game_task, messages_task}, return_when=asyncio.FIRST_COMPLETED
    )
    game_finished = False
    if game_task in done:
        game_finished = game_task.result()
    else:
        messages_task.result()

    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    return game_finished


@router.websocket('/games/{game_id}/')
async def play_game(
    websocket: WebSocket,
    game_id: int,
) -> None:
    user: int | None = None
    game_finished = False
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
    ctx = _GameContext(
        websocket=websocket,
        cache=cache,
        game_service=game_service,
        logger=logger,
    )

    try:
        user = await handle_authentication(websocket=websocket, logger=logger)
        if not user:
            return

        logger.extra['user'] = user
        logger.debug('user verified')
        await channel.subscribe(f'game:{game_id}:{user}')  # pyright: ignore

        player_state = _determine_player_state(game=game, user=user)
        if player_state == 'invalid':
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

        if player_state == 'first_connects':
            logger.debug('first player connected, waiting for second player')

        elif player_state == 'second_joins':
            logger.debug('second player joins game')
            game = await _handle_second_player_join(
                ctx=ctx, game=game, user=user
            )

        elif player_state == 'reconnected':
            logger.debug('player reconnected, restoring view')
            await _handle_player_reconnected(ctx=ctx, game=game, user=user)

        game_finished = await _start_game_tasks(
            ctx=ctx, user=user, game_id=game_id, channel=channel
        )
        with suppress(Exception):
            await websocket.close()
    except WebSocketDisconnect:
        logger.debug('user disconnected')
    except Exception:
        logger.exception('Unexpected exception')
    finally:
        if (
            not game_finished
            and user
            and (opponent := get_opponent(game=game, user=user))
        ):
            await cache.publish(  # pyright: ignore
                f'game:{game_id}:{opponent}',
                DisconnectedMessage(
                    body=DisconnectedMessageBody(
                        message='Opponent disconnected'
                    ),
                ).model_dump_json(),
            )
        await channel.unsubscribe()  # pyright: ignore
