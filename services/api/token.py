from common.exceptions import ExpiredTokenError, InvalidTokenError
from common.token import TokenDetails
from common.token import decode_token as _decode_token
from services.api.config import settings


def decode_token(token: str) -> TokenDetails:
    return _decode_token(
        token=token,
        public_key=settings.public_key,
        algorithm=settings.jwt_algorithm,
    )


def get_user_from_token(token_raw: str) -> int | None:
    try:
        return decode_token(token_raw).sub
    except InvalidTokenError, ExpiredTokenError:
        return None
