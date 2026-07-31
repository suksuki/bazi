from __future__ import annotations

import os
from dataclasses import dataclass

TTS_PROVIDER_PROFILE_REF = "v60.qwen3-tts-proxy.001"
TTS_MODEL = "Qwen3-TTS"
TTS_DEPLOYMENTS = {
    "https://dblife.com/abu-tts/tts": "dblife-public-proxy",
    "http://192.168.0.7:7860/tts": "dblife-server13-private-upstream",
}


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
    tts_enabled: bool = True
    tts_url: str = "https://dblife.com/abu-tts/tts"
    tts_provider_profile_ref: str = TTS_PROVIDER_PROFILE_REF
    tts_provider_deployment_ref: str = "dblife-public-proxy"
    tts_model: str = TTS_MODEL
    tts_abu_voice: str = "Dylan"
    tts_duoduo_voice: str = "Vivian"
    tts_timeout_seconds: float = 45.0
    tts_max_audio_bytes: int = 8 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.tts_model != TTS_MODEL:
            raise ValueError("tts_model_not_controlled_by_proxy_contract")
        if self.tts_provider_profile_ref != TTS_PROVIDER_PROFILE_REF:
            raise ValueError("tts_provider_profile_not_admitted")
        expected_deployment = TTS_DEPLOYMENTS.get(self.tts_url)
        if expected_deployment is None:
            raise ValueError("tts_url_not_admitted")
        if self.tts_provider_deployment_ref != expected_deployment:
            raise ValueError("tts_url_deployment_mismatch")
        if not self.tts_abu_voice or not self.tts_duoduo_voice:
            raise ValueError("tts_voice_required")

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
        tts_url = os.getenv(
            "V60_TTS_URL",
            "https://dblife.com/abu-tts/tts",
        ).strip()
        if not tts_url:
            raise ValueError("tts_url_required")
        tts_timeout_seconds = float(os.getenv("V60_TTS_TIMEOUT_SECONDS", "45"))
        if tts_timeout_seconds <= 0:
            raise ValueError("tts_timeout_seconds_must_be_positive")
        tts_max_audio_bytes = int(os.getenv("V60_TTS_MAX_AUDIO_BYTES", "8388608"))
        if tts_max_audio_bytes <= 0:
            raise ValueError("tts_max_audio_bytes_must_be_positive")

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
            tts_enabled=_environment_bool("V60_TTS_ENABLED", default=True),
            tts_url=tts_url,
            tts_provider_profile_ref=os.getenv(
                "V60_TTS_PROVIDER_PROFILE_REF",
                TTS_PROVIDER_PROFILE_REF,
            ).strip(),
            tts_provider_deployment_ref=os.getenv(
                "V60_TTS_PROVIDER_DEPLOYMENT_REF",
                "dblife-public-proxy",
            ).strip(),
            tts_model=os.getenv("V60_TTS_MODEL", TTS_MODEL).strip(),
            tts_abu_voice=os.getenv("V60_TTS_ABU_VOICE", "Dylan").strip(),
            tts_duoduo_voice=os.getenv("V60_TTS_DUODUO_VOICE", "Vivian").strip(),
            tts_timeout_seconds=tts_timeout_seconds,
            tts_max_audio_bytes=tts_max_audio_bytes,
        )


settings = Settings.from_environment()
