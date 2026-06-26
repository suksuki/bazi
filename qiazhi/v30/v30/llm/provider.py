from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class V30LLMProviderConfig:
    enabled: bool
    execute_llm: bool
    provider: str
    host: str
    port: int
    base_url: str
    model: str
    api_key_env: str
    http_timeout_sec: float
    temperature: float
    max_tokens: int
    config_source: str

    def resolved_base_url(self) -> str:
        return resolve_llm_base_url(self.base_url, self.host, self.port)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["resolved_base_url"] = self.resolved_base_url()
        payload["api_key_present"] = bool(os.getenv(self.api_key_env))
        payload["secret_policy"] = "env_names_only_no_secret_values"
        payload["boundary"] = "v30_llm_provider_config_can_reuse_legacy_env_shape_without_legacy_runtime"
        return payload


def load_v30_llm_provider_config_from_env() -> V30LLMProviderConfig:
    source = "v30" if _has_any_v30_llm_env() else "legacy_compat"
    api_key_env = _env("V30_LLM_API_KEY_ENV", "") or (
        "V30_LLM_API_KEY" if os.getenv("V30_LLM_API_KEY") else "V20_LLM_API_KEY"
    )
    return V30LLMProviderConfig(
        enabled=_bool_env("V30_LLM_ENABLED", _bool_env("V20_LLM_ENABLED", False)),
        execute_llm=_bool_env("V30_LLM_EXECUTE", _bool_env("V20_LLM_EXECUTE", False)),
        provider=_env("V30_LLM_PROVIDER", _env("V20_LLM_PROVIDER", "openai_compatible")) or "openai_compatible",
        host=_env("V30_LLM_HOST", _env("V20_LLM_HOST", "127.0.0.1")) or "127.0.0.1",
        port=_int_env("V30_LLM_PORT", _int_env("V20_LLM_PORT", 11434)),
        base_url=_env("V30_LLM_BASE_URL", _env("V20_LLM_BASE_URL", "")),
        model=_env("V30_LLM_MODEL", _env("V20_LLM_MODEL", "qwen2.5:7b")) or "qwen2.5:7b",
        api_key_env=api_key_env,
        http_timeout_sec=_float_env("V30_LLM_HTTP_TIMEOUT_SEC", _float_env("V20_LLM_HTTP_TIMEOUT_SEC", 15.0)),
        temperature=_float_env("V30_LLM_TEMPERATURE", _float_env("V20_LLM_TEMPERATURE", 0.2)),
        max_tokens=_int_env("V30_LLM_MAX_TOKENS", _int_env("V20_LLM_MAX_TOKENS", 600)),
        config_source=source,
    )


def llm_provider_readiness_report(config: V30LLMProviderConfig | None = None) -> dict[str, object]:
    cfg = config or load_v30_llm_provider_config_from_env()
    local_provider = cfg.provider.lower() in {"ollama", "ollama_native", "local", "local_openai_compatible"}
    api_key_present = bool(os.getenv(cfg.api_key_env))
    ready = bool(cfg.enabled and cfg.resolved_base_url() and (api_key_present or local_provider))
    return {
        "version": "v30.llm_provider_readiness.v1",
        "enabled": cfg.enabled,
        "execute_llm": cfg.execute_llm,
        "provider": cfg.provider,
        "model": cfg.model,
        "resolved_base_url": cfg.resolved_base_url(),
        "api_key_env": cfg.api_key_env,
        "api_key_present": api_key_present,
        "ready_for_connection": ready,
        "config_source": cfg.config_source,
        "runtime_mutation": False,
        "boundary": "llm_readiness_reuses_legacy_env_shape_not_legacy_runtime_or_chart_fact",
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


def _has_any_v30_llm_env() -> bool:
    return any(name.startswith("V30_LLM_") for name in os.environ)


def _env(name: str, default: str) -> str:
    raw = os.getenv(name)
    return default if raw in (None, "") else raw.strip()


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
