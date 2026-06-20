import asyncio
import logging
import signal

from grpc import aio

from common.metrics import setup_logs
from generated import auth_pb2_grpc
from services.auth.config import settings
from services.auth.config.sentry import init_sentry
from services.auth.grpc.interceptors import AuthInterceptor, OTELInterceptor
from services.auth.grpc.service import UserService

logger = logging.getLogger('duo.auth')

if settings.sentry_dsn:
    init_sentry(dsn=settings.sentry_dsn)


async def serve() -> None:
    setup_logs(settings.service_name, settings.otel_url, settings.otel_interval)
    interceptors = (
        OTELInterceptor(),
        AuthInterceptor(),
    )
    server = aio.server(interceptors=interceptors)
    auth_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

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
