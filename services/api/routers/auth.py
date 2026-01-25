from fastapi import APIRouter

from api.schemas.auth import JsonWebToken, UserRegisterRequest

router = APIRouter()


@router.post('/register/')
async def user_register(data: UserRegisterRequest) -> JsonWebToken:
    return JsonWebToken(
        access_token='token' + data.email,
        token_type='Bearer',
        issued_at=123.1,
        expired_at=12.1,
    )

@router.post('/login/')
async def user_login(data: UserRegisterRequest) -> JsonWebToken:
    return JsonWebToken(
        access_token='token' + data.email,
        token_type='Bearer',
        issued_at=123.1,
        expired_at=12.1,
    )
