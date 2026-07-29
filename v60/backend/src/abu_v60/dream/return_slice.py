from __future__ import annotations

from typing import Any

from abu_v60.game import (
    DreamEpisodeContract,
    DreamEpisodeDefinition,
    EpisodeNarrativeContract,
)
from abu_v60.story.packages import default_episode_source_registry

RETURN_PACKAGE_REF = "v60.episode-package.yanzhou-wet-bank.v1"
_COMPATIBILITY_STRUCTURE_REF = "v60-fact-return-slice-compatibility-view"


def return_episode_definition(structure_fact_ref: str) -> DreamEpisodeDefinition:
    """Compatibility view over the canonical hash-locked source package."""

    return default_episode_source_registry().compile_definition(
        RETURN_PACKAGE_REF,
        bindings={"structure_fact_ref": structure_fact_ref},
    )


def _compatibility_definition() -> DreamEpisodeDefinition:
    return return_episode_definition(_COMPATIBILITY_STRUCTURE_REF)


_COMPATIBILITY_DEFINITION = _compatibility_definition()

RETURN_ACTOR_REF = _COMPATIBILITY_DEFINITION.actor_ref
RETURN_TREE_REF = _COMPATIBILITY_DEFINITION.tree_ref
RETURN_QUESTION_REF = _COMPATIBILITY_DEFINITION.runtime.question_ref
RETURN_EPISODE_REF = _COMPATIBILITY_DEFINITION.runtime.episode_ref
RETURN_HISTORY_EVENT_REF = _COMPATIBILITY_DEFINITION.runtime.baseline_event_ref
RETURN_FUTURE_EVENT_REF = _COMPATIBILITY_DEFINITION.runtime.world_event_ref
RETURN_QUESTION_PROMPT = _COMPATIBILITY_DEFINITION.prompt
RETURN_QUESTION_OPTIONS = [
    option.model_dump(mode="json") for option in _COMPATIBILITY_DEFINITION.options
]
RETURN_HISTORICAL_EVIDENCE = [
    dict(evidence) for evidence in _COMPATIBILITY_DEFINITION.baseline_evidence
]
RETURN_SEALED_FUTURE_OUTCOME = _COMPATIBILITY_DEFINITION.sealed_outcome.model_dump(mode="json")
RETURN_RESOLUTION_RULE = _COMPATIBILITY_DEFINITION.resolution_rule.model_dump(mode="json")


def return_episode_narrative() -> EpisodeNarrativeContract:
    return _COMPATIBILITY_DEFINITION.runtime.narrative


def return_episode_contract() -> DreamEpisodeContract:
    return _COMPATIBILITY_DEFINITION.runtime


def return_tree_organs(structure_fact_ref: str) -> dict[str, dict[str, Any]]:
    definition = return_episode_definition(structure_fact_ref)
    return {key: organ.model_dump(mode="json") for key, organ in definition.organ_set.items()}
