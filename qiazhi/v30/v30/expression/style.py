from __future__ import annotations

from v30.contracts import ClientKey, LocaleKey, RoleKey
from v30.expression.contracts import StyleProfile


USER_VISIBLE_ENGINEERING_TOKENS = [
    "policy_effect",
    "rule_decision_state",
    "macro_dimension_context",
    "krp_unit_weights",
    "dynamic_graph_paths_scored",
    "quality_gate",
    "runtime pointer",
    "trace_id",
    "evidence-bound",
    "mechanism paths",
    "Current chart",
]


ROLE_VOICE = {
    "guest": "warm_plain_bazi",
    "user": "calm_bazi_consultation",
    "practitioner": "dense_bazi_practitioner",
    "analyst": "traceable_bazi_analyst",
    "admin": "diagnostic_operator",
    "lab": "validation_researcher",
}

CLIENT_KEYS = {"web", "mobile", "admin", "lab"}


def resolve_style_profile(
    *,
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> StyleProfile:
    role: RoleKey = role_key if role_key in ROLE_VOICE else "user"  # type: ignore[assignment]
    loc: LocaleKey = locale if locale in {"zh", "en", "ko"} else "zh"  # type: ignore[assignment]
    resolved_client: ClientKey = client if client in CLIENT_KEYS else "web"  # type: ignore[assignment]
    density = "compact" if resolved_client == "mobile" or role == "guest" else "standard"
    if role in {"analyst", "admin", "lab"}:
        density = "diagnostic"
    return StyleProfile(
        style_profile_id=f"v30.expression.style.{role}.{loc}.{resolved_client}",
        role_key=role,
        locale=loc,
        client=resolved_client,
        voice=ROLE_VOICE[role],
        density=density,
        allowed_terms=["日主", "格局", "原局", "大运", "流年", "藏干", "用神候选", "结构动态"],
        forbidden_tokens=[] if role in {"analyst", "admin", "lab"} else USER_VISIBLE_ENGINEERING_TOKENS,
    )


def resolve_style_profile_from_role_state(
    role_state: dict[str, object],
    *,
    locale: str = "zh",
    client: str = "web",
) -> StyleProfile:
    role_key = str(role_state.get("role_key") or "user")
    profile = resolve_style_profile(role_key=role_key, locale=locale, client=str(role_state.get("client") or client))
    density = str(role_state.get("answer_density") or profile.density)
    voice = str(role_state.get("expression_voice") or profile.voice)
    style_profile_id = str(
        role_state.get("style_profile_id")
        or f"v30.expression.style.{profile.role_key}.{profile.locale}.{profile.client}"
    )
    return profile.model_copy(
        update={
            "style_profile_id": style_profile_id,
            "voice": voice,
            "density": density,
        }
    )
