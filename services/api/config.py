from pathlib import Path

from pydantic import Field, IPvAnyAddress, PostgresDsn, SecretStr, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).parent


class BaseDuoSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_PATH / '.env',
        extra='ignore',
    )


class DatabaseSettings(BaseDuoSettings):
    name: str = Field(alias='postgres_db')
    host: IPvAnyAddress = Field(alias='postgres_host')
    port: int = Field(alias='postgres_port')
    user: str = Field(alias='postgres_user')
    password: SecretStr = Field(alias='postgres_password')

    @property
    def dsn(self) -> PostgresDsn:
        dsn_str = (
            f'postgresql+psycopg2://'
            f'{self.user}:{self.password.get_secret_value()}@'
            f'{self.host}:{self.port}/{self.name}'
        )
        return TypeAdapter(PostgresDsn).validate_strings(dsn_str)


class Settings(BaseDuoSettings):
    debug: bool = Field(alias='duo_debug')
    secret_key: SecretStr = Field(alias='duo_secret_key')

    db: DatabaseSettings = DatabaseSettings()  # type: ignore


settings = Settings()  # type: ignore
