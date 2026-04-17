"""V12 三色元数据（M1）：与 docs/V12_BRAIN_FRAMEWORK.md §1 对齐的 Pydantic 模型。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StaticFact(BaseModel):
    """真值层：可复算基线与输入侧结构。"""

    model_config = {"extra": "forbid"}

    schema_version: str = Field(default="static_fact.v1", description="契约版本")
    pillars: Dict[str, Any] = Field(default_factory=dict, description="四柱干支结构（序列化自 FourPillars）")
    hidden_stems_profile: Dict[str, Any] = Field(
        default_factory=dict,
        description="藏干及柱绑静态结构（若当前实现分散，由投影器收敛）",
    )
    temporal_anchors: Dict[str, Any] = Field(
        default_factory=dict,
        description="大运/流年等输入锚；通常来自 metadata.temporal_context",
    )
    physics_param_version_id: str = Field(
        default="",
        description="L0 参数版本；通常来自 physics_tensor.audit_log.param_version_id",
    )
    baseline_tensor: Dict[str, Any] = Field(
        default_factory=dict,
        description="当前帧与物理根一致的能量基准子集：deity_scores、abs_nodes、normalized 等",
    )
    climate_baseline: Dict[str, Any] = Field(
        default_factory=dict,
        description="调候/气候基线块；通常 meta.climate_field_correction_v1",
    )


class DynamicInference(BaseModel):
    """推演层：插件与法典产物、意志上下文、张量快照（不含用户裁决勾选）。"""

    model_config = {"extra": "forbid"}

    schema_version: str = Field(default="dynamic_inference.v1")
    l1_audit: Dict[str, Any] = Field(
        default_factory=dict,
        description="L1 摘要：如 l1_robber_wealth_v1、energy_vault_flags、work_eligible、PATTERN_SOVEREIGNTY_PROTECTION 等",
    )
    l2_pattern_rows: List[Dict[str, Any]] = Field(default_factory=list, description="法典格局行 meta.pattern_thresholds")
    l2_engine_provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="引擎名、摘要 headline、manifest 指纹等",
    )
    plugin_registry_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="enabled_plugins、plugin_specs、blind_school_features",
    )
    will_intention_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="meta.intention_context",
    )
    conflict_and_topology: Dict[str, Any] = Field(
        default_factory=dict,
        description="conflict_topology_v1、branch_interactions 等",
    )
    semantic_label_bundle: Dict[str, Any] = Field(default_factory=dict, description="meta.semantic_label_bundle_v1")
    causal_routing: Dict[str, Any] = Field(default_factory=dict, description="meta.causal_routing")
    post_will_tensor_delta: Dict[str, Any] = Field(default_factory=dict, description="可选意志后差分占位")
    current_tensor_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="推演用只读快照：除 baseline 外 meta.params、confidence、audit_log 摘要等",
    )
    plugin_outputs_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="physics_tensor.plugin_outputs 浅拷贝（插件输出快照）",
    )


class ArbiterBias(BaseModel):
    """裁决偏置层：用户意志、Inbox、持久化侧车（仅投影已有字段，不推断）。"""

    model_config = {"extra": "forbid"}

    schema_version: str = Field(default="arbiter_bias.v1")
    user_intention_id: str = Field(default="", description="seek_wealth 等；来自 bundle 顶层或 metadata 扩展键")
    inbox_selection_trace: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="可选：plugin_selection_trace 等与 Inbox 勾选相关的审计条目投影",
    )
    persistence_layer: Dict[str, Any] = Field(default_factory=dict, description="metadata.persistence_layer 序列化")
    history_context: Dict[str, Any] = Field(default_factory=dict, description="metadata.history_context 序列化")
    active_verdict_skeleton: Dict[str, Any] = Field(
        default_factory=dict,
        description="metadata.active_verdict_skeleton（user_will_lines 等）",
    )
    manual_energy_patch: Dict[str, Any] = Field(default_factory=dict, description="metadata.manual_energy_patch")
    psv_runtime_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="PSV 引擎可调阈值局部覆盖（与 PSVRuntimeConfig 字段同名）；持久化可写入 persistence_layer 并由投影器汇入",
    )
    interrupt_request: Dict[str, Any] = Field(
        default_factory=dict,
        description="M3 ActiveProbing 逻辑断点请求（pending/resolved/resumed）。",
    )
    interrupt_state: str = Field(
        default="",
        description="M3 状态机状态摘要：pending/acknowledged/resolved/resumed/expired。",
    )
    bias_ack_tokens: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="与 M1 Logic Interrupter 确认令牌对齐；当前自 history / persistence 可空",
    )


class TriLayerMetadata(BaseModel):
    """三色总容器。"""

    model_config = {"extra": "forbid"}

    tri_layer_schema_version: str = Field(default="tri_layer.v1", description="总包版本")
    static_fact: StaticFact
    dynamic_inference: DynamicInference
    arbiter_bias: ArbiterBias
