import json
import logging
from typing import Any, override

from grpc import StatusCode
from grpc.aio import ServicerContext

from common.proto import datetime_to_timestamp
from common.types.game import (
    RESULT_TO_PROTO_MAP,
    STATUS_TO_PROTO_MAP,
    TYPE_FROM_PROTO_MAP,
    TYPE_TO_PROTO_MAP,
    Result,
    Status,
)
from generated import game_pb2, game_pb2_grpc
from services.game.db.crud import (
    game_create,
    game_move_create,
    game_update,
    get_game_by_id,
)
from services.game.db.models import Game
from services.game.engines.factory import get_game_engine_class
from services.game.grpc.interceptors import get_current_user_id

logger = logging.getLogger('duo.game.grpc')


def game_to_proto(game: Game) -> game_pb2.Game:
    assert game.id is not None
    return game_pb2.Game(
        id=game.id,
        type=TYPE_TO_PROTO_MAP[game.type],
        result=RESULT_TO_PROTO_MAP[game.result],
        status=STATUS_TO_PROTO_MAP[game.status],
        player1=game.player1,
        player2=game.player2,
        current_player=game.current_player,
        turn_number=game.turn_number,
        created_at=datetime_to_timestamp(game.created_at),
        updated_at=datetime_to_timestamp(game.updated_at),
    )


class GameService(game_pb2_grpc.GameServiceServicer):
    @override
    async def CreateGame(
        self,
        request: game_pb2.CreateGameRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.Game:
        user_id = get_current_user_id()
        if user_id is None:
            logger.warning('unauthenticated game create')
            await context.abort(code=StatusCode.UNAUTHENTICATED)

        game = await game_create(
            type=TYPE_FROM_PROTO_MAP[request.type],
            player1=user_id,
            current_player=user_id,
            turn_number=1,
        )
        logger.info(
            'game created',
            extra={
                'game_id': game.id,
                'type': game.type,
                'player1': user_id,
            },
        )
        return game_to_proto(game)

    @override
    async def JoinGame(
        self,
        request: game_pb2.JoinGameRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.JoinGameResponse:
        game = await get_game_by_id(id=request.game_id)
        if game is None:
            logger.info(
                'join failed, game not found',
                extra={
                    'game_id': request.game_id,
                },
            )
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details=f'Not found game with id {request.game_id}',
            )

        if game.status != Status.IN_QUEUE:
            logger.info(
                'join rejected, game not in queue',
                extra={
                    'game_id': game.id,
                    'status': game.status,
                },
            )
            await context.abort(code=StatusCode.FAILED_PRECONDITION)

        engine = get_game_engine_class(game.type).new_game(
            p1=game.player1, p2=request.player_id
        )
        game = await game_update(
            game=game,
            player2=request.player_id,
            status=Status.IN_PROGRESS,
            state=engine.state.model_dump(),
        )

        logger.info(
            'player joined game',
            extra={
                'game_id': game.id,
                'player_id': request.player_id,
            },
        )
        assert game.player2 is not None
        return game_pb2.JoinGameResponse(
            game=game_to_proto(game),
            player1_view=engine.get_player_view(game.player1).model_dump_json(),
            player2_view=engine.get_player_view(game.player2).model_dump_json(),
        )

    @override
    async def MakeGameAbandoned(
        self,
        request: game_pb2.MakeGameAbandonedRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.Game:
        game = await get_game_by_id(id=request.game_id)
        if game is None:
            logger.info(
                'abandon failed, game not found',
                extra={
                    'game_id': request.game_id,
                },
            )
            await context.abort(code=StatusCode.NOT_FOUND)

        game = await game_update(game=game, status=Status.ABANDONED)
        logger.info('game abandoned', extra={'game_id': game.id})
        return game_to_proto(game=game)

    @override
    async def GetGameById(
        self,
        request: game_pb2.GetGameByIdRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.Game:
        game = await get_game_by_id(id=request.game_id)
        if game is None:
            logger.info('game not found', extra={'game_id': request.game_id})
            await context.abort(code=StatusCode.NOT_FOUND)
        return game_to_proto(game=game)

    @override
    async def MakeMove(
        self,
        request: game_pb2.MakeMoveRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.MakeMoveResponse:
        game = await get_game_by_id(id=request.game_id)
        if game is None:
            logger.info(
                'move failed, game not found',
                extra={
                    'game_id': request.game_id,
                    'player_id': request.player_id,
                },
            )
            await context.abort(code=StatusCode.NOT_FOUND)

        if game.status != Status.IN_PROGRESS:
            logger.info(
                'move rejected, game not in progress',
                extra={
                    'game_id': game.id,
                    'player_id': request.player_id,
                    'status': game.status,
                },
            )
            await context.abort(code=StatusCode.FAILED_PRECONDITION)

        if request.player_id != game.current_player:
            logger.info(
                'move rejected, not players turn',
                extra={
                    'game_id': game.id,
                    'player_id': request.player_id,
                },
            )
            await context.abort(code=StatusCode.INVALID_ARGUMENT)

        engine_class = get_game_engine_class(game.type)

        move = engine_class.load_move(request.move_data)
        engine = engine_class.load_game(game.state)

        if not engine.is_move_possible(move):
            logger.info(
                'move rejected, illegal move',
                extra={
                    'game_id': game.id,
                    'player_id': request.player_id,
                    'move': request.move_data,
                },
            )
            await context.abort(code=StatusCode.INVALID_ARGUMENT)

        engine.make_move(move=move)
        winner = engine.get_winner()
        is_draw = engine.is_draw()
        status = game.status
        result = game.result
        current_player: int | None = engine.get_current_player()

        if is_draw:
            result = Result.DRAW
            status = Status.FINISHED
            current_player = None

        if winner:
            current_player = None
            status = Status.FINISHED
            if winner == game.player1:
                result = Result.P1_WON
            else:
                result = Result.P2_WON

        current_turn = game.turn_number
        game = await game_update(
            game=game,
            state=engine.state.model_dump(),
            current_player=current_player,
            status=status,
            result=result,
            turn_number=game.turn_number + 1,
        )
        await game_move_create(
            game_id=request.game_id,
            player_id=request.player_id,
            turn_number=current_turn,
            move_data=json.loads(request.move_data),
        )

        logger.info(
            'move made',
            extra={
                'game_id': game.id,
                'player_id': request.player_id,
                'turn': current_turn,
            },
        )
        if status == Status.FINISHED:
            logger.info(
                'game finished',
                extra={
                    'game_id': game.id,
                    'result': result,
                    'winner': winner or None,
                },
            )

        assert game.player2 is not None
        return game_pb2.MakeMoveResponse(
            game=game_to_proto(game),
            player1_view=engine.get_player_view(game.player1).model_dump_json(),
            player2_view=engine.get_player_view(game.player2).model_dump_json(),
        )

    @override
    async def GetPlayerView(
        self,
        request: game_pb2.GetPlayerViewRequest,
        context: ServicerContext[Any, Any],
    ) -> game_pb2.GamePlayerView:
        game = await get_game_by_id(id=request.game_id)
        if game is None:
            logger.info(
                'player view, game not found',
                extra={
                    'game_id': request.game_id,
                },
            )
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details=f'Not found game with id {request.game_id}',
            )

        if request.player_id not in [game.player1, game.player2]:
            logger.info(
                'player view rejected, player not in game',
                extra={
                    'game_id': game.id,
                    'player_id': request.player_id,
                },
            )
            await context.abort(
                code=StatusCode.INVALID_ARGUMENT,
                details=f'player {request.player_id} not in the game {game.id}',
            )

        engine = get_game_engine_class(game.type).load_game(game.state)
        return game_pb2.GamePlayerView(
            game_state=engine.get_player_view(
                request.player_id
            ).model_dump_json()
        )
