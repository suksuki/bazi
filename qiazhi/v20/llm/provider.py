from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class LLMProviderConfig:
    enabled: bool
    execute_llm: bool
    provider: str
    host: str
    port: int
    base_url: str
    model: str
    embedding_model: str
    api_key_env: str = "V20_LLM_API_KEY"
    audit_model: str = ""
    audit_base_url: str = ""
    audit_api_key_env: str = "V20_LLM_AUDIT_API_KEY"
    http_timeout_sec: float = 15.0
    fuse_wait_timeout_sec: float = 30.0
    temperature: float = 0.2
    max_tokens: int = 800
    role: str = "bounded_assistive_llm"

    def resolved_base_url(self) -> str:
        return resolve_llm_base_url(self.base_url, self.host, self.port)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resolved_base_url"] = self.resolved_base_url()
        payload["secret_policy"] = "env_names_only_no_secret_values"
        payload["guardrails"] = [
            "LLM_PROVIDER_CONFIG_ONLY",
            "NO_SECRET_VALUES_RENDERED",
            "LLM_OUTPUT_REQUIRES_CONTRACT_VALIDATION",
            "DETERMINISTIC_FALLBACK_REQUIRED",
        ]
        return payload


def load_llm_provider_config_from_env() -> LLMProviderConfig:
    return LLMProviderConfig(
        enabled=_bool_env("V20_LLM_ENABLED", False),
        execute_llm=_bool_env("V20_LLM_EXECUTE", False),
        provider=os.getenv("V20_LLM_PROVIDER", "openai_compatible").strip() or "openai_compatible",
        host=os.getenv("V20_LLM_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_int_env("V20_LLM_PORT", 11434),
        base_url=os.getenv("V20_LLM_BASE_URL", "").strip(),
        model=os.getenv("V20_LLM_MODEL", "qwen2.5:7b").strip() or "qwen2.5:7b",
        embedding_model=os.getenv("V20_LLM_EMBEDDING_MODEL", "").strip(),
        audit_model=os.getenv("V20_LLM_AUDIT_MODEL", "").strip(),
        audit_base_url=os.getenv("V20_LLM_AUDIT_BASE_URL", "").strip(),
        http_timeout_sec=_float_env("V20_LLM_HTTP_TIMEOUT_SEC", 15.0),
        fuse_wait_timeout_sec=_float_env("V20_LLM_FUSE_WAIT_TIMEOUT_SEC", 30.0),
        temperature=_float_env("V20_LLM_TEMPERATURE", 0.2),
        max_tokens=_int_env("V20_LLM_MAX_TOKENS", 800),
    )


def llm_provider_readiness_report(config: LLMProviderConfig | None = None) -> dict[str, object]:
    cfg = config or load_llm_provider_config_from_env()
    api_key_present = bool(os.getenv(cfg.api_key_env))
    audit_api_key_present = bool(os.getenv(cfg.audit_api_key_env))
    local_provider = cfg.provider.lower() in {"ollama", "ollama_native", "local", "local_openai_compatible"}
    resolved_url = cfg.resolved_base_url()
    ready = bool(cfg.enabled and resolved_url and (api_key_present or local_provider))
    return {
        "version": "v20.llm_provider_readiness.v1",
        "enabled": cfg.enabled,
        "execute_llm": cfg.execute_llm,
        "provider": cfg.provider,
        "model": cfg.model,
        "embedding_model": cfg.embedding_model,
        "resolved_base_url": resolved_url,
        "api_key_env": cfg.api_key_env,
        "api_key_present": api_key_present,
        "audit_model": cfg.audit_model,
        "audit_base_url": cfg.audit_base_url,
        "audit_api_key_env": cfg.audit_api_key_env,
        "audit_api_key_present": audit_api_key_present,
        "ready_for_connection": ready,
        "connection_policy": "explicit_llm_task_only_no_healthcheck_network_call",
        "runtime_mutation": False,
        "guardrails": [
            "LLM_READINESS_ONLY",
            "NO_NETWORK_CONNECTION_ATTEMPTED",
            "NO_SECRET_VALUES_RENDERED",
            "LLM_IS_ASSISTIVE_NOT_AUTHORITATIVE",
        ],
    }


def resolve_llm_base_url(base_url: str, host: str, port: int) -> str:
    explicit = str(base_url or "").strip()
    if explicit:
        return explicit.rstrip("/")
    clean_host = str(host or "").strip()
    if not clean_host:
        return ""
    raw = clean_host if clean_host.startswith(("http://", "https://")) else f"http://{clean_host}"
    parsed = urlsplit(raw)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    host_part = netloc.rsplit("@", 1)[-1]
    if port and ":" not in host_part:
        netloc = f"{netloc}:{port}"
    candidate = urlunsplit((scheme, netloc, path.rstrip("/"), "", "")).rstrip("/")
    if not candidate.endswith("/v1"):
        candidate += "/v1"
    return candidate


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return float(raw)
