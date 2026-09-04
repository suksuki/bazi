from __future__ import annotations

from functools import lru_cache

from abu_v60.architecture.contracts import (
    ModuleKind,
    ModuleStatus,
    ProductUnitPlacement,
    ProductUnitRole,
    RuntimeArchitecture,
    RuntimeModule,
)


@lru_cache(maxsize=1)
def runtime_architecture() -> RuntimeArchitecture:
    """Return the full V60 runtime after the product reduction.

    The research LAB remains an internal unit because it trains and audits the
    local Mingli system. It is intentionally absent from the public entry flow.
    """

    architecture = RuntimeArchitecture(
        architecture_version="v60.runtime-architecture.081",
        modules=(
            RuntimeModule(
                module_id="identity",
                kind=ModuleKind.AUTHORITY,
                version="v60.identity.002",
                status=ModuleStatus.ACTIVE,
                owns_schemas=("identity",),
                capabilities=(
                    "account_session",
                    "profile_consent",
                    "idempotent_identity_admission",
                ),
                writes_canonical_state=True,
            ),
            RuntimeModule(
                module_id="mingli",
                kind=ModuleKind.ENGINE,
                version="v60.mingli-cognitive-engine.051",
                status=ModuleStatus.ACTIVE,
                owns_schemas=("mingli",),
                reads_from=("identity",),
                capabilities=(
                    "deterministic_chart",
                    "typed_fact_projection",
                    "versioned_reading_envelope",
                    "formal_bounded_reading_summary",
                    "dayun_year_month_evidence_projection",
                    "single_specialist_agent_case_packet",
                    "one_call_whole_chart_agent_interpretation",
                    "deterministic_reading_claim_graph",
                    "progressive_one_focus_reading",
                    "three_pass_dev_method_distillation",
                    "append_only_synthetic_distillation_history",
                ),
                writes_canonical_state=True,
            ),
            RuntimeModule(
                module_id="knowledge",
                kind=ModuleKind.AUTHORITY,
                version="v60.knowledge-authority.008",
                status=ModuleStatus.BOUNDED,
                capabilities=(
                    "versioned_rule_profile_refs",
                    "hash_locked_profile_registry",
                    "professional_gate_boundary",
                    "explicit_active_profile_selection",
                ),
            ),
            RuntimeModule(
                module_id="cognition",
                kind=ModuleKind.ENGINE,
                version="v60.cognitive-decision-kernel.004",
                status=ModuleStatus.ACTIVE,
                owns_schemas=("cognition",),
                reads_from=("mingli", "knowledge"),
                capabilities=(
                    "authority_routing",
                    "bounded_reasoner_proposal",
                    "epistemic_gate",
                    "immutable_decision_record",
                ),
                writes_canonical_state=True,
            ),
            RuntimeModule(
                module_id="media",
                kind=ModuleKind.PLATFORM,
                version="v60.media-library.006",
                status=ModuleStatus.ACTIVE,
                owns_schemas=("media",),
                reads_from=("identity", "mingli"),
                capabilities=(
                    "hash_locked_assets",
                    "runtime_cue_resolution",
                    "private_mingli_narration_asset",
                    "server_side_qwen3_tts_adapter",
                    "sentence_clause_subtitle_timeline",
                    "six_pillar_particle_focus_sync",
                ),
                writes_canonical_state=True,
            ),
            RuntimeModule(
                module_id="migration",
                kind=ModuleKind.PLATFORM,
                version="v60.migration-boundary.003",
                status=ModuleStatus.ACTIVE,
                owns_schemas=("platform",),
                reads_from=("identity", "mingli", "media"),
                capabilities=(
                    "manifested_import",
                    "immutable_batch_admission",
                    "v50_runtime_isolation",
                    "removed_runtime_data_boundary",
                ),
                writes_canonical_state=True,
            ),
            RuntimeModule(
                module_id="unit-mingli",
                kind=ModuleKind.PRODUCT_UNIT,
                version="v60.unit-mingli.039",
                status=ModuleStatus.ACTIVE,
                reads_from=("mingli", "media"),
                capabilities=(
                    "formal_chart_workspace",
                    "progressive_focused_reading",
                    "four_six_pillar_stage",
                    "owner_review_initial_reading",
                ),
            ),
            RuntimeModule(
                module_id="unit-abu",
                kind=ModuleKind.PRODUCT_UNIT,
                version="v60.unit-abu-says.009",
                status=ModuleStatus.ACTIVE,
                reads_from=("mingli", "media"),
                capabilities=(
                    "same_reading_expression",
                    "lazy_focused_speech",
                    "subtitle_synchronized_six_pillar_animation",
                ),
            ),
            RuntimeModule(
                module_id="unit-lab",
                kind=ModuleKind.PRODUCT_UNIT,
                version="v60.unit-lab.037",
                status=ModuleStatus.BOUNDED,
                reads_from=("knowledge", "cognition", "mingli"),
                capabilities=(
                    "internal_synthetic_method_lab",
                    "controlled_synthetic_ab_comparison",
                    "recoverable_training_progress",
                    "append_only_run_history_discovery",
                ),
            ),
        ),
        product_units=("unit-mingli", "unit-abu", "unit-lab"),
        product_core="unit-mingli",
        priority_breakthrough="unit-abu",
        unit_placements=(
            ProductUnitPlacement(
                unit_id="unit-mingli",
                priority=1,
                role=ProductUnitRole.CORE_TRUTH_PRODUCT,
                boundary="Owns reproducible chart calculation and bounded reading truth.",
            ),
            ProductUnitPlacement(
                unit_id="unit-abu",
                priority=2,
                role=ProductUnitRole.NATIVE_EXPRESSION_LAYER,
                boundary="Expresses the persisted reading without performing a second reading.",
            ),
            ProductUnitPlacement(
                unit_id="unit-lab",
                priority=3,
                role=ProductUnitRole.RESEARCH_IMPROVEMENT_LOOP,
                boundary="Internal-only evaluation and distillation; never a public route.",
            ),
        ),
    )
    architecture.validate_boundaries()
    return architecture
