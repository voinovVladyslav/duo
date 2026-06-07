import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.grpc import GRPCIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


def init_sentry(dsn: str) -> None:
    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=True,
        auto_enabling_integrations=False,
        traces_sample_rate=0,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        release=os.getenv('SENTRY_RELEASE'),
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(),
            RedisIntegration(),
            StarletteIntegration(),
            GRPCIntegration(),
        ],
    )
