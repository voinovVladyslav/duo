import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Request
from grpc import StatusCode, aio

from common.masks import mask_email
from generated import auth_pb2
from services.api.dependencies import UserServiceDep
from services.api.schemas.auth import (
    JsonWebToken,
    UserLoginRequest,
    UserRegisterRequest,
)

router = APIRouter(tags=['auth'])

logger = logging.getLogger('duo.api.auth')


@router.post('/register/')
async def user_register(
    data: UserRegisterRequest,
    stub: UserServiceDep,
    request: Request,
) -> JsonWebToken:
    extra = {
        'client': request.client.host if request.client else 'unknown',
        'email': mask_email(data.email),
    }
    try:
        resp = await stub.CreateUser(
            auth_pb2.CreateUserRequest(
                email=data.email,
                password=data.password.get_secret_value(),
            ),
            timeout=2,
        )
        logger.info('user registered', extra=extra)
        return JsonWebToken(
            access_token=resp.access_token,
            token_type='Bearer',
            issued_at=resp.issued_at.ToDatetime().timestamp(),
            expires_at=resp.expires_at.ToDatetime().timestamp(),
        )
    except aio.AioRpcError as exc:
        extra = {**extra, 'reason': exc.code().name}
        if exc.code() == StatusCode.ALREADY_EXISTS:
            logger.info('failed to register user. already exists', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='User already exists',
            )
        logger.exception('internal server error', extra=extra)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to register. Try again later',
        )


@router.post('/login/')
async def user_login(
    data: UserLoginRequest, stub: UserServiceDep, request: Request
) -> JsonWebToken:
    extra = {
        'client': request.client.host if request.client else 'unknown',
        'email': mask_email(data.email),
    }
    try:
        resp = await stub.LoginUser(
            auth_pb2.LoginUserRequest(
                email=data.email,
                password=data.password.get_secret_value(),
            ),
            timeout=2,
        )
        logger.info('user logged in', extra=extra)
        return JsonWebToken(
            access_token=resp.access_token,
            token_type='Bearer',
            issued_at=resp.issued_at.ToDatetime().timestamp(),
            expires_at=resp.expires_at.ToDatetime().timestamp(),
        )
    except aio.AioRpcError as exc:
        extra = {**extra, 'reason': exc.code().name}
        if exc.code() in [
            StatusCode.UNAUTHENTICATED,
            StatusCode.INVALID_ARGUMENT,
            StatusCode.NOT_FOUND,
        ]:
            logger.info('failed login attempt', extra=extra)
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Invalid email or password',
            )

        logger.exception('internal server error', extra=extra)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Internal error',
        )
