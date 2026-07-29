from __future__ import annotations

import os
from dataclasses import dataclass


def _environment_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid_boolean_environment_value:{name}")


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    environment: str
    world_runtime_enabled: bool
    world_runtime_poll_seconds: float
    reasoner_enabled: bool
    reasoner_provider: str | None
    reasoner_model: str | None
    reasoner_api_key: str | None
    reasoner_base_url: str
    reasoner_timeout_seconds: float
    reasoner_profile_ref: str
    reasoner_think: bool
    reasoner_temperature: float
    reasoner_top_p: float
    reasoner_top_k: int
    reasoner_num_ctx: int
    reasoner_num_predict: int
    reasoner_keep_alive: str

    @classmethod
    def from_environment(cls) -> Settings:
        poll_seconds = float(os.getenv("V60_WORLD_RUNTIME_POLL_SECONDS", "1"))
        if poll_seconds <= 0:
            raise ValueError("world_runtime_poll_seconds_must_be_positive")
        reasoner_timeout_seconds = float(os.getenv("V60_REASONER_TIMEOUT_SECONDS", "30"))
        if reasoner_timeout_seconds <= 0:
            raise ValueError("reasoner_timeout_seconds_must_be_positive")
        reasoner_num_ctx = int(os.getenv("V60_REASONER_NUM_CTX", "32768"))
        if reasoner_num_ctx <= 0:
            raise ValueError("reasoner_num_ctx_must_be_positive")
        reasoner_temperature = float(os.getenv("V60_REASONER_TEMPERATURE", "0"))
        if not 0 <= reasoner_temperature <= 2:
            raise ValueError("reasoner_temperature_out_of_range")
        reasoner_top_p = float(os.getenv("V60_REASONER_TOP_P", "0.95"))
        if not 0 < reasoner_top_p <= 1:
            raise ValueError("reasoner_top_p_out_of_range")
        reasoner_top_k = int(os.getenv("V60_REASONER_TOP_K", "64"))
        if reasoner_top_k <= 0:
            raise ValueError("reasoner_top_k_must_be_positive")
        reasoner_num_predict = int(os.getenv("V60_REASONER_NUM_PREDICT", "1200"))
        if reasoner_num_predict <= 0:
            raise ValueError("reasoner_num_predict_must_be_positive")
        reasoner_profile_ref = os.getenv(
            "V60_REASONER_PROFILE_REF",
            "v60.model-serving.gemma4-structured-decision.001",
        ).strip()
        if not reasoner_profile_ref:
            raise ValueError("reasoner_profile_ref_required")
        reasoner_keep_alive = os.getenv(
            "V60_REASONER_KEEP_ALIVE",
            "30m",
        ).strip()
        if not reasoner_keep_alive:
            raise ValueError("reasoner_keep_alive_required")

        reasoner_provider = os.getenv("V60_REASONER_PROVIDER")
        reasoner_model = os.getenv("V60_REASONER_MODEL")
        reasoner_api_key = os.getenv("V60_REASONER_API_KEY") or os.getenv("OPENAI_API_KEY")
        return cls(
            database_url=os.getenv(
                "V60_DATABASE_URL",
                "postgresql+psycopg:///qiazhi_v60?host=/tmp",
            ),
            environment=os.getenv("V60_ENVIRONMENT", "local"),
            world_runtime_enabled=_environment_bool(
                "V60_WORLD_RUNTIME_ENABLED",
                default=True,
            ),
            world_runtime_poll_seconds=poll_seconds,
            reasoner_enabled=_environment_bool(
                "V60_REASONER_ENABLED",
                default=False,
            ),
            reasoner_provider=reasoner_provider.strip() if reasoner_provider else None,
            reasoner_model=reasoner_model.strip() if reasoner_model else None,
            reasoner_api_key=reasoner_api_key.strip() if reasoner_api_key else None,
            reasoner_base_url=os.getenv(
                "V60_REASONER_BASE_URL",
                "https://api.openai.com/v1",
            ).rstrip("/"),
            reasoner_timeout_seconds=reasoner_timeout_seconds,
            reasoner_profile_ref=reasoner_profile_ref,
            reasoner_think=_environment_bool(
                "V60_REASONER_THINK",
                default=False,
            ),
            reasoner_temperature=reasoner_temperature,
            reasoner_top_p=reasoner_top_p,
            reasoner_top_k=reasoner_top_k,
            reasoner_num_ctx=reasoner_num_ctx,
            reasoner_num_predict=reasoner_num_predict,
            reasoner_keep_alive=reasoner_keep_alive,
        )


settings = Settings.from_environment()
