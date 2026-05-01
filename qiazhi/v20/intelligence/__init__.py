from v20.intelligence.feature_discovery import (
    build_feature_discovery_question_policy,
    build_feature_discovery_report,
    build_feature_discovery_training_signal,
    validate_feature_discovery_report,
)
from v20.intelligence.knowledge_semantic_model import (
    build_knowledge_semantic_model,
    validate_knowledge_semantic_model,
)


def build_intelligence_generation_manifest() -> dict[str, object]:
    from v20.intelligence.generation import build_intelligence_generation_manifest as _build

    return _build()

__all__ = [
    "build_feature_discovery_question_policy",
    "build_feature_discovery_report",
    "build_feature_discovery_training_signal",
    "build_intelligence_generation_manifest",
    "build_knowledge_semantic_model",
    "validate_knowledge_semantic_model",
    "validate_feature_discovery_report",
]
