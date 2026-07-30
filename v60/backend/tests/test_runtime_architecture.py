from pathlib import Path

from abu_v60.architecture import runtime_architecture
from abu_v60.system_manifest import runtime_manifest


def test_runtime_architecture_has_one_owner_per_schema_and_five_units() -> None:
    architecture = runtime_architecture()
    architecture.validate_boundaries()
    assert architecture.architecture_version == "v60.runtime-architecture.051"
    assert architecture.product_units == (
        "unit-mingli",
        "unit-dream",
        "unit-lab",
        "unit-abu",
        "unit-theater",
    )
    assert architecture.product_core == "unit-mingli"
    assert architecture.priority_breakthrough == "unit-dream"
    assert [item.unit_id for item in architecture.unit_placements] == [
        "unit-mingli",
        "unit-dream",
        "unit-lab",
        "unit-abu",
        "unit-theater",
    ]
    owners = {
        schema: module.module_id
        for module in architecture.modules
        for schema in module.owns_schemas
    }
    assert owners == {
        "identity": "identity",
        "mingli": "mingli",
        "cognition": "cognition",
        "world": "world",
        "story": "story",
        "dream": "dream-game",
        "media": "media",
        "platform": "migration",
    }


def test_product_units_are_projection_or_command_surfaces_not_fact_owners() -> None:
    architecture = runtime_architecture()
    units = {
        module.module_id: module
        for module in architecture.modules
        if module.module_id in architecture.product_units
    }
    assert all(not unit.owns_schemas for unit in units.values())
    assert all(not unit.writes_canonical_state for unit in units.values())


def test_manifest_exposes_world_game_and_localization_reservation() -> None:
    manifest = runtime_manifest()
    assert manifest["engines"]["decision"] == "v60.cognitive-decision-kernel.004"
    assert manifest["engines"]["context"] == "v60.experience-context.003"
    assert manifest["engines"]["game"] == "v60.dream-game-engine.018"
    assert manifest["engines"]["world"] == "v60.world-continuity-engine.004"
    assert manifest["engines"]["mingli"] == "v60.mingli-cognitive-engine.025"
    assert manifest["engines"]["story"] == "v60.life-story-engine.011"
    source_review = manifest["source_review_profiles"]
    assert len(source_review) == 1
    assert source_review[0]["active"] is True
    assert source_review[0]["professionally_reviewed"] is False
    assert source_review[0]["profile_hash"] == (
        "e21e13ff2f79dbd4c180b34ee651996c30a0ac545931d3ce95d1b96a6a5b145c"
    )
    relation_effect_admission = manifest["relation_effect_rule_admission"]
    assert relation_effect_admission["professional_rule_count"] == 0
    assert relation_effect_admission["admitted_effect_rule_profiles"] == []
    assert relation_effect_admission["runtime_effect_authority"] == "NONE"
    assert (
        relation_effect_admission["policy"]["runtime_scope"]
        == "RELATION_EFFECT_RULE_PREFLIGHT"
    )
    assert (
        relation_effect_admission["policy"]["effect_conclusion_allowed"]
        is False
    )
    assert (
        relation_effect_admission["proposal"]["professionally_reviewed"]
        is False
    )
    assert relation_effect_admission["proposal"]["research_only"] is True
    sources = manifest["episode_source_packages"]
    assert sources["canonical_story"]["runtime_access"] == "ADMISSION_ONLY"
    assert len(sources["canonical_story"]["packages"]) == 5
    assert len(sources["canonical_story"]["transitions"]) == 4
    assert sources["three_life_qualification"]["runtime_access"] == "ADMISSION_ONLY"
    assert (
        sources["three_life_qualification"]["registry_version"]
        == "v60.episode-source-registry.003"
    )
    assert len(sources["three_life_qualification"]["packages"]) == 5
    assert len(sources["three_life_qualification"]["transitions"]) == 2
    assert manifest["architecture"]["localization_status"] == "RESERVED"
    assert manifest["architecture"]["default_locale"] == "zh-CN"
    assert manifest["reasoner_runtime"] == {
        "runtime_ref": "v60.bounded-reasoner-runtime.002",
        "status": "NOT_CONFIGURED",
        "provider": None,
        "model_ref": None,
        "prompt_ref": "v60.prompt.compare-qualified-candidates.001",
        "model_profile": None,
        "network_calls_enabled": False,
        "structured_output_required": True,
        "canonical_domain_write_allowed": False,
    }


def test_lab_candidate_projection_is_read_only_and_owned_by_mingli() -> None:
    architecture = runtime_architecture()
    modules = {module.module_id: module for module in architecture.modules}

    assert modules["mingli"].version == "v60.mingli-cognitive-engine.025"
    assert modules["knowledge"].version == "v60.knowledge-authority.008"
    assert modules["unit-mingli"].version == "v60.unit-mingli.019"
    assert modules["unit-abu"].version == "v60.unit-abu-says.007"
    assert modules["unit-lab"].version == "v60.unit-lab.016"
    assert modules["unit-dream"].version == "v60.unit-dream.019"
    assert "structural_candidate_projection" in modules["mingli"].capabilities
    assert "candidate_qualification_receipt" in modules["mingli"].capabilities
    assert "versioned_reading_envelope" in modules["mingli"].capabilities
    assert "profile_driven_fact_compilation" in modules["mingli"].capabilities
    assert "append_only_reading_history" in modules["mingli"].capabilities
    assert "profile_pinned_reading_replay" in modules["mingli"].capabilities
    assert "deterministic_quant_foundation_vector" in modules["mingli"].capabilities
    assert "append_only_quant_vector_history" in modules["mingli"].capabilities
    assert "ten_god_occurrence_matrix" in modules["mingli"].capabilities
    assert "source_manifestation_evidence_projection" in modules["mingli"].capabilities
    assert "bounded_source_coordinate_relation_review" in modules["mingli"].capabilities
    assert "append_only_source_coordinate_review_history" in modules["mingli"].capabilities
    assert "mechanism_candidate_evidence_vector" in modules["mingli"].capabilities
    assert "append_only_mechanism_vector_history" in modules["mingli"].capabilities
    assert "bounded_life_domain_evidence_projection" in modules["mingli"].capabilities
    assert "append_only_life_domain_vector_history" in modules["mingli"].capabilities
    assert "bounded_mechanism_attention_comparison" in modules["mingli"].capabilities
    assert "owner_case_intake" in modules["mingli"].capabilities
    assert "single_active_owner_case_selection" in modules["mingli"].capabilities
    assert "formal_bounded_reading_summary" in modules["mingli"].capabilities
    assert "versioned_evidence_explanation_projection" in modules["mingli"].capabilities
    assert "support_counter_unknown_separation" in modules["mingli"].capabilities
    assert "versioned_mechanism_qualification_projection" in modules["mingli"].capabilities
    assert "evidence_gap_and_falsifier_matrix" in modules["mingli"].capabilities
    assert "versioned_candidate_evidence_depth_projection" in modules["mingli"].capabilities
    assert "carrier_source_timing_competition_contrast" in modules["mingli"].capabilities
    assert (
        "versioned_source_usability_prerequisite_projection"
        in modules["mingli"].capabilities
    )
    assert "source_scope_competition_and_evidence_gaps" in modules["mingli"].capabilities
    assert (
        "verified_attention_decision_trace_projection"
        in modules["mingli"].capabilities
    )
    assert (
        "versioned_source_discussion_abstention_receipt"
        in modules["mingli"].capabilities
    )
    assert (
        "professional_rule_chain_fail_closed_abstention"
        in modules["mingli"].capabilities
    )
    assert (
        "versioned_relation_effect_research_frontier"
        in modules["mingli"].capabilities
    )
    assert (
        "scope_dependency_rule_demand_classification"
        in modules["mingli"].capabilities
    )
    assert (
        "versioned_relation_effect_rule_admission_review"
        in modules["mingli"].capabilities
    )
    assert (
        "shortcut_pre_admission_rejection"
        in modules["mingli"].capabilities
    )
    assert (
        "competing_relation_interpretation_hold"
        in modules["mingli"].capabilities
    )
    assert (
        "versioned_relation_effect_evidence_packet"
        in modules["mingli"].capabilities
    )
    assert (
        "professional_evidence_readiness_projection"
        in modules["mingli"].capabilities
    )
    assert (
        "relation_effect_decision_path_withheld"
        in modules["mingli"].capabilities
    )
    assert (
        "append_only_relation_effect_evidence_request_receipt"
        in modules["mingli"].capabilities
    )
    assert (
        "account_private_evidence_preparation_request"
        in modules["mingli"].capabilities
    )
    assert (
        "server_derived_evidence_request_items"
        in modules["mingli"].capabilities
    )
    assert (
        "append_only_relation_effect_candidate_material"
        in modules["mingli"].capabilities
    )
    assert (
        "account_private_structured_bibliography_candidate"
        in modules["mingli"].capabilities
    )
    assert (
        "candidate_material_not_professional_evidence"
        in modules["mingli"].capabilities
    )
    assert "explicit_active_profile_selection" in modules["knowledge"].capabilities
    assert "hash_locked_quant_foundation_profile" in modules["knowledge"].capabilities
    assert "hash_locked_source_coordinate_review_profile" in modules["knowledge"].capabilities
    assert "hash_locked_mechanism_evidence_profile" in modules["knowledge"].capabilities
    assert (
        "hash_locked_relation_effect_admission_policy"
        in modules["knowledge"].capabilities
    )
    assert (
        "hash_locked_unadmitted_rule_proposal"
        in modules["knowledge"].capabilities
    )
    assert (
        "empty_professional_effect_rule_registry"
        in modules["knowledge"].capabilities
    )
    assert "candidate_path_projection" in modules["unit-lab"].capabilities
    assert "qualification_trace" in modules["unit-lab"].capabilities
    assert "shared_reading_identity" in modules["unit-lab"].capabilities
    assert "shared_explanation_claim_inspection" in modules["unit-lab"].capabilities
    assert "native_abu_expression" in modules["unit-mingli"].capabilities
    assert "owner_case_intake_and_switching" in modules["unit-mingli"].capabilities
    assert "inspectable_support_and_boundaries" in modules["unit-mingli"].capabilities
    assert "candidate_evidence_completeness" in modules["unit-mingli"].capabilities
    assert "candidate_evidence_contrast" in modules["unit-mingli"].capabilities
    assert "source_coordinate_review_summary" in modules["unit-mingli"].capabilities
    assert "source_usability_prerequisite_summary" in modules["unit-mingli"].capabilities
    assert (
        "shared_attention_decision_trace_summary"
        in modules["unit-mingli"].capabilities
    )
    assert (
        "source_discussion_abstention_summary"
        in modules["unit-mingli"].capabilities
    )
    assert (
        "relation_effect_research_frontier_summary"
        in modules["unit-mingli"].capabilities
    )
    assert (
        "relation_effect_shortcut_rejection_summary"
        in modules["unit-mingli"].capabilities
    )
    assert (
        "relation_effect_evidence_readiness_summary"
        in modules["unit-mingli"].capabilities
    )
    assert (
        "relation_effect_evidence_preparation_request"
        in modules["unit-mingli"].capabilities
    )
    assert "return_to_grove_after_reconciliation" in modules["unit-dream"].capabilities
    assert "pre_outcome_question_basis" in modules["unit-dream"].capabilities
    assert "read_only_reading_observation_lens" in modules["unit-dream"].capabilities
    assert (
        "reading_lens_no_tree_candidate_or_order_mutation"
        in modules["unit-dream"].capabilities
    )
    assert (
        "reading_lens_encounter_continuity"
        in modules["unit-dream"].capabilities
    )
    assert (
        "dream_outcome_not_owner_mingli_evidence"
        in modules["unit-dream"].capabilities
    )
    assert "repeatable_grove_cycle" in modules["dream-game"].capabilities
    assert (
        "completed_history_resurrection_guard"
        in modules["dream-game"].capabilities
    )
    assert (
        "account_private_return_echo_projection"
        in modules["dream-game"].capabilities
    )
    assert (
        "return_echo_committed_source_validation"
        in modules["dream-game"].capabilities
    )
    assert (
        "multi_tree_canonical_chapter_frontiers"
        in modules["dream-game"].capabilities
    )
    assert (
        "append_only_return_attention_selection"
        in modules["dream-game"].capabilities
    )
    assert (
        "same_tree_attention_application"
        in modules["dream-game"].capabilities
    )
    assert (
        "return_attention_not_owner_evidence"
        in modules["dream-game"].capabilities
    )
    assert (
        "pending_return_attention_projection"
        in modules["dream-game"].capabilities
    )
    assert (
        "source_echo_revalidated_attention_lineage"
        in modules["dream-game"].capabilities
    )
    assert (
        "read_only_attention_follow_through"
        in modules["dream-game"].capabilities
    )
    assert (
        "account_history_grove_chapter_routing"
        in modules["dream-game"].capabilities
    )
    assert (
        "canonical_graph_route_authority"
        in modules["dream-game"].capabilities
    )
    assert (
        "continuation_opportunity_root_materialization"
        in modules["dream-game"].capabilities
    )
    assert (
        "attention_independent_chapter_routing"
        in modules["dream-game"].capabilities
    )
    assert "terminal_chapter_wait" in modules["dream-game"].capabilities
    assert "grove_return_echo" in modules["unit-dream"].capabilities
    assert "grove_return_attention_choice" in modules["unit-dream"].capabilities
    assert "same_tree_opening_attention" in modules["unit-dream"].capabilities
    assert "grove_pending_attention_marker" in modules["unit-dream"].capabilities
    assert (
        "full_phase_attention_follow_through"
        in modules["unit-dream"].capabilities
    )
    assert (
        "post_reveal_attention_material_contrast"
        in modules["unit-dream"].capabilities
    )
    assert "same_tree_new_chapter_preview" in modules["unit-dream"].capabilities
    assert (
        "attention_independent_chapter_entry"
        in modules["unit-dream"].capabilities
    )
    assert "terminal_story_wait_state" in modules["unit-dream"].capabilities
    assert (
        "focusable_terminal_chapter_state"
        in modules["unit-dream"].capabilities
    )
    assert (
        "multiple_same_tree_story_chains"
        in modules["unit-dream"].capabilities
    )
    assert "mingli_reading_expression" in modules["unit-abu"].capabilities
    assert "shared_mingli_explanation_identity" in modules["unit-abu"].capabilities
    assert "shared_mechanism_qualification_identity" in modules["unit-abu"].capabilities
    assert "mechanism_requirement_matrix" in modules["unit-lab"].capabilities
    assert "role_source_timing_competition_inspection" in modules["unit-lab"].capabilities
    assert (
        "source_coordinate_relation_intersection_inspection"
        in modules["unit-lab"].capabilities
    )
    assert "source_scope_competition_inspection" in modules["unit-lab"].capabilities
    assert (
        "decision_gate_and_evidence_scope_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "source_discussion_receipt_lineage_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "relation_effect_rule_demand_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "relation_effect_preflight_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "competing_relation_interpretation_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "relation_effect_evidence_packet_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "runtime_basis_professional_evidence_separation"
        in modules["unit-lab"].capabilities
    )
    assert (
        "relation_effect_evidence_request_receipt_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "relation_effect_candidate_material_inspection"
        in modules["unit-lab"].capabilities
    )
    assert (
        "same_reading_decision_trace_handoff"
        in modules["unit-abu"].capabilities
    )
    assert (
        "same_source_discussion_abstention_handoff"
        in modules["unit-abu"].capabilities
    )
    assert modules["unit-lab"].writes_canonical_state is False
    assert modules["unit-lab"].owns_schemas == ()


def test_product_units_share_one_validated_experience_context() -> None:
    architecture = runtime_architecture()
    modules = {module.module_id: module for module in architecture.modules}

    context = modules["experience-context"]
    assert context.owns_schemas == ()
    assert context.writes_canonical_state is False
    assert "single_lineage_context" in context.capabilities
    assert "cutoff_evidence_guard" in context.capabilities
    assert "narrative_phase_alignment" in context.capabilities
    assert all(
        "experience-context" in modules[unit_id].reads_from
        for unit_id in architecture.product_units
    )


def test_story_owns_hash_locked_episode_source_packages() -> None:
    architecture = runtime_architecture()
    modules = {module.module_id: module for module in architecture.modules}

    assert "hash_locked_episode_source_packages" in modules["story"].capabilities
    assert "source_bound_world_event_definitions" in modules["story"].capabilities
    assert "source_bound_episode_graph" in modules["story"].capabilities
    assert (
        "multiple_candidate_continuation_graphs"
        in modules["story"].capabilities
    )
    assert modules["story"].writes_canonical_state is True


def test_dream_game_has_one_versioned_command_api() -> None:
    architecture = runtime_architecture()
    modules = {module.module_id: module for module in architecture.modules}
    dream = modules["dream-game"]
    assert {
        "optimistic_command_envelope",
        "single_command_endpoint",
        "semantic_command_replay",
        "immutable_command_receipt",
        "world_owned_waiting",
        "episode_scoped_public_projection",
        "mutable_canonical_state_exclusion",
    }.issubset(dream.capabilities)

    api_source = (
        Path(__file__).resolve().parents[1] / "src" / "abu_v60" / "api" / "dream.py"
    ).read_text(encoding="utf-8")
    assert '@router.post("/command")' in api_source
    assert '@router.post("/answer")' not in api_source
    assert '@router.post("/advance-world")' not in api_source
    assert '@router.post("/reveal")' not in api_source


def test_world_runtime_writes_are_owned_by_world_engine() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    allowed = {
        source_root / "world" / "actor_admission.py",
        source_root / "world" / "admission.py",
        source_root / "world" / "service.py",
    }
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        if path in allowed:
            continue
        source = path.read_text(encoding="utf-8")
        if any(
            statement in source
            for statement in (
                "INSERT INTO world.",
                "UPDATE world.",
                "DELETE FROM world.",
            )
        ):
            offenders.append(str(path.relative_to(source_root)))
    assert offenders == []


def test_bootstrap_writes_route_through_each_schema_owner() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    allowed_by_schema = {
        "platform": {source_root / "migration" / "admission.py"},
        "identity": {
            source_root / "identity" / "admission.py",
            source_root / "identity" / "service.py",
        },
        "mingli": {
            source_root / "mingli" / "admission.py",
            source_root / "mingli" / "corpus.py",
            source_root / "mingli" / "domain_store.py",
            source_root / "mingli" / "mechanism_store.py",
            source_root / "mingli" / "quant_store.py",
            source_root / "mingli" / "reading_store.py",
            source_root / "mingli" / "relation_effect_material.py",
            source_root / "mingli" / "relation_effect_request.py",
            source_root / "mingli" / "source_review_store.py",
            source_root / "mingli" / "timing_store.py",
        },
        "dream": {
            source_root / "dream" / "grove.py",
            source_root / "dream" / "outcomes.py",
                source_root / "dream" / "persistence.py",
                source_root / "dream" / "return_attention.py",
                source_root / "dream" / "service.py",
            source_root / "dream" / "tree_admission.py",
        },
    }
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for schema, allowed in allowed_by_schema.items():
            if path in allowed:
                continue
            if any(
                statement in source
                for statement in (
                    f"INSERT INTO {schema}.",
                    f"UPDATE {schema}.",
                    f"DELETE FROM {schema}.",
                )
            ):
                offenders.append(f"{schema}:{path.relative_to(source_root)}")
    assert offenders == []


def test_world_event_writes_are_owned_by_world_admission_and_continuity() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    allowed = {
        source_root / "world" / "admission.py",
        source_root / "world" / "service.py",
    }
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        if path in allowed:
            continue
        source = path.read_text(encoding="utf-8")
        if any(
            statement in source
            for statement in (
                "INSERT INTO world.events",
                "UPDATE world.events",
                "DELETE FROM world.events",
                "INSERT INTO world.event_evidence",
                "UPDATE world.event_evidence",
                "DELETE FROM world.event_evidence",
            )
        ):
            offenders.append(str(path.relative_to(source_root)))
    assert offenders == []


def test_cognition_runtime_writes_are_owned_by_decision_ledger() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    allowed = {source_root / "decision" / "service.py"}
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        if path in allowed:
            continue
        source = path.read_text(encoding="utf-8")
        if any(
            statement in source
            for statement in (
                "INSERT INTO cognition.",
                "UPDATE cognition.",
                "DELETE FROM cognition.",
            )
        ):
            offenders.append(str(path.relative_to(source_root)))
    assert offenders == []


def test_story_runtime_writes_are_owned_by_episode_admission() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    allowed = {source_root / "story" / "admission.py"}
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        if path in allowed:
            continue
        source = path.read_text(encoding="utf-8")
        if any(
            statement in source
            for statement in (
                "INSERT INTO story.",
                "UPDATE story.",
                "DELETE FROM story.",
            )
        ):
            offenders.append(str(path.relative_to(source_root)))
    assert offenders == []
