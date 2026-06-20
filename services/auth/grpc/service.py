import logging
from typing import Any, override

from google.protobuf.empty_pb2 import Empty
from grpc import StatusCode
from grpc.aio import ServicerContext

from common.masks import mask_email
from common.proto import datetime_to_timestamp
from generated import auth_pb2_grpc
from generated.auth_pb2 import (
    AuthResponse,
    CreateUserRequest,
    GetUserByIdRequest,
    LoginUserRequest,
    UpdateUserEmailRequest,
    UpdateUserPasswordRequest,
    User,
)
from services.auth.db.crud import (
    get_user_by_email,
    get_user_by_id,
    user_create,
    user_update,
)
from services.auth.exceptions import EmailAlreadyUsedError
from services.auth.grpc.interceptors import get_current_user
from services.auth.password import check_password
from services.auth.token import issue_token

logger = logging.getLogger('duo.auth.grpc')


class UserService(auth_pb2_grpc.UserServiceServicer):
    @override
    async def CreateUser(
        self,
        request: CreateUserRequest,
        context: ServicerContext[Any, Any],
    ) -> AuthResponse:
        email = mask_email(request.email)
        try:
            user = await user_create(
                email=request.email,
                password=request.password,
            )
        except EmailAlreadyUsedError:
            logger.info(
                'registration rejected, email in use',
                extra={
                    'email': email,
                },
            )
            await context.abort(
                code=StatusCode.ALREADY_EXISTS, details='Email already used'
            )

        logger.info('user created', extra={'user_id': user.id, 'email': email})
        token = issue_token(user=user)
        return AuthResponse(
            access_token=token.access_token,
            expires_at=datetime_to_timestamp(token.expires_at),
            issued_at=datetime_to_timestamp(token.issued_at),
        )

    @override
    async def LoginUser(
        self, request: LoginUserRequest, context: ServicerContext[Any, Any]
    ) -> AuthResponse:
        email = mask_email(request.email)
        user = await get_user_by_email(email=request.email)
        if user is None:
            logger.info('login failed, user not found', extra={'email': email})
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details='User not found',
            )

        if not check_password(request.password, user.hashed_password):
            logger.info(
                'login failed, bad password',
                extra={
                    'user_id': user.id,
                    'email': email,
                },
            )
            await context.abort(
                code=StatusCode.INVALID_ARGUMENT,
                details='Invalid password',
            )

        logger.info(
            'user logged in',
            extra={
                'user_id': user.id,
                'email': email,
            },
        )
        token = issue_token(user=user)
        return AuthResponse(
            access_token=token.access_token,
            expires_at=datetime_to_timestamp(token.expires_at),
            issued_at=datetime_to_timestamp(token.issued_at),
        )

    @override
    async def UpdateUserEmail(
        self,
        request: UpdateUserEmailRequest,
        context: ServicerContext[Any, Any],
    ) -> User:
        user = get_current_user()
        if user is None:
            logger.warning('unauthenticated email update')
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        new_email = request.new_email
        try:
            await user_update(user=user, email=new_email)
        except EmailAlreadyUsedError:
            logger.info(
                'email update rejected, in use',
                extra={
                    'user_id': user.id,
                    'new_email': mask_email(new_email),
                },
            )
            await context.abort(
                code=StatusCode.ALREADY_EXISTS, details='Email already exists'
            )
        except Exception:
            logger.exception(
                'failed to update email',
                extra={
                    'user_id': user.id,
                },
            )
            await context.abort(
                code=StatusCode.INTERNAL, details='Unhandled exception'
            )

        logger.info(
            'user email updated',
            extra={
                'user_id': user.id,
                'new_email': mask_email(new_email),
            },
        )
        assert user.id is not None
        return User(
            id=user.id,
            email=user.email,
            created_at=datetime_to_timestamp(user.created_at),
            updated_at=datetime_to_timestamp(user.updated_at),
            password_updated_at=datetime_to_timestamp(user.password_updated_at),
        )

    @override
    async def UpdateUserPassword(
        self,
        request: UpdateUserPasswordRequest,
        context: ServicerContext[Any, Any],
    ) -> AuthResponse:
        user = get_current_user()
        if user is None:
            logger.warning('unauthenticated password update')
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        new_password = request.new_password
        try:
            await user_update(user=user, password=new_password)
        except Exception:
            logger.exception(
                'failed to update password',
                extra={
                    'user_id': user.id,
                },
            )
            await context.abort(
                code=StatusCode.INTERNAL, details='Unhandled exception'
            )

        logger.info('user password updated', extra={'user_id': user.id})
        token = issue_token(user=user)
        return AuthResponse(
            access_token=token.access_token,
            expires_at=datetime_to_timestamp(token.expires_at),
            issued_at=datetime_to_timestamp(token.issued_at),
        )

    @override
    async def GetCurrentUser(
        self, request: Empty, context: ServicerContext[Any, Any]
    ) -> User:
        user = get_current_user()
        if user is None:
            logger.warning('unauthenticated GetCurrentUser')
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        assert user.id is not None
        return User(
            id=user.id,
            email=user.email,
            created_at=datetime_to_timestamp(user.created_at),
            updated_at=datetime_to_timestamp(user.updated_at),
            password_updated_at=datetime_to_timestamp(user.password_updated_at),
        )

    @override
    async def GetUserById(
        self, request: GetUserByIdRequest, context: ServicerContext[Any, Any]
    ) -> User:
        user = await get_user_by_id(id=request.id)
        if user is None:
            logger.info(
                'user lookup not found',
                extra={
                    'target_id': request.id,
                },
            )
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details='User not found',
            )

        assert user.id is not None
        return User(
            id=user.id,
            email=user.email,
            created_at=datetime_to_timestamp(user.created_at),
            updated_at=datetime_to_timestamp(user.updated_at),
            password_updated_at=datetime_to_timestamp(user.password_updated_at),
        )
