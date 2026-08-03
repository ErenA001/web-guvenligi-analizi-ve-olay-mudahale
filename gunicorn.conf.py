import os

bind = os.getenv("BIND", "0.0.0.0:5001")
workers = max(1, int(os.getenv("WEB_CONCURRENCY", "4")))
worker_class = "sync"
timeout = 60
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
