"""
Centralized UI label dictionaries for zh/en/ko used by both frontend (via API) and backend renderers.
This module is the single source of truth for all user-facing micro-copy that appears in
workbench, admin, profiles, and answer composition layers.
"""
from __future__ import annotations


def locale_key(locale: str) -> str:
    if str(locale).startswith("ko"):
        return "ko"
    if str(locale).startswith("en"):
        return "en"
    return "zh"


# ---------------------------------------------------------------------------
# Pillar labels (workbench chart panel)
# ---------------------------------------------------------------------------
PILLAR_LABELS = {
    "zh": {
        "year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱",
        "luck": "大运", "flow_year": "流年",
        "year_hint": "原局", "month_hint": "原局", "day_hint": "日主",
        "hour_hint": "原局", "luck_hint": "运势背景", "flow_year_hint": "当前触发",
    },
    "en": {
        "year": "Year", "month": "Month", "day": "Day", "hour": "Hour",
        "luck": "Luck", "flow_year": "Flow Year",
        "year_hint": "natal", "month_hint": "natal", "day_hint": "day master",
        "hour_hint": "natal", "luck_hint": "luck cycle", "flow_year_hint": "current trigger",
    },
    "ko": {
        "year": "연주", "month": "월주", "day": "일주", "hour": "시주",
        "luck": "대운", "flow_year": "유년",
        "year_hint": "원국", "month_hint": "원국", "day_hint": "일간",
        "hour_hint": "원국", "luck_hint": "운세 배경", "flow_year_hint": "현재 촉발",
    },
}

# ---------------------------------------------------------------------------
# Ten-god display prefix
# ---------------------------------------------------------------------------
TEN_GOD_LABELS = {
    "zh": {"visible": "透出", "hidden": "藏干"},
    "en": {"visible": "Visible", "hidden": "Hidden"},
    "ko": {"visible": "투출", "hidden": "장간"},
}

# ---------------------------------------------------------------------------
# Feature state labels used by workbench feature chips
# ---------------------------------------------------------------------------
FEATURE_STATE_LABELS = {
    "zh": {
        "active": "已入主链", "available": "可用", "evidence_gap": "补证",
        "requires_review": "复核", "blocked_or_countered": "被反证",
        "confirmed": "成立", "candidate": "候选", "weak_candidate": "弱候选",
        "volatile": "岁运引动", "mixed": "成而不纯", "_default": "状态",
    },
    "en": {
        "active": "mainline", "available": "available", "evidence_gap": "evidence gap",
        "requires_review": "review", "blocked_or_countered": "countered",
        "confirmed": "confirmed", "candidate": "candidate", "weak_candidate": "weak",
        "volatile": "volatile", "mixed": "mixed", "_default": "state",
    },
    "ko": {
        "active": "주요 연결", "available": "가용", "evidence_gap": "근거 부족",
        "requires_review": "검토", "blocked_or_countered": "반증",
        "confirmed": "성립", "candidate": "후보", "weak_candidate": "약후보",
        "volatile": "세운 변동", "mixed": "혼합", "_default": "상태",
    },
}

# ---------------------------------------------------------------------------
# Portrait / axis labels
# ---------------------------------------------------------------------------
PORTRAIT_DOMAIN_LABELS = {
    "zh": {
        "strength": "强弱", "career": "事业", "wealth": "财运",
        "ten_god": "十神", "useful_god": "用神", "time": "时间",
        "branch": "地支", "element": "五行", "pattern": "格局",
        "relationship": "关系", "health": "健康", "_default": "命理",
    },
    "en": {
        "strength": "Capacity", "career": "Career", "wealth": "Wealth",
        "ten_god": "Ten Gods", "useful_god": "Useful God", "time": "Timing",
        "branch": "Branches", "element": "Elements", "pattern": "Pattern",
        "relationship": "Relationship", "health": "Health", "_default": "Bazi",
    },
    "ko": {
        "strength": "강약", "career": "직업", "wealth": "재운",
        "ten_god": "십성", "useful_god": "용신", "time": "시간",
        "branch": "지지", "element": "오행", "pattern": "격국",
        "relationship": "관계", "health": "건강", "_default": "사주",
    },
}

PORTRAIT_TEMPERATURE_LABELS = {
    "zh": {"hot": "高关注", "warm": "成形", "mild": "待复核", "cool": "线索"},
    "en": {"hot": "high focus", "warm": "forming", "mild": "review", "cool": "signal"},
    "ko": {"hot": "높은 관심", "warm": "형성", "mild": "검토", "cool": "단서"},
}

PORTRAIT_ATTENTION_LABELS = {
    "zh": {"high": "高关注", "medium": "重点观察", "normal": "常规画像", "_default": "画像"},
    "en": {"high": "High Focus", "medium": "Key Watch", "normal": "Standard", "_default": "Profile"},
    "ko": {"high": "높은 관심", "medium": "주요 관찰", "normal": "일반", "_default": "프로필"},
}

AXIS_TIER_LABELS = {
    "zh": {"micro": "微观骨架", "decision": "裁决路径", "macro": "应用场景", "time": "时序引动", "_default": "结构层"},
    "en": {"micro": "Micro Spine", "decision": "Decision Path", "macro": "Applied Scenario", "time": "Timing Trigger", "_default": "Structure"},
    "ko": {"micro": "미시 구조", "decision": "판정 경로", "macro": "응용 시나리오", "time": "시간 촉발", "_default": "구조층"},
}

AXIS_STATE_LABELS = {
    "zh": {
        "confirmed": "已成", "chain_review": "链式", "mixed": "成而不纯",
        "candidate": "候选", "weak_candidate": "偏弱", "volatile": "引动",
        "requires_review": "需复核", "countered": "反制", "blocked": "受阻", "_default": "结构",
    },
    "en": {
        "confirmed": "Confirmed", "chain_review": "Chain", "mixed": "Mixed",
        "candidate": "Candidate", "weak_candidate": "Weak", "volatile": "Volatile",
        "requires_review": "Review", "countered": "Countered", "blocked": "Blocked", "_default": "Structure",
    },
    "ko": {
        "confirmed": "성립", "chain_review": "연쇄", "mixed": "혼합",
        "candidate": "후보", "weak_candidate": "약세", "volatile": "변동",
        "requires_review": "검토", "countered": "반제", "blocked": "차단", "_default": "구조",
    },
}

# ---------------------------------------------------------------------------
# Intent type labels
# ---------------------------------------------------------------------------
INTENT_TYPE_LABELS = {
    "zh": {
        "confirm_structure": "确认结构", "explore_candidate": "展开候选",
        "collect_evidence": "补齐证据", "resolve_mixed_state": "裁决混合",
        "inspect_timing_trigger": "岁运引动", "ask_practitioner_review": "命理师复核",
        "explain_boundary": "边界说明", "explore_structure": "结构追问",
        "suppress_output": "不输出", "_default": "智能意图",
    },
    "en": {
        "confirm_structure": "Confirm Structure", "explore_candidate": "Explore Candidate",
        "collect_evidence": "Collect Evidence", "resolve_mixed_state": "Resolve Mixed",
        "inspect_timing_trigger": "Timing Trigger", "ask_practitioner_review": "Practitioner Review",
        "explain_boundary": "Boundary", "explore_structure": "Explore Structure",
        "suppress_output": "Suppress", "_default": "Intent",
    },
    "ko": {
        "confirm_structure": "구조 확인", "explore_candidate": "후보 탐색",
        "collect_evidence": "근거 보완", "resolve_mixed_state": "혼합 판정",
        "inspect_timing_trigger": "세운 촉발", "ask_practitioner_review": "명리사 검토",
        "explain_boundary": "경계 설명", "explore_structure": "구조 추적",
        "suppress_output": "출력 안 함", "_default": "의도",
    },
}

# ---------------------------------------------------------------------------
# Latent scenario labels
# ---------------------------------------------------------------------------
LATENT_SCENARIO_LABELS = {
    "zh": {
        "wealth": "财务变化", "career": "事业节点", "relationship": "关系重心",
        "relocation": "环境迁移", "stress": "压力恢复", "global": "行动节奏", "_default": "命主校准",
    },
    "en": {
        "wealth": "Financial Change", "career": "Career Node", "relationship": "Relationship Focus",
        "relocation": "Relocation", "stress": "Stress Recovery", "global": "Action Rhythm", "_default": "Subject Calibration",
    },
    "ko": {
        "wealth": "재무 변화", "career": "직업 전환", "relationship": "관계 중심",
        "relocation": "환경 이동", "stress": "스트레스 회복", "global": "행동 리듬", "_default": "주체 보정",
    },
}

LATENT_FIELD_LABELS = {
    "zh": {"year_option": "时间", "result_option": "结果", "intensity": "强度", "confidence": "把握"},
    "en": {"year_option": "Period", "result_option": "Result", "intensity": "Intensity", "confidence": "Confidence"},
    "ko": {"year_option": "시기", "result_option": "결과", "intensity": "강도", "confidence": "확신"},
}

LATENT_YEAR_LABELS = {
    "zh": {
        "unknown": "不确定", "birth_to_12": "0-12岁", "13_to_18": "13-18岁",
        "19_to_24": "19-24岁", "25_to_30": "25-30岁", "31_to_36": "31-36岁",
        "37_to_42": "37-42岁", "43_to_48": "43-48岁", "49_to_54": "49-54岁", "55_plus": "55岁以后",
    },
    "en": {
        "unknown": "Uncertain", "birth_to_12": "0–12", "13_to_18": "13–18",
        "19_to_24": "19–24", "25_to_30": "25–30", "31_to_36": "31–36",
        "37_to_42": "37–42", "43_to_48": "43–48", "49_to_54": "49–54", "55_plus": "55+",
    },
    "ko": {
        "unknown": "불확실", "birth_to_12": "0-12세", "13_to_18": "13-18세",
        "19_to_24": "19-24세", "25_to_30": "25-30세", "31_to_36": "31-36세",
        "37_to_42": "37-42세", "43_to_48": "43-48세", "49_to_54": "49-54세", "55_plus": "55세 이후",
    },
}

LATENT_INTENSITY_LABELS = {
    "zh": {"none": "无", "mild": "轻微", "clear": "明显", "strong": "强烈"},
    "en": {"none": "None", "mild": "Mild", "clear": "Clear", "strong": "Strong"},
    "ko": {"none": "없음", "mild": "경미", "clear": "뚜렷", "strong": "강함"},
}

LATENT_CONFIDENCE_LABELS = {
    "zh": {"low": "低", "medium": "中", "high": "高"},
    "en": {"low": "Low", "medium": "Medium", "high": "High"},
    "ko": {"low": "낮음", "medium": "중간", "high": "높음"},
}

# ---------------------------------------------------------------------------
# Misc workbench micro-copy
# ---------------------------------------------------------------------------
WORKBENCH_COPY = {
    "zh": {
        "day_master_prefix": "日主",
        "waiting": "等待测算。",
        "measuring": "正在根据当前问题重新测算。",
        "measure_failed": "测算失败：",
        "generating": "生成中",
        "send": "发送",
        "enter_direction": "请输入想继续看的方向。",
        "chat_placeholder": "输入想继续看的方向",
        "auto_route": "自动路由",
        "no_features": "当前尚未发现可展示的命理特征。",
        "no_portrait": "当前视图隐藏画像投影。",
        "no_evidence": "暂无可展示证据。",
        "no_questions": "确认四柱后会生成建议问题。",
        "no_rule_hits": "当前暂无规则命中。",
        "no_rules_fired": "未触发规则",
        "await_graph": "等待画像图谱。",
        "graph_ready": "当前盘已形成图谱画像。",
        "graph_mainline": "主线",
        "graph_pressure": "压力",
        "graph_timing": "时间",
        "graph_default_item": "暂按主题画像展开",
        "structural_anchor": "结构锚点：",
        "match_rate": "匹配率",
        "condition_hit": "条件命中",
        "decision_state": "决策态：",
        "expand": "展开",
        "collapse": "收起",
        "practitioner_title": "命理师校准",
        "practitioner_expand": "展开命理师校准",
        "practitioner_collapse": "收起命理师校准",
        "observation_expand": "展开观测页面",
        "observation_collapse": "收起观测页面",
        "pending_decision": "待裁决",
        "accepted": "已接收",
        "refreshed": "已刷新",
        "items": "项",
        "recording": "记录中",
        "record_failed": "记录失败",
        "recorded_refresh": "已记录 · 刷新问题",
        "accepted_refresh": "已接收 · 刷新问题",
        "question_source": "推荐问题",
        "follow_up": "继续追问",
        "manual_measure": "手动测算",
        "queuing": "排队中",
        "chat_pending": "正在生成回复...",
        "chat_no_reply": "本轮没有生成可展示回复。",
        "calibrated_count": "已校准",
        "dynamic_validation": "动态裁决验证",
        "feature_state_model": "特征状态模型",
        "question_intent_model": "问题意图模型",
        "defeasible_model": "可反证裁决模型",
        "rule_hit_traces": "条规则命中轨迹",
        "ten_god_bazi": "命理测算",
    },
    "en": {
        "day_master_prefix": "DM",
        "waiting": "Awaiting reading.",
        "measuring": "Re-reading based on current question.",
        "measure_failed": "Reading failed: ",
        "generating": "Generating",
        "send": "Send",
        "enter_direction": "Enter a direction to explore.",
        "chat_placeholder": "Enter a direction to explore",
        "auto_route": "Auto Route",
        "no_features": "No displayable Bazi features found yet.",
        "no_portrait": "Portrait projection hidden in this view.",
        "no_evidence": "No evidence to display.",
        "no_questions": "Suggested questions appear after confirming four pillars.",
        "no_rule_hits": "No rule hits yet.",
        "no_rules_fired": "No rules fired",
        "await_graph": "Awaiting portrait graph.",
        "graph_ready": "Portrait graph is ready for this chart.",
        "graph_mainline": "Mainline",
        "graph_pressure": "Pressure",
        "graph_timing": "Timing",
        "graph_default_item": "Expand by topic portrait",
        "structural_anchor": "Structural anchor: ",
        "match_rate": "match",
        "condition_hit": "Conditions met",
        "decision_state": "Decision state: ",
        "expand": "Expand",
        "collapse": "Collapse",
        "practitioner_title": "Practitioner Calibration",
        "practitioner_expand": "Expand practitioner calibration",
        "practitioner_collapse": "Collapse practitioner calibration",
        "observation_expand": "Expand observation page",
        "observation_collapse": "Collapse observation page",
        "pending_decision": "pending",
        "accepted": "accepted",
        "refreshed": "refreshed",
        "items": "items",
        "recording": "recording",
        "record_failed": "record failed",
        "recorded_refresh": "recorded · refreshing",
        "accepted_refresh": "accepted · refreshing",
        "question_source": "Suggested",
        "follow_up": "Follow-up",
        "manual_measure": "Manual Reading",
        "queuing": "queuing",
        "chat_pending": "Generating reply…",
        "chat_no_reply": "No displayable reply this turn.",
        "calibrated_count": "calibrated",
        "dynamic_validation": "Decision Validation",
        "feature_state_model": "Feature State Model",
        "question_intent_model": "Question Intent Model",
        "defeasible_model": "Defeasible Decision Model",
        "rule_hit_traces": "rule hit traces",
        "ten_god_bazi": "Bazi Reading",
    },
    "ko": {
        "day_master_prefix": "일간",
        "waiting": "분석 대기 중.",
        "measuring": "현재 질문 기반으로 재분석 중.",
        "measure_failed": "분석 실패: ",
        "generating": "생성 중",
        "send": "보내기",
        "enter_direction": "탐색 방향을 입력하세요.",
        "chat_placeholder": "탐색 방향을 입력하세요",
        "auto_route": "자동 라우팅",
        "no_features": "표시 가능한 사주 특징이 아직 없습니다.",
        "no_portrait": "현재 뷰에서 투사가 숨겨져 있습니다.",
        "no_evidence": "표시할 근거가 없습니다.",
        "no_questions": "사주를 확인하면 추천 질문이 생성됩니다.",
        "no_rule_hits": "아직 규칙 적중 없음.",
        "no_rules_fired": "촉발된 규칙 없음",
        "await_graph": "프로필 그래프 대기 중.",
        "graph_ready": "현재 명식의 그래프가 준비되었습니다.",
        "graph_mainline": "주요 축",
        "graph_pressure": "압력",
        "graph_timing": "시간",
        "graph_default_item": "주제별로 전개",
        "structural_anchor": "구조 앵커: ",
        "match_rate": "일치율",
        "condition_hit": "조건 충족",
        "decision_state": "판정 상태: ",
        "expand": "열기",
        "collapse": "닫기",
        "practitioner_title": "명리사 보정",
        "practitioner_expand": "명리사 보정 열기",
        "practitioner_collapse": "명리사 보정 닫기",
        "observation_expand": "관측 페이지 열기",
        "observation_collapse": "관측 페이지 닫기",
        "pending_decision": "대기 중",
        "accepted": "접수됨",
        "refreshed": "갱신됨",
        "items": "건",
        "recording": "기록 중",
        "record_failed": "기록 실패",
        "recorded_refresh": "기록됨 · 질문 갱신",
        "accepted_refresh": "접수됨 · 질문 갱신",
        "question_source": "추천 질문",
        "follow_up": "추가 질문",
        "manual_measure": "수동 분석",
        "queuing": "대기 중",
        "chat_pending": "답변 생성 중…",
        "chat_no_reply": "이번에 표시할 답변이 없습니다.",
        "calibrated_count": "보정 완료",
        "dynamic_validation": "동적 판정 검증",
        "feature_state_model": "특징 상태 모델",
        "question_intent_model": "질문 의도 모델",
        "defeasible_model": "반증 가능 판정 모델",
        "rule_hit_traces": "규칙 적중 이력",
        "ten_god_bazi": "사주 분석",
    },
}

# ---------------------------------------------------------------------------
# Admin page labels
# ---------------------------------------------------------------------------
ADMIN_LABELS = {
    "zh": {
        "nav_entry": "入口", "nav_profiles": "档案", "nav_measure": "测算",
        "refresh": "刷新", "models": "模型", "status_label": "状态",
        "no_data": "暂无数据。", "await_db_url": "等待 V20_DATABASE_URL。", "logout": "登出",
    },
    "en": {
        "nav_entry": "Entry", "nav_profiles": "Profiles", "nav_measure": "Reading",
        "refresh": "Refresh", "models": "Models", "status_label": "Status",
        "no_data": "No data.", "await_db_url": "Waiting for V20_DATABASE_URL.", "logout": "Log Out",
    },
    "ko": {
        "nav_entry": "입구", "nav_profiles": "프로필", "nav_measure": "분석",
        "refresh": "새로고침", "models": "모델", "status_label": "상태",
        "no_data": "데이터 없음.", "await_db_url": "V20_DATABASE_URL 대기 중.", "logout": "로그아웃",
    },
}

# ---------------------------------------------------------------------------
# Latent result labels (large map)
# ---------------------------------------------------------------------------
LATENT_RESULT_LABELS = {
    "zh": {
        "no_clear_change": "没有明显变化", "income_up": "收入/资源上升",
        "income_down": "收入下降", "resource_gain": "获得资源支持",
        "resource_pressure": "资源或财务压力", "role_up": "角色上升",
        "role_down": "角色下降", "platform_change": "平台变化",
        "responsibility_change": "责任变化", "relationship_stabilized": "关系稳定",
        "relationship_changed": "关系变化", "relationship_pressure": "关系压力",
        "family_focus_shift": "家庭重心变化", "city_change": "城市变化",
        "work_environment_change": "工作环境变化", "home_environment_change": "居住环境变化",
        "travel_or_mobility_up": "流动增加", "stable": "基本稳定",
        "recovered_fast": "恢复较快", "recovered_slow": "恢复较慢",
        "repeated_pressure": "压力反复", "support_helped": "外部支持有效",
        "not_observed": "尚未观察", "result_fast": "见效快",
        "result_slow": "见效慢", "needs_repeated_attempts": "需要反复尝试",
        "external_help_decisive": "外部帮助关键", "mixed": "混合",
    },
    "en": {
        "no_clear_change": "No clear change", "income_up": "Income/resources up",
        "income_down": "Income down", "resource_gain": "Resource support gained",
        "resource_pressure": "Resource/financial pressure", "role_up": "Role elevated",
        "role_down": "Role declined", "platform_change": "Platform change",
        "responsibility_change": "Responsibility change", "relationship_stabilized": "Relationship stabilized",
        "relationship_changed": "Relationship changed", "relationship_pressure": "Relationship pressure",
        "family_focus_shift": "Family focus shift", "city_change": "City change",
        "work_environment_change": "Work environment change", "home_environment_change": "Home environment change",
        "travel_or_mobility_up": "Mobility increased", "stable": "Mostly stable",
        "recovered_fast": "Recovered quickly", "recovered_slow": "Recovered slowly",
        "repeated_pressure": "Repeated pressure", "support_helped": "External support helped",
        "not_observed": "Not yet observed", "result_fast": "Quick results",
        "result_slow": "Slow results", "needs_repeated_attempts": "Needs repeated attempts",
        "external_help_decisive": "External help decisive", "mixed": "Mixed",
    },
    "ko": {
        "no_clear_change": "뚜렷한 변화 없음", "income_up": "수입/자원 상승",
        "income_down": "수입 감소", "resource_gain": "자원 지원 확보",
        "resource_pressure": "자원/재정 압력", "role_up": "역할 상승",
        "role_down": "역할 하락", "platform_change": "플랫폼 변화",
        "responsibility_change": "책임 변화", "relationship_stabilized": "관계 안정",
        "relationship_changed": "관계 변화", "relationship_pressure": "관계 압력",
        "family_focus_shift": "가정 중심 변화", "city_change": "도시 변경",
        "work_environment_change": "근무 환경 변화", "home_environment_change": "주거 환경 변화",
        "travel_or_mobility_up": "이동 증가", "stable": "대체로 안정",
        "recovered_fast": "빠른 회복", "recovered_slow": "느린 회복",
        "repeated_pressure": "반복적 압력", "support_helped": "외부 지원 효과",
        "not_observed": "아직 관찰 안 됨", "result_fast": "빠른 성과",
        "result_slow": "느린 성과", "needs_repeated_attempts": "반복 시도 필요",
        "external_help_decisive": "외부 도움 결정적", "mixed": "혼합",
    },
}


# ---------------------------------------------------------------------------
# Helper: get a label from a locale dict with fallback
# ---------------------------------------------------------------------------
def get_label(table: dict[str, dict[str, str]], locale: str, key: str) -> str:
    lang = locale_key(locale)
    bucket = table.get(lang, table.get("zh", {}))
    return bucket.get(key, bucket.get("_default", key))
