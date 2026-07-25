from __future__ import annotations

import os
from typing import Literal

from core.contracts.base import V50Model


CognitiveTask = Literal[
    "birth_intake",
    "baseline_cognition",
    "pattern_preview",
    "pattern_hypothesis",
    "work_path_portrait",
    "ziwei_integration",
    "prediction_probe",
    "career_reasoning",
    "wealth_reasoning",
    "domain_reasoning",
    "case_turn",
]


class ModelRoute(V50Model):
    task: CognitiveTask
    model: str
    role: Literal["intake", "whole_chart", "dual_lens", "domain", "case_revision"]
    temperature: float
    max_tokens: int
    num_ctx: int
    thinking: bool = False


class ModelPolicyRouter:
    """Selects execution capacity for a task; it never selects a Mingli answer."""

    def __init__(self, routes: dict[CognitiveTask, ModelRoute]) -> None:
        self._routes = dict(routes)

    @classmethod
    def from_env(cls) -> "ModelPolicyRouter":
        whole_model = os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")
        pattern_model = os.getenv("V50_MINGLI_PATTERN_MODEL", whole_model)
        work_model = os.getenv("V50_MINGLI_WORK_MODEL", whole_model)
        domain_model = os.getenv("V50_MINGLI_DOMAIN_MODEL", whole_model)
        intake_model = os.getenv("V50_ABU_INTAKE_MODEL", "qwen3:8b")
        whole_ctx = int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768"))
        domain_ctx = int(os.getenv("V50_MINGLI_DOMAIN_NUM_CTX", "32768"))
        specs: dict[CognitiveTask, tuple[str, str, float, int, int]] = {
            "birth_intake": (intake_model, "intake", 0.0, 700, 8192),
            "baseline_cognition": (whole_model, "whole_chart", 0.0, 3200, whole_ctx),
            "pattern_preview": (pattern_model, "whole_chart", 0.0, 420, whole_ctx),
            "pattern_hypothesis": (pattern_model, "whole_chart", 0.0, 2600, whole_ctx),
            "work_path_portrait": (work_model, "whole_chart", 0.0, 2600, whole_ctx),
            "ziwei_integration": (whole_model, "dual_lens", 0.05, 2800, whole_ctx),
            "prediction_probe": (whole_model, "whole_chart", 0.05, 2200, whole_ctx),
            "career_reasoning": (domain_model, "domain", 0.0, 2800, domain_ctx),
            "wealth_reasoning": (domain_model, "domain", 0.0, 2800, domain_ctx),
            "domain_reasoning": (domain_model, "domain", 0.0, 2800, domain_ctx),
            "case_turn": (whole_model, "case_revision", 0.18, 3600, whole_ctx),
        }
        return cls({
            task: ModelRoute(
                task=task,
                model=model,
                role=role,
                temperature=temperature,
                max_tokens=max_tokens,
                num_ctx=num_ctx,
                thinking=(
                    _env_bool("V50_MINGLI_PATTERN_THINKING", False)
                    if task == "pattern_hypothesis"
                    else _env_bool("V50_MINGLI_CASE_TURN_THINKING", False)
                    if task == "case_turn"
                    else False
                ),
            )
            for task, (model, role, temperature, max_tokens, num_ctx) in specs.items()
        })

    def route(self, task: CognitiveTask) -> ModelRoute:
        return self._routes[task]

    def manifest(self) -> list[dict[str, object]]:
        return [self._routes[key].model_dump(mode="json") for key in sorted(self._routes)]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
