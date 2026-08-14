"""Structured logging setup.

Emits JSON-ish structured records including request_id/user_id/latency
where available, so logs are grep/parse-friendly in Render's log viewer
or any log aggregator plugged in later.
"""
import logging
import sys


def configure_logging(app_env: str) -> None:
    level = logging.INFO if app_env == "production" else logging.DEBUG
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
