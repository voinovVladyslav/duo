import logging
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.secrets import load_public_key

logger = logging.getLogger('duo.api.config')

BASE_PATH = Path(__file__).parent


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / '.env',
        extra='ignore',
    )

    debug: bool = Field(alias='duo_api_debug')
    allowed_origins: list[str] = Field(alias='duo_allowed_origins')
    auth_service_url: str = Field(alias='duo_auth_service_url')
    game_service_url: str = Field(alias='duo_game_service_url')

    jwt_algorithm: str = 'EdDSA'
    public_key_path: Path = Field(alias='duo_api_public_key_path')
    _public_key: Ed25519PublicKey | None = None
    redis_dsn: RedisDsn = Field(alias='duo_api_redis_dsn')

    @property
    def public_key(self) -> Ed25519PublicKey:
        assert self._public_key is not None, 'Public key is not loaded properly'
        return self._public_key

    def model_post_init(self, context: Any, /) -> None:
        self._public_key = load_public_key(BASE_PATH / self.public_key_path)
        logger.debug('Loaded encryption keys successfully')


settings = ApiSettings()  # pyright: ignore[reportCallIssue]
