from common.logging.main import setup_logging
from common.metrics import setup_logs
from services.game.config import settings

setup_logging()
setup_logs(settings.service_name, settings.otel_url, settings.otel_interval)
