import asyncio
import logging
import signal

from grpc import aio
from opentelemetry.instrumentation.grpc import (  # pyright: ignore[reportMissingTypeStubs]
    GrpcAioInstrumentorServer,
)
from opentelemetry.instrumentation.logging import (  # pyright: ignore[reportMissingTypeStubs]
    LoggingInstrumentor,
)

from common.otel import setup_logs, setup_tracing
from generated import game_pb2_grpc
from services.game.config import settings
from services.game.config.sentry import init_sentry
from services.game.grpc.interceptors import AuthInterceptor, OTELInterceptor
from services.game.grpc.services.game import GameService
from services.game.grpc.services.game_move import GameMoveService

logger = logging.getLogger('duo.game')

if settings.sentry_dsn:
    init_sentry(dsn=settings.sentry_dsn)


async def serve() -> None:
    setup_logs(settings.service_name, settings.otel_url, settings.otel_interval)
    setup_tracing(settings.service_name, settings.otel_url)
    GrpcAioInstrumentorServer().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)
    interceptors = (
        OTELInterceptor(),
        AuthInterceptor(),
    )
    server = aio.server(interceptors=interceptors)
    game_pb2_grpc.add_GameServiceServicer_to_server(GameService(), server)
    game_pb2_grpc.add_GameMoveServiceServicer_to_server(
        GameMoveService(), server
    )

    port = server.add_insecure_port(settings.server_url)
    await server.start()
    logger.info('running server on port: %s', port)

    stop_event = asyncio.Event()

    def handle_signal():
        logger.info('Shutdown signal received')
        stop_event.set()

    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGTERM, handle_signal)
        loop.add_signal_handler(signal.SIGINT, handle_signal)
    except NotImplementedError:
        # windows does not have this function
        pass

    await stop_event.wait()

    logger.info('Shutting down gracefully')
    await server.stop(grace=5)
    logger.info('Shutdown complete')


if __name__ == '__main__':
    asyncio.run(serve())
