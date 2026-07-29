from __future__ import annotations

from abu_v60.provenance import canonical_json
from abu_v60.story import default_episode_source_registry


def main() -> None:
    registry = default_episode_source_registry()
    compilations = registry.compile_all(
        bindings={
            "structure_fact_ref": "v60-fact-episode-source-audit",
            "timing_vector_ref": "v60-timing-vector-episode-source-audit",
            "life_domain_vector_ref": "v60-life-domain-vector-episode-source-audit",
        },
    )
    print(
        canonical_json(
            {
                "status": "READY",
                "manifest": registry.public_manifest(),
                "compiled": [
                    {
                        "package_ref": item.package_ref,
                        "episode_ref": item.definition.runtime.episode_ref,
                        "question_ref": item.definition.runtime.question_ref,
                        "world_event_refs": [
                            event.world_event_ref
                            for event in item.world_event_definitions
                        ],
                    }
                    for item in compilations
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
