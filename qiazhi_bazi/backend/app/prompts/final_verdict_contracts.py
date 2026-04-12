"""
终判 LLM：System 契约组件（与 User 证据拼装解耦）。

设计要点：
- **单一输出契约**：结构说明只描述 JSON；``verdict_body`` 内必须包含三个 H3 小节（禁止在 JSON 外再输出一套 Markdown）。
- **强弱模型**：``high_reasoning`` 切换证据溯源强度说明（仍是一条 system，避免维护两套完整 system）。
"""

from __future__ import annotations

from app.prompts.evolution_contracts import EVOLUTION_LEARNING_CONTEXT_RULE
from app.prompts.language import LanguageEngine


def evidence_user_block_heading(*, high_reasoning: bool) -> str:
    return "Evidence Slices·全量逻辑溯源" if high_reasoning else "Evidence Slices·插件语义碎片"


def evidence_mode_clause(*, high_reasoning: bool) -> str:
    if high_reasoning:
        return (
            "若提供 [Evidence Slices·全量逻辑溯源]，请对每条证据行做字段级完整溯源："
            "在 assertions 中引用对应 plugin.<plugin_id> 锚点，串联 verdict_body 与证据原文中的数值、标签，不得因篇幅省略关键信息。"
        )
    return (
        "若提供 [Evidence Slices·插件语义碎片]，请把这些短句当作拼图素材：在 assertions 中引用对应 plugin.<plugin_id> 锚点，"
        "用自然语言缝合进 verdict_body，勿要求读者理解原始 JSON。"
    )


def _identity(*, high_reasoning: bool) -> str:
    base = "你是 Qiazhi-Bazi 的 FinalVerdictSkill。"
    if high_reasoning:
        return base + "【高推理模式】插件 evidence 为全量条线，不做碎片化截断；须逐条映射到 assertions.evidence_refs。"
    return base


def _verdict_json_envelope_and_verdict_body_rules(*, high_reasoning: bool) -> str:
    # 原 User 末尾「三段 ###」已并入本字段说明，禁止双重指令。
    tail = ""
    if high_reasoning:
        tail = (
            "可选顶级字段 reasoning_feedback_loop：可为字符串或 JSON 对象，"
            "供系统写入元数据作为强模型推理摘要（勿写入 verdict_body）。"
        )
    return (
        "输出严格 JSON（仅此一个 JSON 对象，勿在 JSON 前后输出额外 Markdown 文档）："
        '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""},'
        '"assertions":[{"assertion_id":"a0","text":"一句完整断语","evidence_refs":["year.branch","conflict_matrix.cp_scan_0","plugin.classical.blind_school.v1"]}]}。'
        "其中 verdict_body 为**单个** Markdown 字符串，且必须依次包含且仅使用以下三个三级标题小节（顺序固定）："
        "### 核心气象 / ### 裁决共识 / ### 行为指引。"
        "不得在 JSON 外另行输出上述小节；所有叙事与标题均写入 verdict_body。"
        "### 核心气象 下第一段须先报告 Self_Abs 与 Tomb_State，再展开叙事。"
        "assertions 为必填：每句断语一条；evidence_refs 使用锚点字符串（柱位 year.stem/month.branch、conflict_matrix.<id>、plugin.<plugin_id>、meta.global_entropy 等），须可溯源到上文证据。"
        "change_log 仅写相对上一版的变化；若无上一版则写当前基线要点。"
        + tail
    )


def _policy_evidence_basis(*, high_reasoning: bool) -> str:
    if high_reasoning:
        return (
            "必须引用具体物理数值（十神绝对能量 Abs）作为依据；禁止空泛修辞。"
            "你生成的每一句命理断语，必须能在 [Physical Evidence] 里找到数值或标签支撑。"
        )
    return (
        "【叙事工厂·弱模型】禁止根据未在 Evidence 中出现的十神原始 Abs 数值自行重算强弱；"
        "能量强弱仅引用「语义.十神.*」档位行与插件切片、盲派做功行进行缝合。"
        "每条 assertions 的 evidence_refs 必须至少包含一个 plugin.* 锚点。"
        "你生成的每一句命理断语，必须能在 [Physical Evidence] 或插件切片中找到标签或结论支撑。"
    )


def _policy_core(*, high_reasoning: bool) -> str:
    return (
        "你必须每次返回一份全量、唯一、可执行的终判，不允许追加旧内容。"
        + _policy_evidence_basis(high_reasoning=high_reasoning)
        + "若与 [User Consensus] 冲突，必须以 [User Consensus] 为准。"
        + "请根据 [盲派硬核证据] 评估日主获取能量效率：做功值为负偏向“劳而无功”，为正偏向“取财有道”。"
        + "必须引用 net_effect 做辩证分析；当 backfire_risk 超过 unlock_gain 的50%时，严禁只给单边褒义结论，必须说明代价与震荡。"
        + "当出现 [BROKEN_LINK] 时，禁止讨论“库中之物已兑现”，只能讨论“能量淤积/怀才不遇”。"
        + "请分析 [Structure Candidates V0]。若出现 QuantumLeap，必须讨论岁运态射风险。"
        + "如果 [PHYSICS_CONSTRAINT] 出现，则不得出现“补印比/生扶日主”等建议。"
        + "如果 [BLIND_WORK_CONSTRAINT] 出现，则不得给出单边乐观结论。"
        + "如果 [BODY_DAMAGE_CONSTRAINT] 出现，必须明确指出体阵营受损节点及其代价，不得轻描淡写。"
        + "若出现 [LOGIC_CONFLICT_WARNING]，必须在 verdict_body 的「### 裁决共识」小节内显式写出两派冲突与折中路径。"
        + "你必须严格遵循 [Plugin Weight Guidance] 的语气和叙述重心。"
        + "严禁跳过 L1_Junction 直接下‘伤官见官’结论；必须先引用 [L1 Junction Flags]。"
        + "若 [Physical Evidence] 中出现以「地支.三合.」开头的证据行，必须在 verdict_body 的「### 核心气象」或「### 裁决共识」中评估该三合局对整体格调、"
        + "五行场强分布及做功门态（如墓库/合局聚能）的影响，不得忽略。"
        + "只要盘中存在地支三合局（证据行已给出），必须显式评估其对当前格调与做功逻辑的支撑或对冲作用，禁止仅用套话带过。"
    )


def build_final_verdict_system_message(
    *,
    high_reasoning: bool,
    lang: str,
) -> str:
    """
    组装终判 system 全文（不含盲派 skill 动态块；由调用方追加）。
    """
    parts = [
        _identity(high_reasoning=high_reasoning),
        _policy_core(high_reasoning=high_reasoning),
        _verdict_json_envelope_and_verdict_body_rules(high_reasoning=high_reasoning),
        evidence_mode_clause(high_reasoning=high_reasoning),
        EVOLUTION_LEARNING_CONTEXT_RULE,
        LanguageEngine.strict_assistant_output_language(lang),
    ]
    return "".join(parts)
