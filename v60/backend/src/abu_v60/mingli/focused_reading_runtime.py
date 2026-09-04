from __future__ import annotations

import re
import time
from typing import Any, Protocol

from abu_v60.llm_transport import JsonTransport, LlmTransportError, default_json_transport
from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.focused_reading_contracts import (
    MINGLI_FOCUS_ORDER,
    MINGLI_FOCUSED_PROMPT_VERSION,
    MINGLI_FOCUSED_RUNTIME_VERSION,
    MingliFocus,
    MingliFocusedPassResult,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.settings import Settings, settings

MINGLI_FOCUSED_PROVIDER_PROFILE_REF = "v60.model-serving.mingli-focused-text.008"
MINGLI_FOCUSED_NORMALIZER_VERSION = "v60.mingli-focused-normalizer.006"
MINGLI_FOCUSED_CONTEXT_MAX_CHARS = 6000
MINGLI_FOCUSED_OUTPUT_MAX_CHARS = 3000
MINGLI_FOCUSED_NUM_CTX = 4096
MINGLI_FOCUSED_NUM_PREDICT = 320
MINGLI_FOCUSED_SEED = 42
QWEN38_INSTRUCT_TEMPERATURE = 0.7
QWEN38_INSTRUCT_TOP_P = 0.8
QWEN38_INSTRUCT_TOP_K = 20
QWEN38_INSTRUCT_MIN_P = 0.0
QWEN38_INSTRUCT_PRESENCE_PENALTY = 1.5
QWEN38_INSTRUCT_REPEAT_PENALTY = 1.0

MINGLI_FOCUSED_SYSTEM_PROMPT = """
你是一位经验丰富、表达直接的八字命理师。每次只回答一个具体问题，不要包办整份命盘。
命盘资料由系统计算，四柱、十神、藏干、关系和岁运坐标不得重算或补造。
判断不闭合时写清成立条件，不编造已经发生的经历，不做疾病、灾祸或收益承诺。
只输出普通中文正文，不输出 JSON、Markdown、字段名、证据编号或思维过程。
""".strip()

FOCUSED_QUESTIONS: dict[MingliFocus, str] = {
    "STRUCTURE": (
        "只判断原局总纲：比较月令、根、印比、泄耗、财官压力，明确日主承载状态、"
        "最能统领全盘的主路径、一个竞争路径和主路径在原局内的失效条件，不谈岁运。"
        "控制在140至240字。"
    ),
    "LIFE_IMAGE_PERSONALITY": (
        "只解释生命意象与性情：以已经形成的原局总纲为准，给一个贴合日主五行的自然"
        "意象，并说明由结构推出的稳定行为模式及其边界。控制在120至200字。"
    ),
    "CAREER_WEALTH": (
        "只判断事业与财富：沿用原局主路径，分别说明做事方式、资源如何转化、财富如何"
        "形成以及最关键的承载或阻断条件，不列行业清单，不承诺收益。控制在140至220字。"
    ),
    "RELATIONSHIP_FAMILY": (
        "只判断关系与家庭：分别说明关系互动模式与家庭责任模式，必须同时看对应星轴、"
        "日支夫妻宫或相应宫位，不推断具体伴侣性格和既成事件。控制在140至220字。"
    ),
    "TIMING": (
        "只判断当前大运与所选流年：先复述原局基线，再说明大运改变哪条路径、流年如何"
        "继续推动或阻断；必须点名资料中的大运和流年，不补流月。控制在140至220字。"
    ),
}

MINGLI_FOCUSED_PROMPT_HASH = content_hash(
    {
        "prompt_version": MINGLI_FOCUSED_PROMPT_VERSION,
        "system": MINGLI_FOCUSED_SYSTEM_PROMPT,
        "questions": FOCUSED_QUESTIONS,
        "context_version": "v60.mingli-focused-context.001",
        "prompt_transport": "qwen38_chatml_nonthinking_raw_v1",
    }
)


class MingliFocusedRuntimeError(RuntimeError):
    pass


class MingliFocusedRuntimeUnavailable(MingliFocusedRuntimeError):
    pass


class MingliFocusedProvider(Protocol):
    provider_id: str
    model_ref: str
    model_digest: str
    provider_profile_ref: str
    provider_profile_hash: str

    def generate(self, *, packet: MingliAgentCasePacket) -> tuple[MingliFocusedPassResult, ...]: ...

    def generate_focus(
        self,
        *,
        packet: MingliAgentCasePacket,
        focus: MingliFocus,
        structure_text: str | None,
    ) -> MingliFocusedPassResult: ...


class OllamaFocusedReadingProvider:
    """Several small prose calls; deterministic code owns normalization."""

    provider_id = "ollama-generate"

    def __init__(
        self,
        *,
        model_ref: str,
        model_digest: str,
        base_url: str,
        timeout_seconds: float,
        temperature: float,
        top_p: float,
        top_k: int,
        keep_alive: str,
        transport: JsonTransport = default_json_transport,
    ) -> None:
        if not model_ref or len(model_digest) != 64:
            raise ValueError("mingli_focused_provider_identity_invalid")
        self.model_ref = model_ref
        self.model_digest = model_digest
        self.provider_profile_ref = MINGLI_FOCUSED_PROVIDER_PROFILE_REF
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = min(timeout_seconds, 180.0)
        self._is_qwen38 = model_ref.lower().startswith("qwen3.8")
        self._temperature = QWEN38_INSTRUCT_TEMPERATURE if self._is_qwen38 else temperature
        self._top_p = QWEN38_INSTRUCT_TOP_P if self._is_qwen38 else top_p
        self._top_k = QWEN38_INSTRUCT_TOP_K if self._is_qwen38 else top_k
        self._min_p = QWEN38_INSTRUCT_MIN_P if self._is_qwen38 else 0.0
        self._presence_penalty = QWEN38_INSTRUCT_PRESENCE_PENALTY if self._is_qwen38 else 0.0
        self._repeat_penalty = QWEN38_INSTRUCT_REPEAT_PENALTY
        self._keep_alive = keep_alive
        self._transport = transport
        self.provider_profile_hash = content_hash(self.provider_profile)

    @property
    def provider_profile(self) -> dict[str, Any]:
        return {
            "provider_profile_ref": self.provider_profile_ref,
            "provider_id": self.provider_id,
            "model_ref": self.model_ref,
            "model_digest": self.model_digest,
            "runtime_ref": MINGLI_FOCUSED_RUNTIME_VERSION,
            "prompt_version": MINGLI_FOCUSED_PROMPT_VERSION,
            "prompt_hash": MINGLI_FOCUSED_PROMPT_HASH,
            "normalizer_version": MINGLI_FOCUSED_NORMALIZER_VERSION,
            "call_count": len(MINGLI_FOCUS_ORDER),
            "structured_output_mode": "natural_text",
            "prompt_transport": "raw_combined_system_and_question",
            "chat_template_mode": (
                "QWEN38_OFFICIAL_CHATML_NON_THINKING" if self._is_qwen38 else "RAW_COMBINED_TEXT"
            ),
            "think": False,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "top_k": self._top_k,
            "min_p": self._min_p,
            "presence_penalty": self._presence_penalty,
            "repeat_penalty": self._repeat_penalty,
            "seed": MINGLI_FOCUSED_SEED,
            "num_ctx": MINGLI_FOCUSED_NUM_CTX,
            "num_predict_per_call": MINGLI_FOCUSED_NUM_PREDICT,
            "keep_alive": self._keep_alive,
        }

    def generate(
        self,
        *,
        packet: MingliAgentCasePacket,
    ) -> tuple[MingliFocusedPassResult, ...]:
        results: list[MingliFocusedPassResult] = []
        structure_text: str | None = None
        for focus in MINGLI_FOCUS_ORDER:
            result = self.generate_focus(
                packet=packet,
                focus=focus,
                structure_text=structure_text,
            )
            results.append(result)
            if focus == "STRUCTURE":
                structure_text = result.normalized_text
        return tuple(results)

    def generate_focus(
        self,
        *,
        packet: MingliAgentCasePacket,
        focus: MingliFocus,
        structure_text: str | None,
    ) -> MingliFocusedPassResult:
        if focus != "STRUCTURE" and not structure_text:
            raise MingliFocusedRuntimeError("mingli_focused_structure_required")
        context = focused_context(
            packet,
            focus=focus,
            structure_text=structure_text,
        )
        context_json = canonical_json(context)
        if len(context_json) > MINGLI_FOCUSED_CONTEXT_MAX_CHARS:
            raise MingliFocusedRuntimeError(f"mingli_focused_context_budget_exceeded:{focus}")
        started = time.monotonic()
        try:
            response = self._transport(
                url=f"{self._base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                payload=self._payload(
                    focus=focus,
                    context_json=context_json,
                ),
                timeout_seconds=self._timeout_seconds,
            )
        except LlmTransportError as exc:
            raise MingliFocusedRuntimeError(
                f"mingli_focused_provider_failed:{focus}:{exc}"
            ) from exc
        duration_ms = max(0, round((time.monotonic() - started) * 1000))
        raw_text = response.get("response")
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise MingliFocusedRuntimeError(f"mingli_focused_provider_output_missing:{focus}")
        normalized_text, codes = normalize_focused_text(
            raw_text,
            focus=focus,
            packet=packet,
        )
        input_tokens = _nonnegative_int(response.get("prompt_eval_count"))
        output_tokens = _nonnegative_int(response.get("eval_count"))
        response_ref = stable_ref(
            "v60-mingli-focused-provider-response",
            {
                "provider_id": self.provider_id,
                "model_ref": self.model_ref,
                "model_digest": self.model_digest,
                "provider_profile_hash": self.provider_profile_hash,
                "packet_hash": packet.packet_hash,
                "focus": focus,
                "context_hash": content_hash(context),
                "raw_text_hash": content_hash(raw_text),
                "created_at": response.get("created_at"),
            },
        )
        return MingliFocusedPassResult.issue(
            focus=focus,
            question=FOCUSED_QUESTIONS[focus],
            context_hash=content_hash(context),
            provider_response_ref=response_ref,
            raw_text=raw_text.strip(),
            normalized_text=normalized_text,
            normalization_codes=codes,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            duration_ms=duration_ms,
        )

    def _payload(self, *, focus: MingliFocus, context_json: str) -> dict[str, Any]:
        user_prompt = f"本次问题：{FOCUSED_QUESTIONS[focus]}\n\n命盘资料：{context_json}"
        return {
            "model": self.model_ref,
            "prompt": self._render_prompt(user_prompt),
            "raw": True,
            "stream": False,
            "think": False,
            "options": {
                "temperature": self._temperature,
                "top_p": self._top_p,
                "top_k": self._top_k,
                "min_p": self._min_p,
                "presence_penalty": self._presence_penalty,
                "repeat_penalty": self._repeat_penalty,
                "seed": MINGLI_FOCUSED_SEED,
                "num_ctx": MINGLI_FOCUSED_NUM_CTX,
                "num_predict": MINGLI_FOCUSED_NUM_PREDICT,
                "stop": ["<|im_end|>"],
            },
            "keep_alive": self._keep_alive,
        }

    def _render_prompt(self, user_prompt: str) -> str:
        if not self._is_qwen38:
            return f"{MINGLI_FOCUSED_SYSTEM_PROMPT}\n\n{user_prompt}"
        return (
            "<|im_start|>system\n"
            f"{MINGLI_FOCUSED_SYSTEM_PROMPT}<|im_end|>\n"
            "<|im_start|>user\n"
            f"{user_prompt}<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>\n\n</think>\n\n"
        )


def focused_context(
    packet: MingliAgentCasePacket,
    *,
    focus: MingliFocus,
    structure_text: str | None,
) -> dict[str, Any]:
    pillars = tuple(
        {
            "位置": item.slot,
            "四柱": item.pillar,
            "明干十神": item.visible_ten_god,
            "藏干十神": tuple(
                f"{stem}{ten_god}"
                for stem, ten_god in zip(
                    item.hidden_stems,
                    item.hidden_ten_gods,
                    strict=True,
                )
            ),
        }
        for item in packet.pillars
    )
    base: dict[str, Any] = {
        "日主": packet.day_master_stem,
        "月令": packet.month_command_branch,
        "四柱与透藏": pillars,
        "根候选": packet.day_master_support.same_element_hidden_support,
        "日主同字根候选": packet.day_master_support.same_identity_hidden_support,
        "明干同类": packet.day_master_support.visible_peer_support,
        "印星生扶": packet.day_master_support.resource_support,
        "已准入原局关系": tuple(
            _relation_label(item.relation_type, item.left_branch, item.right_branch)
            for item in packet.natal_relations
        ),
    }
    if structure_text is not None:
        base["前序原局总纲"] = structure_text
    if focus == "STRUCTURE":
        base["机制候选"] = tuple(
            {
                "名称": item.label,
                "结构": item.structural_statement,
                "角色顺序": item.role_summary,
                "待检查阻断": item.blocker_codes,
            }
            for item in packet.mechanism_observations
        )
    elif focus == "LIFE_IMAGE_PERSONALITY":
        base["意象边界"] = f"主角必须保持{packet.day_master_element}的五行物象"
    elif focus == "CAREER_WEALTH":
        base["十神坐标"] = _ten_god_coordinates(packet)
    elif focus == "RELATIONSHIP_FAMILY":
        day = packet.pillars[2]
        base.update(
            {
                "性别": packet.gender,
                "夫妻宫": {
                    "日支": day.branch,
                    "藏干十神": day.hidden_ten_gods,
                },
                "十神坐标": _ten_god_coordinates(packet),
            }
        )
    elif focus == "TIMING":
        base.update(
            {
                "分析日期": packet.timing_analysis_date,
                "大运与流年": tuple(
                    {
                        "层": item.layer,
                        "干支": item.pillar,
                        "十神": item.ten_god_label,
                        "起年": item.start_year,
                        "止年": item.end_year,
                    }
                    for item in packet.timing_coordinates
                ),
                "已准入岁运关系": tuple(
                    _relation_label(
                        item.relation_type,
                        item.left_branch,
                        item.right_branch,
                    )
                    for item in packet.timing_relations
                ),
                "流月资料": "未提供",
            }
        )
    return base


def normalize_focused_text(
    raw_text: str,
    *,
    focus: MingliFocus,
    packet: MingliAgentCasePacket,
) -> tuple[str, tuple[str, ...]]:
    """Normalize presentation only; semantic uncertainty stays visible."""

    codes: set[str] = set()
    text = raw_text.strip()
    without_fence = re.sub(
        r"```(?:json|markdown|text)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    without_fence = without_fence.replace("```", "")
    if without_fence != text:
        codes.add("MARKDOWN_FENCE_REMOVED")
    text = without_fence
    without_evidence = re.sub(r"(?<![A-Za-z0-9])E\d{3}(?![A-Za-z0-9])", "", text)
    if without_evidence != text:
        codes.add("EVIDENCE_TOKEN_REMOVED")
    text = without_evidence
    lines = []
    markdown_removed = False
    for raw_line in text.replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r"^(?:#{1,6}\s*|[-*+]\s+|\d+[.)、]\s*)", "", line)
        normalized = normalized.replace("**", "").strip()
        markdown_removed = markdown_removed or normalized != line
        if normalized:
            lines.append(re.sub(r"[ \t]+", " ", normalized))
    if markdown_removed:
        codes.add("MARKDOWN_PRESENTATION_REMOVED")
    text = "\n".join(lines).strip()
    if not text:
        raise MingliFocusedRuntimeError("mingli_focused_normalization_empty")
    if len(text) > MINGLI_FOCUSED_OUTPUT_MAX_CHARS:
        boundary = max(
            text.rfind(marker, 0, MINGLI_FOCUSED_OUTPUT_MAX_CHARS)
            for marker in ("。", "！", "？", "\n")
        )
        text = text[: boundary + 1 if boundary >= 120 else MINGLI_FOCUSED_OUTPUT_MAX_CHARS]
        codes.add("OUTPUT_LENGTH_TRUNCATED")
    text, visible_ten_god_codes = _normalize_visible_ten_god_coordinates(
        text,
        packet=packet,
    )
    codes.update(visible_ten_god_codes)
    text, focus_scope_codes = _normalize_focus_scope(text, focus=focus)
    codes.update(focus_scope_codes)
    if re.search(r"必然|注定|百分之百|绝对会|一定会|必定|唯有|只有.+才|方能", text):
        codes.add("ABSOLUTE_CLAIM_REQUIRES_REVIEW")
    if re.search(r"疾病|癌症|死亡|灾祸|血光|牢狱|身心失衡", text):
        codes.add("HEALTH_DISASTER_CLAIM_REQUIRES_REVIEW")
    if re.search(r"焦虑|抑郁|精神失常|心理疾病", text):
        codes.add("PSYCHOLOGICAL_CLAIM_REQUIRES_REVIEW")
    if re.search(r"原生家庭|童年|早年|离婚|丧偶|已经发生|曾经", text):
        codes.add("UNSUPPORTED_BIOGRAPHICAL_CLAIM_REQUIRES_REVIEW")
    if re.search(r"从财|从杀|从势|从儿|专旺|身弱财旺(?:格局)?", text):
        codes.add("REGIME_ASSERTION_REQUIRES_REVIEW")
    if focus != "TIMING" and re.search(r"大运|流年|岁运", text):
        codes.add("TIMING_SCOPE_LEAK_REQUIRES_REVIEW")
    if focus == "TIMING":
        expected = tuple(item.pillar for item in packet.timing_coordinates)
        if any(item not in text for item in expected):
            codes.add("TIMING_COORDINATE_OMITTED")
    codes.update(_five_element_causal_codes(text))
    codes.update(_pillar_coordinate_codes(text, packet=packet))
    codes.update(_hidden_stem_coordinate_codes(text, packet=packet))
    codes.update(_unadmitted_relation_codes(text, packet=packet, focus=focus))
    return text, tuple(sorted(codes))


def _normalize_visible_ten_god_coordinates(
    text: str,
    *,
    packet: MingliAgentCasePacket,
) -> tuple[str, set[str]]:
    """Repair explicit visible-stem counts from deterministic packet facts."""

    pattern = re.compile(
        r"(?P<positions>[年月日时](?:柱|干)?"
        r"(?:[、及与和][年月日时](?:柱|干)?)+)"
        r"(?P<count>[一二两三四]?)透"
        r"(?P<ten_god>正财|偏财|正官|七杀|正印|偏印|食神|伤官|比肩|劫财)"
    )
    slot_labels = {
        "year": "年",
        "month": "月",
        "day": "日",
        "hour": "时",
    }
    numeral_values = {"": None, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4}
    count_labels = {1: "一", 2: "两", 3: "三", 4: "四"}
    repaired = False

    def replace_claim(match: re.Match[str]) -> str:
        nonlocal repaired
        ten_god = match.group("ten_god")
        claimed_positions = tuple(re.findall(r"[年月日时]", match.group("positions")))
        actual_positions = tuple(
            slot_labels[item.slot]
            for item in packet.pillars
            if item.slot in slot_labels and item.visible_ten_god == ten_god
        )
        claimed_count = numeral_values[match.group("count")]
        if (
            claimed_positions == actual_positions
            and (claimed_count is None or claimed_count == len(actual_positions))
        ):
            return match.group(0)

        repaired = True
        if not actual_positions:
            return f"天干不透{ten_god}"
        labels = "、".join(f"{position}干" for position in actual_positions)
        if len(actual_positions) == 1:
            return f"{labels}透{ten_god}"
        return f"{labels}{count_labels[len(actual_positions)]}透{ten_god}"

    normalized = pattern.sub(replace_claim, text)
    return (
        normalized,
        {"VISIBLE_TEN_GOD_COORDINATE_REPAIRED"} if repaired else set(),
    )


def _normalize_focus_scope(
    text: str,
    *,
    focus: MingliFocus,
) -> tuple[str, set[str]]:
    if focus == "TIMING":
        return text, set()
    scoped = re.sub(
        r"若岁运再行([木火土金水])地[，,]\1势过旺则",
        r"若\1势继续过旺，",
        text,
    )
    normalized = scoped.replace(
        "焚木，导致日主彻底枯竭",
        "日主承载会进一步减弱",
    )
    codes: set[str] = set()
    if scoped != text:
        codes.add("TIMING_SCOPE_PHRASE_REMOVED")
    if normalized != scoped:
        codes.add("ABSOLUTE_TONE_SOFTENED")
    return normalized, codes


def _five_element_causal_codes(text: str) -> set[str]:
    generates = {"木火", "火土", "土金", "金水", "水木"}
    controls = {"木土", "土水", "水火", "火金", "金木"}
    leaks = {pair[::-1] for pair in generates}
    for source, verb, target in re.findall(
        r"([木火土金水])(?:能|可|来|以)?(?:化)?(生|克|泄)"
        r"(?:[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥])?"
        r"([木火土金水])",
        text,
    ):
        valid = generates if verb == "生" else controls if verb == "克" else leaks
        if source + target not in valid:
            return {"FIVE_ELEMENT_CAUSAL_CONFLICT_REQUIRES_REVIEW"}
    if "财印相生" in text:
        return {"FIVE_ELEMENT_CAUSAL_CONFLICT_REQUIRES_REVIEW"}
    return set()


def _hidden_stem_coordinate_codes(
    text: str,
    *,
    packet: MingliAgentCasePacket,
) -> set[str]:
    hidden_by_branch = {item.branch: set(item.hidden_stems) for item in packet.pillars}
    for match in re.finditer(
        r"([子丑寅卯辰巳午未申酉戌亥、及与和]+)(?:中|内)?藏"
        r"([甲乙丙丁戊己庚辛壬癸、及与和]+)",
        text,
    ):
        branches = set(re.findall(r"[子丑寅卯辰巳午未申酉戌亥]", match.group(1)))
        stems = set(re.findall(r"[甲乙丙丁戊己庚辛壬癸]", match.group(2)))
        admitted = set().union(*(hidden_by_branch.get(branch, set()) for branch in branches))
        if stems - admitted:
            return {"HIDDEN_STEM_COORDINATE_CONFLICT_REQUIRES_REVIEW"}
    return set()


def _pillar_coordinate_codes(
    text: str,
    *,
    packet: MingliAgentCasePacket,
) -> set[str]:
    codes: set[str] = set()
    month = packet.pillars[1]
    direct_month_stems = re.findall(
        r"月令(?:为|是)?(?:正财|偏财|正官|七杀|正印|偏印|食神|伤官|比肩|劫财)?"
        r"([甲乙丙丁戊己庚辛壬癸])[木火土金水]?",
        text,
    )
    if any(stem not in month.hidden_stems for stem in direct_month_stems):
        codes.add("MONTH_COMMAND_COORDINATE_CONFLICT_REQUIRES_REVIEW")

    branch_counts = {
        branch: sum(item.branch == branch for item in packet.pillars)
        for branch in "子丑寅卯辰巳午未申酉戌亥"
    }
    numerals = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4}
    for segment in re.findall(r"地支([^。！？；，]*)", text):
        claims = re.findall(r"([一二两三四])([子丑寅卯辰巳午未申酉戌亥])", segment)
        if any(branch_counts[branch] != numerals[count] for count, branch in claims):
            codes.add("BRANCH_COUNT_CONFLICT_REQUIRES_REVIEW")
            break
    return codes


def _unadmitted_relation_codes(
    text: str,
    *,
    packet: MingliAgentCasePacket,
    focus: MingliFocus,
) -> set[str]:
    relations = packet.timing_relations if focus == "TIMING" else packet.natal_relations
    admitted = {item.relation_type for item in relations}
    terms = {
        "六冲": "six_clash_membership",
        "六合": "six_harmony_membership",
        "同支": "same_branch_membership",
    }
    codes = {
        "UNADMITTED_RELATION_TERM_REQUIRES_REVIEW"
        for term, relation_type in terms.items()
        if term in text and relation_type not in admitted
    }
    if re.search(r"三合|三会|相刑|三刑|六害|相害|相破", text):
        codes.add("UNADMITTED_RELATION_TERM_REQUIRES_REVIEW")
    if re.search(r"甲己合|乙庚合|丙辛合|丁壬合|戊癸合", text):
        codes.add("UNADMITTED_RELATION_TERM_REQUIRES_REVIEW")
    relation_language = re.search(
        r"六冲|六合|同支|相冲|冲克|相合|合化|三合|三会|相刑|相害|相破",
        text,
    )
    effect_language = re.search(
        r"引发|导致|阻断|动荡|断裂|冲击|冲动|受损|破坏|激发|改变|加剧|化去",
        text,
    )
    if re.search(r"[木火土金水]局", text) or (relation_language and effect_language):
        codes.add("UNADMITTED_RELATION_EFFECT_REQUIRES_REVIEW")
    return codes


def _ten_god_coordinates(packet: MingliAgentCasePacket) -> tuple[dict[str, Any], ...]:
    values: dict[str, list[str]] = {}
    for item in packet.pillars:
        values.setdefault(item.visible_ten_god, []).append(f"{item.slot}干{item.stem}")
        for stem, ten_god in zip(
            item.hidden_stems,
            item.hidden_ten_gods,
            strict=True,
        ):
            values.setdefault(ten_god, []).append(f"{item.slot}支藏{stem}")
    return tuple({"十神": key, "坐标": tuple(value)} for key, value in sorted(values.items()))


def _relation_label(relation_type: str, left: str, right: str) -> str:
    label = {
        "same_branch_membership": "同支成员",
        "six_clash_membership": "六冲成员",
        "six_harmony_membership": "六合成员",
    }[relation_type]
    return f"{left}{right}{label}"


def _nonnegative_int(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


class MingliFocusedRuntime:
    def __init__(self, *, provider: MingliFocusedProvider | None, enabled: bool) -> None:
        self._provider = provider
        self._enabled = enabled

    @property
    def ready(self) -> bool:
        return self._enabled and self._provider is not None

    def required_provider(self) -> MingliFocusedProvider:
        if not self.ready or self._provider is None:
            raise MingliFocusedRuntimeUnavailable("mingli_focused_runtime_not_ready")
        return self._provider


def configured_mingli_focused_runtime(
    current_settings: Settings = settings,
) -> MingliFocusedRuntime:
    enabled = (
        current_settings.mingli_agent_enabled
        and current_settings.mingli_agent_provider == "ollama-generate"
        and not current_settings.mingli_agent_think
    )
    provider = None
    if enabled:
        provider = OllamaFocusedReadingProvider(
            model_ref=current_settings.mingli_agent_model,
            model_digest=current_settings.mingli_agent_model_digest,
            base_url=current_settings.mingli_agent_base_url,
            timeout_seconds=current_settings.mingli_agent_timeout_seconds,
            temperature=current_settings.mingli_agent_temperature,
            top_p=current_settings.mingli_agent_top_p,
            top_k=current_settings.mingli_agent_top_k,
            keep_alive=current_settings.mingli_agent_keep_alive,
        )
    return MingliFocusedRuntime(provider=provider, enabled=enabled)


def mingli_focused_runtime_manifest(
    current_settings: Settings = settings,
) -> dict[str, Any]:
    runtime = configured_mingli_focused_runtime(current_settings)
    if not runtime.ready:
        return {
            "runtime_ref": MINGLI_FOCUSED_RUNTIME_VERSION,
            "status": "DISABLED",
            "runtime_role": "PRODUCT_FOCUSED_READING",
            "generation_mode": "PROGRESSIVE_ONE_FOCUS_PER_REQUEST",
            "product_call_count_per_request": 1,
            "dev_batch_call_count": len(MINGLI_FOCUS_ORDER),
            "network_calls_enabled": False,
            "openai_api_required": False,
            "production_dependencies": ("DETERMINISTIC_LOCAL_SYSTEM", "LOCAL_QWEN"),
            "publication_allowed": False,
            "canonical_fact_write_allowed": False,
        }
    provider = runtime.required_provider()
    return {
        "runtime_ref": MINGLI_FOCUSED_RUNTIME_VERSION,
        "status": "READY_FOR_OWNER_REVIEW",
        "runtime_role": "PRODUCT_FOCUSED_READING",
        "generation_mode": "PROGRESSIVE_ONE_FOCUS_PER_REQUEST",
        "product_call_count_per_request": 1,
        "dev_batch_call_count": len(MINGLI_FOCUS_ORDER),
        "network_calls_enabled": True,
        "openai_api_required": False,
        "production_dependencies": ("DETERMINISTIC_LOCAL_SYSTEM", "LOCAL_QWEN"),
        "prompt_version": MINGLI_FOCUSED_PROMPT_VERSION,
        "prompt_hash": MINGLI_FOCUSED_PROMPT_HASH,
        "provider_profile": provider.provider_profile,
        "provider_profile_hash": provider.provider_profile_hash,
        "focus_order": MINGLI_FOCUS_ORDER,
        "teacher_review_runtime_dependency": False,
        "publication_allowed": False,
        "canonical_fact_write_allowed": False,
    }
