import logging

from opentelemetry import _logs, metrics
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from common.logging.filters import KeywordLevelFilter


def setup_metrics(
    service_name: str,
    endpoint: str,
    export_interval_millis: int = 5_000,
) -> metrics.Meter:
    exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(
        exporter=exporter,
        export_interval_millis=export_interval_millis,
    )
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return metrics.get_meter(service_name)


def setup_logs(
    service_name: str,
    endpoint: str,
    export_interval_millis: int = 5_000,
) -> None:
    resource = Resource.create({'service.name': service_name})
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=endpoint, insecure=True),
            schedule_delay_millis=export_interval_millis,
        )
    )
    _logs.set_logger_provider(provider)
    handler = LoggingHandler(level=logging.INFO)
    handler.addFilter(
        KeywordLevelFilter([{'level': 'WARNING', 'keywords': ['uvicorn']}])
    )
    logging.getLogger().addHandler(handler)
