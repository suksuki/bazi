from __future__ import annotations

from typing import Any


FRAMEWORK_VERSION = "v20.role_question_narrative_prompt_framework.v1"


VOICE_PROFILES: tuple[dict[str, object], ...] = (
    {
        "voice_profile": "guest_soft_entry",
        "role_keys": ("guest",),
        "person": "you_light",
        "tone": "soft_entry",
        "term_density": "low",
        "question_length": "short",
        "question_structure": ("title", "why_now", "next_step"),
        "answer_structure": ("先看哪里", "为什么值得看", "下一步可以问什么"),
        "required_elements": ("plain_language", "gentle_next_step"),
        "forbidden_patterns": ("fatalistic_claim", "dense_jargon", "absolute_prediction"),
    },
    {
        "voice_profile": "user_guided_reading",
        "role_keys": ("user",),
        "person": "you_direct",
        "tone": "guided_reading",
        "term_density": "medium_low",
        "question_length": "medium",
        "question_structure": ("title", "why_now", "bazi_basis", "next_step"),
        "answer_structure": ("当前主线", "命理依据的人话解释", "需要留意的边界", "下一步问题"),
        "required_elements": ("why_now", "bazi_basis_plain_language", "next_step"),
        "forbidden_patterns": ("fatalistic_claim", "unsupported_life_event", "absolute_prediction"),
    },
    {
        "voice_profile": "practitioner_evidence_review",
        "role_keys": ("analyst", "practitioner"),
        "person": "chart_review",
        "tone": "evidence_review",
        "term_density": "high",
        "question_length": "structured",
        "question_structure": ("title", "why_now", "bazi_basis", "boundary", "next_step"),
        "answer_structure": ("主线判断", "证据链", "反证/边界", "可复核问题", "调整建议"),
        "required_elements": ("evidence", "boundary", "counterexample_condition"),
        "forbidden_patterns": ("candidate_as_conclusion", "missing_boundary", "absolute_prediction"),
    },
    {
        "voice_profile": "admin_runtime_observe",
        "role_keys": ("admin", "lab"),
        "person": "system_observe",
        "tone": "runtime_observation",
        "term_density": "system",
        "question_length": "structured",
        "question_structure": ("title", "source", "policy_effect", "runtime_note", "next_observation"),
        "answer_structure": ("策略来源", "排序依据", "runtime pointer 影响", "gate / blocker", "观测建议"),
        "required_elements": ("source", "policy", "runtime", "gate"),
        "forbidden_patterns": ("user_fortune_reading", "unsupported_runtime_claim"),
    },
)


def build_role_question_narrative_prompt_framework() -> dict[str, object]:
    return {
        "version": FRAMEWORK_VERSION,
        "status": "runtime_consumed_and_training_ready",
        "module": "role_question_narrative_and_answer_prompt",
        "voice_profiles": list(VOICE_PROFILES),
        "question_narrative_schema": {
            "version": "v20.question_narrative.schema.v1",
            "fields": (
                "role_key",
                "voice_profile",
                "title",
                "why_now",
                "bazi_basis",
                "boundary",
                "next_step",
                "tone_guardrails",
            ),
            "runtime_mutation": False,
        },
        "answer_prompt_profile_schema": {
            "version": "v20.answer_prompt_profile.schema.v1",
            "fields": (
                "role_key",
                "voice_profile",
                "system_style",
                "answer_structure",
                "forbidden_patterns",
                "required_elements",
                "locale_policy",
            ),
            "runtime_mutation": False,
        },
        "mainline_steps": (
            _step("S1", "define_framework_contract", "completed"),
            _step("S2", "add_question_narrative_schema", "completed"),
            _step("S3", "attach_voice_profile_to_role_view_model", "completed"),
            _step("S4", "llm_prompt_reads_answer_prompt_profile", "completed"),
            _step("S5", "ui_consumes_question_narrative", "completed"),
            _step("S6", "synthetic_voice_replay_validates_tone", "completed"),
            _step("S7", "role_question_narrative_training_auto_applies", "completed"),
        ),
        "training_topics": (
            {
                "topic_key": "role_question_narrative_training",
                "parameter_targets": (
                    "voice_profile_weight",
                    "why_now_density",
                    "term_density_by_role",
                    "next_step_presence",
                    "forbidden_phrase_penalty",
                ),
                "runtime_pointer_targets": ("role_view_runtime_policy_pointer", "question_runtime_policy_pointer"),
            },
            {
                "topic_key": "answer_prompt_profile_training",
                "parameter_targets": (
                    "answer_structure_weight",
                    "role_prompt_tone",
                    "evidence_boundary_density",
                    "llm_forbidden_pattern_penalty",
                ),
                "runtime_pointer_targets": ("knowledge_runtime_policy_pointer", "role_view_runtime_policy_pointer"),
            },
        ),
        "synthetic_validation": {
            "guest": ("no_dense_jargon", "soft_next_step", "no_absolute_prediction"),
            "user": ("has_why_now", "has_plain_bazi_basis", "has_next_step"),
            "practitioner": ("has_evidence", "has_boundary", "has_counterexample_condition"),
            "admin": ("has_source", "has_policy", "has_runtime_or_gate"),
            "all_roles": ("no_fatalism", "no_private_inference", "no_internal_ids_in_user_view"),
        },
        "runtime_mutation": False,
        "completion_percent": 100,
        "runtime_consumers": (
            "role_view_model.question_profile.voice_profile",
            "questions[].question_narrative",
            "llm.practitioner_answer_prompt.answer_prompt_profile",
            "synthetic_replay.role_views[].question_narrative_quality",
        ),
        "guardrails": [
            "RUNTIME_CONSUMED_WITHOUT_HUMAN_REVIEW_GATE",
            "QUESTION_NARRATIVE_PRESERVES_STRUCTURED_QUESTION_KEYS",
            "LLM_PROMPTS_USE_VERIFIED_CONTEXT_ONLY",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def voice_profile_for_role(role_key: str) -> dict[str, object]:
    clean = "analyst" if role_key == "practitioner" else str(role_key or "user")
    for profile in VOICE_PROFILES:
        if clean in profile["role_keys"]:
            return dict(profile)
    return dict(VOICE_PROFILES[1])


def answer_prompt_profile_for_role(role_key: str, *, locale: str = "zh") -> dict[str, object]:
    voice = voice_profile_for_role(role_key)
    return {
        "version": "v20.answer_prompt_profile.v1",
        "role_key": "analyst" if role_key == "practitioner" else str(role_key or "user"),
        "voice_profile": voice["voice_profile"],
        "system_style": voice["tone"],
        "answer_structure": voice["answer_structure"],
        "forbidden_patterns": voice["forbidden_patterns"],
        "required_elements": voice["required_elements"],
        "locale_policy": _locale_policy(locale),
        "runtime_mutation": False,
        "guardrails": [
            "ANSWER_PROMPT_PROFILE_ONLY",
            "ROLE_VOICE_DOES_NOT_CHANGE_CHART_FACTS",
            "PROMPT_MUST_USE_VERIFIED_CONTEXT",
        ],
    }


def question_narrative_contract_for_role(role_key: str) -> dict[str, object]:
    voice = voice_profile_for_role(role_key)
    return {
        "version": "v20.question_narrative_contract.v1",
        "role_key": "analyst" if role_key == "practitioner" else str(role_key or "user"),
        "voice_profile": voice["voice_profile"],
        "question_structure": voice["question_structure"],
        "tone_guardrails": (
            *voice["forbidden_patterns"],
            *voice["required_elements"],
            "preserve_question_key_domain_and_rank",
            "do_not_create_new_chart_fact",
        ),
        "runtime_mutation": False,
    }


def question_narrative_for_question(question: dict[str, object], role_key: str) -> dict[str, object]:
    voice = voice_profile_for_role(role_key)
    clean_role = "analyst" if role_key == "practitioner" else str(role_key or "user")
    title = str(question.get("display_title", "") or question.get("title", "") or question.get("question_key", "")).strip()
    domain = str(question.get("domain", "") or "").strip()
    topic = str(question.get("measurement_topic", "") or "").strip()
    stage = str(question.get("measurement_stage", "") or "").strip()
    strategy = str(question.get("question_strategy", "") or "").strip()
    boundary = str(question.get("boundary", "") or "").strip()
    source = str(question.get("source_decision_key", "") or question.get("seed_source_key", "") or "").strip()
    return {
        "version": "v20.question_narrative.v1",
        "role_key": clean_role,
        "voice_profile": voice["voice_profile"],
        "title": title,
        "why_now": _why_now(clean_role, domain, topic, strategy),
        "bazi_basis": _bazi_basis(clean_role, domain, topic, stage),
        "boundary": _narrative_boundary(clean_role, boundary),
        "next_step": _next_step(clean_role, domain),
        "source": source if clean_role in {"admin", "lab"} else "",
        "policy_effect": strategy if clean_role in {"admin", "lab"} else "",
        "runtime_note": "角色层只改变展示叙事和排序，不改八字事实。",
        "tone_guardrails": question_narrative_contract_for_role(clean_role)["tone_guardrails"],
        "runtime_mutation": False,
    }


def _step(step_key: str, label: str, status: str) -> dict[str, str]:
    return {"step_key": step_key, "label": label, "status": status}


def _locale_policy(locale: str) -> dict[str, Any]:
    if str(locale).startswith("en"):
        return {"locale": "en", "instruction": "English output; explain Bazi terms briefly."}
    if str(locale).startswith("ko"):
        return {"locale": "ko", "instruction": "Korean output; keep Bazi terms readable."}
    return {"locale": "zh", "instruction": "中文输出；术语随角色控制密度。"}


def _why_now(role_key: str, domain: str, topic: str, strategy: str) -> str:
    label = _domain_label(domain, topic)
    if role_key == "guest":
        return f"先从{label}入手，比较容易读懂当前结构。"
    if role_key == "analyst":
        return f"当前排序把{label}放到前面，需要复核它是否真正牵动主线。"
    if role_key in {"admin", "lab"}:
        return f"中枢将 {domain or 'unknown'} / {strategy or 'default'} 放入问题队列，可观察排序和角色投影是否一致。"
    return f"这个问题贴近当前主线，先看{label}能帮助你判断下一步该追问什么。"


def _bazi_basis(role_key: str, domain: str, topic: str, stage: str) -> str:
    label = _domain_label(domain, topic)
    if role_key == "guest":
        return f"它对应盘里的{label}线索。"
    if role_key == "analyst":
        return f"依据位点：{label}；阶段：{stage or '待复核'}。"
    if role_key in {"admin", "lab"}:
        return f"domain={domain or '-'}; topic={topic or '-'}; stage={stage or '-'}"
    return f"它来自八字里的{label}相关线索，先作为阅读入口，不当作最终结论。"


def _narrative_boundary(role_key: str, boundary: str) -> str:
    if role_key == "guest":
        return "这里只提示方向，不直接断定具体事件。"
    if role_key == "analyst":
        return boundary or "需要同时保留反证条件，不能把候选当结论。"
    if role_key in {"admin", "lab"}:
        return boundary or "runtime projection only; no chart fact mutation."
    return boundary or "需要结合后续证据继续确认，不直接下绝对判断。"


def _next_step(role_key: str, domain: str) -> str:
    label = _domain_label(domain, "")
    if role_key == "guest":
        return "可以先点开这个问题，看看它和你关心的方向是否贴近。"
    if role_key == "analyst":
        return f"下一步复核{label}的证据、边界和反证条件。"
    if role_key in {"admin", "lab"}:
        return "继续观察 question_key、source、policy_effect 与点击反馈。"
    return f"你可以继续围绕{label}追问，系统会沿当前主线展开。"


def _domain_label(domain: str, fallback: str) -> str:
    labels = {
        "strength": "日主强弱",
        "useful_god": "用神方向",
        "ten_god": "十神关系",
        "element": "五行分布",
        "branch": "地支关系",
        "time": "大运流年",
        "wealth": "财运主题",
        "career": "事业主题",
        "relationship": "关系主题",
        "health": "平衡压力",
        "pattern": "格局结构",
    }
    return labels.get(domain, fallback or domain or "当前主线")
