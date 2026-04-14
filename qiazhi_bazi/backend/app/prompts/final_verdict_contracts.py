"""
终判 LLM：System 契约（与 User 证据拼装解耦）。

约束尽量后置：assertion_id / evidence_refs 形态以 JSON 示例为准，parse 阶段裁剪与启发式补全。
"""

from __future__ import annotations

from app.prompts.evolution_contracts import EVOLUTION_LEARNING_CONTEXT_RULE
from app.prompts.language import LanguageEngine


def _strict_json_only_header(*, lang: str) -> str:
    u = (lang or "ZH").upper()
    if u == "EN":
        return (
            "[STRICT_JSON_ONLY] Do not output any natural language outside JSON, chain-of-thought, or English explanations "
            "outside the JSON object. Do not use Markdown code fences. "
            "Your output must be valid JSON text (single-line or multi-line), starting with \"{\" and ending with \"}\"."
        )
    if u == "KO":
        return (
            "[STRICT_JSON_ONLY] JSON 객체 외부에는 자연어·사고 과정·Markdown 펜스를 출력하지 마십시오. "
            "출력은 반드시 유효한 JSON 텍스트(단일 또는 여러 줄)이며, 첫 문자는 \"{\", 마지막 문자는 \"}\"여야 합니다."
        )
    return (
        "[STRICT_JSON_ONLY] 严禁输出任何自然语言、思考过程或英文解释。禁止任何 Markdown 围栏。"
        "你的输出必须是合法的 JSON 对象文本（单行或多行均可），首字符为「{」末字符为「}」。"
    )


def evidence_user_block_heading(*, high_reasoning: bool) -> str:
    """兼容旧拼装路径。"""
    return "插件切片·全量" if high_reasoning else "插件切片·摘要"


def evidence_mode_clause(*, high_reasoning: bool) -> str:
    """已并入 System JSON 示例；保留函数供注册表/旧测试 import。"""
    return ""


def _identity(*, high_reasoning: bool, lang: str) -> str:
    u = (lang or "ZH").upper()
    if u == "EN":
        tail = (
            " High reasoning: you may expand Auxiliary trace fields and reasoning_feedback_loop metadata (not in verdict_body)."
            if high_reasoning
            else ""
        )
        return (
            "Role: Final Narrator (final verdict synthesis slot only). "
            "You are NOT a free-form writer. Ziping metaphysics context; User payload is backend-devolved "
            "without floating-point literals in physical facts."
            + tail
        )
    if u == "KO":
        tail = (
            " 고차원 추론: Auxiliary·추적 및 reasoning_feedback_loop 메타데이터를 확장할 수 있음(verdict_body 외)."
            if high_reasoning
            else ""
        )
        return (
            "역할: 최종 내레이터(종심, SYNTHESIS 슬롯 전용). 자유 서술 작가가 아닙니다. "
            "자평(子平) 맥락; User 페이로드는 백엔드가 수치 리터럴 없이 요약한 물리 사실."
            + tail
        )
    tail = "高推理可展开 Auxiliary·溯源与 reasoning_feedback_loop 元字段。" if high_reasoning else ""
    return (
        "角色：Final Narrator（终审·仅SYNTHESIS槽位）。你不是自由写作器。"
        "简体中文子平语境；User 经后端脱水，无浮点物理字面量。"
        + tail
    )


def _verdict_json_envelope_and_verdict_body_rules(*, high_reasoning: bool, lang: str) -> str:
    u = (lang or "ZH").upper()
    tail = " Optional top-level reasoning_feedback_loop (do not put it in verdict_body)." if high_reasoning else ""
    if u == "EN":
        return (
            "Emit exactly one JSON object (no surrounding Markdown): "
            '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""},'
            '"assertions":[{"assertion_id":"a0","text":"one sentence","evidence_refs":["VF01","year.stem","plugin.sys.core.physics"]]}。'
            "BLACKOUT TEST MODE: verdict_body may contain ONLY one heading: "
            "### SYNTHESIS. No extra sections, no free-writing expansion. "
            "change_log records deltas vs the previous version. "
            "Preserve every VF01, VF02, … token from [VerdictSkeleton] / [Verified Facts] verbatim in verdict_body."
            + tail
        )
    if u == "KO":
        return (
            "출력은 JSON 객체 하나만(Markdown 펜스 없음): "
            '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""},'
            '"assertions":[{"assertion_id":"a0","text":"한 문장","evidence_refs":["VF01","year.stem","plugin.sys.core.physics"]]}。'
            "BLACKOUT TEST MODE: verdict_body는 ### SYNTHESIS 한 개 섹션만 허용. "
            "자유 서술 확장 금지. change_log는 이전 버전 대비 차이. "
            "[VerdictSkeleton]/[Verified Facts]의 VF01, VF02 … 토큰은 원문 그대로 보존."
            + tail
        )
    tail_zh = " 可选顶层 reasoning_feedback_loop（勿写入 verdict_body）。" if high_reasoning else ""
    return (
        "仅输出一个 JSON（前后无其它 Markdown）："
        '{"verdict_body":"markdown","change_log":{"physics_diff":[],"consensus_diff":[],"text_diff_hint":""},'
        '"assertions":[{"assertion_id":"a0","text":"一句断语","evidence_refs":["VF01","year.stem","plugin.sys.core.physics"]]}。'
        "BLACKOUT 测试模式：verdict_body 仅允许一个三级标题 ### SYNTHESIS，"
        "禁止自由写作扩展段落；change_log 写相对上一版差异。"
        + tail_zh
    )


def _policy_core(*, high_reasoning: bool, lang: str) -> str:
    u = (lang or "ZH").upper()
    if u == "EN":
        return (
            "Fact boundary follows [Verified Facts] and [User Decisions]; on conflict prefer the latter. "
            "Use only qualitative lines already present for blind school / tomb / luck-year etc.; do not invent numbers."
            + (
                " High reasoning: you may elaborate Auxiliary; do not invent unseen pillars or plugin facts."
                if high_reasoning
                else ""
            )
        )
    if u == "KO":
        return (
            "사실 경계는 [Verified Facts]·[User Decisions]를 따르며 충돌 시 후자 우선. "
            "맹파/묘고/세운 등은 Context에 이미 있는 정성 문장만 사용하고 수치를 새로 만들지 마십시오."
            + (" 고차원 추론: Auxiliary는 확장 가능하나 미등장 기둥·플러그인 사실을 발명하지 마십시오." if high_reasoning else "")
        )
    return (
        "事实边界以 [Verified Facts]、[User Decisions] 为准，冲突时从后者。"
        "盲派/墓库/岁运等只使用 Context 已有定性句，不补数值。"
        + (" 高推理：可铺陈 Auxiliary，不得发明未出现的柱支或插件事实。" if high_reasoning else "")
    )


def _contract_polish_mode_clause(*, lang: str) -> str:
    u = (lang or "ZH").upper()
    if u == "EN":
        return (
            "[CONTRACT_MODE] You are a semantic polish agent only. The system has already fixed conclusions; do not change logic. "
            "In verdict_body you must preserve every VF01, VF02, … token exactly as in [VerdictSkeleton] and [Verified Facts] "
            "(including the VF prefix and two digits); do not delete, rewrite, or renumber them; only polish surrounding prose.\n"
        )
    if u == "KO":
        return (
            "[CONTRACT_MODE] 현재는 의미 다듬기 에이전트입니다. 시스템이 결론을 확정했으므로 논리를 바꾸지 마십시오. "
            "verdict_body에서 [VerdictSkeleton]·[Verified Facts]의 VF01, VF02 … 표기는(VF 접두어+두 자리) 원문 그대로 유지하고 "
            "삭제·재작성·재번호를 금지하며, 주변 문장만 자연스럽게 다듬으십시오.\n"
        )
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
    contract_head = _contract_polish_mode_clause(lang=lang) if contract_polish_mode else ""
    parts = [
        _strict_json_only_header(lang=lang),
        contract_head,
        _identity(high_reasoning=high_reasoning, lang=lang),
        _policy_core(high_reasoning=high_reasoning, lang=lang),
        _verdict_json_envelope_and_verdict_body_rules(high_reasoning=high_reasoning, lang=lang),
        EVOLUTION_LEARNING_CONTEXT_RULE,
        LanguageEngine.strict_assistant_output_language(lang),
    ]
    return "".join(parts)
