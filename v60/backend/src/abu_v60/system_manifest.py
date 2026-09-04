from __future__ import annotations

from typing import Final

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.media.focused_speech import FOCUSED_SPEECH_TIMELINE_VERSION
from abu_v60.mingli.focused_reading_runtime import mingli_focused_runtime_manifest
from abu_v60.settings import settings

PRODUCT_ID: Final = "abu-knows-v60"
PRODUCT_VERSION: Final = "0.2.0"
FOUNDATION_VERSION: Final = "v60.foundation.045"
DECISION_POLICY_VERSION: Final = "v60.cognitive-decision-kernel.004"
MINGLI_ENGINE_VERSION: Final = "v60.mingli-cognitive-engine.051"
ASSET_REGISTRY_VERSION: Final = "v60.asset-registry.003"
MEDIA_RUNTIME_VERSION: Final = "v60.runtime-media-registry.009"
PUBLIC_PRODUCT_EXPOSURE_VERSION: Final = "v60.public-product-exposure.003"
ENTRY_EXPERIENCE: Final = "MINGLI_HOME"


def public_product_exposure_manifest() -> dict[str, object]:
    return {
        "policy_version": PUBLIC_PRODUCT_EXPOSURE_VERSION,
        "public_units": ["MINGLI_READING", "ABU_SAYS"],
        "lab": {
            "status": "INTERNAL_ONLY",
            "public_entry_allowed": False,
            "public_route_allowed": False,
        },
    }


def _public_architecture_manifest() -> dict[str, object]:
    return {
        "architecture_version": "v60.public-runtime-architecture.002",
        "default_locale": "zh-CN",
        "product_units": ["unit-mingli", "unit-abu"],
        "product_core": "unit-mingli",
        "entry_flow": ["AUTH", "CHART", "MINGLI_READING", "ABU_SAYS"],
        "modules": [
            {
                "module_id": "identity",
                "status": "ACTIVE",
                "capabilities": ["account_session", "private_profile"],
            },
            {
                "module_id": "mingli",
                "status": "ACTIVE",
                "capabilities": [
                    "deterministic_chart",
                    "formal_bounded_reading",
                    "progressive_one_focus_reading",
                ],
            },
            {
                "module_id": "abu-expression",
                "status": "ACTIVE",
                "capabilities": ["same_reading_expression", "lazy_focused_speech"],
            },
        ],
        "internal_surfaces_registered": settings.internal_surfaces_enabled,
    }


def runtime_manifest() -> dict[str, object]:
    knowledge = KnowledgeAuthority()
    return {
        "product_id": PRODUCT_ID,
        "product_version": PRODUCT_VERSION,
        "foundation_version": FOUNDATION_VERSION,
        "entry_experience": ENTRY_EXPERIENCE,
        "engines": {
            "decision": DECISION_POLICY_VERSION,
            "mingli": MINGLI_ENGINE_VERSION,
        },
        "architecture": _public_architecture_manifest(),
        "knowledge_profiles": knowledge.public_manifest(),
        "candidate_rule_profiles": knowledge.candidate_rule_manifest(),
        "quant_foundation_profiles": knowledge.quant_foundation_manifest(),
        "source_review_profiles": knowledge.source_review_manifest(),
        "mechanism_evidence_profiles": knowledge.mechanism_evidence_manifest(),
        "timing_evidence_profiles": knowledge.timing_evidence_manifest(),
        "relation_effect_rule_admission": knowledge.relation_effect_rule_admission_manifest(),
        "knowledge_profile_selection": knowledge.selection_manifest(),
        "asset_registry_version": ASSET_REGISTRY_VERSION,
        "media_runtime_version": MEDIA_RUNTIME_VERSION,
        "public_product_exposure": public_product_exposure_manifest(),
        "authority": {
            "chart": "DETERMINISTIC_LOCAL_SYSTEM",
            "interpretation": "LOCAL_QWEN_WITH_LOCAL_NORMALIZATION",
            "expression": "SAME_READING_ONLY",
            "consent": "HUMAN",
            "formal_commit": "EPISTEMIC_GATE",
        },
        "mingli_focused_runtime": mingli_focused_runtime_manifest(),
        "speech_runtime": {
            "status": "READY" if settings.tts_enabled else "DISABLED",
            "actor_ref": "ABU_NARRATOR_V1",
            "generation_mode": "LAZY_FROM_PERSISTED_FOCUSED_PASS",
            "timeline_version": FOCUSED_SPEECH_TIMELINE_VERSION,
            "clock_source": "HTML_AUDIO_CURRENT_TIME",
            "subtitle_granularity": "SENTENCE_OR_CLAUSE",
            "particle_focus": "EXPLICIT_COORDINATE_TERMS_ONLY",
            "text_first": True,
            "upstream_url_exposed": False,
        },
        "v50_runtime_dependency": False,
    }
