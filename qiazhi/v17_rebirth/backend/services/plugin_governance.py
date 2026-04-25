from __future__ import annotations

from dataclasses import dataclass
from typing import Any


GOVERNANCE_PROTOCOL_VERSION = "v17.plugin_governance.v1"


@dataclass(frozen=True)
class PluginGovernanceProfile:
    plugin_id: str
    governance_class: str
    authority_level: str
    output_contract: str
    metadata_scope: str
    learning_family: str
    can_emit_physical_proposal: bool = False
    can_enter_authority: bool = False
    can_enter_prompt: bool = True
    can_enter_decision_inbox: bool = True
    override_forbidden: bool = True
    max_bias_ratio: float = 0.0
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": GOVERNANCE_PROTOCOL_VERSION,
            "plugin_id": self.plugin_id,
            "governance_class": self.governance_class,
            "authority_level": self.authority_level,
            "output_contract": self.output_contract,
            "metadata_scope": self.metadata_scope,
            "learning_family": self.learning_family,
            "can_emit_physical_proposal": bool(self.can_emit_physical_proposal),
            "can_enter_authority": bool(self.can_enter_authority),
            "can_enter_prompt": bool(self.can_enter_prompt),
            "can_enter_decision_inbox": bool(self.can_enter_decision_inbox),
            "override_forbidden": bool(self.override_forbidden),
            "max_bias_ratio": round(float(self.max_bias_ratio or 0.0), 4),
            "notes": list(self.notes),
        }


def classify_plugin_governance(
    *,
    plugin_id: str,
    layer: str = "",
    causal_tier: int | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the plugin sovereignty profile used by Admin, tests, and learning audits.

    The profile is intentionally conservative: it describes what a plugin is allowed
    to do, not what it happened to do in one run.
    """
    pid = str(plugin_id or "").strip()
    layer_tag = str(layer or "").strip().upper()
    manifest = manifest if isinstance(manifest, dict) else {}
    domain = str(manifest.get("Domain") or manifest.get("domain") or "").strip().lower()

    if pid.startswith("l0.foundation.") or layer_tag == "L0":
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="physical_foundation",
            authority_level="level_0_physics",
            output_contract="fact_only",
            metadata_scope="public_physics_contract",
            learning_family="l0_static_basis",
            can_emit_physical_proposal=False,
            can_enter_authority=False,
            notes=("L0 exposes auditable basis facts; settlement is owned by physics kernels.",),
        ).to_dict()

    if pid.startswith("l1.physics.") or layer_tag == "L1":
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="physical_relation_operator",
            authority_level="level_1_relation",
            output_contract="fact_or_modifier_proposal",
            metadata_scope="physics_runtime_contract",
            learning_family=_relation_learning_family(pid),
            can_emit_physical_proposal=True,
            can_enter_authority=False,
            max_bias_ratio=0.0,
            notes=("May propose runtime displacement; must settle through unified kernel.",),
        ).to_dict()

    if pid.startswith("classical.ziping."):
        is_resolver = "god_ring_resolver" in pid or pid.endswith(".summary.v1")
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="ziping_umbrella",
            authority_level="level_1_hard" if is_resolver else "level_2_ziping_axis",
            output_contract="authority_or_evidence",
            metadata_scope="public_authority_contract",
            learning_family="ziping_authority",
            can_emit_physical_proposal=False,
            can_enter_authority=True,
            override_forbidden=True,
            max_bias_ratio=1.0 if is_resolver else 0.35,
            notes=("Ziping umbrella owns hard authority; bridge plugins may enhance but not bypass resolver.",),
        ).to_dict()

    if pid.startswith("classical.pattern.") or pid in {"ten_god_pattern"}:
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="structure_enhancement",
            authority_level="level_2_structure",
            output_contract="pattern_candidate_or_evidence",
            metadata_scope="public_topic_contract",
            learning_family="pattern_specialization",
            can_enter_authority=True,
            max_bias_ratio=0.35,
            notes=("Pattern plugins enhance structure survival and candidate ranking.",),
        ).to_dict()

    if pid.startswith("classical.climate."):
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="climate_structure_enhancement",
            authority_level="level_2_structure",
            output_contract="climate_evidence",
            metadata_scope="public_topic_contract",
            learning_family="climate_field",
            can_enter_authority=True,
            max_bias_ratio=0.28,
            notes=("Climate topic consumes the L0/L1 climate field; it does not rewrite base totals.",),
        ).to_dict()

    if pid.startswith("classical.blind."):
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="soft_bias_topic",
            authority_level="level_3_soft_bias",
            output_contract="blind_theme_bias",
            metadata_scope="public_topic_contract",
            learning_family="blind_theme",
            can_enter_authority=True,
            max_bias_ratio=0.18,
            notes=("Blind school is optional and bias-only; it cannot override Ziping hard constraints.",),
        ).to_dict()

    if pid.startswith("classical.xiangfa."):
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="semantic_only_topic",
            authority_level="level_3_semantic",
            output_contract="semantic_mapping",
            metadata_scope="public_topic_contract",
            learning_family="xiangfa_theme",
            can_enter_authority=False,
            can_enter_decision_inbox=False,
            max_bias_ratio=0.0,
            notes=("Xiangfa only supplies semantic mapping, evidence, narrative hints, and event framing.",),
        ).to_dict()

    if pid.startswith("modern.macro."):
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="macro_theme_topic",
            authority_level="level_3_macro_topic",
            output_contract="macro_theme_reading",
            metadata_scope="public_topic_contract",
            learning_family="macro_theme",
            can_enter_authority=False,
            max_bias_ratio=0.0,
            notes=("Macro theme reads lower-layer signals and structures life-topic interpretation; it cannot change physics or authority.",),
        ).to_dict()

    if pid.startswith("modern.topic."):
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="topic_decoder",
            authority_level="level_3_topic_decoder",
            output_contract="topic_profile",
            metadata_scope="public_topic_contract",
            learning_family="topic_decoder",
            can_enter_authority=False,
            max_bias_ratio=0.0,
            notes=("Topic decoders produce auditable profile contracts for LLM prompts; they cannot rewrite physics, authority, or parameters.",),
        ).to_dict()

    if "risk" in pid or pid in {"officer_see_hurt", "kong_wang", "shensha"}:
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="risk_guard",
            authority_level="level_2_risk_guard",
            output_contract="risk_evidence_or_bias",
            metadata_scope="public_topic_contract",
            learning_family="risk_matrix",
            can_enter_authority=True,
            max_bias_ratio=0.30,
            notes=("Risk matrix amplifies or flags risk; it is not a primary structure replacement.",),
        ).to_dict()

    if pid in {"narrative_clip"} or layer_tag in {"L3", "L4"} or domain in {"narrative", "strategy"}:
        return PluginGovernanceProfile(
            plugin_id=pid,
            governance_class="narrative_or_strategy",
            authority_level="level_3_narrative",
            output_contract="narrative_hint",
            metadata_scope="prompt_context",
            learning_family="narrative",
            can_enter_authority=False,
            max_bias_ratio=0.0,
            notes=("Narrative plugins can shape wording, not physical or hard authority state.",),
        ).to_dict()

    return PluginGovernanceProfile(
        plugin_id=pid,
        governance_class="general_fact_plugin",
        authority_level=f"level_{max(1, min(3, int(causal_tier or 3)))}_unclassified",
        output_contract="fact_or_context",
        metadata_scope="solver_trace",
        learning_family="unclassified",
        can_enter_authority=False,
        max_bias_ratio=0.0,
        notes=("Default conservative profile; promote only after explicit protocol review.",),
    ).to_dict()


def _relation_learning_family(plugin_id: str) -> str:
    pid = str(plugin_id or "").strip()
    for key in (
        "sanhe",
        "banhe",
        "liuhe",
        "liuchong",
        "liuhai",
        "liupo",
        "sanxing",
        "anhe",
        "muku",
        "stem_fusion",
    ):
        if key in pid:
            return f"relation.{key}"
    return "relation.general"
