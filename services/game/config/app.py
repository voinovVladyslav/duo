import logging
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.secrets import load_public_key

logger = logging.getLogger('duo.game.config')

BASE_PATH = Path(__file__).parent.parent


class GameSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / '.env',
        extra='ignore',
    )
    jwt_algorithm: str = 'EdDSA'
    server_url: str = Field(
        alias='duo_game_server_url',
        default='localhost:50052',
    )

    db_host: str = Field(alias='postgres_host')
    db_port: str = Field(alias='postgres_port')
    db_name: str = Field(alias='postgres_db')
    db_user: str = Field(alias='postgres_user')
    db_pass: SecretStr = Field(alias='postgres_password')
    db_pool_size: int = Field(alias='duo_game_db_pool_size', default=5)
    db_max_overflow: int = Field(alias='duo_game_db_max_overflow', default=2)

    public_key_path: Path = Field(alias='duo_game_public_key_path')
    _public_key: Ed25519PublicKey | None = None

    sentry_dsn: str = Field(alias='duo_game_sentry_dsn', default='')

    @property
    def db_dsn(self) -> PostgresDsn:
        dsn = PostgresDsn.build(
            scheme='postgresql+asyncpg',
            username=self.db_user,
            password=self.db_pass.get_secret_value(),
            host=self.db_host,
            port=int(self.db_port),
            path=self.db_name,
        )
        return dsn

    @property
    def public_key(self) -> Ed25519PublicKey:
        assert self._public_key is not None, 'Public key is not loaded properly'
        return self._public_key

    def model_post_init(self, context: Any, /) -> None:
        self._public_key = load_public_key(BASE_PATH / self.public_key_path)
        logger.debug('Loaded encryption keys successfully')


settings = GameSettings()  # pyright: ignore[reportCallIssue]
