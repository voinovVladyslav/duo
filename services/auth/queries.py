from datetime import datetime
from typing import Any

from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from common.exceptions import InvalidTokenError
from common.models import model_update
from services.auth.db import get_session_ctx
from services.auth.exceptions import EmailAlreadyUsedError
from services.auth.models import User
from services.auth.password import hash_password
from services.auth.token import decode_token


async def get_user_by_id(
    session: AsyncSession | None = None,
    *,
    id: int,
) -> User | None:
    async with get_session_ctx(session=session) as s:
        result = await s.exec(select(User).where(User.id == id))
        user = result.first()
        return user


async def get_user_by_email(
    session: AsyncSession | None = None,
    *,
    email: EmailStr,
) -> User | None:
    async with get_session_ctx(session=session) as s:
        result = await s.exec(select(User).where(User.email == email))
        user = result.first()
        return user


async def get_user_from_token(
    session: AsyncSession | None = None, *, token: str
) -> User:
    """
    Get user from token or raise error

    `common.exceptions.InvalidTokenError`
    `common.exceptions.ExpiredTokenError`
    """
    decoded_token = decode_token(token=token)
    async with get_session_ctx(session) as s:
        user = await get_user_by_id(session=s, id=decoded_token.sub)
        if not user:
            raise InvalidTokenError(
                'User specified as sub value does not exists'
            )

        return user


async def user_create(
    session: AsyncSession | None = None,
    *,
    email: EmailStr,
    password: str,
) -> User:
    """
    raises `EmailAlreadyUsedError`
    """
    try:
        async with get_session_ctx(session=session) as s:
            hashed_password = hash_password(password)
            user = User(email=email, hashed_password=hashed_password)
            s.add(user)
            await s.commit()
            await s.refresh(user)
            return user
    except IntegrityError as exc:
        raise EmailAlreadyUsedError(
            f'Could not create user with email {email}. Already in use'
        ) from exc


async def user_update(
    *,
    user: User,
    session: AsyncSession | None = None,
    **fields: Any,
) -> User:
    """
    Updates `user`

    raises `EmailAlreadyUsedError`
    """
    password = fields.pop('password', '')
    if password:
        fields['hashed_password'] = hash_password(password)
        fields['password_updated_at'] = datetime.now()

    user, updates = model_update(model=user, **fields)
    if not updates:
        return user

    try:
        async with get_session_ctx(session=session) as s:
            s.add(user)
            await s.commit()
            await s.refresh(user)
            return user
    except IntegrityError as exc:
        raise EmailAlreadyUsedError(
            'User with this email already exists'
        ) from exc
