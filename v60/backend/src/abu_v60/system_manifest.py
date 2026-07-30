from __future__ import annotations

from typing import Final

from abu_v60.architecture import runtime_architecture
from abu_v60.decision.reasoner import reasoner_runtime_manifest
from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.story.packages import (
    default_episode_source_registry,
    qualification_episode_source_registry,
)

PRODUCT_ID: Final = "abu-knows-v60"
PRODUCT_VERSION: Final = "0.1.0"
FOUNDATION_VERSION: Final = "v60.foundation.016"
EXPERIENCE_CONTEXT_VERSION: Final = "v60.experience-context.003"
DECISION_POLICY_VERSION: Final = "v60.cognitive-decision-kernel.004"
DREAM_GAME_ENGINE_VERSION: Final = "v60.dream-game-engine.018"
WORLD_ENGINE_VERSION: Final = "v60.world-continuity-engine.004"
MINGLI_ENGINE_VERSION: Final = "v60.mingli-cognitive-engine.025"
STORY_ENGINE_VERSION: Final = "v60.life-story-engine.011"
ASSET_REGISTRY_VERSION: Final = "v60.asset-registry.002"
MEDIA_RUNTIME_VERSION: Final = "v60.runtime-media-registry.001"
PRIMARY_WORLD_ID: Final = "abu-dream-world-v1"
ENTRY_EXPERIENCE: Final = "PRIVATE_LIFE_TREE_HOME"


def runtime_manifest() -> dict[str, object]:
    knowledge = KnowledgeAuthority()
    return {
        "product_id": PRODUCT_ID,
        "product_version": PRODUCT_VERSION,
        "foundation_version": FOUNDATION_VERSION,
        "entry_experience": ENTRY_EXPERIENCE,
        "engines": {
            "context": EXPERIENCE_CONTEXT_VERSION,
            "decision": DECISION_POLICY_VERSION,
            "game": DREAM_GAME_ENGINE_VERSION,
            "world": WORLD_ENGINE_VERSION,
            "mingli": MINGLI_ENGINE_VERSION,
            "story": STORY_ENGINE_VERSION,
        },
        "architecture": runtime_architecture().public_manifest(),
        "knowledge_profiles": knowledge.public_manifest(),
        "candidate_rule_profiles": knowledge.candidate_rule_manifest(),
        "quant_foundation_profiles": knowledge.quant_foundation_manifest(),
        "source_review_profiles": knowledge.source_review_manifest(),
        "mechanism_evidence_profiles": knowledge.mechanism_evidence_manifest(),
        "timing_evidence_profiles": knowledge.timing_evidence_manifest(),
        "relation_effect_rule_admission": (
            knowledge.relation_effect_rule_admission_manifest()
        ),
        "knowledge_profile_selection": knowledge.selection_manifest(),
        "asset_registry_version": ASSET_REGISTRY_VERSION,
        "media_runtime_version": MEDIA_RUNTIME_VERSION,
        "authority": {
            "facts": "SYSTEM",
            "world_outcomes": "SYSTEM",
            "interpretation": "BOUNDED_LLM_REASONER",
            "formal_commit": "EPISTEMIC_GATE",
            "consent": "HUMAN",
            "global_knowledge": "OWNER_PROFESSIONAL_REVIEW",
        },
        "reasoner_runtime": reasoner_runtime_manifest(),
        "episode_source_packages": {
            "canonical_story": default_episode_source_registry().public_manifest(),
            "three_life_qualification": (qualification_episode_source_registry().public_manifest()),
        },
        "v50_runtime_dependency": False,
    }
