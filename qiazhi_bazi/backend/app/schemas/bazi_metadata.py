"""BaziMetadata v1.0：四柱、矛盾矩阵、能量流向（不接老系统复杂分值）。"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class FlowState(str, Enum):
    """当前盘面能量流向标签（可扩展）。"""

    UNKNOWN = "unknown"
    GENERATING = "生"
    CONTROLLING = "克"
    SAME = "比劫"
    OUTPUT = "泄"
    RESOURCE = "印"


class StemBranchPair(BaseModel):
    stem: str = Field(..., description="天干一字，如 甲")
    branch: str = Field(..., description="地支一字，如 寅")
    energy_value: int = Field(default=100, description="该柱能量值（0-100）")


class FourPillars(BaseModel):
    """四柱干支。"""

    year: StemBranchPair
    month: StemBranchPair
    day: StemBranchPair
    hour: StemBranchPair


class ConflictPoint(BaseModel):
    """刑冲合化等潜在作用点（扫描结果之一）。"""

    id: Optional[str] = Field(default=None, description="稳定锚点 ID，供终判段落与 Debug 联动")
    kind: str = Field(..., description="如 clash、combine、punish、harm、sanhe")
    positions: List[str] = Field(
        default_factory=list,
        description="涉及柱位或地支，如 [month_branch, day_branch]",
    )
    detail: str = Field(default="", description="人可读说明，如 寅申冲")
    source: Optional[str] = Field(default=None, description="scanner=初始扫描；l1_physics=L1 流水线/合成场回写")


class PluginSelectionTraceEntry(BaseModel):
    """L0–L4 插件入选轨迹（审计用）。"""

    plugin_id: str = Field(default="", description="插件 ID，如 classical.blind_school.v1")
    layer_id: str = Field(default="", description="L0 / L1 / …")
    status: str = Field(default="", description="ALWAYS_ON | SELECTED 等")
    reason: str = Field(default="", description="入选或常驻理由（含 MatchScore 因子摘要）")


class ConfirmedVerdictRecord(BaseModel):
    """用户签发后归档的断言记忆。"""

    verdict_id: str = Field(default="", description="终判 version_id 或业务主键")
    body_excerpt: str = Field(default="", description="正文摘录")
    confirmed_at: str = Field(default="", description="ISO 时间")
    source_metadata_hash: str = Field(default="", description="签发时元数据指纹（与终判证书 hash 对齐或独立）")
    evidence_refs: List[str] = Field(default_factory=list, description="归档时的证据锚点列表")
    model_id: str = Field(
        default="unknown",
        description="签发或归档时的 LLM 模型 id（runtime_config.llm.model；禁止空串）",
    )
    suppressed_inbox_card_ids: List[str] = Field(
        default_factory=list,
        description="终判签发时从 resolved_card_ids 等汇总的 Inbox 卡片屏蔽 id，供叙事工厂复现时过滤",
    )
    decision_kinds: List[str] = Field(
        default_factory=list,
        description="结构化意志类型，如 UPDATE_PHYSICS_PARAM（与 persistence_layer.confirmed_verdicts 对齐）",
    )
    physics_param_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="UPDATE_PHYSICS_PARAM 时写入 physics_config / interaction 覆盖的键值",
    )


class VerdictRegenerationEvent(BaseModel):
    """终判再生/重写审计（如 Regenerate、η 微调后静默重算）。"""

    occurred_at: str = Field(default="", description="ISO 时间")
    reason: str = Field(default="", description="人可读原因，如 η 参数微调触发重写")
    trigger: str = Field(default="", description="manual_regenerate | physics_recalc | inbox_execute 等")
    model_id: str = Field(default="unknown", description="本次推理所用 LLM 模型 id（禁止空串）")
    version_id: str = Field(default="", description="本次终判 version_id")
    previous_version_id: str = Field(default="", description="上一版 version_id，无则空")


class VerdictModelStamp(BaseModel):
    """每次终判生成强制落库的模型指纹（含首版），供弱/强模型同命例对比。"""

    occurred_at: str = Field(default="", description="ISO 时间")
    model_id: str = Field(default="unknown", description="runtime_config.llm.model 或等价标识")
    version_id: str = Field(default="", description="本次终判 version_id")


class HistoryContext(BaseModel):
    """断言记忆体：已确认终判、再生轨迹与元数据指纹。"""

    confirmed_verdicts: List[ConfirmedVerdictRecord] = Field(default_factory=list)
    regeneration_events: List[VerdictRegenerationEvent] = Field(
        default_factory=list,
        description="每次 Regenerate / 物理重算触发的终判重写记录",
    )
    verdict_model_stamps: List[VerdictModelStamp] = Field(
        default_factory=list,
        description="每次终判成功即追加一条（与 regeneration 独立）；跨会话审计用",
    )
    learning_annotation: Dict[str, Any] = Field(
        default_factory=dict,
        description="裁决者偏好与 Regenerate/修正差分；建议 schema=learning_annotation.v1，entries 为列表",
    )


class InferenceTraceStep(BaseModel):
    """单步：输入摘要 → 匹配分 → 输出摘要 → 因果仲裁备注。"""

    step_index: int = Field(default=0, description="全局序号")
    layer_id: str = Field(default="", description="L0–L4")
    plugin_id: str = Field(default="", description="插件 ID")
    input_summary: str = Field(default="", description="触发输入 / 上下文摘要")
    match_score: Optional[float] = Field(default=None, description="Inbox MatchScore，无则 null")
    output_summary: str = Field(default="", description="输出 / 轨迹摘要")
    arbitration_note: str = Field(default="", description="causal_routing 或路由审计一句话")


class InferenceTrace(BaseModel):
    """L0–L4 全量因果轨迹（可回放）。"""

    version: str = Field(default="1.0", description="轨迹格式版本")
    steps: List[InferenceTraceStep] = Field(default_factory=list)


class VerdictAssertionAnchor(BaseModel):
    """单句断言及其元数据锚点（LLM 或启发式回填）。"""

    assertion_id: str = Field(default="", description="a0 / 行号等")
    text: str = Field(default="", description="断语文本")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="如 year.branch、conflict_matrix.sanhe_cluster_0、plugin.classical.blind_school.v1",
    )


class VerdictAnchorLayer(BaseModel):
    """断言层：与 BaziMetadata 同步的锚点集合。"""

    narrative_version_id: str = Field(default="", description="与终判 version_id 对齐")
    assertions: List[VerdictAssertionAnchor] = Field(default_factory=list)
    final_verdict: str = Field(
        default="",
        description="终审 LLM 整合后的主判词纯文本（写入前不含指纹注释；供断言区首位展示）",
    )
    verdict_skeleton: str = Field(
        default="",
        description="物理预判 Markdown 骨架：由 VF 经 semantic_translator.build_verdict_skeleton 生成；Orchestrator 每轮刷新",
    )


class ManualEnergyPatchEntry(BaseModel):
    """单条个人能量补丁：在 deity_scores 展示层上做加减，不修改全局物理常数表。"""

    delta_by_deity: Dict[str, float] = Field(default_factory=dict, description="十神名 -> 分值偏移")
    param_key: str = Field(default="", description="来源物理审计键（白名单之一）")
    suggested_value: float = Field(default=1.0, description="LLM 建议的目标参数值（仅溯源）")
    reason: str = Field(default="", description="采纳理由摘要")
    confirmed_at: str = Field(default="", description="ISO 时间")
    source_card_id: str = Field(default="", description="Decision Inbox 卡片 id")


class ManualEnergyPatchState(BaseModel):
    """manual_energy_patch 协议：与 seed 指纹绑定的一组补丁。"""

    patch_protocol: str = Field(default="manual_energy_patch.v1", description="协议版本")
    seed_hash: str = Field(default="", description="与前端 seedPayloadSignature 对齐")
    entries: List[ManualEnergyPatchEntry] = Field(default_factory=list)


class SemanticVerdictArchiveEntry(BaseModel):
    """用户确认后的断语归档。"""

    id: str = Field(default="", description="稳定 id（uuid 或业务键）")
    text: str = Field(default="", description="归档正文")
    seed_hash: str = Field(default="", description="生辰指纹")
    confirmed_at: str = Field(default="", description="ISO 时间")
    source_card_id: str = Field(default="", description="来源 Inbox 卡片 id")


class PersistenceConfirmedPhysicsWill(BaseModel):
    """持久化侧车中的结构化意志项（与 semantic_verdicts 并列）。"""

    verdict_id: str = Field(default="", description="业务锚 id，可与终判 version 对齐")
    kinds: List[str] = Field(
        default_factory=list,
        description="勾选类型；含 UPDATE_PHYSICS_PARAM 时将 payload 强制写入 physics/interaction",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="PhysicsConfig 与 interaction_param 白名单键的并集；由 Will Injection 拆分",
    )


class PersistenceLayer(BaseModel):
    """持久化侧车：与命例实例绑定、跨引擎重算保留。"""

    persistence_protocol: str = Field(default="persistence_layer.v1", description="协议版本")
    semantic_verdicts: List[SemanticVerdictArchiveEntry] = Field(
        default_factory=list,
        description="已确认语义断语（与 seed_hash 逐项对齐）",
    )
    confirmed_verdicts: List[PersistenceConfirmedPhysicsWill] = Field(
        default_factory=list,
        description="结构化意志归档（含 UPDATE_PHYSICS_PARAM 等）；Orchestrator 静默环读取",
    )
    will_temporal_anchor_dayun: str = Field(
        default="",
        description="用户确认意志时的大运干支锚；与当前 temporal_context/dayun 不一致时提示复核",
    )


class ConflictMatrix(BaseModel):
    """盘面扫描出的刑冲合化潜在点集合。"""

    points: List[ConflictPoint] = Field(default_factory=list)


class ActiveVerdictSkeleton(BaseModel):
    """语义快照：引擎预判骨架 + 用户意志硬编码（中控终判 v1；见 SEMANTIC_SNAPSHOT_AND_MANDATORY_NARRATION_v1.md）。"""

    protocol: str = Field(default="active_verdict_skeleton.v1", description="子协议版本")
    engine_bullets: List[str] = Field(
        default_factory=list,
        description="由 conflict_matrix、四柱、[semantic_label_bundle] VF 脱水行等拼装的因果标签行",
    )
    user_will_lines: List[str] = Field(
        default_factory=list,
        description="Decision Inbox 勾选文本；由终判入口与 analyze 后刷新合并",
    )
    updated_at: str = Field(default="", description="ISO8601 UTC，物理或意志变更时刷新")


class BaziMetadata(BaseModel):
    """四柱元数据根对象：v1 核心 + v2 记忆体（history / inference / verdict_anchor）。"""

    version: str = Field(default="1.0", description="四柱协议主版本（与历史 API 对齐）")
    memory_schema_version: str = Field(default="2.0", description="记忆体与因果轨迹扩展版本")
    pillars: Optional[FourPillars] = None
    conflict_matrix: ConflictMatrix = Field(default_factory=ConflictMatrix)
    flow_state: FlowState = FlowState.UNKNOWN
    notes: str = Field(default="", description="可选备注")
    temporal_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Chronos V2：大运/流年干支与参考年，供引动审计",
    )
    plugin_selection_trace: List[PluginSelectionTraceEntry] = Field(
        default_factory=list,
        description="L0–L4 插件入选与常驻理由，供黑匣子元数据审计",
    )
    history_context: HistoryContext = Field(
        default_factory=HistoryContext,
        description="经用户确认的断言记忆与 source_metadata_hash",
    )
    inference_trace: InferenceTrace = Field(
        default_factory=InferenceTrace,
        description="L0–L4 Input→MatchScore→Output→Arbitration 全链路",
    )
    verdict_anchor_layer: VerdictAnchorLayer = Field(
        default_factory=VerdictAnchorLayer,
        description="当前终判断言与 evidence_refs，与 Debug 回放联动",
    )
    reasoning_feedback_loop: Optional[Any] = Field(
        default=None,
        description="强模型可选回写的推理摘要（与终判 JSON 顶级字段对齐，供进化管线）",
    )
    manual_energy_patch: Optional[ManualEnergyPatchState] = Field(
        default=None,
        description="当前命例上的十神展示层柔性干预（与 seed 指纹绑定；不由 analyze-seed 覆盖）",
    )
    persistence_layer: Optional[PersistenceLayer] = Field(
        default=None,
        description="用户确认断语等侧车持久化（与 seed 指纹逐项绑定）",
    )
    active_verdict_skeleton: Optional[ActiveVerdictSkeleton] = Field(
        default=None,
        description="中控语义快照：物理/插件更新即刷新；终判前合并 Inbox 意志",
    )


_SIX_CLASH = {
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
}

_SIX_COMBINE = {
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
}

_CLASH_LABEL: Dict[frozenset[str], str] = {
    frozenset(("子", "午")): "子午冲",
    frozenset(("丑", "未")): "丑未冲",
    frozenset(("寅", "申")): "寅申冲",
    frozenset(("卯", "酉")): "卯酉冲",
    frozenset(("辰", "戌")): "辰戌冲",
    frozenset(("巳", "亥")): "巳亥冲",
}

_COMBINE_LABEL: Dict[frozenset[str], str] = {
    frozenset(("子", "丑")): "子丑合",
    frozenset(("寅", "亥")): "寅亥合",
    frozenset(("卯", "戌")): "卯戌合",
    frozenset(("辰", "酉")): "辰酉合",
    frozenset(("巳", "申")): "巳申合",
    frozenset(("午", "未")): "午未合",
}


class PhysicalScanner:
    """原子探测器：仅做地支六冲与六合识别。"""

    def scan(self, pillars: FourPillars) -> ConflictMatrix:
        branches = {
            "year_branch": pillars.year.branch,
            "month_branch": pillars.month.branch,
            "day_branch": pillars.day.branch,
            "hour_branch": pillars.hour.branch,
        }
        keys = list(branches.keys())
        points: List[ConflictPoint] = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                p1, p2 = keys[i], keys[j]
                b1, b2 = branches[p1], branches[p2]
                pair_key = frozenset((b1, b2))
                pair: Tuple[str, str] = (b1, b2)
                if pair in _SIX_CLASH or (b2, b1) in _SIX_CLASH:
                    points.append(
                        ConflictPoint(
                            kind="clash",
                            positions=[p1, p2],
                            detail=_CLASH_LABEL.get(pair_key, f"{b1}{b2}冲"),
                        )
                    )
                if pair in _SIX_COMBINE or (b2, b1) in _SIX_COMBINE:
                    points.append(
                        ConflictPoint(
                            kind="combine",
                            positions=[p1, p2],
                            detail=_COMBINE_LABEL.get(pair_key, f"{b1}{b2}合"),
                        )
                    )
        return ConflictMatrix(points=points)


def detect_clashes(pillars: FourPillars) -> ConflictMatrix:
    """兼容旧接口：返回原子探测矩阵（含六冲与六合）。"""
    return PhysicalScanner().scan(pillars)
