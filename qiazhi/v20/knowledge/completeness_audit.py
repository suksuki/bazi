from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v20.knowledge.directory import build_knowledge_directory_manifest
from v20.knowledge.directory_seeds import build_full_directory_seed_library
from v20.knowledge.rule_library import build_knowledge_rule_library
from v20.validation.rule_synthetic import RULE_SYNTHETIC_CASES


KNOWLEDGE_COMPLETENESS_AUDIT_VERSION = "v20.knowledge_completeness_audit.v1"


DOMAIN_TO_NODE = {
    "element": "L1",
    "strength": "L2",
    "ten_god": "L3",
    "branch": "L4",
    "pattern": "L5",
    "useful_god": "L6",
    "time": "L9",
    "wealth": "L10",
    "career": "L10",
    "relationship": "L10",
    "health": "L10",
}

SOURCE_PREFIX_TO_NODE = {
    "v20.calendar.": "L0",
    "v20.auxiliary.": "L11",
    "v20.applied.mobility_": "L10",
    "v20.palace.": "L7",
    "v20.blind_lifa.": "L8",
    "v20.answer_governance.": "L12",
}

SYNTHETIC_CASE_PREFIX_TO_NODE = {
    "v20.rule.synthetic.calendar_": "L0",
    "v20.rule.synthetic.auxiliary_": "L11",
    "v20.rule.synthetic.palace_": "L7",
    "v20.rule.synthetic.blind_lifa_": "L8",
    "v20.rule.synthetic.answer_governance_": "L12",
}

EXTERNAL_TOPIC_RULE_PREFIXES = {
    "true_solar_time": ("v20.calendar.birth_time_boundary",),
    "early_late_zi_hour": ("v20.calendar.birth_time_boundary",),
    "hidden_stem_weight": ("v20.calendar.hidden_stem_weight_boundary",),
    "day_master_month_command_climate": ("v20.climate.month_command_adjustment",),
    "useful_god_conflict_arbitration": ("v20.useful_god_arbitration.conflict_path",),
    "luck_pillar_start_age": ("v20.time.trigger_stack_boundary",),
    "annual_monthly_trigger_stack": ("v20.time.trigger_stack_boundary",),
    "common_shen_sha_low_weight": ("v20.auxiliary.common_symbol_low_weight",),
    "study_exam_topic": ("v20.applied.study_exam_learning_path",),
    "children_family_topic": ("v20.applied.children_family_context",),
    "migration_topic": ("v20.applied.mobility_migration_branch_time",),
    "housing_property_topic": ("v20.applied.housing_property_context", "v20.applied.asset_cashflow_structure"),
    "social_cooperation_topic": ("v20.applied.social_peer_network",),
    "startup_management_topic": ("v20.applied.startup_management_context",),
    "palace_projection_boundary": ("v20.palace.topic_projection_boundary",),
    "blind_lifa_auxiliary_boundary": ("v20.blind_lifa.auxiliary_boundary",),
    "answer_governance_boundary": ("v20.answer_governance.boundary",),
}


EXTERNAL_TOPIC_MAP: tuple[dict[str, object], ...] = (
    {"topic_key": "true_solar_time", "label": "真太阳时与出生地", "node_key": "L0", "priority": "P0"},
    {"topic_key": "early_late_zi_hour", "label": "早子时/晚子时边界", "node_key": "L0", "priority": "P0"},
    {"topic_key": "day_master_month_command_climate", "label": "日主 × 月令调候", "node_key": "L1", "priority": "P0"},
    {"topic_key": "hidden_stem_weight", "label": "藏干权重与通根强度", "node_key": "L0", "priority": "P0"},
    {"topic_key": "ten_god_by_position", "label": "十神落年/月/日/时", "node_key": "L3", "priority": "P1"},
    {"topic_key": "useful_god_conflict_arbitration", "label": "用神路径冲突仲裁", "node_key": "L6", "priority": "P0"},
    {"topic_key": "luck_pillar_start_age", "label": "起运顺逆与起运年龄", "node_key": "L9", "priority": "P0"},
    {"topic_key": "annual_monthly_trigger_stack", "label": "大运/流年/流月触发栈", "node_key": "L9", "priority": "P0"},
    {"topic_key": "common_shen_sha_low_weight", "label": "常见神煞低权重辅助", "node_key": "L11", "priority": "P0"},
    {"topic_key": "empty_branch", "label": "空亡辅助边界", "node_key": "L11", "priority": "P1"},
    {"topic_key": "twelve_growth_stage", "label": "十二长生辅助边界", "node_key": "L11", "priority": "P1"},
    {"topic_key": "na_yin_archive", "label": "纳音归档辅助", "node_key": "L11", "priority": "P2"},
    {"topic_key": "study_exam_topic", "label": "学业考试专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "children_family_topic", "label": "子女家庭专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "migration_topic", "label": "迁移远行专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "housing_property_topic", "label": "房产居住专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "social_cooperation_topic", "label": "人际合作专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "startup_management_topic", "label": "创业管理专题", "node_key": "L10", "priority": "P2"},
    {"topic_key": "palace_projection_boundary", "label": "宫位主题投射边界", "node_key": "L7", "priority": "P0"},
    {"topic_key": "blind_lifa_auxiliary_boundary", "label": "盲派辅助取象边界", "node_key": "L8", "priority": "P0"},
    {"topic_key": "answer_governance_boundary", "label": "回答治理证据边界", "node_key": "L12", "priority": "P1"},
)


def build_knowledge_completeness_audit() -> dict[str, object]:
    directory = build_knowledge_directory_manifest()
    seeds = build_full_directory_seed_library()
    library = build_knowledge_rule_library()
    rules = [row for row in library.get("definitions", ()) if isinstance(row, dict)]
    seed_rows = [row for row in seeds.get("seeds", ()) if isinstance(row, dict)]
    rules_by_node = _rules_by_node(rules)
    seeds_by_node = Counter(str(row.get("directory_node", "")) for row in seed_rows)
    synthetic_by_node = _synthetic_by_node()
    external_by_node = _external_by_node()
    rows = []
    for node in directory.get("nodes", ()):
        if not isinstance(node, dict):
            continue
        node_key = str(node.get("node_id", ""))
        node_rules = rules_by_node.get(node_key, ())
        node_external = external_by_node.get(node_key, ())
        missing_external_topics = _missing_external_topics(node_rules, node_external)
        missing_p0_external_topics = tuple(
            topic for topic in missing_external_topics if topic.get("priority") == "P0"
        )
        rows.append(
            {
                "version": "v20.knowledge_completeness_node_audit.v1",
                "node_key": node_key,
                "label": str(node.get("title", "")),
                "priority": str(node.get("priority", "")),
                "seed_count": int(seeds_by_node.get(node_key, 0)),
                "rule_count": len(node_rules),
                "runtime_allowed_count": sum(1 for row in node_rules if row.get("runtime_allowed") is True),
                "condition_atom_count": sum(len(row.get("condition_atoms", ())) for row in node_rules),
                "portrait_output_count": sum(len(row.get("portrait_outputs", ())) for row in node_rules),
                "question_output_count": sum(len(row.get("question_outputs", ())) for row in node_rules),
                "answer_guidance_count": sum(len(row.get("answer_guidance", ())) for row in node_rules),
                "counterexample_count": sum(len(row.get("counterexamples", ())) for row in node_rules),
                "synthetic_case_count": int(synthetic_by_node.get(node_key, 0)),
                "external_topic_count": len(node_external),
                "external_topics": node_external,
                "missing_external_topics": missing_external_topics,
                "missing_p0_external_topics": missing_p0_external_topics,
                "gap_tags": _gap_tags(
                    node_key=node_key,
                    rules=node_rules,
                    seed_count=int(seeds_by_node.get(node_key, 0)),
                    synthetic_count=int(synthetic_by_node.get(node_key, 0)),
                    external_topics=node_external,
                    missing_p0_external_topics=missing_p0_external_topics,
                    missing_application_topics=tuple(
                        topic for topic in missing_external_topics if node_key == "L10"
                    ),
                ),
                "runtime_mutation": False,
            }
        )
    total_external = len(EXTERNAL_TOPIC_MAP)
    covered_external = sum(1 for row in EXTERNAL_TOPIC_MAP if _external_topic_covered(row, rows))
    p0_gaps = [
        {"node_key": row["node_key"], "label": row["label"], "gap_tags": row["gap_tags"]}
        for row in rows
        if row["priority"] == "P0" and row["gap_tags"]
    ]
    return {
        "version": KNOWLEDGE_COMPLETENESS_AUDIT_VERSION,
        "status": "needs_work" if p0_gaps else "complete",
        "node_count": len(rows),
        "p0_node_count": sum(1 for row in rows if row["priority"] == "P0"),
        "seed_count": len(seed_rows),
        "rule_count": len(rules),
        "runtime_allowed_count": sum(1 for row in rules if row.get("runtime_allowed") is True),
        "synthetic_case_count": len(RULE_SYNTHETIC_CASES),
        "external_topic_count": total_external,
        "external_topic_covered_count": covered_external,
        "external_completeness_percent": round(covered_external / max(1, total_external) * 100),
        "node_audits": rows,
        "p0_gaps": p0_gaps,
        "next_actions": _next_actions(rows),
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_COMPLETENESS_AUDIT_READ_ONLY",
            "EXTERNAL_TOPICS_ARE_GAP_REFERENCES_NOT_RUNTIME_TRUTH",
            "NO_RUNTIME_POINTER_WRITE_FROM_AUDIT",
            "AUDIT_FEEDS_KNOWLEDGE_BRAIN_MAINLINE",
        ],
    }


def _rules_by_node(rules: list[dict[str, object]]) -> dict[str, tuple[dict[str, object], ...]]:
    rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for rule in rules:
        node = _node_for_rule(rule)
        if node:
            rows[node].append(rule)
    return {key: tuple(value) for key, value in rows.items()}


def _node_for_rule(rule: dict[str, object]) -> str:
    source_id = str(rule.get("source_knowledge_id", ""))
    for prefix, node in SOURCE_PREFIX_TO_NODE.items():
        if source_id.startswith(prefix):
            return node
    return DOMAIN_TO_NODE.get(str(rule.get("domain", "")), "")


def _synthetic_by_node() -> Counter[str]:
    counter: Counter[str] = Counter()
    for case in RULE_SYNTHETIC_CASES:
        for prefix, node in SYNTHETIC_CASE_PREFIX_TO_NODE.items():
            if case.case_id.startswith(prefix):
                counter[node] += 1
        for domain in case.expected_rule_domains:
            node = DOMAIN_TO_NODE.get(str(domain))
            if node:
                counter[node] += 1
    return counter


def _external_by_node() -> dict[str, tuple[dict[str, object], ...]]:
    rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    for topic in EXTERNAL_TOPIC_MAP:
        rows[str(topic["node_key"])].append(dict(topic))
    return {key: tuple(value) for key, value in rows.items()}


def _external_topic_covered(topic: dict[str, object], node_rows: list[dict[str, object]]) -> bool:
    node_key = str(topic.get("node_key", ""))
    priority = str(topic.get("priority", ""))
    row = next((item for item in node_rows if item["node_key"] == node_key), {})
    if not row:
        return False
    if priority == "P0":
        topic_key = str(topic.get("topic_key", ""))
        missing_topics = {
            str(item.get("topic_key", ""))
            for item in row.get("missing_p0_external_topics", ())
            if isinstance(item, dict)
        }
        return topic_key not in missing_topics and int(row.get("synthetic_case_count", 0) or 0) > 0
    return int(row.get("seed_count", 0) or 0) > 0


def _missing_external_topics(
    rules: tuple[dict[str, object], ...],
    external_topics: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    source_ids = tuple(str(row.get("source_knowledge_id", "")) for row in rules)
    missing: list[dict[str, object]] = []
    for topic in external_topics:
        topic_key = str(topic.get("topic_key", ""))
        prefixes = EXTERNAL_TOPIC_RULE_PREFIXES.get(topic_key, ())
        if not prefixes:
            continue
        if prefixes and any(source_id.startswith(prefix) for source_id in source_ids for prefix in prefixes):
            continue
        missing.append(dict(topic))
    return tuple(missing)


def _gap_tags(
    *,
    node_key: str,
    rules: tuple[dict[str, object], ...],
    seed_count: int,
    synthetic_count: int,
    external_topics: tuple[dict[str, object], ...],
    missing_p0_external_topics: tuple[dict[str, object], ...],
    missing_application_topics: tuple[dict[str, object], ...],
) -> list[str]:
    gaps: list[str] = []
    p0_topics = [row for row in external_topics if row.get("priority") == "P0"]
    if seed_count <= 0:
        gaps.append("missing_directory_seed")
    if p0_topics and not rules:
        gaps.append("missing_runtime_rule_for_p0_external_topics")
    if p0_topics and synthetic_count <= 0:
        gaps.append("missing_synthetic_case_for_p0_external_topics")
    if rules and sum(len(row.get("answer_guidance", ())) for row in rules) <= 0:
        gaps.append("missing_answer_guidance")
    if missing_p0_external_topics:
        gaps.append("needs_p0_atomized_knowledge_units")
    if node_key == "L10" and missing_application_topics:
        gaps.append("needs_application_topic_expansion")
    return list(dict.fromkeys(gaps))


def _next_actions(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    actions = []
    for row in rows:
        for gap in row.get("gap_tags", ()):
            actions.append(
                {
                    "node_key": row["node_key"],
                    "label": row["label"],
                    "action": _action_for_gap(str(gap)),
                    "gap_tag": str(gap),
                }
            )
    return actions[:24]


def _action_for_gap(gap: str) -> str:
    return {
        "missing_directory_seed": "add_directory_seed",
        "missing_runtime_rule_for_p0_external_topics": "add_runtime_knowledge_rule",
        "missing_synthetic_case_for_p0_external_topics": "add_synthetic_case",
        "missing_answer_guidance": "add_answer_guidance",
        "needs_p0_atomized_knowledge_units": "split_p0_topic_into_atomized_knowledge_units",
        "needs_application_topic_expansion": "add_application_topic_units",
    }.get(gap, "review_gap")
