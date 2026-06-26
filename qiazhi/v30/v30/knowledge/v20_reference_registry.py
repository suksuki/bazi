from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model


V20_REFERENCE_REGISTRY_VERSION = "v30.v20_reference_registry_for_m3.v1"


class V20ReferenceAsset(V30Model):
    asset_id: str
    v20_paths: list[str] = Field(default_factory=list)
    asset_type: str
    m3_target: str
    reusable_concepts: list[str] = Field(default_factory=list)
    required_v30_contracts: list[str] = Field(default_factory=list)
    migration_boundary: str
    priority: int = 0


V20_REFERENCE_ASSETS: tuple[V20ReferenceAsset, ...] = (
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_expanded_knowledge_units",
        v20_paths=["../v20/knowledge/loader.py:_expanded_knowledge_units"],
        asset_type="knowledge_units",
        m3_target="KRP_LIBRARY_UNITS",
        reusable_concepts=[
            "qishi_flow_gate",
            "climate_gate",
            "useful_god_path_gate",
            "palace_position_gate",
            "time_stack_gate",
            "blind_image_auxiliary_boundary",
            "ten_god_role_gate",
            "element_flow_gate",
            "branch_storage_gate",
            "branch_mechanism_gate",
            "branch_combination_gate",
            "zuogong_gate",
            "domain_application_boundaries",
        ],
        required_v30_contracts=[
            "KnowledgeRulePortraitUnit",
            "FeatureEvidence",
            "RuleEvidenceSpec",
            "source_family_id",
            "runtime_boundary",
        ],
        migration_boundary="no_v20_runtime_import__v20_knowledge_units_are_reference_assets_not_runtime_imports",
        priority=100,
    ),
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_structure_mechanism_units",
        v20_paths=["../v20/knowledge/structure_mechanisms.py"],
        asset_type="structure_mechanism_units",
        m3_target="v30.structure.mechanism_graph",
        reusable_concepts=[
            "食神制杀",
            "伤官制杀",
            "食伤生财",
            "财生官",
            "官印相生",
            "杀印相生",
            "印星承身",
            "比劫承身",
            "印制食伤",
            "比劫夺财",
            "财破印",
        ],
        required_v30_contracts=[
            "MechanismPath",
            "DynamicGraphPath",
            "path_score_reasons",
            "counter_evidence_boundary",
        ],
        migration_boundary="no_v20_runtime_import__v20_mechanism_labels_must_be_rebuilt_as_v30_evidence_bound_paths",
        priority=95,
    ),
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_structure_dynamics_graph_v2",
        v20_paths=["../v20/dynamics/graph_engine.py"],
        asset_type="dynamic_graph_algorithm",
        m3_target="v30.structure.dynamic_graph",
        reusable_concepts=[
            "weighted_dynamic_graph_path_extraction",
            "node_edge_path_report",
            "family_chain",
            "edge_role",
            "dominant_path",
            "semantic_candidates",
            "runtime_policy_weights",
            "guardrails",
        ],
        required_v30_contracts=[
            "DynamicGraphNode",
            "DynamicGraphEdge",
            "DynamicGraphPath",
            "StructureState.path_scores",
            "structure_policy.weights",
        ],
        migration_boundary="no_v20_runtime_import__v20_dynamic_graph_logic_is_pattern_reference_v30_runtime_owns_algorithm",
        priority=90,
    ),
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_structure_knowledge_coverage",
        v20_paths=["../v20/validation/structure_dynamics_knowledge_coverage.py"],
        asset_type="coverage_audit",
        m3_target="m3_core_spine_synthetic_and_training_signals",
        reusable_concepts=[
            "observed_structure_label_coverage",
            "mechanism_unit_supported",
            "knowledge_unit_supported",
            "rule_catalog_supported",
            "unsupported_label_gap",
        ],
        required_v30_contracts=[
            "SyntheticBaziCase.observed",
            "SyntheticTrainingSignal",
            "krp_source_coverage",
            "dynamic_path_coverage",
        ],
        migration_boundary="no_v20_runtime_import__v20_coverage_audit_becomes_v30_validation_signal_not_runtime_dependency",
        priority=85,
    ),
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_rule_portrait_batch",
        v20_paths=["../v20/validation/rule_portrait_batch.py", "../v20/knowledge/rule_extraction.py"],
        asset_type="rule_portrait_validation_batch",
        m3_target="m3_rule_portrait_validation",
        reusable_concepts=[
            "rule_domain_generation",
            "portrait_axis_coverage",
            "rule_candidate_alignment",
            "runtime_blocked_guard",
        ],
        required_v30_contracts=[
            "RuleEvidenceSpec",
            "KnowledgeRulePortraitUnit",
            "macro_portrait_projection",
            "SyntheticTrainingSignal",
        ],
        migration_boundary="no_v20_runtime_import__v20_rule_portrait_batch_informs_v30_validation_only_no_old_runtime_execution",
        priority=80,
    ),
    V20ReferenceAsset(
        asset_id="v30.m3.reference.v20_source_catalog_and_completeness",
        v20_paths=["../v20/knowledge/source_catalog.py", "../v20/knowledge/completeness_audit.py", "../v20/knowledge/coverage.py"],
        asset_type="knowledge_governance",
        m3_target="v30.knowledge.source_registry",
        reusable_concepts=[
            "source_catalog",
            "completeness_audit",
            "coverage_gap",
            "review_queue",
        ],
        required_v30_contracts=[
            "KnowledgeSourceFamily",
            "source_family_id",
            "validation_requirements",
            "runtime_boundary",
        ],
        migration_boundary="no_v20_runtime_import__v20_governance_is_reference_for_v30_source_registry_not_shared_state",
        priority=75,
    ),
)


def list_v20_reference_assets() -> list[V20ReferenceAsset]:
    return sorted(V20_REFERENCE_ASSETS, key=lambda row: (-row.priority, row.asset_id))


def summarize_v20_reference_registry() -> dict[str, object]:
    assets = list_v20_reference_assets()
    return {
        "version": V20_REFERENCE_REGISTRY_VERSION,
        "asset_count": len(assets),
        "asset_ids": [asset.asset_id for asset in assets],
        "asset_types": sorted({asset.asset_type for asset in assets}),
        "m3_targets": sorted({asset.m3_target for asset in assets}),
        "required_v30_contracts": sorted({
            contract for asset in assets for contract in asset.required_v30_contracts
        }),
        "boundary": "v20_assets_are_reference_inputs_v30_runtime_contracts_remain_authoritative",
    }
