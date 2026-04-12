"""进化与学习相关提示词片段：与 BaziMetadata.history_context 协议对齐，供 Registry 审计。"""

from __future__ import annotations

# 与终判 User 中可选块 [LearningAnnotation·裁决者修正上下文] 配套；亦适用于强模型 reasoning_feedback_loop 元数据回写说明。
EVOLUTION_LEARNING_CONTEXT_RULE: str = (
    "【学习标注 learning_annotation】当 User 中出现 [LearningAnnotation·裁决者修正上下文] 时："
    "该块仅承载历史 Regenerate/修订摘要与断言 id 差分，不是新物理事实。"
    "弱叙事工厂模式下必须以 [Physical Evidence]、插件切片与 plugin.* 锚为准，"
    "learning_annotation 仅可影响语气、结构与折中措辞；"
    "高推理模式下可更积极对齐裁决者稳定偏好，但若与插件证据冲突，仍以插件与物理证据链为准。"
    "【reasoning_feedback_loop】若你在 JSON 顶层提供该字段，系统会写入元数据供进化管线消费，"
    "勿将其冗长内容复制进 verdict_body。"
)

# 物理审计 LLM（AuditPhysicsWithLlm）：与 runtime llm.is_high_reasoning_mode 同步启用，抑制弱模型「复读式 sql_patch」。
PHYSICS_AUDIT_HIGH_REASONING_SQL_DISCIPLINE: str = (
    "【高推理·SQL 纪律】根字段 sql_patch 与 logic_proposal.sql_patch："
    "若无实质性参数变更意图，二者均应使用空字符串 \"\"；"
    "禁止用单条 UPDATE 仅复读 consensus_history 中已确认的 param_value（文书式合规）；"
    "仅当 logic_proposal 中 suggested_value 相对当前共识确有调参意图时，才输出对应唯一合法 UPDATE。"
)

PHYSICS_AUDIT_HIGH_REASONING_CAUSAL_TRACE: str = (
    "【高推理·因果溯源】causal_reasoning 须显式串联 User 中给出的 InferenceTrace 步骤（若存在）与"
    " plugin_outputs / 十神分值中的硬证据链（可点名 plugin.sys.core.physics 等）；"
    "说明「表象能量路径」为何在逻辑上被另一条证据截断或削弱，避免空泛修辞。"
)
