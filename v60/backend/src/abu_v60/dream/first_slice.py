from __future__ import annotations

from typing import Any

from abu_v60.game import (
    DreamEpisodeContract,
    DreamEpisodeDefinition,
    EpisodeNarrativeContract,
)
from abu_v60.story.packages import default_episode_source_registry

FIRST_PACKAGE_REF = "v60.episode-package.yanzhou-old-channel.v1"
_COMPATIBILITY_STRUCTURE_REF = "v60-fact-first-slice-compatibility-view"


def first_episode_definition(structure_fact_ref: str) -> DreamEpisodeDefinition:
    """Compatibility view over the canonical hash-locked source package."""

    return default_episode_source_registry().compile_definition(
        FIRST_PACKAGE_REF,
        bindings={"structure_fact_ref": structure_fact_ref},
    )


def _compatibility_definition() -> DreamEpisodeDefinition:
    return first_episode_definition(_COMPATIBILITY_STRUCTURE_REF)


_COMPATIBILITY_DEFINITION = _compatibility_definition()

FIRST_ACTOR_REF = _COMPATIBILITY_DEFINITION.actor_ref
FIRST_TREE_REF = _COMPATIBILITY_DEFINITION.tree_ref
FIRST_QUESTION_REF = _COMPATIBILITY_DEFINITION.runtime.question_ref
FIRST_EPISODE_REF = _COMPATIBILITY_DEFINITION.runtime.episode_ref
HISTORY_EVENT_REF = _COMPATIBILITY_DEFINITION.runtime.baseline_event_ref
FUTURE_EVENT_REF = _COMPATIBILITY_DEFINITION.runtime.world_event_ref
QUESTION_PROMPT = _COMPATIBILITY_DEFINITION.prompt
QUESTION_OPTIONS = [option.model_dump(mode="json") for option in _COMPATIBILITY_DEFINITION.options]
HISTORICAL_EVIDENCE = [dict(evidence) for evidence in _COMPATIBILITY_DEFINITION.baseline_evidence]
SEALED_FUTURE_OUTCOME = _COMPATIBILITY_DEFINITION.sealed_outcome.model_dump(mode="json")
FIRST_RESOLUTION_RULE = _COMPATIBILITY_DEFINITION.resolution_rule.model_dump(mode="json")


def first_episode_narrative() -> EpisodeNarrativeContract:
    return _COMPATIBILITY_DEFINITION.runtime.narrative


def first_episode_contract() -> DreamEpisodeContract:
    return _COMPATIBILITY_DEFINITION.runtime


def first_tree_organs(structure_fact_ref: str) -> dict[str, dict[str, Any]]:
    definition = first_episode_definition(structure_fact_ref)
    return {key: organ.model_dump(mode="json") for key, organ in definition.organ_set.items()}
