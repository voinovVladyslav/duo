from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from google.protobuf.empty_pb2 import Empty
from grpc import StatusCode, aio

from generated import auth_pb2
from services.api.dependencies import UserServiceDep
from services.api.schemas.auth import (
    JsonWebToken,
    UserDisplay,
    UserUpdateEmailRequest,
    UserUpdatePasswordRequest,
)
from services.api.security import Credentials
from services.api.token import get_user_from_token

router = APIRouter(tags=['users'])


@router.get('/me/')
async def user_me(
    credentials: Credentials,
    stub: UserServiceDep,
) -> UserDisplay:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )

    try:
        resp = await stub.GetCurrentUser(
            Empty(),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        return UserDisplay(
            id=resp.id,
            email=resp.email,
            created_at=resp.created_at.ToDatetime(),
            updated_at=resp.updated_at.ToDatetime(),
            password_updated_at=resp.password_updated_at.ToDatetime()
            if resp.HasField('password_updated_at')
            else None,
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
            )

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Bad request'
        )


@router.get('/{user_id}/')
async def user_detail(
    user_id: int,
    credentials: Credentials,
    stub: UserServiceDep,
) -> UserDisplay:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    try:
        resp = await stub.GetUserById(
            auth_pb2.GetUserByIdRequest(
                id=user_id,
            ),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        return UserDisplay(
            id=resp.id,
            email=resp.email,
            created_at=resp.created_at.ToDatetime(),
            updated_at=resp.updated_at.ToDatetime(),
            password_updated_at=resp.password_updated_at.ToDatetime()
            if resp.HasField('password_updated_at')
            else None,
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not Authorized'
            )
        if exc.code() == StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Not Found'
            )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Unexpected error',
        )


@router.post('/update/email/')
async def user_update_email(
    credentials: Credentials,
    data: UserUpdateEmailRequest,
    stub: UserServiceDep,
) -> UserDisplay:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    try:
        resp = await stub.UpdateUserEmail(
            auth_pb2.UpdateUserEmailRequest(new_email=data.email),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        return UserDisplay(
            id=resp.id,
            email=resp.email,
            created_at=resp.created_at.ToDatetime(),
            updated_at=resp.updated_at.ToDatetime(),
            password_updated_at=resp.password_updated_at.ToDatetime()
            if resp.HasField('password_updated_at')
            else None,
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Unauthenticated'
            )

        if exc.code() == StatusCode.ALREADY_EXISTS:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='User with this email already exists',
            )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Unexpected error',
        )


@router.post('/update/password/')
async def user_update_password(
    credentials: Credentials,
    data: UserUpdatePasswordRequest,
    stub: UserServiceDep,
) -> JsonWebToken:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    try:
        resp = await stub.UpdateUserPassword(
            auth_pb2.UpdateUserPasswordRequest(
                new_password=data.password.get_secret_value()
            ),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        return JsonWebToken(
            access_token=resp.access_token,
            token_type='Bearer',
            issued_at=resp.issued_at.ToDatetime().timestamp(),
            expires_at=resp.expires_at.ToDatetime().timestamp(),
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Unauthenticated'
            )

        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Unknown error'
        )
