import json
from datetime import datetime
from http import HTTPStatus
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from grpc import StatusCode

from common.proto import datetime_to_timestamp
from generated import game_pb2
from services.api.routers import game_moves as game_moves_router
from services.api.routers.game_moves import (
    _require_authenticated_user,
    _rpc_error_to_http_exception,
)


def make_game_move_proto(id=1, game_id=10, player_id=100, turn_number=1):
    now = datetime.utcnow()
    return game_pb2.GameMove(
        id=id,
        game_id=game_id,
        player_id=player_id,
        turn_number=turn_number,
        move_data=json.dumps({'x': 1}),
        created_at=datetime_to_timestamp(now),
        updated_at=datetime_to_timestamp(now),
    )


def test_require_authenticated_user(monkeypatch):
    bearer_token = 100
    monkeypatch.setattr(
        'services.api.routers.game_moves.get_user_from_token',
        lambda t: bearer_token,
    )

    assert _require_authenticated_user('Bearer tok') == bearer_token


def test_require_authenticated_user_rejects(monkeypatch):
    monkeypatch.setattr(
        'services.api.routers.game_moves.get_user_from_token', lambda t: None
    )

    with pytest.raises(HTTPException) as excinfo:
        _require_authenticated_user('Bearer tok')

    assert excinfo.value.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize(
    ('code', 'status_code', 'detail'),
    [
        (
            StatusCode.UNAUTHENTICATED,
            HTTPStatus.UNAUTHORIZED,
            'Not authenticated',
        ),
        (StatusCode.PERMISSION_DENIED, HTTPStatus.FORBIDDEN, 'Forbidden'),
        (StatusCode.NOT_FOUND, HTTPStatus.NOT_FOUND, 'Not found'),
    ],
)
def test_rpc_error_to_http_exception(code, status_code, detail):
    class FakeRpcError:
        def code(self):
            return code

    exc = _rpc_error_to_http_exception(FakeRpcError())

    assert exc.status_code == status_code
    assert exc.detail == detail


@pytest.mark.asyncio
async def test_get_moves_for_game_allowed(monkeypatch):
    move = make_game_move_proto()

    class Stub:
        async def get_moves_for_game(
            self, request, timeout=None, metadata=None
        ):
            return game_pb2.ListMoveResponse(moves=[move])

    monkeypatch.setattr(
        'services.api.routers.game_moves.get_user_from_token', lambda t: 100
    )

    response = await game_moves_router.list_game_moves(
        SimpleNamespace(credentials='Bearer tok'),
        Stub(),
        move.game_id,
    )

    assert isinstance(response, list)
    assert response[0].id == move.id
