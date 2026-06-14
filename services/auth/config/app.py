import logging
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.secrets import load_private_key, load_public_key

logger = logging.getLogger('duo.auth.config')

BASE_PATH = Path(__file__).parent.parent


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / '.env',
        extra='ignore',
    )
    private_key_path: Path = Field(alias='duo_auth_private_key_path')
    public_key_path: Path = Field(alias='duo_auth_public_key_path')
    _private_key: Ed25519PrivateKey | None = None
    _public_key: Ed25519PublicKey | None = None

    jwt_lifetime: int = 60 * 60 * 24 * 30  # 30 days
    jwt_algorithm: str = 'EdDSA'

    db_host: str = Field(alias='postgres_host')
    db_port: str = Field(alias='postgres_port')
    db_name: str = Field(alias='postgres_db')
    db_user: str = Field(alias='postgres_user')
    db_pass: SecretStr = Field(alias='postgres_password')

    db_pool_size: int = Field(alias='duo_auth_db_pool_size', default=5)
    db_max_overflow: int = Field(alias='duo_auth_db_max_overflow', default=2)

    sentry_dsn: str = Field(alias='duo_auth_sentry_dsn', default='')

    server_url: str = Field(
        alias='duo_auth_server_url',
        default='localhost:50051',
    )

    service_name: str = 'duo.auth'
    otel_url: str = Field(alias='duo_auth_otel_url')
    otel_interval: int = Field(alias='duo_auth_otel_interval', default=30_000)

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
    def private_key(self) -> Ed25519PrivateKey:
        assert self._private_key is not None, (
            'Private key is not loaded properly'
        )
        return self._private_key

    @property
    def public_key(self) -> Ed25519PublicKey:
        assert self._public_key is not None, 'Public key is not loaded properly'
        return self._public_key

    def model_post_init(self, context: Any, /) -> None:
        self._public_key = load_public_key(BASE_PATH / self.public_key_path)
        self._private_key = load_private_key(BASE_PATH / self.private_key_path)
        logger.debug('Loaded encryption keys successfully')


settings = AuthSettings()  # pyright: ignore[reportCallIssue]
