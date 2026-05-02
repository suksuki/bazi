from __future__ import annotations


def build_macro_dimension_catalog() -> dict[str, object]:
    dimensions = (
        _dimension(
            "wealth",
            "财富",
            "wealth",
            "财星、食伤生财、财库、比劫分夺、承载力与现金流结构。",
            ("wealth/", "interaction/", "branch_advanced/", "time_context/"),
            ("财星显隐", "食伤生财", "财库开闭", "比劫分财", "岁运引动"),
        ),
        _dimension(
            "career",
            "事业",
            "career",
            "官杀规则、印星平台、食伤表达、格局承接与职业结构。",
            ("career/", "interaction/", "pattern/", "time_context/"),
            ("官杀规则", "伤官见官", "官印相生", "格局事业承接", "学业考试"),
        ),
        _dimension(
            "relationship",
            "关系",
            "relationship",
            "人际、合作、资源分配、比劫互动和外部关系结构。",
            ("relationship/", "interaction/", "palace/", "blind/lifa/"),
            ("比劫合作竞争", "人际互动", "合作承接", "关系宫位", "外部资源分配"),
        ),
        _dimension(
            "romance",
            "感情",
            "relationship",
            "婚恋、伴侣星、日支、关系宫位、合冲引动与亲密关系边界。",
            ("relationship/romance/", "palace/", "interaction/", "time_context/"),
            ("配偶星", "日支夫妻宫", "感情合冲", "关系承接", "婚恋安全边界"),
        ),
        _dimension(
            "health",
            "健康",
            "health",
            "五行偏枯、寒暖燥湿、承载压力、节律恢复与医疗禁断边界。",
            ("health/", "element/", "strength/", "time_context/"),
            ("五行偏枯", "寒暖燥湿", "压力恢复", "节律边界", "医疗禁断"),
        ),
    )
    return {
        "version": "v20.macro_dimension_catalog.v1",
        "status": "ready",
        "dimension_count": len(dimensions),
        "dimensions": dimensions,
        "current_primary_dimensions": ("wealth", "career", "relationship", "romance", "health"),
        "expansion_policy": "open_ended_add_macro_dimension_without_changing_core_bazi_domains_first",
        "runtime_mutation": False,
        "guardrails": [
            "MACRO_DIMENSIONS_ARE_READING_TOPICS_NOT_CORE_BAZI_FACTS",
            "NEW_MACRO_DIMENSIONS_MUST_MAP_TO_EXISTING_BAZI_EVIDENCE_DOMAINS_FIRST",
            "ROMANCE_USES_RELATIONSHIP_EVIDENCE_UNTIL_DEDICATED_RULES_ARE_REVIEWED",
            "HEALTH_REMAINS_NON_MEDICAL_STRUCTURE_BOUNDARY",
        ],
    }


def _dimension(
    dimension_key: str,
    title: str,
    evidence_domain: str,
    scope: str,
    directories: tuple[str, ...],
    first_wave_topics: tuple[str, ...],
) -> dict[str, object]:
    return {
        "dimension_key": dimension_key,
        "title": title,
        "layer": "macro_application",
        "evidence_domain": evidence_domain,
        "scope": scope,
        "directories": directories,
        "first_wave_topics": first_wave_topics,
        "status": "directory_ready",
        "content_status": "needs_topic_units",
        "runtime_allowed": False,
    }
