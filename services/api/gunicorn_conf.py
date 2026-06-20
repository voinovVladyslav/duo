import os
from pathlib import Path

from common.logging.main import get_logging_config

bind = '0.0.0.0:8000'
# sched_getaffinity respects container CPU quotas;
# multiprocessing.cpu_count() returns host CPUs
workers = len(os.sched_getaffinity(0)) * 2 + 1
worker_class = 'uvicorn_worker.UvicornWorker'

timeout = 120
graceful_timeout = 30
keepalive = 5

# recycle workers to prevent memory leaks; jitter avoids thundering herd
max_requests = 1000
max_requests_jitter = 100

# tmpfs for worker heartbeat files — prevents false timeouts in Docker
worker_tmp_dir = '/dev/shm'

accesslog = '-'
errorlog = '-'

logconfig_dict = get_logging_config(
    Path(__file__).parent.parent.parent / 'common/logging/config.prod.json'
)
