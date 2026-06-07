import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from common.metrics import setup_metrics

meter = setup_metrics('duo.api', 'localhost:4317')
http_requests = meter.create_counter(
    'http.server.request.count', description='Total HTTP requests'
)
http_latency = meter.create_histogram(
    'http.servier.request.duration',
    description='HTTP request duration in ms',
    unit='ms',
)


def get_route(scope: Scope) -> str:
    path: str | None = getattr(scope.get('route'), 'path', None)
    if path is not None:
        return scope.get('root_path', '') + path
    return scope.get('path', 'unknown')


class OTELMiddleware:
    """
    This middleware should be the latests in the middleware list
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        status_code: int = 500

        async def patched_send(message: Message) -> None:
            nonlocal status_code
            if message.get('type') == 'http.response.start':
                status_code = message.get('status', 500)
            await send(message)

        start = time.perf_counter()
        await self.app(scope, receive, patched_send)
        duration = (time.perf_counter() - start) * 1_000

        path = get_route(scope)
        labels = {
            'method': scope.get('method', ''),
            'path': path,
            'status': status_code,
        }
        http_requests.add(1, labels)
        http_latency.record(duration, labels)
