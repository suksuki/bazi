from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from abu_v60.dream.first_slice import (
    FIRST_ACTOR_REF,
    FIRST_RESOLUTION_RULE,
    FIRST_TREE_REF,
    HISTORICAL_EVIDENCE,
    QUESTION_OPTIONS,
    QUESTION_PROMPT,
    SEALED_FUTURE_OUTCOME,
    first_episode_contract,
    first_episode_definition,
    first_tree_organs,
)
from abu_v60.dream.return_slice import (
    RETURN_ACTOR_REF,
    RETURN_HISTORICAL_EVIDENCE,
    RETURN_QUESTION_OPTIONS,
    RETURN_QUESTION_PROMPT,
    RETURN_RESOLUTION_RULE,
    RETURN_SEALED_FUTURE_OUTCOME,
    RETURN_TREE_REF,
    return_episode_contract,
    return_episode_definition,
    return_tree_organs,
)
from abu_v60.game import DreamEpisodeDefinition
from abu_v60.provenance import content_hash
from abu_v60.story.packages import (
    EPISODE_SOURCE_REGISTRY_HASH,
    QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
    EpisodeSourcePackageError,
    EpisodeSourceRegistry,
    default_episode_source_registry,
    qualification_episode_source_registry,
)

CONTENT_ROOT = (
    Path(__file__).resolve().parents[2] / "content" / "dream" / "episodes"
)


def test_registry_and_packages_are_hash_locked() -> None:
    manifest = default_episode_source_registry().public_manifest()

    assert manifest == {
        "registry_version": "v60.episode-source-registry.002",
        "registry_hash": EPISODE_SOURCE_REGISTRY_HASH,
        "runtime_access": "ADMISSION_ONLY",
        "packages": [
            {
                "package_ref": "v60.episode-package.yanzhou-old-channel.v1",
                "package_hash": (
                    "39c72d431c94813c1404fd7d0a91eb4cdb53a9065e344e0350de68d33a28aaed"
                ),
                "binding_keys": ["structure_fact_ref"],
            },
            {
                "package_ref": "v60.episode-package.yanzhou-wet-bank.v1",
                "package_hash": (
                    "0e6b48db2daa791ab72e4b7309b11201b456bb1be8aecc5b1668ac31fa796bda"
                ),
                "binding_keys": ["structure_fact_ref"],
            },
            {
                "package_ref": (
                    "v60.episode-package.yanzhou-shared-night-water.v1"
                ),
                "package_hash": (
                    "72646d1c2ad45def33b726ce4dde3bded590e3581a08e15df10f7b6cd46c4888"
                ),
                "binding_keys": ["structure_fact_ref"],
            },
            {
                "package_ref": "v60.episode-package.yanzhou-water-record.v1",
                "package_hash": (
                    "7fd44db2922b1e5d486505458dbbd32f39cd7c87dd9ec4ca33595e1e77ea4361"
                ),
                "binding_keys": ["timing_vector_ref"],
            },
            {
                "package_ref": "v60.episode-package.yanzhou-roster-duty.v1",
                "package_hash": (
                    "87b9dd4f823dfca5ae17582a68a9490a0a72d0905e6b0ae697c4b8f3b9492921"
                ),
                "binding_keys": ["life_domain_vector_ref"],
            },
        ],
        "transitions": [
            {
                "transition_ref": "v60-episode-transition-cff6c9c680248cf9a1c4",
                "transition_hash": (
                    "3ec1f24bc48be37b8d9491a673e6c4c141c89313211fc01ee9d6fa195a9348a2"
                ),
                "from_package_ref": (
                    "v60.episode-package.yanzhou-old-channel.v1"
                ),
                "to_package_ref": "v60.episode-package.yanzhou-wet-bank.v1",
            },
            {
                "transition_ref": "v60-episode-transition-98228c9b6543be58f6ec",
                "transition_hash": (
                    "d4aab33c29a2f4604ee6e7ace6ebc944caed26999d542ec02a9af10623fda395"
                ),
                "from_package_ref": (
                    "v60.episode-package.yanzhou-wet-bank.v1"
                ),
                "to_package_ref": (
                    "v60.episode-package.yanzhou-shared-night-water.v1"
                ),
            },
            {
                "transition_ref": "v60-episode-transition-c3542deabecb97a76d25",
                "transition_hash": (
                    "ddd2cdbcf5473038d9411e70df4c83695035fca1fa13c307edd619e8e86ff2be"
                ),
                "from_package_ref": (
                    "v60.episode-package.yanzhou-shared-night-water.v1"
                ),
                "to_package_ref": "v60.episode-package.yanzhou-water-record.v1",
            },
            {
                "transition_ref": "v60-episode-transition-6e461f3019d35530687e",
                "transition_hash": (
                    "9b2ca87cbadcbb964a5f4ec176b166522084becd606b2c988e9519a634b04807"
                ),
                "from_package_ref": (
                    "v60.episode-package.yanzhou-water-record.v1"
                ),
                "to_package_ref": (
                    "v60.episode-package.yanzhou-roster-duty.v1"
                ),
            },
        ],
    }
    assert "prompt" not in json.dumps(manifest)
    assert "sealed_outcome" not in json.dumps(manifest)


def test_three_life_qualification_registry_is_hash_locked_and_public_safe() -> None:
    registry = qualification_episode_source_registry()
    manifest = registry.public_manifest()

    assert manifest["registry_hash"] == QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH
    assert manifest["runtime_access"] == "ADMISSION_ONLY"
    assert len(manifest["packages"]) == 3
    assert manifest["transitions"] == []
    assert {
        package["package_ref"] for package in manifest["packages"]
    } == {
        "v60.episode-package.wenxi-archive-trial.v1",
        "v60.episode-package.heyang-dyed-cloth.v1",
        "v60.episode-package.zhaoning-lantern-roster.v1",
    }
    serialized = json.dumps(manifest)
    assert "prompt" not in serialized
    assert "sealed_outcome" not in serialized

    compiled = (
        registry.compile_package(
            "v60.episode-package.wenxi-archive-trial.v1",
            bindings={
                "career_structure_fact_ref": "fact:career",
                "career_life_domain_vector_ref": "domain:career",
            },
        ),
        registry.compile_package(
            "v60.episode-package.heyang-dyed-cloth.v1",
            bindings={
                "wealth_structure_fact_ref": "fact:wealth",
                "wealth_life_domain_vector_ref": "domain:wealth",
            },
        ),
        registry.compile_package(
            "v60.episode-package.zhaoning-lantern-roster.v1",
            bindings={
                "relationship_structure_fact_ref": "fact:relationship",
                "relationship_life_domain_vector_ref": "domain:relationship",
            },
        ),
    )
    assert len({item.definition.actor_ref for item in compiled}) == 3
    assert len({item.definition.tree_ref for item in compiled}) == 3
    assert all(item.definition.runtime.entrypoint for item in compiled)


def test_first_episode_package_preserves_existing_contract() -> None:
    structure_ref = "v60-fact-structure-package-test"
    expected = DreamEpisodeDefinition(
        runtime=first_episode_contract(),
        actor_ref=FIRST_ACTOR_REF,
        tree_ref=FIRST_TREE_REF,
        question_version=1,
        prompt=QUESTION_PROMPT,
        options=QUESTION_OPTIONS,
        baseline_evidence=HISTORICAL_EVIDENCE,
        resolution_rule=FIRST_RESOLUTION_RULE,
        sealed_outcome=SEALED_FUTURE_OUTCOME,
        world_event_type="CHANNEL_SUPPORT_OUTCOME",
        world_event_summary="观察旧水渠恢复后是否持续支持坡下根系。",
        organ_set=first_tree_organs(structure_ref),
    )

    assert first_episode_definition(structure_ref) == expected


def test_return_episode_package_preserves_existing_contract() -> None:
    structure_ref = "v60-fact-structure-package-test"
    expected = DreamEpisodeDefinition(
        runtime=return_episode_contract(),
        actor_ref=RETURN_ACTOR_REF,
        tree_ref=RETURN_TREE_REF,
        question_version=1,
        prompt=RETURN_QUESTION_PROMPT,
        options=RETURN_QUESTION_OPTIONS,
        baseline_evidence=RETURN_HISTORICAL_EVIDENCE,
        resolution_rule=RETURN_RESOLUTION_RULE,
        sealed_outcome=RETURN_SEALED_FUTURE_OUTCOME,
        world_event_type="WET_BANK_ROOT_SPREAD",
        world_event_summary="观察松开一块挡水石后，新细根是否扩大支持范围。",
        organ_set=return_tree_organs(structure_ref),
    )

    assert return_episode_definition(structure_ref) == expected


def test_package_compilation_is_deterministic() -> None:
    registry = default_episode_source_registry()
    bindings = {"structure_fact_ref": "v60-fact-structure-deterministic"}

    first = registry.compile_definition(
        "v60.episode-package.yanzhou-old-channel.v1",
        bindings=bindings,
    )
    second = registry.compile_definition(
        "v60.episode-package.yanzhou-old-channel.v1",
        bindings=bindings,
    )

    assert first == second
    assert content_hash(first.model_dump(mode="json")) == content_hash(
        second.model_dump(mode="json")
    )


def test_package_compilation_binds_world_events_and_transition_graph() -> None:
    registry = default_episode_source_registry()
    first = registry.compile_package(
        "v60.episode-package.yanzhou-old-channel.v1",
        bindings={"structure_fact_ref": "v60-fact-structure-world-bindings"},
    )
    returning = registry.compile_package(
        "v60.episode-package.yanzhou-wet-bank.v1",
        bindings={"structure_fact_ref": "v60-fact-structure-world-bindings"},
    )
    shared_night_water = registry.compile_package(
        "v60.episode-package.yanzhou-shared-night-water.v1",
        bindings={"structure_fact_ref": "v60-fact-structure-world-bindings"},
    )
    water_record = registry.compile_package(
        "v60.episode-package.yanzhou-water-record.v1",
        bindings={"timing_vector_ref": "v60-timing-vector-world-bindings"},
    )
    roster_duty = registry.compile_package(
        "v60.episode-package.yanzhou-roster-duty.v1",
        bindings={
            "life_domain_vector_ref": "v60-life-domain-vector-world-bindings"
        },
    )

    assert {
        event.world_event_ref for event in first.world_event_definitions
    } == {
        first.definition.runtime.baseline_event_ref,
        first.definition.runtime.world_event_ref,
    }
    assert {
        event.world_event_ref for event in returning.world_event_definitions
    } == {returning.definition.runtime.world_event_ref}
    assert {
        event.world_event_ref
        for event in shared_night_water.world_event_definitions
    } == {shared_night_water.definition.runtime.world_event_ref}
    assert {
        event.world_event_ref for event in water_record.world_event_definitions
    } == {water_record.definition.runtime.world_event_ref}
    assert {
        event.world_event_ref for event in roster_duty.world_event_definitions
    } == {roster_duty.definition.runtime.world_event_ref}
    (
        first_transition,
        second_transition,
        third_transition,
        fourth_transition,
    ) = registry.transitions()
    assert (
        first_transition.from_question_ref
        == first.definition.runtime.question_ref
    )
    assert (
        first_transition.to_question_ref
        == returning.definition.runtime.question_ref
    )
    assert (
        second_transition.from_question_ref
        == returning.definition.runtime.question_ref
    )
    assert (
        second_transition.to_question_ref
        == shared_night_water.definition.runtime.question_ref
    )
    assert (
        third_transition.from_question_ref
        == shared_night_water.definition.runtime.question_ref
    )
    assert (
        third_transition.to_question_ref
        == water_record.definition.runtime.question_ref
    )
    assert (
        fourth_transition.from_question_ref
        == water_record.definition.runtime.question_ref
    )
    assert (
        fourth_transition.to_question_ref
        == roster_duty.definition.runtime.question_ref
    )
    assert water_record.definition.runtime.continuation_question_ref is None
    assert returning.definition.runtime.continuation_question_ref is None


@pytest.mark.parametrize(
    "bindings",
    (
        {},
        {
            "structure_fact_ref": "v60-fact-structure-test",
            "unexpected": "forbidden",
        },
    ),
)
def test_package_compilation_rejects_inexact_bindings(
    bindings: dict[str, str],
) -> None:
    with pytest.raises(
        EpisodeSourcePackageError,
        match="episode_source_bindings_invalid",
    ):
        default_episode_source_registry().compile_definition(
            "v60.episode-package.yanzhou-old-channel.v1",
            bindings=bindings,
        )


def test_package_compilation_rejects_unknown_package() -> None:
    with pytest.raises(EpisodeSourcePackageError, match="package_unknown"):
        default_episode_source_registry().compile_definition(
            "v60.episode-package.unknown.v1",
            bindings={"structure_fact_ref": "v60-fact-structure-test"},
        )


def test_registry_rejects_tampered_package(tmp_path: Path) -> None:
    copied_root = tmp_path / "episodes"
    shutil.copytree(CONTENT_ROOT, copied_root)
    package_path = copied_root / "yanzhou-old-channel-v1.json"
    payload = json.loads(package_path.read_text(encoding="utf-8"))
    payload["definition_template"]["prompt"] = "tampered"
    package_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EpisodeSourcePackageError, match="package_hash_mismatch"):
        EpisodeSourceRegistry(
            root=copied_root,
            expected_registry_hash=EPISODE_SOURCE_REGISTRY_HASH,
        )


def test_compiler_rejects_world_event_drift_even_with_rehashed_source(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "episodes"
    shutil.copytree(CONTENT_ROOT, copied_root)
    package_path = copied_root / "yanzhou-old-channel-v1.json"
    package_payload = json.loads(package_path.read_text(encoding="utf-8"))
    scheduled_event = next(
        event
        for event in package_payload["world_event_definitions"]
        if event["initial_status"] == "SCHEDULED"
    )
    scheduled_event["due_tick"] += 1
    package_path.write_text(json.dumps(package_payload), encoding="utf-8")

    registry_path = copied_root / "registry.json"
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_payload["packages"][0]["package_hash"] = content_hash(package_payload)
    registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")
    registry = EpisodeSourceRegistry(
        root=copied_root,
        expected_registry_hash=content_hash(registry_payload),
    )

    with pytest.raises(
        EpisodeSourcePackageError,
        match="future_world_event_mismatch",
    ):
        registry.compile_package(
            "v60.episode-package.yanzhou-old-channel.v1",
            bindings={"structure_fact_ref": "v60-fact-structure-test"},
        )


def test_registry_rejects_transition_semantic_drift(tmp_path: Path) -> None:
    copied_root = tmp_path / "episodes"
    shutil.copytree(CONTENT_ROOT, copied_root)
    registry_path = copied_root / "registry.json"
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_payload["transitions"][0]["definition"]["label"] = "drifted"
    registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

    with pytest.raises(
        EpisodeSourcePackageError,
        match="transition_binding_mismatch",
    ):
        EpisodeSourceRegistry(
            root=copied_root,
            expected_registry_hash=content_hash(registry_payload),
        )


def test_registry_rejects_path_escape_before_reading_package(tmp_path: Path) -> None:
    registry_payload = {
        "registry_version": "v60.episode-source-registry.002",
        "packages": [
            {
                "package_ref": "v60.episode-package.escape.v1",
                "path": "../escape.json",
                "package_hash": "0" * 64,
            }
        ],
        "transitions": [],
    }
    (tmp_path / "registry.json").write_text(
        json.dumps(registry_payload),
        encoding="utf-8",
    )

    with pytest.raises(EpisodeSourcePackageError, match="package_path_invalid"):
        EpisodeSourceRegistry(
            root=tmp_path,
            expected_registry_hash=content_hash(registry_payload),
        )


def test_legacy_python_exporter_cannot_overwrite_canonical_packages() -> None:
    tools_root = Path(__file__).resolve().parents[2] / "tools"

    assert not (tools_root / "export_episode_source_packages.py").exists()
    audit_source = (tools_root / "audit_episode_source_packages.py").read_text(
        encoding="utf-8"
    )
    assert "write_text" not in audit_source
    assert "first_slice" not in audit_source
    assert "return_slice" not in audit_source


def test_legacy_episode_modules_are_registry_backed_compatibility_views() -> None:
    dream_root = (
        Path(__file__).resolve().parents[1] / "src" / "abu_v60" / "dream"
    )

    for filename in ("first_slice.py", "return_slice.py"):
        source = (dream_root / filename).read_text(encoding="utf-8")
        assert "default_episode_source_registry().compile_definition" in source
        assert not any("\u4e00" <= character <= "\u9fff" for character in source)


def test_seed_navigation_uses_registry_transitions() -> None:
    seed_source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "abu_v60"
        / "dream"
        / "seed.py"
    ).read_text(encoding="utf-8")

    assert "source_registry.transitions()" in seed_source
    assert "first_episode.runtime.continuation_question_ref" not in seed_source
