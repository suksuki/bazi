"""进化与学习相关提示词片段：与 BaziMetadata.history_context 协议对齐，供 Registry 审计。"""

from __future__ import annotations

# 与终判 User 中可选块 [LearningAnnotation·裁决者修正上下文] 配套；亦适用于强模型 reasoning_feedback_loop 元数据回写说明。
EVOLUTION_LEARNING_CONTEXT_RULE: str = (
    "[LearningAnnotation] 仅历史修订摘要与断言 id 差分，不新增物理事实；"
    "语气可受其牵引，事实仍以 User 的 [Verified Facts] 与插件短锚为准。"
    "顶层 reasoning_feedback_loop（可选）写入元数据，勿写入 verdict_body。"
)

# 物理审计 LLM（AuditPhysicsWithLlm）：与 runtime llm.is_high_reasoning_mode 同步启用，抑制弱模型「复读式 sql_patch」。
PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE: str = (
    "【高推理·SQL】无实质调参意图时 sql_patch 与 logic_proposal.sql_patch 置空串；"
    "仅当 suggested_value 相对共识确有变更意图时输出唯一合法 UPDATE。"
)

PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE: str = (
    "【高推理·因果】causal_reasoning 串联 InferenceTrace（若有）与十神/插件输出中的可点名键，解释主矛盾成因。"
)
