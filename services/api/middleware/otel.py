import time
from collections.abc import Awaitable, Callable
from typing import Any, override

import grpc
from grpc.aio import (
    ClientCallDetails,
    UnaryUnaryCall,
    UnaryUnaryClientInterceptor,
)
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from common.otel import setup_metrics
from services.api.config import settings

meter = setup_metrics(
    settings.service_name, settings.otel_url, settings.otel_interval
)

http_requests = meter.create_counter('http.server.request.count')
http_latency = meter.create_histogram('http.server.request.duration', unit='ms')
http_request_size = meter.create_histogram(
    'http.server.request.size', unit='by'
)
http_response_size = meter.create_histogram(
    'http.server.response.size', unit='by'
)
http_active_connections = meter.create_up_down_counter(
    'http.server.active_connections', unit='1'
)

ws_connections_total = meter.create_counter('ws.server.connection.count')
ws_disconnections_total = meter.create_counter('ws.server.disconnection.count')
ws_connections_active = meter.create_up_down_counter(
    'ws.server.connection.active', unit='1'
)
ws_connections_duration = meter.create_histogram(
    'ws.server.connection.duration', unit='s'
)
ws_message_size = meter.create_histogram('ws.server.message.size', unit='by')
ws_messages_sent = meter.create_counter('ws.server.message.sent')
ws_messages_received = meter.create_counter('ws.server.message.received')


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


def match_route(scope: Scope) -> str:
    app = scope.get('app')
    if app is None:
        return 'unknown'
    for route in app.router.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return getattr(route, 'path', scope['path'])
    return 'unknown'


class OTELMiddleware:
    """
    This middleware should be the latests in the middleware list
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] == 'websocket':
            await self._handle_ws(scope, receive, send)
        elif scope['type'] == 'http':
            await self._handle_http(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send):
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
            http_request_size.record(int(val), labels)

        http_response_size.record(response_size_bytes, labels)
        http_requests.add(1, labels)
        http_latency.record(duration, labels)

    async def _handle_ws(self, scope: Scope, receive: Receive, send: Send):
        labels = {'path': match_route(scope)}

        ws_connections_total.add(1, labels)
        ws_connections_active.add(1, labels)

        async def patched_receive():
            result = await receive()
            size = len(str(result).encode())
            ws_message_size.record(size, {**labels, 'direction': 'in'})
            ws_messages_received.add(1, labels)
            return result

        async def patched_send(message: Message):
            size = len(str(message).encode())
            ws_message_size.record(size, {**labels, 'direction': 'out'})
            await send(message)
            ws_messages_sent.add(1, labels)

        start = time.perf_counter()
        await self.app(scope, patched_receive, patched_send)
        duration = time.perf_counter() - start

        ws_connections_active.add(-1, labels)
        ws_disconnections_total.add(1, labels)
        ws_connections_duration.record(duration, labels)


grpc_requests = meter.create_counter(
    'grpc.client.request.count',
    description='Total gRPC client calls',
)
grpc_latency = meter.create_histogram(
    'grpc.client.request.duration',
    unit='ms',
    description='gRPC client request duration in ms',
)


class OTELClientInterceptor(UnaryUnaryClientInterceptor):
    @override
    async def intercept_unary_unary(
        self,
        continuation: Callable[
            [ClientCallDetails, Any], Awaitable[UnaryUnaryCall[Any, Any]]
        ],
        client_call_details: ClientCallDetails,
        request: Any,
    ):
        start = time.perf_counter()
        code = 'OK'
        try:
            call = await continuation(client_call_details, request)
            await call
            code = (await call.code()).name
            # return the call (not the response) so outer interceptors
            # (e.g. OTEL tracing) can attach done-callbacks to a real
            # UnaryUnaryCall instead of a UnaryUnaryCallResponse wrapper
            return call
        except grpc.aio.AioRpcError as exc:
            code = exc.code().name
            raise
        finally:
            duration = (time.perf_counter() - start) * 1_000
            full_method = client_call_details.method
            if isinstance(full_method, bytes):
                full_method = full_method.decode()
            _, service, method = full_method.split('/')
            labels = {
                'code': code,
                'service': service,
                'method': method,
            }
            grpc_requests.add(1, labels)
            grpc_latency.record(duration, labels)
