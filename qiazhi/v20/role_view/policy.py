from __future__ import annotations

from v20.role_view.model import RoleViewPolicy


POLICY_VERSION = "v20.role_view_policy.v1"


ROLE_VIEW_POLICIES = {
    "guest": RoleViewPolicy(
        role_key="guest",
        portrait_depth="entry_overview",
        question_style="starter_questions",
        explanation_style="plain_entry",
        visibility_level="public_entry",
        question_limit=3,
        portrait_limit=2,
    ),
    "user": RoleViewPolicy(
        role_key="user",
        portrait_depth="guided_summary",
        question_style="guided_questions",
        explanation_style="guided_plain_language",
        visibility_level="public_guided",
        question_limit=6,
        portrait_limit=4,
    ),
    "analyst": RoleViewPolicy(
        role_key="analyst",
        portrait_depth="technical_review",
        question_style="review_questions",
        explanation_style="technical_review",
        visibility_level="technical_review",
        question_limit=10,
        portrait_limit=8,
    ),
    "lab": RoleViewPolicy(
        role_key="lab",
        portrait_depth="experiment_observation",
        question_style="observation_questions",
        explanation_style="experiment_observation",
        visibility_level="experiment_observation",
        question_limit=12,
        portrait_limit=10,
    ),
    "admin": RoleViewPolicy(
        role_key="admin",
        portrait_depth="full_observation",
        question_style="full_observation_questions",
        explanation_style="system_observation",
        visibility_level="system_observation",
        question_limit=12,
        portrait_limit=10,
    ),
}


GUEST_QUESTION_TITLES = {
    "career": "事业先看整体节奏还是关键压力？",
    "wealth": "财务先看稳定度还是机会点？",
    "relationship": "关系先看相处节奏还是沟通压力？",
    "health": "身心状态先看压力来源还是调节方式？",
    "time": "近期变化先看哪段时间更明显？",
    "element": "五行状态先看哪里偏强或偏弱？",
    "strength": "当前命局先看支撑够不够？",
    "useful_god": "下一步先看适合补什么方向？",
}


def role_view_policy(role_key: str) -> RoleViewPolicy:
    return ROLE_VIEW_POLICIES.get(role_key, ROLE_VIEW_POLICIES["user"])
