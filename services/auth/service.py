import logging
from typing import Any, override

from google.protobuf.empty_pb2 import Empty
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import StatusCode
from grpc.aio import ServicerContext

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
from services.auth.exceptions import EmailAlreadyUsedError
from services.auth.interceptors import get_current_user
from services.auth.password import check_password
from services.auth.queries import (
    get_user_by_email,
    get_user_by_id,
    user_create,
    user_update,
)
from services.auth.token import issue_token

logger = logging.getLogger('duo.auth.grpc')


class UserService(auth_pb2_grpc.UserServiceServicer):
    @override
    async def CreateUser(
        self,
        request: CreateUserRequest,
        context: ServicerContext[Any, Any],
    ) -> AuthResponse:
        try:
            user = await user_create(
                email=request.email,
                password=request.password,
            )
        except EmailAlreadyUsedError:
            await context.abort(
                code=StatusCode.ALREADY_EXISTS, details='Email already used'
            )

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
        user = await get_user_by_email(email=request.email)
        if user is None:
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details='User not found',
            )

        if not check_password(request.password, user.hashed_password):
            await context.abort(
                code=StatusCode.INVALID_ARGUMENT,
                details='Invalid password',
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
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        new_email = request.new_email
        try:
            await user_update(user=user, email=new_email)
        except EmailAlreadyUsedError:
            await context.abort(
                code=StatusCode.ALREADY_EXISTS, details='Email already exists'
            )
        except Exception as exc:
            logger.exception('UpdateUserEmail: Unhandled exception: %s', exc)
            await context.abort(
                code=StatusCode.INTERNAL, details='Unhandled exception'
            )

        assert user.id is not None
        user_msg = User(
            id=user.id,
            email=user.email,
            created_at=Timestamp().FromDatetime(user.created_at),
            updated_at=Timestamp().FromDatetime(user.updated_at),
        )
        if user.password_updated_at is not None:
            user_msg.password_updated_at.CopyFrom(
                datetime_to_timestamp(user.password_updated_at)
            )
        return user_msg

    @override
    async def UpdateUserPassword(
        self,
        request: UpdateUserPasswordRequest,
        context: ServicerContext[Any, Any],
    ) -> AuthResponse:
        user = get_current_user()
        if user is None:
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        new_password = request.new_password
        try:
            await user_update(user=user, password=new_password)
        except Exception as exc:
            logger.exception('UpdateUserPassword: unhandled exception: %s', exc)
            await context.abort(
                code=StatusCode.INTERNAL, details='Unhandled exception'
            )

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
            await context.abort(
                code=StatusCode.UNAUTHENTICATED,
                details='Not authenticated',
            )

        assert user.id is not None
        user_msg = User(
            id=user.id,
            email=user.email,
            created_at=datetime_to_timestamp(user.created_at),
            updated_at=datetime_to_timestamp(user.updated_at),
        )
        if user.password_updated_at is not None:
            user_msg.password_updated_at.CopyFrom(
                datetime_to_timestamp(user.password_updated_at)
            )
        return user_msg

    @override
    async def GetUserById(
        self, request: GetUserByIdRequest, context: ServicerContext[Any, Any]
    ) -> User:
        user = await get_user_by_id(id=request.id)
        if user is None:
            await context.abort(
                code=StatusCode.NOT_FOUND,
                details='User not found',
            )

        assert user.id is not None
        user_msg = User(
            id=user.id,
            email=user.email,
            created_at=datetime_to_timestamp(user.created_at),
            updated_at=datetime_to_timestamp(user.updated_at),
        )
        if user.password_updated_at is not None:
            user_msg.password_updated_at.CopyFrom(
                datetime_to_timestamp(user.password_updated_at)
            )
        return user_msg
