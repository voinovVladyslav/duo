import json

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from google.protobuf import timestamp_pb2
from grpc import StatusCode, aio

from generated import game_pb2

from services.api.routers import games as games_router


class FakeStub:
    def __init__(self, resp=None, exc=None):
        self._resp = resp
        self._exc = exc

    async def GetMovesForGame(self, req, timeout=None, metadata=None):
        if self._exc:
            raise self._exc
        return self._resp

    async def GetMoveById(self, req, timeout=None, metadata=None):
        if self._exc:
            raise self._exc
        return self._resp


class FakeRpcError(aio.AioRpcError):
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code


@pytest.mark.asyncio
async def test_list_moves_allowed(monkeypatch):
    move = game_pb2.GameMove(
        id=1,
        game_id=10,
        player_id=100,
        turn_number=1,
        move_data=json.dumps({'x': 1}),
        created_at=timestamp_pb2.Timestamp(seconds=0),
        updated_at=timestamp_pb2.Timestamp(seconds=0),
    )
    resp = game_pb2.ListMoveResponse(moves=[move])

    stub = FakeStub(resp=resp)

    # ensure token validation passes
    monkeypatch.setattr(
        'services.api.routers.games.get_user_from_token', lambda t: 100
    )

    result = await games_router.list_moves(
        SimpleNamespace(credentials='token'), stub, 10
    )

    assert len(result) == 1
    assert result[0].id == 1


@pytest.mark.asyncio
async def test_list_moves_forbidden(monkeypatch):
    exc = FakeRpcError(StatusCode.PERMISSION_DENIED)
    stub = FakeStub(exc=exc)

    monkeypatch.setattr(
        'services.api.routers.games.get_user_from_token', lambda t: 9999
    )

    with pytest.raises(HTTPException) as excinfo:
        await games_router.list_moves(
            SimpleNamespace(credentials='token'), stub, 10
        )

    assert excinfo.value.status_code == 403
