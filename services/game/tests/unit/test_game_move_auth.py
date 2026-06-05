import asyncio
from datetime import datetime

import pytest

from types import SimpleNamespace

from grpc import StatusCode

from generated import game_pb2

from services.game.grpc.services.game_move import GameMoveService


class AbortCalled(Exception):
    def __init__(self, code):
        self.code = code


class DummyContext:
    async def abort(self, *, code, details: str | None = None):
        raise AbortCalled(code)


def make_move(id=1, game_id=10, player_id=100, turn_number=1):
    now = datetime.utcnow()
    return SimpleNamespace(
        id=id,
        game_id=game_id,
        player_id=player_id,
        turn_number=turn_number,
        move_data={'x': 1},
        created_at=now,
        updated_at=now,
    )


def make_game(id=10, player1=100, player2=200):
    now = datetime.utcnow()
    return SimpleNamespace(
        id=id,
        type=0,
        result=0,
        status=0,
        player1=player1,
        player2=player2,
        current_player=player1,
        turn_number=1,
        created_at=now,
        updated_at=now,
        state={},
    )


@pytest.mark.asyncio
async def test_get_move_by_id_allowed(monkeypatch):
    svc = GameMoveService()
    move = make_move()
    game = make_game()

    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_move_by_id',
        lambda id: asyncio.Future(),
    )

    # set the future result for get_game_move_by_id
    fut = asyncio.Future()
    fut.set_result(move)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_move_by_id',
        lambda id: fut,
    )

    # get_game_by_id
    fut_g = asyncio.Future()
    fut_g.set_result(game)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_by_id',
        lambda id: fut_g,
    )

    # current user is player1
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_current_user_id',
        lambda: game.player1,
    )

    resp = await svc.GetMoveById(
        game_pb2.GetMoveByIdRequest(move_id=move.id), DummyContext()
    )

    assert resp.id == move.id
    assert resp.game_id == move.game_id


@pytest.mark.asyncio
async def test_get_move_by_id_forbidden(monkeypatch):
    svc = GameMoveService()
    move = make_move()
    game = make_game()

    fut = asyncio.Future()
    fut.set_result(move)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_move_by_id',
        lambda id: fut,
    )

    fut_g = asyncio.Future()
    fut_g.set_result(game)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_by_id',
        lambda id: fut_g,
    )

    # current user is not a player
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_current_user_id',
        lambda: 9999,
    )

    with pytest.raises(AbortCalled) as excinfo:
        await svc.GetMoveById(
            game_pb2.GetMoveByIdRequest(move_id=move.id), DummyContext()
        )

    assert excinfo.value.code == StatusCode.PERMISSION_DENIED


@pytest.mark.asyncio
async def test_get_moves_for_game_allowed(monkeypatch):
    svc = GameMoveService()
    move = make_move()
    game = make_game()

    fut_g = asyncio.Future()
    fut_g.set_result(game)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_by_id',
        lambda id: fut_g,
    )

    fut_moves = asyncio.Future()
    fut_moves.set_result([move])
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_moves',
        lambda game_id: fut_moves,
    )

    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_current_user_id',
        lambda: game.player1,
    )

    resp = await svc.GetMovesForGame(
        game_pb2.GetMovesForGameRequest(game_id=game.id), DummyContext()
    )

    assert len(list(resp.moves)) == 1


@pytest.mark.asyncio
async def test_get_moves_for_game_forbidden(monkeypatch):
    svc = GameMoveService()
    game = make_game()

    fut_g = asyncio.Future()
    fut_g.set_result(game)
    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_game_by_id',
        lambda id: fut_g,
    )

    monkeypatch.setattr(
        'services.game.grpc.services.game_move.get_current_user_id',
        lambda: 9999,
    )

    with pytest.raises(AbortCalled) as excinfo:
        await svc.GetMovesForGame(
            game_pb2.GetMovesForGameRequest(game_id=game.id), DummyContext()
        )

    assert excinfo.value.code == StatusCode.PERMISSION_DENIED
