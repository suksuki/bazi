from __future__ import annotations

import pytest

from v19.knowledge import KnowledgeKernel, KnowledgeKernelError


def _unit_payload(knowledge_id: str = "core.day_master_strength") -> dict:
    return {
        "knowledge_id": knowledge_id,
        "domain": "strength",
        "title": "Day Master Strength",
        "statement": "Day-master strength is a core carrying-capacity signal and must be evaluated before theme conclusions.",
        "conditions": {"requires": ["month_command", "root_strength", "support_pressure_balance"]},
        "feature_mapping": {
            "evidence_type": "core_strength_evidence",
            "input_requirements": ["canonical_chart", "ten_god_map", "root_index"],
            "detection_logic": {"op": "weighted_strength_balance"},
            "output_fields": ["support_score", "pressure_score", "strength_tendency"],
        },
        "effects": {"carrying_capacity": 0.72, "theme_modifier": 0.48},
        "risks": ["Theme predictions become unstable when carrying capacity is skipped."],
        "uncertainty": ["Seasonal command and roots can conflict."],
        "conflicts": ["follow_vs_support", "regulation_vs_output"],
        "source_refs": ["v19:owner_seed"],
        "confidence_prior": 0.78,
        "version": "v1",
    }


def test_register_review_and_compile_evidence_template() -> None:
    kernel = KnowledgeKernel()
    created = kernel.register_unit(_unit_payload(), actor="owner")
    reviewed = kernel.review_unit("core.day_master_strength", reviewer="owner")
    template = kernel.compile_evidence_template("core.day_master_strength")

    assert created["status"] == "draft"
    assert reviewed["status"] == "reviewed"
    assert template["knowledge_id"] == "core.day_master_strength"
    assert template["runtime_scope"] == "evidence_template_only"
    assert template["evidence_type"] == "core_strength_evidence"
    assert "NO_DIRECT_PREDICTION" in template["guardrails"]
    assert "NO_ACTIVE_RULE" in template["guardrails"]
    assert template["provenance"]["content_hash"].startswith("sha256:")


def test_reviewed_knowledge_is_immutable() -> None:
    kernel = KnowledgeKernel()
    kernel.register_unit(_unit_payload(), actor="owner")
    kernel.review_unit("core.day_master_strength", reviewer="owner")
    changed = _unit_payload()
    changed["statement"] = "Changed after review."

    with pytest.raises(KnowledgeKernelError) as exc:
        kernel.register_unit(changed, actor="owner")

    assert exc.value.code == "REVIEWED_KNOWLEDGE_IMMUTABLE"


def test_draft_and_deprecated_units_cannot_compile() -> None:
    kernel = KnowledgeKernel()
    kernel.register_unit(_unit_payload("core.root_strength"), actor="owner")

    with pytest.raises(KnowledgeKernelError) as draft_error:
        kernel.compile_evidence_template("core.root_strength")
    assert draft_error.value.code == "KNOWLEDGE_REVIEW_REQUIRED"

    kernel.deprecate_unit("core.root_strength", reason="schema replaced")
    with pytest.raises(KnowledgeKernelError) as deprecated_error:
        kernel.compile_evidence_template("core.root_strength")
    assert deprecated_error.value.code == "DEPRECATED_KNOWLEDGE_LOCKED"


def test_kernel_is_domain_neutral_not_wealth_centered() -> None:
    kernel = KnowledgeKernel()
    for knowledge_id, domain in [
        ("core.ten_god_visibility", "ten_god"),
        ("core.branch_combination_clash", "core_structure"),
        ("theme.wealth_mapping", "theme_mapping"),
    ]:
        payload = _unit_payload(knowledge_id)
        payload["domain"] = domain
        kernel.register_unit(payload, actor="owner")
        kernel.review_unit(knowledge_id, reviewer="owner")

    assert {row["domain"] for row in kernel.list_units()} == {"ten_god", "core_structure", "theme_mapping"}
    assert len(kernel.list_units(domain="theme_mapping")) == 1
