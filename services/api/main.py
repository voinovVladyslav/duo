import time
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from grpc import aio
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from services.api.config import settings
from services.api.routers.auth import router as auth_router
from services.api.routers.games import router as games_router
from services.api.routers.users import router as users_router
from services.api.routers.websockets import router as ws_router


def setup_metrics(service_name: str, endpoint: str) -> metrics.Meter:
    exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(
        exporter=exporter, export_interval_millis=15_000
    )
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return metrics.get_meter(service_name)


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
app.include_router(auth_router, prefix='/auth')
app.include_router(users_router, prefix='/users')
app.include_router(games_router, prefix='/games')
app.include_router(ws_router, prefix='/ws')


meter = setup_metrics('duo.api', 'localhost:4317')
http_requests = meter.create_counter(
    'http_requests_total', description='Total HTTP requests'
)
http_latency = meter.create_histogram(
    'http_request_duration_ms', description='HTTP request duration in ms'
)


@app.middleware('http')
async def otel_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()

    response = await call_next(request)
    duration = time.perf_counter() - start
    labels = {
        'method': request.method,
        'path': request.url.path,
        'status': response.status_code,
    }
    http_requests.add(1, labels)
    http_latency.record(duration, labels)
    return response


@app.get('/', tags=['status'])
def main() -> dict[str, Any]:
    return {'status': 'ok'}
