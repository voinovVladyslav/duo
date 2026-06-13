import time
from collections.abc import Awaitable, Callable
from typing import Any, override

import grpc
from grpc.aio import (
    ClientCallDetails,
    UnaryUnaryCall,
    UnaryUnaryClientInterceptor,
)

from services.api.middleware.otel import meter

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
            result = await call
            code = (await call.code()).name
            return result
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
