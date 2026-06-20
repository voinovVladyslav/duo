import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from google.protobuf.empty_pb2 import Empty
from grpc import StatusCode, aio

from common.masks import mask_email
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

logger = logging.getLogger('duo.api.users')


@router.get('/me/')
async def user_me(
    credentials: Credentials,
    stub: UserServiceDep,
) -> UserDisplay:
    user = get_user_from_token(credentials.credentials)
    if user is None:
        logger.info('rejected invalid token on /me')
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
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            logger.info('unauthenticated on /me', extra={'user_id': user})
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
            )

        logger.exception('failed to fetch /me', extra={'user_id': user})
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
        logger.info('rejected invalid token on user detail')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    extra = {'user_id': user, 'target_id': user_id}
    try:
        resp = await stub.GetUserById(
            auth_pb2.GetUserByIdRequest(id=user_id),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        return UserDisplay(
            id=resp.id,
            email=resp.email,
            created_at=resp.created_at.ToDatetime(),
            updated_at=resp.updated_at.ToDatetime(),
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            logger.info('unauthenticated on user detail', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Not Authorized'
            )
        if exc.code() == StatusCode.NOT_FOUND:
            logger.info('user detail not found', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Not Found'
            )
        logger.exception('failed to fetch user detail', extra=extra)
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
        logger.info('rejected invalid token on email update')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    extra = {'user_id': user, 'new_email': mask_email(data.email)}
    try:
        resp = await stub.UpdateUserEmail(
            auth_pb2.UpdateUserEmailRequest(new_email=data.email),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        logger.info('user email updated', extra=extra)
        return UserDisplay(
            id=resp.id,
            email=resp.email,
            created_at=resp.created_at.ToDatetime(),
            updated_at=resp.updated_at.ToDatetime(),
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            logger.info('unauthenticated on email update', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Unauthenticated'
            )

        if exc.code() == StatusCode.ALREADY_EXISTS:
            logger.info('email update conflict', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='User with this email already exists',
            )
        logger.exception('failed to update email', extra=extra)
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
        logger.info('rejected invalid token on password update')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Not authenticated'
        )
    extra = {'user_id': user}
    try:
        resp = await stub.UpdateUserPassword(
            auth_pb2.UpdateUserPasswordRequest(
                new_password=data.password.get_secret_value()
            ),
            timeout=2,
            metadata=(('authorization', credentials.credentials),),
        )
        logger.info('user password updated', extra=extra)
        return JsonWebToken(
            access_token=resp.access_token,
            token_type='Bearer',
            issued_at=resp.issued_at.ToDatetime().timestamp(),
            expires_at=resp.expires_at.ToDatetime().timestamp(),
        )
    except aio.AioRpcError as exc:
        if exc.code() == StatusCode.UNAUTHENTICATED:
            logger.info('unauthenticated on password update', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail='Unauthenticated'
            )

        logger.exception('failed to update password', extra=extra)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Unknown error'
        )
