import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from common.metrics import setup_metrics

meter = setup_metrics('duo.api', 'localhost:4317')
http_requests = meter.create_counter(
    'http.server.request.count',
    description='Total HTTP requests',
)
http_latency = meter.create_histogram(
    'http.server.request.duration',
    unit='ms',
    description='HTTP request duration in ms',
)
http_request_size_bytes = meter.create_histogram(
    'http.server.request.size_bytes',
    unit='by',
    description='HTTP request size in bytes',
)
http_response_size_bytes = meter.create_histogram(
    'http.server.response.size_bytes',
    unit='by',
    description='HTTP response size in bytes',
)
http_active_connections = meter.create_up_down_counter(
    'http.server.active_connections',
    unit='1',
    description='HTTP requests currently performed',
)


def get_route(scope: Scope) -> str:
    path: str | None = getattr(scope.get('route'), 'path', None)
    if path is not None:
        return scope.get('root_path', '') + path
    return scope.get('path', 'unknown')


def get_header_value(
    target: bytes,
    headers: list[tuple[bytes, bytes]],
) -> bytes | None:
    for header_name, header_value in headers:
        if header_name == target:
            return header_value
    return None


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
        response_size_bytes: int = 0

        async def patched_send(message: Message) -> None:
            nonlocal status_code
            nonlocal response_size_bytes
            if message.get('type') == 'http.response.start':
                status_code = message.get('status', 500)
                val = get_header_value(
                    b'content-length',
                    message.get('headers', []),
                )
                if val:
                    response_size_bytes = int(val)
            await send(message)

        labels = {
            'method': scope.get('method', ''),
        }
        http_active_connections.add(1, labels)

        start = time.perf_counter()
        await self.app(scope, receive, patched_send)
        duration = (time.perf_counter() - start) * 1_000

        http_active_connections.add(-1, labels)

        path = get_route(scope)
        labels['path'] = path
        labels['status'] = status_code

        val = get_header_value(
            b'content-length',
            scope.get('headers', []),
        )
        if val:
            http_request_size_bytes.record(int(val), labels)

        http_response_size_bytes.record(response_size_bytes, labels)
        http_requests.add(1, labels)
        http_latency.record(duration, labels)
