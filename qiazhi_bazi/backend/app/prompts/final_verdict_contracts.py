"""
终判 LLM：System 契约（与 User 证据拼装解耦）。

约束尽量后置：assertion_id / evidence_refs 形态以 JSON 示例为准，parse 阶段裁剪与启发式补全。
"""

from __future__ import annotations

from app.prompts.evolution_contracts import EVOLUTION_LEARNING_CONTEXT_RULE
from app.prompts.language import LanguageEngine

STRICT_JSON_ONLY_HEADER = (
    "[STRICT_JSON_ONLY] 严禁输出任何自然语言、思考过程或英文解释。禁止任何 Markdown 围栏。"
    "你的输出必须是合法的 JSON 对象文本（单行或多行均可），首字符为「{」末字符为「}」。"
)


def evidence_user_block_heading(*, high_reasoning: bool) -> str:
    """兼容旧拼装路径。"""
    return "插件切片·全量" if high_reasoning else "插件切片·摘要"


def evidence_mode_clause(*, high_reasoning: bool) -> str:
    """已并入 System JSON 示例；保留函数供注册表/旧测试 import。"""
    return ""


def _identity(*, high_reasoning: bool) -> str:
    tail = "高推理可展开 Auxiliary·溯源与 reasoning_feedback_loop 元字段。" if high_reasoning else ""
    return (
        "角色：Final Narrator（终审）。简体中文子平语境；User 经后端脱水，无浮点物理字面量。"
        + tail
    )


def _verdict_json_envelope_and_verdict_body_rules(*, high_reasoning: bool) -> str:
    tail = " 可选顶层 reasoning_feedback_loop（勿写入 verdict_body）。" if high_reasoning else ""
    return (
        "仅输出一个 JSON（前后无其它 Markdown）："
        '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""},'
        '"assertions":[{"assertion_id":"a0","text":"一句断语","evidence_refs":["VF01","year.stem","plugin.sys.core.physics"]]}。'
        "verdict_body 仅含三个三级标题：### 核心气象 / ### 裁决共识 / ### 行为指引；change_log 写相对上一版差异。"
        + tail
    )


def _policy_core(*, high_reasoning: bool) -> str:
    return (
        "事实边界以 [Verified Facts]、[User Decisions] 为准，冲突时从后者。"
        "盲派/墓库/岁运等只使用 Context 已有定性句，不补数值。"
        + (" 高推理：可铺陈 Auxiliary，不得发明未出现的柱支或插件事实。" if high_reasoning else "")
    )


def _contract_polish_mode_clause() -> str:
    return (
        "[CONTRACT_MODE] 你当前是语义润色代理。系统已完成定论，严禁改动逻辑。"
        "verdict_body 中必须原样保留 [VerdictSkeleton] 与 [Verified Facts] 已出现的全部 VF01、VF02 等引用字样（含「VF」前缀与两位数字），"
        "禁止删除、改写或重新编号；仅可将这些引用周围的句子润色为子平语境自然语言。\n"
    )


def build_final_verdict_system_message(
    *,
    high_reasoning: bool,
    lang: str,
    contract_polish_mode: bool = False,
) -> str:
    """组装终判 system 全文（不含盲派 skill 动态块；由调用方追加）。"""
    contract_head = _contract_polish_mode_clause() if contract_polish_mode else ""
    parts = [
        STRICT_JSON_ONLY_HEADER,
        contract_head,
        _identity(high_reasoning=high_reasoning),
        _policy_core(high_reasoning=high_reasoning),
        _verdict_json_envelope_and_verdict_body_rules(high_reasoning=high_reasoning),
        EVOLUTION_LEARNING_CONTEXT_RULE,
        LanguageEngine.strict_assistant_output_language(lang),
    ]
    return "".join(parts)
