from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


SENSITIVE_KEYS = {"authorization", "cookie", "password", "token", "secret", "api_key", "database_url", "redis_url"}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in getattr(record, "event_payload", {}).items():
            payload[key] = _redact(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def configure_json_logging() -> None:
    if os.getenv("V20_JSON_LOGS", "1").strip().lower() in {"0", "false", "no"}:
        return
    root = logging.getLogger()
    if any(getattr(handler, "_v20_json_handler", False) for handler in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler._v20_json_handler = True  # type: ignore[attr-defined]
    root.handlers = [handler]
    root.setLevel(_log_level())


def get_logger(name: str) -> logging.Logger:
    configure_json_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, message: str, **payload: Any) -> None:
    logger.log(level, message, extra={"event_payload": payload})


def _log_level() -> int:
    raw = os.getenv("V20_LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, raw, logging.INFO)


def _redact(key: str, value: Any) -> Any:
    lowered = key.lower()
    if any(marker in lowered for marker in SENSITIVE_KEYS):
        return "[redacted]"
    if isinstance(value, dict):
        return {str(child_key): _redact(str(child_key), child_value) for child_key, child_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(key, row) for row in value]
    return value
