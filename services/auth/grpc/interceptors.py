import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any, cast, override

import grpc

from common.exceptions import ExpiredTokenError, InvalidTokenError
from common.metrics import setup_metrics
from services.auth.config import settings
from services.auth.db.crud import get_user_from_token
from services.auth.db.models import User
from services.auth.exceptions import UnsupportedGRPCMethodError

request_user: ContextVar[User | None] = ContextVar('request_user', default=None)

meter = setup_metrics(
    settings.service_name, settings.otel_url, settings.otel_interval
)
grpc_requests = meter.create_counter(
    'grpc.server.request.count',
    description='Total gRPC calls',
)
grpc_latency = meter.create_histogram(
    'grpc.server.request.duration',
    unit='ms',
    description='gRPC request duration in ms',
)


def get_current_user() -> User | None:
    return request_user.get()


class AuthInterceptor(grpc.aio.ServerInterceptor):
    @override
    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails],
            Awaitable[grpc.RpcMethodHandler[Any, Any]],
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ):
        handler = await continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        token = str(metadata.get('authorization', ''))
        if not token:
            return handler

        try:
            user = await get_user_from_token(token=token)
        except InvalidTokenError, ExpiredTokenError:
            user = None

        # Wraps only unary_unary as it's only used methods
        if handler.unary_unary is not None:

            async def new_unary_unary(
                request: Any, context: grpc.ServicerContext
            ):
                assert handler.unary_unary is not None
                with request_user.set(user):
                    return await handler.unary_unary(request, context)

            return grpc.unary_unary_rpc_method_handler(
                new_unary_unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        raise UnsupportedGRPCMethodError('Only unary_unary is supported')


class OTELInterceptor(grpc.aio.ServerInterceptor):
    @override
    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails],
            Awaitable[grpc.RpcMethodHandler[Any, Any]],
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ):
        handler = await continuation(handler_call_details)
        # Wraps only unary_unary as it's only used methods
        if handler.unary_unary is not None:

            async def new_unary_unary(
                request: Any,
                context: grpc.aio.ServicerContext[Any, Any],
            ):
                assert handler.unary_unary is not None
                start = time.perf_counter()
                try:
                    result = await handler.unary_unary(
                        request, cast(grpc.ServicerContext, context)
                    )
                except Exception as exc:
                    raise exc
                finally:
                    code = context.code().name if context.code() else 'OK'
                    duration = (time.perf_counter() - start) * 1_000
                    _, service, method = handler_call_details.method.split('/')
                    labels = {
                        'code': code,
                        'service': service,
                        'method': method,
                    }
                    grpc_requests.add(1, labels)
                    grpc_latency.record(duration, labels)
                return result

            return grpc.unary_unary_rpc_method_handler(
                new_unary_unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        raise UnsupportedGRPCMethodError('Only unary_unary is supported')
