from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from grpc import aio

from services.api.config import settings
from services.api.middleware.otel import OTELMiddleware
from services.api.routers.auth import router as auth_router
from services.api.routers.games import router as games_router
from services.api.routers.users import router as users_router
from services.api.routers.websockets import router as ws_router

if settings.sentry_dsn:
    import os

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.grpc import GRPCIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.auth_channel = aio.insecure_channel(
        str(settings.auth_service_url)
    )
    app.state.game_channel = aio.insecure_channel(
        str(settings.game_service_url)
    )
    app.state.cache = await redis.from_url(str(settings.redis_dsn))

    yield

    await app.state.auth_channel.close()
    await app.state.game_channel.close()
    await app.state.cache.aclose()


app = FastAPI(
    title='Duo API',
    version='v0.0.1',
    root_path='/api/v1',
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods='*',
    allow_headers='*',
)
app.add_middleware(OTELMiddleware)

app.include_router(auth_router, prefix='/auth')
app.include_router(users_router, prefix='/users')
app.include_router(games_router, prefix='/games')
app.include_router(ws_router, prefix='/ws')


@app.get('/', tags=['status'])
async def main() -> dict[str, Any]:
    return {'status': 'ok'}
