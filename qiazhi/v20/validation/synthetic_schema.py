from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SyntheticCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    expected_feature_domains: tuple[str, ...] = field(default_factory=tuple)
    expected_question_keys: tuple[str, ...] = field(default_factory=tuple)
    expected_rule_candidate_domains: tuple[str, ...] = field(default_factory=tuple)
    forbidden_text: tuple[str, ...] = ("发财", "破财", "疾病", "应期", "一定", "必然")
    mutation_invariants: tuple[str, ...] = ("no_rule_mutation", "no_answer_mutation", "no_core_fact_mutation")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExpectedRuntimeOutput:
    feature_domains: tuple[str, ...] = field(default_factory=tuple)
    rule_domains: tuple[str, ...] = field(default_factory=tuple)
    portrait_labels: tuple[str, ...] = field(default_factory=tuple)
    question_keys: tuple[str, ...] = field(default_factory=tuple)
    dag_stages: tuple[str, ...] = field(default_factory=tuple)
    role_keys: tuple[str, ...] = ("guest", "user", "analyst", "admin")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "ExpectedRuntimeOutput":
        row = payload if isinstance(payload, dict) else {}
        return cls(
            feature_domains=_tuple_of_str(row.get("feature_domains")),
            rule_domains=_tuple_of_str(row.get("rule_domains")),
            portrait_labels=_tuple_of_str(row.get("portrait_labels")),
            question_keys=_tuple_of_str(row.get("question_keys")),
            dag_stages=_tuple_of_str(row.get("dag_stages")),
            role_keys=_tuple_of_str(row.get("role_keys")) or ("guest", "user", "analyst", "admin"),
        )


@dataclass(frozen=True)
class RoleViewExpectation:
    role_key: str
    required_stages: tuple[str, ...] = field(default_factory=tuple)
    forbidden_stages: tuple[str, ...] = field(default_factory=tuple)
    max_question_count: int = 0
    required_visibility: str = ""
    forbidden_terms: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RoleViewExpectation":
        return cls(
            role_key=str(payload.get("role_key") or ""),
            required_stages=_tuple_of_str(payload.get("required_stages")),
            forbidden_stages=_tuple_of_str(payload.get("forbidden_stages")),
            max_question_count=max(0, _int_value(payload.get("max_question_count"), default=0)),
            required_visibility=str(payload.get("required_visibility") or ""),
            forbidden_terms=_tuple_of_str(payload.get("forbidden_terms")),
        )


@dataclass(frozen=True)
class QuestionReviewExpectation:
    required_actions: tuple[str, ...] = field(default_factory=tuple)
    required_reasons: tuple[str, ...] = field(default_factory=tuple)
    forbidden_runtime_mutations: tuple[str, ...] = (
        "core_fact_mutation",
        "rule_truth_mutation",
        "useful_god_truth_mutation",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "QuestionReviewExpectation":
        row = payload if isinstance(payload, dict) else {}
        return cls(
            required_actions=_tuple_of_str(row.get("required_actions")),
            required_reasons=_tuple_of_str(row.get("required_reasons")),
            forbidden_runtime_mutations=_tuple_of_str(row.get("forbidden_runtime_mutations"))
            or ("core_fact_mutation", "rule_truth_mutation", "useful_god_truth_mutation"),
        )


@dataclass(frozen=True)
class NegativeExpectation:
    forbidden_text: tuple[str, ...] = ("发财", "破财", "疾病", "应期", "一定", "必然")
    forbidden_portrait_labels: tuple[str, ...] = field(default_factory=tuple)
    forbidden_question_stages: tuple[str, ...] = field(default_factory=tuple)
    forbidden_role_stages: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "NegativeExpectation":
        row = payload if isinstance(payload, dict) else {}
        role_stages: dict[str, tuple[str, ...]] = {}
        raw_role_stages = row.get("forbidden_role_stages", {})
        if isinstance(raw_role_stages, dict):
            role_stages = {str(key): _tuple_of_str(value) for key, value in raw_role_stages.items()}
        return cls(
            forbidden_text=_tuple_of_str(row.get("forbidden_text")) or ("发财", "破财", "疾病", "应期", "一定", "必然"),
            forbidden_portrait_labels=_tuple_of_str(row.get("forbidden_portrait_labels")),
            forbidden_question_stages=_tuple_of_str(row.get("forbidden_question_stages")),
            forbidden_role_stages=role_stages,
        )


@dataclass(frozen=True)
class SyntheticBaziCase:
    case_id: str
    case_type: str
    target_pattern: str
    chart_input: dict[str, str]
    chart_constraints: dict[str, Any] = field(default_factory=dict)
    time_context: dict[str, Any] = field(default_factory=dict)
    expected: ExpectedRuntimeOutput = field(default_factory=ExpectedRuntimeOutput)
    negative: NegativeExpectation = field(default_factory=NegativeExpectation)
    role_expectations: tuple[RoleViewExpectation, ...] = field(default_factory=tuple)
    question_review_expectation: QuestionReviewExpectation = field(default_factory=QuestionReviewExpectation)
    quality_gates: tuple[str, ...] = (
        "rule_precision",
        "portrait_alignment",
        "question_focus",
        "role_separation",
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    guardrails: tuple[str, ...] = (
        "SYNTHETIC_BAZI_CASE_IS_TRAINING_FIXTURE",
        "NO_DESTINY_TRUTH_LABEL",
        "NO_USER_PRIVATE_TEXT",
        "NO_RUNTIME_RULE_MUTATION",
    )

    @property
    def pillar_displays(self) -> tuple[str, str, str, str]:
        return (
            str(self.chart_input.get("year") or ""),
            str(self.chart_input.get("month") or ""),
            str(self.chart_input.get("day") or ""),
            str(self.chart_input.get("hour") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SyntheticBaziCase":
        chart_input = payload.get("chart_input", {})
        if not isinstance(chart_input, dict):
            chart_input = {}
        expected = ExpectedRuntimeOutput.from_dict(_dict_value(payload.get("expected")))
        negative = NegativeExpectation.from_dict(_dict_value(payload.get("negative")))
        role_rows = payload.get("role_expectations", ())
        roles = tuple(
            RoleViewExpectation.from_dict(row)
            for row in role_rows
            if isinstance(row, dict)
        )
        return cls(
            case_id=str(payload.get("case_id") or ""),
            case_type=str(payload.get("case_type") or ""),
            target_pattern=str(payload.get("target_pattern") or ""),
            chart_input={str(key): str(value) for key, value in chart_input.items()},
            chart_constraints=_dict_value(payload.get("chart_constraints")),
            time_context=_dict_value(payload.get("time_context")),
            expected=expected,
            negative=negative,
            role_expectations=roles,
            question_review_expectation=QuestionReviewExpectation.from_dict(
                _dict_value(payload.get("question_review_expectation"))
            ),
            quality_gates=_tuple_of_str(payload.get("quality_gates"))
            or ("rule_precision", "portrait_alignment", "question_focus", "role_separation"),
            metadata=_dict_value(payload.get("metadata")),
            guardrails=_tuple_of_str(payload.get("guardrails"))
            or (
                "SYNTHETIC_BAZI_CASE_IS_TRAINING_FIXTURE",
                "NO_DESTINY_TRUTH_LABEL",
                "NO_USER_PRIVATE_TEXT",
                "NO_RUNTIME_RULE_MUTATION",
            ),
        )


def minimal_synthetic_bazi_cases() -> tuple[SyntheticBaziCase, ...]:
    return MINIMAL_SYNTHETIC_BAZI_CASES


def synthetic_bazi_case_manifest(cases: tuple[SyntheticBaziCase, ...] = ()) -> dict[str, Any]:
    rows = cases or MINIMAL_SYNTHETIC_BAZI_CASES
    case_types = tuple(sorted({case.case_type for case in rows}))
    role_keys = tuple(sorted({role.role_key for case in rows for role in case.role_expectations}))
    dag_stages = tuple(sorted({stage for case in rows for stage in case.expected.dag_stages}))
    return {
        "version": "v20.synthetic_bazi_case_manifest.v1",
        "case_count": len(rows),
        "case_types": case_types,
        "role_keys": role_keys,
        "dag_stages": dag_stages,
        "quality_gates": tuple(sorted({gate for case in rows for gate in case.quality_gates})),
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_CASE_MANIFEST_ONLY",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_USER_PRIVATE_TEXT",
        ],
    }


def synthetic_bazi_coverage_report(cases: tuple[SyntheticBaziCase, ...] = ()) -> dict[str, Any]:
    rows = cases or MINIMAL_SYNTHETIC_BAZI_CASES
    manifest = synthetic_bazi_case_manifest(rows)
    feature_domains = _sorted_case_values(rows, lambda case: case.expected.feature_domains)
    rule_domains = _sorted_case_values(rows, lambda case: case.expected.rule_domains)
    question_keys = _sorted_case_values(rows, lambda case: case.expected.question_keys)
    portrait_labels = _sorted_case_values(rows, lambda case: case.expected.portrait_labels)
    boundary_capabilities = _boundary_capabilities(rows)
    required_domains = ("strength", "ten_god", "branch", "element", "wealth", "career", "relationship", "health")
    required_stages = ("entry", "focus", "structure", "timing", "review", "observe", "advice", "closure")
    missing_domains = tuple(domain for domain in required_domains if domain not in set(feature_domains) | set(rule_domains))
    missing_stages = tuple(stage for stage in required_stages if stage not in manifest["dag_stages"])
    missing_capabilities = tuple(
        capability
        for capability in (
            "extreme_structure",
            "negative_boundary",
            "multi_time_layer",
            "role_leakage_guardrail",
            "question_dag",
            "role_observation",
        )
        if capability not in boundary_capabilities
    )
    gaps = missing_domains + missing_stages + missing_capabilities
    return {
        "version": "v20.synthetic_bazi_coverage_report.v1",
        "status": "pass" if not gaps else "needs_expansion",
        "case_count": len(rows),
        "case_types": manifest["case_types"],
        "feature_domains": feature_domains,
        "rule_domains": rule_domains,
        "question_keys": question_keys,
        "portrait_labels": portrait_labels,
        "dag_stages": manifest["dag_stages"],
        "role_keys": manifest["role_keys"],
        "boundary_capabilities": boundary_capabilities,
        "missing_domains": missing_domains,
        "missing_stages": missing_stages,
        "missing_capabilities": missing_capabilities,
        "gap_count": len(gaps),
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_COVERAGE_REPORT_ONLY",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
        ],
    }


def validate_synthetic_bazi_case_schema(case: SyntheticBaziCase) -> tuple[str, ...]:
    failures: list[str] = []
    if not case.case_id:
        failures.append("missing_case_id")
    if not case.case_type:
        failures.append("missing_case_type")
    if not case.target_pattern:
        failures.append("missing_target_pattern")
    if any(not value for value in case.pillar_displays):
        failures.append("missing_pillar_display")
    if not case.expected.feature_domains and not case.expected.rule_domains:
        failures.append("missing_expected_domains")
    if "NO_RUNTIME_RULE_MUTATION" not in case.guardrails:
        failures.append("missing_no_runtime_rule_mutation_guardrail")
    if "NO_USER_PRIVATE_TEXT" not in case.guardrails:
        failures.append("missing_no_user_private_text_guardrail")
    return tuple(failures)


def _sorted_case_values(
    cases: tuple[SyntheticBaziCase, ...],
    getter: Any,
) -> tuple[str, ...]:
    return tuple(sorted({value for case in cases for value in getter(case)}))


def _boundary_capabilities(cases: tuple[SyntheticBaziCase, ...]) -> tuple[str, ...]:
    capabilities: set[str] = set()
    for case in cases:
        if case.case_type == "extreme_structure_case":
            capabilities.add("extreme_structure")
        if case.case_type == "negative_boundary_case":
            capabilities.add("negative_boundary")
        if case.case_type == "time_layer_case":
            capabilities.add("multi_time_layer")
        if case.case_type == "role_leakage_case":
            capabilities.add("role_leakage_guardrail")
        if case.case_type == "question_dag_case":
            capabilities.add("question_dag")
        if case.case_type == "role_observation_case":
            capabilities.add("role_observation")
    return tuple(sorted(capabilities))


def _case(
    case_id: str,
    case_type: str,
    target_pattern: str,
    pillars: tuple[str, str, str, str],
    *,
    feature_domains: tuple[str, ...],
    rule_domains: tuple[str, ...],
    portrait_labels: tuple[str, ...],
    question_keys: tuple[str, ...],
    dag_stages: tuple[str, ...],
    guest_forbidden: tuple[str, ...] = ("review", "observe"),
    analyst_required: tuple[str, ...] = ("review",),
) -> SyntheticBaziCase:
    return SyntheticBaziCase(
        case_id=case_id,
        case_type=case_type,
        target_pattern=target_pattern,
        chart_input={
            "year": pillars[0],
            "month": pillars[1],
            "day": pillars[2],
            "hour": pillars[3],
        },
        chart_constraints={
            "target_pattern": target_pattern,
            "constraint_source": "minimal_synthetic_bazi_case_set",
        },
        expected=ExpectedRuntimeOutput(
            feature_domains=feature_domains,
            rule_domains=rule_domains,
            portrait_labels=portrait_labels,
            question_keys=question_keys,
            dag_stages=dag_stages,
        ),
        negative=NegativeExpectation(
            forbidden_role_stages={"guest": guest_forbidden, "user": ("observe",)},
        ),
        role_expectations=(
            RoleViewExpectation(
                role_key="guest",
                required_stages=("entry",),
                forbidden_stages=guest_forbidden,
                max_question_count=3,
                required_visibility="public_entry",
                forbidden_terms=("复核", "证据边界", "runtime", "policy"),
            ),
            RoleViewExpectation(
                role_key="user",
                required_stages=("focus",),
                forbidden_stages=("observe",),
                max_question_count=6,
                required_visibility="public_guided",
            ),
            RoleViewExpectation(
                role_key="analyst",
                required_stages=analyst_required,
                max_question_count=10,
                required_visibility="technical_review",
            ),
            RoleViewExpectation(
                role_key="admin",
                required_stages=("observe",),
                max_question_count=12,
                required_visibility="system_observation",
            ),
        ),
        question_review_expectation=QuestionReviewExpectation(
            required_actions=("approve", "rewrite", "downrank", "merge", "delete"),
            required_reasons=(
                "role_mismatch",
                "mainline_mismatch",
                "too_technical",
                "duplicate",
                "unfocused",
            ),
        ),
        metadata={"fixture_stage": "N1"},
    )


MINIMAL_SYNTHETIC_BAZI_CASES: tuple[SyntheticBaziCase, ...] = (
    _case(
        "v20.synthetic.bazi.wealth_weak_dm_001",
        "portrait_question_case",
        "财星可见但日主承接不足",
        ("庚午", "辛巳", "丁丑", "乙巳"),
        feature_domains=("strength", "wealth", "ten_god"),
        rule_domains=("wealth", "strength"),
        portrait_labels=("财星压力", "资源承接"),
        question_keys=("q_income_stability",),
        dag_stages=("entry", "focus", "structure", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.output_to_wealth_001",
        "question_dag_case",
        "食伤生财但需看承接",
        ("甲子", "戊辰", "甲午", "辛酉"),
        feature_domains=("ten_god", "wealth", "career"),
        rule_domains=("ten_god", "wealth"),
        portrait_labels=("输出变现", "财星通道"),
        question_keys=("q_income_stability", "q_career_structure"),
        dag_stages=("entry", "focus", "structure", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.injury_officer_with_resource_001",
        "metamorphic_case",
        "伤官见官见印缓冲",
        ("壬寅", "甲辰", "丙子", "甲午"),
        feature_domains=("ten_god", "career", "strength"),
        rule_domains=("career", "ten_god"),
        portrait_labels=("事业压力", "印星缓冲"),
        question_keys=("q_career_structure",),
        dag_stages=("focus", "structure", "review", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.branch_collision_001",
        "rule_case",
        "地支冲合需要分层复核",
        ("甲子", "戊辰", "甲午", "辛酉"),
        feature_domains=("branch", "relationship", "time"),
        rule_domains=("branch",),
        portrait_labels=("地支互动", "关系牵动"),
        question_keys=("q_branch_relation_detail",),
        dag_stages=("focus", "structure", "review", "timing"),
    ),
    _case(
        "v20.synthetic.bazi.useful_god_candidate_001",
        "rule_case",
        "用神只能作为候选路径",
        ("壬寅", "甲辰", "丙子", "甲午"),
        feature_domains=("useful_god", "strength", "element"),
        rule_domains=("useful_god", "strength"),
        portrait_labels=("用神候选", "结构扶抑"),
        question_keys=("q_useful_god_candidates",),
        dag_stages=("structure", "review", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.time_trigger_001",
        "interaction_case",
        "大运流年显式引动",
        ("庚午", "辛巳", "丁丑", "乙巳"),
        feature_domains=("time", "branch", "ten_god"),
        rule_domains=("time",),
        portrait_labels=("时间触发", "岁运引动"),
        question_keys=("q_time_layer_context",),
        dag_stages=("focus", "timing", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.relationship_projection_001",
        "portrait_question_case",
        "关系主题回到地支和十神互动",
        ("甲子", "戊辰", "甲午", "辛酉"),
        feature_domains=("relationship", "branch", "ten_god"),
        rule_domains=("relationship", "branch"),
        portrait_labels=("关系互动", "地支牵动"),
        question_keys=("q_relationship_structure",),
        dag_stages=("entry", "focus", "structure", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.health_boundary_001",
        "negative_boundary_case",
        "健康只看五行平衡边界",
        ("壬寅", "甲辰", "丙子", "甲午"),
        feature_domains=("health", "element"),
        rule_domains=("health", "element"),
        portrait_labels=("五行平衡", "结构压力边界"),
        question_keys=("q_health_balance_boundary",),
        dag_stages=("entry", "focus", "advice"),
    ),
    _case(
        "v20.synthetic.bazi.pattern_review_001",
        "role_review_case",
        "格局只进入复核路径",
        ("庚午", "辛巳", "丁丑", "乙巳"),
        feature_domains=("pattern", "strength", "ten_god"),
        rule_domains=("pattern",),
        portrait_labels=("格局复核", "结构候选"),
        question_keys=("q_pattern_structure",),
        dag_stages=("structure", "review", "closure"),
    ),
    _case(
        "v20.synthetic.bazi.admin_observe_policy_001",
        "role_observation_case",
        "管理员观察问题来源和策略版本",
        ("甲子", "戊辰", "甲午", "辛酉"),
        feature_domains=("strength", "ten_god", "branch"),
        rule_domains=("strength", "branch"),
        portrait_labels=("地支互动", "十神角色"),
        question_keys=("q_branch_relation_detail",),
        dag_stages=("observe", "review", "closure"),
        guest_forbidden=("review", "observe", "policy"),
        analyst_required=("review",),
    ),
    _case(
        "v20.synthetic.bazi.extreme_same_element_001",
        "extreme_structure_case",
        "同类五行过重只进入结构边界复核",
        ("甲寅", "甲寅", "甲寅", "甲寅"),
        feature_domains=("strength", "element", "ten_god"),
        rule_domains=("strength", "element"),
        portrait_labels=("日主承载", "五行平衡"),
        question_keys=("q_strength_assessment", "q_element_balance"),
        dag_stages=("entry", "structure", "review", "advice"),
        guest_forbidden=("review", "observe", "policy", "arbitration"),
    ),
    _case(
        "v20.synthetic.bazi.full_collision_boundary_001",
        "negative_boundary_case",
        "多重冲动只提示结构波动不作断言",
        ("甲子", "庚午", "甲子", "庚午"),
        feature_domains=("branch", "relationship", "time"),
        rule_domains=("branch", "relationship"),
        portrait_labels=("地支互动", "关系互动"),
        question_keys=("q_branch_relation_detail", "q_relationship_structure"),
        dag_stages=("focus", "structure", "review", "advice"),
        guest_forbidden=("review", "observe", "policy", "arbitration"),
    ),
    _case(
        "v20.synthetic.bazi.multi_time_layer_001",
        "time_layer_case",
        "流年流月同时存在时只作为时间层上下文",
        ("庚午", "辛巳", "丁丑", "乙巳"),
        feature_domains=("branch", "ten_god", "wealth"),
        rule_domains=("branch", "wealth"),
        portrait_labels=("时运触发", "财富承接"),
        question_keys=("q_time_layer_context", "q_income_stability"),
        dag_stages=("focus", "timing", "structure", "advice"),
        guest_forbidden=("review", "observe", "policy", "arbitration"),
    ),
    _case(
        "v20.synthetic.bazi.role_leakage_guardrail_001",
        "role_leakage_case",
        "游客不得看到复核和策略观测语言",
        ("壬寅", "甲辰", "丙子", "甲午"),
        feature_domains=("useful_god", "strength", "element"),
        rule_domains=("useful_god", "strength"),
        portrait_labels=("用神候选", "结构扶抑"),
        question_keys=("q_useful_god_candidates", "q_strength_assessment"),
        dag_stages=("entry", "focus", "review", "closure"),
        guest_forbidden=("review", "observe", "policy", "arbitration", "technical_review"),
        analyst_required=("review",),
    ),
)


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
