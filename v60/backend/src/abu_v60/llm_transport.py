from __future__ import annotations

import json
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from abu_v60.provenance import canonical_json


class JsonTransport(Protocol):
    def __call__(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class LlmTransportError(RuntimeError):
    pass


def default_json_transport(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    request = Request(
        url,
        data=canonical_json(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise LlmTransportError(f"llm_provider_http_error:{exc.code}:{detail}") from exc
    except URLError as exc:
        raise LlmTransportError(f"llm_provider_network_error:{exc.reason}") from exc
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LlmTransportError("llm_provider_invalid_json") from exc
    if not isinstance(parsed, dict):
        raise LlmTransportError("llm_provider_response_must_be_object")
    return parsed
