from __future__ import annotations

import json
import logging

from v20.ops.logging import JsonLogFormatter, log_event


def test_v20_json_log_formatter_redacts_sensitive_fields() -> None:
    logger = logging.getLogger("v20.test.logging")
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        __file__,
        1,
        "request_completed",
        (),
        None,
        extra={
            "event_payload": {
                "event": "request_completed",
                "path": "/api/v20/auth/login",
                "status_code": 200,
                "password": "secret-password",
                "nested": {"token": "secret-token", "safe": "visible"},
                "redis_url": "redis://:secret@localhost:6379/0",
            }
        },
    )

    rendered = JsonLogFormatter().format(record)
    payload = json.loads(rendered)

    assert payload["message"] == "request_completed"
    assert payload["event"] == "request_completed"
    assert payload["path"] == "/api/v20/auth/login"
    assert payload["password"] == "[redacted]"
    assert payload["nested"]["token"] == "[redacted]"
    assert payload["nested"]["safe"] == "visible"
    assert payload["redis_url"] == "[redacted]"
    assert "secret-password" not in rendered
    assert "secret-token" not in rendered
    assert "redis://:secret" not in rendered


def test_v20_log_event_uses_structured_payload(caplog) -> None:
    logger = logging.getLogger("v20.test.log_event")
    caplog.set_level(logging.INFO, logger=logger.name)

    log_event(logger, logging.INFO, "request_completed", event="request_completed", status_code=200)

    assert caplog.records[-1].event_payload == {"event": "request_completed", "status_code": 200}
