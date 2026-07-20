from __future__ import annotations

import time

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.agent_api import _is_current_cognitive_record
from product.agent_job_store import MemoryAgentJobStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from core.contracts import BirthInputCanonical
from core.mingli_agent import CaseCognitiveWorkspace, ChartWorldInstance, MingliAgent, MingliCognitiveRecord, MingliContextCompiler, ProbePlanner, apply_deliberation_selection, apply_probe_response, build_case_workspace, build_deliberation_view, compile_chart_world, undo_deliberation_selection
from core.life_domains import LifeDomain
from core.life_case import build_baseline_insight, commit_baseline_life_case, commit_case_revision, commit_temporal_prior, validate_formal_insight
from core.mingli_agent.probe import _project_option_label
from core.mingli_agent.context import _public_birth_location
from core.mingli_agent.fact_review import repair_locked_fact_assertions
from core.mingli_agent.reasoner import _citation_allowed, _contains_asserted_relation, _contains_role_conflict, _domain_context_payload, _forbidden_domain_tokens, _normalize_domain_reading, _normalize_prediction_probe, _prediction_stage_errors, _repair_pattern_locally, _review_hypothesis_space, _sanitize_pattern_alternatives, _sanitize_work_questions, _semantic_text_errors, sanitize_public_mingli_payload
from core.mingli_agent.contracts import (
    BirthIntakeDraft,
    CaseAssertion,
    CaseTurnDraft,
    CognitiveHypothesis,
    DiscriminatingProbe,
    DomainCausalReading,
    DualLensCognitionDraft,
    PatternHypothesisDraft,
    PatternPreviewDraft,
    PredictionProbeDraft,
    PriorPrediction,
    SalientPhenomenon,
    UsefulGodReasoning,
    WholeChartCognitionDraft,
    WorkPathPortraitDraft,
    WorkPathReasoning,
    WorldFact,
    ZiweiLensObservation,
)


class FakeCognitiveModel:
    model = "fake-mingli-cognitive-model"

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        if schema is BirthIntakeDraft:
            return BirthIntakeDraft(
                name="测试档案",
                gender="male",
                calendar_type="solar",
                birth_date="1987-05-12",
                birth_time="18:00",
                birth_location="上海",
                timezone="Asia/Shanghai",
                time_precision="exact",
                ready_for_confirmation=True,
            )
        if schema is PatternHypothesisDraft:
            return PatternHypothesisDraft(
                first_look="这张盘先看丁火如何作用于巳酉丑金局，而不是只看月令旺衰。",
                whole_chart_thesis="主线是输出能力能否驾驭结构压力，酉与丁是区分不同解释的关键。",
                salient_phenomena=[SalientPhenomenon(phenomenon_id="s1", observation="巳酉丑连接", why_it_matters="决定压力端是否闭合", evidence_refs=["F001"])],
                hypotheses=_hypotheses(),
                selected_hypothesis_id="h1",
                evidence_refs=["F001"],
            )
        if schema is PatternPreviewDraft:
            return PatternPreviewDraft(
                preview_line="这张盘先看丁火如何作用于巳酉丑金局，以及乙木能否借输出承接规则压力。",
                focus_refs=["F001"],
            )
        if schema is WorkPathPortraitDraft:
            return WorkPathPortraitDraft(
                work_path=_work_path(),
                useful_god_reasoning=[UsefulGodReasoning(candidate="丁火", role="做功用神", why_useful="连接乙木与金局压力", when_harmful="泄身过度且无法制金", applicable_conditions=["金局为主要压力"], invalidating_conditions=["丁火完全失效"], evidence_refs=["F001"])],
                portrait=[_assertion("portrait-1", "portrait", "更习惯用方法和产出处理压力。")],
                unresolved_questions=["现实工作是否依赖复杂问题解决"],
                evidence_refs=["F001"],
            )
        if schema is PredictionProbeDraft:
            return PredictionProbeDraft(prior_predictions=_predictions(), next_probe=_probe())
        if schema is DiscriminatingProbe:
            return _probe()
        if schema is DualLensCognitionDraft:
            return _dual_lens()
        if schema is WholeChartCognitionDraft:
            hypotheses = [
                CognitiveHypothesis(
                    hypothesis_id="h1",
                    name="输出制压候选",
                    thesis="乙木通过丁火输出作用于金局压力。",
                    rank=1,
                    status="primary",
                    supporting_evidence_refs=["F001"],
                    failure_conditions=["丁火失效"],
                    confidence="high",
                ),
                CognitiveHypothesis(
                    hypothesis_id="h2",
                    name="从杀候选",
                    thesis="若输出与同类完全失效，才考虑顺从金势。",
                    rank=2,
                    status="alternative",
                    supporting_evidence_refs=["F001"],
                    failure_conditions=["可见输出仍参与做功"],
                    rejection_reason="丁火与多乙透干使纯从解释不足。",
                    confidence="low",
                ),
            ]
            predictions = [
                PriorPrediction(
                    prediction_id=f"p{index}",
                    claim=claim,
                    why_predicted="来自输出处理压力的主假设。",
                    target_hypothesis_ref="h1",
                    evidence_refs=["F001"],
                    disconfirming_answer="长期完全依赖关系维护且不需要专业判断。",
                )
                for index, claim in enumerate(
                    ["更常通过专业输出解决压力。", "重复低自主工作更容易消耗。", "复杂问题比单纯执行更能激活能力。"],
                    start=1,
                )
            ]
            return WholeChartCognitionDraft(
                first_look="这张盘先看丁火如何作用于巳酉丑金局，而不是只看月令旺衰。",
                whole_chart_thesis="主线是输出能力能否驾驭结构压力，酉与丁是区分不同解释的关键。",
                salient_phenomena=[SalientPhenomenon(phenomenon_id="s1", observation="巳酉丑连接", why_it_matters="决定压力端是否闭合", evidence_refs=["F001"])],
                hypotheses=hypotheses,
                selected_hypothesis_id="h1",
                work_path=WorkPathReasoning(
                    path_statement="乙木生丁火，丁火制金局压力。",
                    source=["乙木"],
                    transformations=["丁火输出"],
                    target=["酉金压力"],
                    body_function_relation="乙为体，丁火制金为用。",
                    closure="conditional",
                    success_conditions=["丁火可用"],
                    failure_conditions=["水印压制输出"],
                    evidence_refs=["F001"],
                ),
                useful_god_reasoning=[UsefulGodReasoning(candidate="丁火", role="做功用神", why_useful="连接乙木与金局压力", when_harmful="泄身过度且无法制金", applicable_conditions=["金局为主要压力"], invalidating_conditions=["丁火完全失效"], evidence_refs=["F001"])],
                portrait=[_assertion("portrait-1", "portrait", "更习惯用方法和产出处理压力。")],
                prior_predictions=predictions,
                next_probe=_probe(),
                dual_lens=_dual_lens() if "紫微可用：true" in prompt else None,
                unresolved_questions=["现实工作是否依赖复杂问题解决"],
                evidence_refs=["F001"],
            )
        if schema is DomainCausalReading:
            domain = next(
                (item.value for item in LifeDomain if item is not LifeDomain.WHOLE_CHART and f"`{item.value}`" in prompt),
                "wealth" if "wealth" in prompt else "career",
            )
            question = {
                "wealth": "能力输出如何完成资源转化与承载？",
                "career": "职业价值如何通过输出处理压力形成？",
            }.get(domain, f"这张盘如何在{domain}领域形成可观察的稳定模式？")
            return _domain(domain, question)
        if schema is CaseTurnDraft:
            return CaseTurnDraft(
                interaction_type="explain",
                abu_message="你的回答支持主假设，但还不足以排除替代解释。",
                canvas_focus="hypotheses",
                interpretation="当前只更新这个案例。",
                hypothesis_updates={"h1": "strengthen", "h2": "weaken"},
                retained_assertion_ids=["portrait-1"],
                next_probe=_probe(),
                suggested_actions=["继续看事业"],
                evidence_refs=["F001"],
            )
        raise AssertionError(schema)


class InvalidZiweiProbeModel(FakeCognitiveModel):
    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is not DualLensCognitionDraft:
            return result
        return result.model_copy(
            update={
                "cross_lens_probe": result.cross_lens_probe.model_copy(
                    update={"question": "请判断命宫与官禄宫哪一个更能解释紫微格局？"}
                )
            }
        )


class SelectiveDomainRepairModel(FakeCognitiveModel):
    def __init__(self):
        self.domain_calls: list[str] = []

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is not DomainCausalReading:
            return result
        self.domain_calls.append(result.domain.value)
        if result.domain is LifeDomain.WEALTH and "只重写这一份" not in prompt:
            bad_assertion = result.assertions[0].model_copy(update={"claim": "财富积累必然伴随激烈冲突。"})
            return result.model_copy(update={"assertions": [bad_assertion, *result.assertions[1:]]})
        return result


class TrackingCognitiveModel(FakeCognitiveModel):
    def __init__(self):
        self.schemas: list[type] = []

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        self.schemas.append(schema)
        return super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )


class SoftReviewPatternModel(TrackingCognitiveModel):
    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is not PatternHypothesisDraft:
            return result
        extra = SalientPhenomenon(
            phenomenon_id="s2",
            observation="月令环境参与全局",
            why_it_matters="它需要在后续假设审阅中补充证据挂接",
            evidence_refs=["F002"],
        )
        return result.model_copy(update={"salient_phenomena": [*result.salient_phenomena, extra]})


class OneHardPatternRepairModel(TrackingCognitiveModel):
    def __init__(self):
        super().__init__()
        self.pattern_calls = 0

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        result = super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )
        if schema is not PatternHypothesisDraft:
            return result
        self.pattern_calls += 1
        if self.pattern_calls == 1:
            hypotheses = list(result.hypotheses)
            hypotheses[0] = hypotheses[0].model_copy(update={"name": "从杀兼食伤制杀"})
            return result.model_copy(update={"hypotheses": hypotheses})
        return result


def _hypotheses() -> list[CognitiveHypothesis]:
    return [
        CognitiveHypothesis(
            hypothesis_id="h1", name="输出制压候选", thesis="乙木通过丁火输出作用于金局压力。",
            rank=1, status="primary", supporting_evidence_refs=["F001"], failure_conditions=["丁火失效"], confidence="high",
        ),
        CognitiveHypothesis(
            hypothesis_id="h2", name="从杀候选", thesis="若输出与同类完全失效，才考虑顺从金势。",
            rank=2, status="alternative", supporting_evidence_refs=["F001"], failure_conditions=["可见输出仍参与做功"],
            rejection_reason="丁火与多乙透干使纯从解释不足。", confidence="low",
        ),
    ]


def _dual_lens() -> DualLensCognitionDraft:
    return DualLensCognitionDraft(
        ziwei_first_look="命宫与身宫把重点放在自主判断如何进入事业舞台。",
        identity_axis="内在倾向先形成判断框架，外在角色再通过具体任务兑现。",
        palace_observations=[
            ZiweiLensObservation(
                observation_id="z1", domain="identity",
                claim="身份重心不只在适应环境，也在建立自己的判断坐标。",
                why_it_matters="这决定用户面对规则时是先顺从还是先形成方法。",
                evidence_refs=["ziwei.palace.identity"],
                counter_conditions=["长期更依赖既有角色定义而非自主判断"],
            ),
            ZiweiLensObservation(
                observation_id="z2", domain="career",
                claim="事业舞台更需要把复杂要求整理成可执行结构。",
                why_it_matters="它与八字的输出制压主线形成互证。",
                evidence_refs=["ziwei.topic_palace_names"],
                counter_conditions=["工作长期不需要分析、协调或结构化输出"],
            ),
        ],
        agreements=["两套系统都指向用判断与输出承接外部复杂度。"],
        tensions=["八字强调长期做功，紫微更强调这种能力在哪个角色舞台被看见。"],
        integrated_thesis="长期擅长把压力转成方法，具体价值更容易在需要判断和组织的事业舞台中被看见。",
        current_stage_note="当前时序只说明相关舞台被激活，仍不能推成确定事件。",
        cross_lens_probe=DiscriminatingProbe(
            probe_id="probe-z1",
            question="面对一个要求很多但规则混乱的任务时，你更常先自己整理方法，还是先等角色与边界被明确？",
            purpose="区分长期输出倾向是否已经进入当前事业角色。",
            distinguishes_hypothesis_refs=["h1", "ziwei-career-stage"],
            options=["先整理方法再推进", "先确认角色边界再行动"],
            expected_updates={"先整理方法再推进": "增强双镜头一致性", "先确认角色边界再行动": "增强当前舞台约束解释"},
        ),
        uncertainties=["当前时序只作候选解释"],
        evidence_refs=["ziwei.palace.identity", "ziwei.topic_palace_names"],
    )


def test_hypothesis_comparison_rejects_duplicate_causal_explanations() -> None:
    world = compile_chart_world(
        reading_id="reading.hypothesis-comparison",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
    )
    context = MingliContextCompiler().compile(world=world, stage="pattern")
    first, second = _hypotheses()
    duplicate = second.model_copy(update={"name": first.name, "thesis": first.thesis})
    pattern = PatternHypothesisDraft(
        first_look="先看可见输出如何承接压力。",
        whole_chart_thesis="比较主动输出与顺从压力两种解释。",
        salient_phenomena=[
            SalientPhenomenon(
                phenomenon_id="s1",
                observation="盘面存在关键结构",
                why_it_matters="影响主做功选择",
                evidence_refs=[context.fact_refs[0]],
            )
        ],
        hypotheses=[
            first.model_copy(update={"supporting_evidence_refs": [context.fact_refs[0]]}),
            duplicate.model_copy(update={"supporting_evidence_refs": [context.fact_refs[0]]}),
        ],
        selected_hypothesis_id="h1",
        evidence_refs=[context.fact_refs[0]],
    )

    receipt = _review_hypothesis_space(pattern=pattern, context=context)

    assert receipt.passed is False
    assert "竞争假设因果签名重复" in receipt.issues


def _predictions() -> list[PriorPrediction]:
    return [
        PriorPrediction(
            prediction_id=f"p{index}", claim=claim, why_predicted="来自输出处理压力的主假设。",
            target_hypothesis_ref="h1", evidence_refs=["F001"], disconfirming_answer="长期完全依赖关系维护且不需要专业判断。",
        )
        for index, claim in enumerate(
            ["更常通过专业输出解决压力。", "重复低自主工作更容易消耗。", "复杂问题比单纯执行更能激活能力。"], start=1,
        )
    ]


def _work_path() -> WorkPathReasoning:
    return WorkPathReasoning(
        path_statement="乙木生丁火，丁火制金局压力。", source=["乙木"], transformations=["丁火输出"], target=["酉金压力"],
        body_function_relation="乙为体，丁火制金为用。", closure="conditional", success_conditions=["丁火可用"],
        failure_conditions=["水印压制输出"], evidence_refs=["F001"],
    )


def _assertion(assertion_id: str, domain: str, claim: str) -> CaseAssertion:
    return CaseAssertion(
        assertion_id=assertion_id,
        domain=LifeDomain(domain) if domain in {item.value for item in LifeDomain} else domain,
        claim=claim,
        rationale="来自整盘主做功。",
        epistemic_status="supported",
        conditions=["主路径成立"],
        falsifiers=["现实长期呈现相反模式"],
        evidence_refs=["F001"],
    )


def _domain(domain: str, question: str) -> DomainCausalReading:
    return DomainCausalReading(
        domain=LifeDomain(domain),
        core_question=question,
        causal_chain=["命局结构形成输出", "输出形成处理方式", "环境决定能否承接", "条件满足后形成领域价值"],
        stable_tendencies=["重视自主判断"],
        favorable_environments=["复杂问题", "明确成果"],
        adverse_environments=["低自主重复执行"],
        opportunity_conditions=["输出有承接"],
        risk_conditions=["输出过度而承载不足"],
        timing_note="时序目前只作条件候选。",
        prior_directions=["技术", "产品", "研究"],
        assertions=[
            _assertion(f"{domain}-1", domain, question),
            _assertion(f"{domain}-2", domain, "当环境缺少承接时，这条路径会转为消耗。"),
        ],
        unknowns=["现实环境是否承接"],
        next_probe=DiscriminatingProbe(
            probe_id=f"probe-{domain}",
            question="现实中更常出现哪一种情况？",
            purpose="区分领域路径被承接还是转为消耗。",
            distinguishes_hypothesis_refs=[f"{domain}-1", f"{domain}-2"],
            options=["能力被环境承接", "长期感到消耗", "两者都不符合"],
            expected_updates={"能力被环境承接": "strengthen first", "长期感到消耗": "strengthen second"},
        ),
    )


def _probe() -> DiscriminatingProbe:
    return DiscriminatingProbe(
        probe_id="probe-1",
        question="面对强规则压力时，你更常主动拆解问题，还是先依附现成体系？",
        purpose="区分输出制压与顺从压力两种假设。",
        distinguishes_hypothesis_refs=["h1", "h2"],
        options=["主动拆解并输出方案", "先依附体系", "两者都不是"],
        expected_updates={"主动拆解并输出方案": "h1 strengthen", "先依附体系": "h2 strengthen"},
    )


def _birth_payload():
    return {
        "birth_input_id": "test-agent-birth",
        "name": "测试命盘",
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1987-05-12",
        "birth_time": "18:00",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
        "year_pillar": "丁巳",
        "month_pillar": "乙巳",
        "day_pillar": "乙丑",
        "hour_pillar": "乙酉",
        "input_quality": "explicit_pillars",
    }


def test_agent_vertical_slice_uses_llm_cognition_and_persists_case():
    store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=store,
        )
    )
    response = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reading"]["whole_chart_thesis"].startswith("主线是输出能力")
    assert "hypotheses" not in body["reading"]
    assert "work_path" not in body["reading"]
    assert body["reading"]["public_work_path"]["path_statement"]
    assert "review" not in body["reading"]
    assert body["reading"]["projection_contract"]["name"] == "GuestReadingProjection"
    assert body["reading"]["experience_mode"] == "guest"
    assert body["reading"]["probe_plan"]["role_mode"] == "guest"
    assert body["reading"]["workspace"]["chart_facts_locked"] is True
    assert body["reading"]["workspace"]["global_update_allowed"] is False
    assert "career" not in body["reading"]
    assert "wealth" not in body["reading"]
    case_id = body["case_id"]
    career = client.post(f"/api/v50/agent/cases/{case_id}/domains/career", json={})
    wealth = client.post(f"/api/v50/agent/cases/{case_id}/domains/wealth", json={})
    assert career.status_code == 200, career.text
    assert wealth.status_code == 200, wealth.text
    assert career.json()["formal_insight"]["status"] == "committed"
    assert career.json()["formal_insight"]["validation"]["passed"] is True
    assert career.json()["reading"]["domain_explorations"]["career"]["reading"]["domain"] == "career"
    assert wealth.json()["reading"]["domain_explorations"]["wealth"]["reading"]["domain"] == "wealth"
    turn = client.post(f"/api/v50/agent/cases/{case_id}/turn", json={"message": "我确实更常主动拆问题。"})
    assert turn.status_code == 200, turn.text
    assert turn.json()["turn"]["hypothesis_updates"]["h1"] == "strengthen"
    assert store.get(case_id=case_id)["record"]["revisions"]

    probe = body["reading"]["probe_plan"]
    before_world = store.get(case_id=case_id)["world"]
    response = client.post(
        f"/api/v50/agent/cases/{case_id}/probe-respond",
        json={
            "plan_id": probe["plan_id"],
            "option_id": probe["options"][0]["option_id"],
            "active_mode": "guest",
            "scenario": "recognition",
            "domain": "whole_chart",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["receipt"]["chart_facts_modified"] is False
    assert response.json()["receipt"]["global_policy_modified"] is False
    stored = store.get(case_id=case_id)
    assert stored["world"] == before_world
    assert CaseCognitiveWorkspace.model_validate(stored["workspace"]).revision_count == 1
    assert sorted(stored["life_case"]["domain_insights"]) == ["career", "wealth"]
    assert stored["life_case"]["domain_insights"]["career"][0]["status"] == "committed"
    assert stored["life_case"]["reality_evidence"][0]["case_local_only"] is True
    assert stored["life_case"]["reality_evidence"][0]["chart_facts_modified"] is False
    assert stored["life_case"]["reality_evidence"][0]["global_theory_modified"] is False


def test_on_demand_life_domain_reasoning_uses_its_own_probe_and_case_local_assertions():
    store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=store,
        )
    )
    started = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()})
    case_id = started.json()["case_id"]
    response = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/career",
        json={"active_mode": "guest", "user_question": "我的职业价值如何形成？"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["cache_hit"] is False
    reading = response.json()["reading"]
    exploration = reading["domain_explorations"]["career"]
    assert exploration["reading"]["domain"] == "career"
    assert len(exploration["reading"]["causal_chain"]) == 4
    plan = reading["probe_plan"]
    assert plan["domain"] == "career"
    assert plan["target_assertion_ids"] == ["career-1", "career-2"]
    assert plan["target_hypothesis_ids"] == []
    assert plan["options"][0]["assertion_updates"]
    answered = client.post(
        f"/api/v50/agent/cases/{case_id}/probe-respond",
        json={
            "plan_id": plan["plan_id"],
            "option_id": plan["options"][0]["option_id"],
            "active_mode": "guest",
            "scenario": "domain",
            "domain": "career",
        },
    )
    assert answered.status_code == 200, answered.text
    receipt = answered.json()["receipt"]
    assert receipt["updated_hypothesis_ids"] == []
    assert receipt["updated_assertion_ids"]
    assert answered.json()["reading"]["workspace"]["chart_facts_locked"] is True
    changed_question = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/career",
        json={"active_mode": "guest", "user_question": ""},
    )
    assert changed_question.status_code == 200
    assert changed_question.json()["cache_hit"] is False


def test_high_risk_domain_language_has_deterministic_server_side_redlines():
    assert "患有" in _forbidden_domain_tokens(LifeDomain.HEALTH_VITALITY)
    assert "一定离婚" in _forbidden_domain_tokens(LifeDomain.RELATIONSHIP)
    assert "生男" in _forbidden_domain_tokens(LifeDomain.CHILDREN_LEGACY)
    assert "必然发生" in _forbidden_domain_tokens(LifeDomain.LIFE_TIMING)


def test_semantic_review_does_not_misread_a_negated_certainty_as_a_prediction():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    world = ChartWorldInstance.model_validate(store.get(case_id=case_id)["world"])
    errors = _semantic_text_errors(text="这个结构并非必然导致某个事件，也不代表一定会发生。", world=world)
    assert not any("过度确定断言" in item for item in errors)
    assert any("内部工程信息泄漏:V40" in item for item in _semantic_text_errors(text="资料来自 V40 导入", world=world))
    assert any("结构性崩塌" in item for item in _semantic_text_errors(text="这一阶段会结构性崩塌", world=world))
    assert _public_birth_location("未记录（V40 导入）") == "未记录"
    sanitized = sanitize_public_mingli_payload({"unknown": "出生时辰未记录（仅凭 V40 导入），会彻底改变判断。"})
    assert sanitized["unknown"] == "出生时辰资料未完整记录，需要重新评估判断。"


def test_domain_context_keeps_only_the_ziwei_palaces_relevant_to_the_current_question():
    payload = {
        "facts": [{"id": "F1"}],
        "ziwei_profile": {
            "status": "ready",
            "palaces": {"命宫": {"star": "武曲"}, "夫妻宫": {"star": "七杀"}, "官禄宫": {"star": "紫微"}},
        },
    }
    focused = _domain_context_payload(payload, relevant_palaces=["夫妻宫", "命宫"])
    assert list(focused["ziwei_profile"]["palaces"]) == ["命宫", "夫妻宫"]
    assert payload["ziwei_profile"]["palaces"].keys() == {"命宫", "夫妻宫", "官禄宫"}


def test_progressive_cognition_emits_real_stage_artifacts_and_can_resume_after_sequence():
    case_store = MemoryAgentCaseStore()
    job_store = MemoryAgentJobStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=case_store,
            agent_job_store=job_store,
        )
    )
    started = client.post(
        "/api/v50/agent/cases",
        json={"birth_input": _birth_payload(), "progressive": True},
    )
    assert started.status_code == 200, started.text
    body = started.json()
    assert body["status"] == "cognitive_job_started"
    assert "reading" not in body

    job = None
    for _ in range(50):
        response = client.get(f"/api/v50/agent/jobs/{body['job_id']}")
        assert response.status_code == 200, response.text
        job = response.json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert job is not None
    assert job["status"] == "completed"
    event_types = [item["event_type"] for item in job["events"]]
    assert event_types == [
        "chart_ready",
        "baseline_draft_ready",
        "formal_insight_draft_ready",
        "baseline_validated",
        "baseline_committed",
    ]
    assert job["events"][1]["payload"]["first_look"].startswith("这张盘先看丁火")
    assert job["events"][1]["epistemic_status"] == "provisional"
    assert job["events"][2]["payload"]["persisted"] is False
    assert job["events"][3]["payload"]["validation"]["passed"] is True
    assert job["events"][3]["payload"]["persisted"] is False
    assert job["events"][4]["payload"]["blocking_core_llm_calls"] == 1
    assert job["events"][-1]["epistemic_status"] == "completed"
    resumed = client.get(f"/api/v50/agent/jobs/{body['job_id']}?after=2").json()
    assert [item["sequence"] for item in resumed["events"]] == [3, 4, 5]
    stored = case_store.get(case_id=body["case_id"])
    assert stored["record"]["cognition"]["whole_chart_thesis"].startswith("主线是输出能力")
    assert stored["life_case"]["baseline_insight"]["status"] == "committed"
    assert stored["first_run"] == {
        "protocol": "single_call_baseline_v1",
        "blocking_core_llm_calls": 1,
        "unselected_domains_precomputed": False,
    }


def test_first_reading_never_runs_domain_reasoning_until_the_user_selects_a_domain():
    model = TrackingCognitiveModel()
    agent = MingliAgent(model)
    world = compile_chart_world(
        reading_id="reading.core-first",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )

    record = agent.first_reading(case_id="case.core-first", world=world)

    assert DomainCausalReading not in model.schemas
    assert record.cognition.career is None
    assert record.cognition.wealth is None
    assert record.domain_explorations == {}

    agent.explore_domain(world=world, record=record, domain=LifeDomain.CAREER)
    assert model.schemas.count(DomainCausalReading) == 1


def test_production_baseline_uses_one_model_call_and_commits_a_traceable_life_case():
    model = TrackingCognitiveModel()
    agent = MingliAgent(model)
    world = compile_chart_world(
        reading_id="reading.single-call-baseline",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )

    record = agent.first_baseline_reading(case_id="case.single-call-baseline", world=world)
    draft = build_baseline_insight(record=record, world=world)
    life_case, validation = commit_baseline_life_case(insight=draft, world=world, profile_id=None)

    assert model.schemas == [WholeChartCognitionDraft]
    assert [item["stage"] for item in record.stage_receipts] == ["baseline_cognition"]
    assert record.domain_explorations == {}
    assert draft.status == "draft"
    assert validation.passed is True
    assert validation.fact_traceability_rate == 1.0
    assert life_case.baseline_insight.status == "committed"
    assert life_case.domain_insights == {}

    invalid = draft.model_copy(update={
        "basis": draft.basis.model_copy(update={"chart_fact_refs": ["fact-that-does-not-exist"]})
    })
    rejected = validate_formal_insight(insight=invalid, world=world)
    assert rejected.passed is False
    assert rejected.errors == ["unknown_evidence_refs:fact-that-does-not-exist"]


def test_editing_birth_material_supersedes_old_life_case_without_deleting_history():
    case_store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=case_store,
    ))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "版本测试",
            "email": "chart-version@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    profile_response = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": _birth_payload()},
    )
    assert profile_response.status_code == 200, profile_response.text
    profile_id = profile_response.json()["profile"]["profile_id"]
    started = client.post(
        "/api/v50/agent/cases",
        json={"profile_id": profile_id, "active_mode": "member"},
    )
    assert started.status_code == 200, started.text
    case_id = started.json()["case_id"]

    changed_birth = {
        **_birth_payload(),
        "birth_date": "1987-05-13",
        "year_pillar": "",
        "month_pillar": "",
        "day_pillar": "",
        "hour_pillar": "",
    }
    updated = client.put(
        f"/api/v50/product/profiles/{profile_id}",
        json={"birth_input": changed_birth},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["superseded_life_case_count"] == 1
    stored = case_store.get(case_id=case_id)
    assert stored["life_case"]["status"] == "superseded"
    assert stored["life_case"]["chart_version"]["active"] is False
    assert stored["life_case"]["revisions"][-1]["kind"] == "chart_version_changed"
    assert stored["life_case"]["baseline_insight"]["status"] == "committed"


def test_temporal_prior_and_case_revision_are_committed_without_overwriting_each_other():
    agent = MingliAgent(FakeCognitiveModel())
    world = compile_chart_world(
        reading_id="reading.prior-review",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    record = agent.first_baseline_reading(case_id="case.prior-review", world=world)
    baseline = build_baseline_insight(record=record, world=world)
    life_case, _ = commit_baseline_life_case(insight=baseline, world=world, profile_id=None)
    prior = baseline.model_copy(update={
        "insight_id": "insight-temporal-prior-test",
        "type": "temporal_prior",
        "claim": "本观察窗口先关注节奏和承载变化。",
        "scope": {"start_at": "2026-07-01", "end_at": "2026-07-31"},
        "status": "draft",
    })
    life_case, prior_receipt = commit_temporal_prior(life_case=life_case, insight=prior, world=world)
    original_prior = life_case.temporal_priors[0].model_dump(mode="json")
    revision = baseline.model_copy(update={
        "insight_id": "insight-case-revision-test",
        "type": "case_revision",
        "claim": "月底现实反馈使当前案例理解需要局部修正。",
        "scope": {"reviewed_window": "2026-07"},
        "basis": baseline.basis.model_copy(update={"reality_context_refs": ["evidence-probe-test"]}),
        "status": "draft",
    })
    life_case, revision_receipt = commit_case_revision(life_case=life_case, insight=revision, world=world)

    assert prior_receipt.passed is True
    assert revision_receipt.passed is True
    assert life_case.temporal_priors[0].model_dump(mode="json") == original_prior
    assert life_case.case_revisions[0].status == "committed"
    assert [item.kind for item in life_case.revisions[-2:]] == [
        "temporal_prior_committed",
        "case_revision_committed",
    ]


def test_soft_pattern_review_never_regenerates_the_full_pattern_or_blocks_the_preview():
    model = SoftReviewPatternModel()
    agent = MingliAgent(model)
    world = compile_chart_world(
        reading_id="reading.soft-pattern-review",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    events: list[str] = []

    record = agent.first_reading(
        case_id="case.soft-pattern-review",
        world=world,
        on_stage=lambda event_type, payload: events.append(event_type),
    )

    assert model.schemas.count(PatternHypothesisDraft) == 1
    assert "pattern_preview_ready" in events
    assert record.hypothesis_comparison is not None
    assert record.hypothesis_comparison.passed is False
    assert record.hypothesis_comparison.uncovered_salient_refs == ["F002"]
    assert not any(item["stage"] == "pattern_hypothesis_hard_repair" for item in record.stage_receipts)


def test_pattern_review_observation_does_not_replace_the_models_selected_hypothesis():
    model = OneHardPatternRepairModel()
    agent = MingliAgent(model)
    world = compile_chart_world(
        reading_id="reading.hard-pattern-repair",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    events: list[str] = []

    record = agent.first_reading(
        case_id="case.hard-pattern-repair",
        world=world,
        on_stage=lambda event_type, payload: events.append(event_type),
    )

    assert model.pattern_calls == 1
    assert events[0] == "pattern_preview_ready"
    assert record.cognition.selected_hypothesis_id == "h1"
    assert record.review.passed is True
    assert all(item.severity == "warning" for item in record.review.issues)
    assert not any("repair" in item["stage"] for item in record.stage_receipts)


def test_prediction_bookkeeping_and_tone_are_repaired_locally_without_rethinking_the_chart():
    world = compile_chart_world(
        reading_id="reading.local-prediction-repair",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    model = FakeCognitiveModel()
    pattern = model.generate(prompt="", schema=PatternHypothesisDraft)
    work = model.generate(prompt="", schema=WorkPathPortraitDraft)
    predictions = model.generate(prompt="", schema=PredictionProbeDraft)
    messy = predictions.model_copy(update={
        "prior_predictions": [
            *predictions.prior_predictions,
            predictions.prior_predictions[0].model_copy(
                update={"prediction_id": "p4", "claim": "压力会彻底改变你的工作方式。"}
            ),
        ]
    })

    repaired = _normalize_prediction_probe(messy, pattern=pattern, work=work, world=world)

    assert 1 <= len(repaired.prior_predictions) <= 3
    assert "彻底改变" not in str(repaired.model_dump(mode="json"))
    assert len(repaired.next_probe.distinguishes_hypothesis_refs) == 2
    assert _prediction_stage_errors(predictions=repaired, world=world) == []


def test_cognitive_record_version_gate_rejects_pre_reliability_records():
    core_receipts = [
        {"stage": stage, "status": "completed"}
        for stage in ("pattern_hypothesis", "work_path_portrait", "prediction_probe")
    ]
    assert _is_current_cognitive_record({
        "record": {
            "version": "deepbazi.mingli_cognitive_record.v3",
            "stage_receipts": core_receipts,
        }
    }) is False
    assert _is_current_cognitive_record({
        "record": {
            "version": "deepbazi.mingli_cognitive_record.v2",
            "stage_receipts": core_receipts,
        }
    }) is False
    assert _is_current_cognitive_record({
        "record": {
            "version": "deepbazi.mingli_cognitive_record.v2",
            "stage_receipts": [
                *core_receipts,
                {"stage": "career_reasoning", "status": "completed"},
                {"stage": "wealth_reasoning", "status": "completed"},
            ],
        }
    }) is False


def test_product_startup_marks_jobs_from_a_stopped_worker_as_interrupted():
    job_store = MemoryAgentJobStore()
    job_store.create(
        job_id="cognitive-job-interrupted",
        case_id="mingli-case-interrupted",
        user_id=None,
        payload={"version": "deepbazi.progressive_cognitive_job.v1"},
    )
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=MemoryAgentCaseStore(),
            agent_job_store=job_store,
        )
    )
    job = client.get("/api/v50/agent/jobs/cognitive-job-interrupted").json()
    assert job["status"] == "failed"
    assert job["events"][-1]["event_type"] == "reading_failed"
    assert job["events"][-1]["payload"]["failure_code"] == "cognitive_job_interrupted"
    assert job["events"][-1]["payload"]["failure_stage"] == "runtime_recovery"


def test_progressive_cognition_adds_ziwei_lens_for_calendar_aligned_birth():
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=MemoryAgentCaseStore(),
            agent_job_store=MemoryAgentJobStore(),
        )
    )
    birth = {
        "birth_input_id": "birth.dual.live",
        "name": "双镜头命盘",
        "gender": "female",
        "calendar_type": "solar",
        "birth_date": "2000-08-16",
        "birth_time": "03:30",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
    }
    started = client.post("/api/v50/agent/cases", json={"birth_input": birth, "progressive": True})
    assert started.status_code == 200, started.text
    job = None
    for _ in range(80):
        job = client.get(f"/api/v50/agent/jobs/{started.json()['job_id']}").json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)

    assert job is not None and job["status"] == "completed", job
    event_types = [item["event_type"] for item in job["events"]]
    assert event_types.count("baseline_draft_ready") == 1
    assert "ziwei_lens_ready" not in event_types
    completed = job["events"][-1]["payload"]["reading"]
    assert completed["lenses_available"] == {"bazi": True, "ziwei": True, "integrated": True}
    assert completed["dual_lens"]["integrated_thesis"].startswith("长期擅长")
    assert "calculator" not in completed["ziwei_profile"]


def test_invalid_ziwei_review_observation_does_not_discard_the_generated_lens():
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(InvalidZiweiProbeModel()),
            agent_case_store=MemoryAgentCaseStore(),
            agent_job_store=MemoryAgentJobStore(),
        )
    )
    birth = {
        "birth_input_id": "birth.dual.review-failure",
        "name": "双镜头审查失败",
        "gender": "female",
        "calendar_type": "solar",
        "birth_date": "2000-08-16",
        "birth_time": "03:30",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
    }
    started = client.post("/api/v50/agent/cases", json={"birth_input": birth, "progressive": True})
    job = None
    for _ in range(80):
        job = client.get(f"/api/v50/agent/jobs/{started.json()['job_id']}").json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)

    assert job is not None and job["status"] == "completed", job
    event_types = [item["event_type"] for item in job["events"]]
    assert event_types.count("baseline_draft_ready") == 1
    assert event_types[-1] == "baseline_committed"


def test_domain_fact_conflict_is_blocked_without_a_second_model_call():
    model = SelectiveDomainRepairModel()
    agent = MingliAgent(model)
    world = compile_chart_world(
        reading_id="reading.selective-domain-repair",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    record = agent.first_reading(case_id="case.selective-domain-repair", world=world)
    assert record.cognition.career is None
    assert record.cognition.wealth is None
    career = agent.explore_domain(world=world, record=record, domain=LifeDomain.CAREER)
    wealth = agent.explore_domain(world=world, record=record, domain=LifeDomain.WEALTH)
    assert career.reading.domain is LifeDomain.CAREER
    assert wealth.reading.domain is LifeDomain.WEALTH
    assert model.domain_calls.count("career") == 1
    assert model.domain_calls.count("wealth") == 1
    assert career.review.repaired is False
    assert wealth.review.repaired is False
    assert wealth.review.passed is False
    assert wealth.review.disposition == "blocked"
    assert wealth.review.commit_eligible is False
    assert "mingli_fact_conflict" in wealth.review.hard_failure_codes


def test_domain_normalization_splits_four_newline_steps_without_rewriting_content():
    reading = _domain("career", "事业如何形成？").model_copy(
        update={"causal_chain": ["结构事实\n能力转化\n环境互动\n条件结果"]}
    )
    normalized = _normalize_domain_reading(reading, domain=LifeDomain.CAREER)
    assert normalized.causal_chain == ["结构事实", "能力转化", "环境互动", "条件结果"]


def test_abu_resolves_whitelisted_capabilities_without_executing_judgment():
    client = TestClient(create_product_app(product_store=MemoryProductStore()))
    birth = client.post(
        "/api/v50/agent/abu/resolve",
        json={
            "message": "我是1990年10月19日下午三点出生在广州",
            "has_case": False,
            "active_mode": "guest",
            "active_domain": "whole_chart",
        },
    )
    assert birth.status_code == 200, birth.text
    assert birth.json()["plan"]["capability_id"] == "profile.create"
    assert birth.json()["plan"]["action_type"] == "CREATE_PROFILE"
    assert birth.json()["plan"]["confirmation_required"] is True

    career = client.post(
        "/api/v50/agent/abu/resolve",
        json={"message": "我想看事业", "has_case": False, "active_mode": "guest", "active_domain": "whole_chart"},
    ).json()["plan"]
    assert career["capability_id"] == "reading.select_domain"
    assert career["action_type"] == "OPEN_DOMAIN"
    assert career["missing_requirements"] == ["confirmed_chart"]
    assert career["executor"] == "client_ui"

def test_probe_planner_projects_one_epistemic_target_into_four_distinct_jobs():
    store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=store,
        )
    )
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    record = MingliCognitiveRecord.model_validate(store.get(case_id=case_id)["record"])
    planner = ProbePlanner()
    plans = {
        mode: planner.plan(record=record, role_mode=mode)
        for mode in ("guest", "member", "practitioner", "research")
    }
    assert len({plan.question for plan in plans.values()}) == 4
    assert plans["guest"].professional_note == ""
    assert "专业鉴别" in plans["practitioner"].purpose
    assert "反证" in plans["research"].purpose
    assert plans["guest"].information_value.role_fit == "high"
    assert plans["member"].information_value.observability == "high"
    assert plans["practitioner"].information_value.source_quality == "medium"
    assert plans["research"].information_value.falsifiability in {"medium", "high"}
    assert all(plan.forbidden_updates == ["chart_facts", "global_theory", "runtime_rules", "model_weights"] for plan in plans.values())


def test_public_probe_options_hide_internal_hypothesis_annotations():
    label = "依靠技能与方法解决（支持食神制杀）"
    assert _project_option_label(label, role_mode="guest") == "依靠技能与方法解决"
    assert _project_option_label(label, role_mode="member") == "依靠技能与方法解决"
    assert _project_option_label(label, role_mode="practitioner") == label
    assert _project_option_label(label, role_mode="research") == label


def test_guest_domain_probe_keeps_the_specific_real_world_question():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    record = MingliCognitiveRecord.model_validate(store.get(case_id=case_id)["record"])
    source = _probe().model_copy(update={
        "probe_id": "guest-domain-specific",
        "question": "命主过去是否经常遇到付出很多、成果却被竞争分薄的情况？",
    })
    plan = ProbePlanner().plan(
        record=record,
        role_mode="guest",
        scenario="domain",
        domain=LifeDomain.WEALTH,
        source_override=source,
    )
    assert plan.question == "你过去是否经常遇到付出很多、成果却被竞争分薄的情况？"


def test_probe_response_creates_case_local_hidden_attribute_revision_and_consumes_probe():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    started = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()
    case_id = started["case_id"]
    plan = started["reading"]["probe_plan"]
    before_world = store.get(case_id=case_id)["world"]

    response = client.post(
        f"/api/v50/agent/cases/{case_id}/probe-respond",
        json={
            "plan_id": plan["plan_id"],
            "option_id": plan["options"][0]["option_id"],
            "active_mode": "guest",
            "scenario": "recognition",
            "domain": "whole_chart",
            "recurrence_count": 2,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reading"]["probe_plan"] is None
    assert body["reading"]["latest_revision"]["chart_facts_modified"] is False
    assert body["revision"]["summary"]
    assert body["receipt"]["updated_hidden_attribute_ids"] == ["pressure_response_pattern"]
    stored = store.get(case_id=case_id)
    assert stored["world"] == before_world
    workspace = CaseCognitiveWorkspace.model_validate(stored["workspace"])
    assert workspace.hidden_attribute_beliefs[0].lifecycle == "candidate"
    assert workspace.probe_history[0].recurrence_count == 2
    assert stored["record"]["revisions"][-1]["kind"] == "probe_revision"
    assert stored["life_case"]["reality_evidence"][0]["evidence_id"] == body["receipt"]["evidence_id"]
    assert stored["life_case"]["revisions"][-1]["kind"] == "reality_evidence_added"


def test_timeline_probe_records_year_and_repeated_independent_evidence_can_stabilize_belief():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    record = MingliCognitiveRecord.model_validate(store.get(case_id=case_id)["record"])
    workspace = build_case_workspace(record)
    planner = ProbePlanner()
    years = [2021, 2024, 2025]
    for index, year in enumerate(years, start=1):
        source = _probe().model_copy(update={"probe_id": f"timeline-{index}", "question": f"{year}年前后是否出现结构变化？"})
        plan = planner.plan(
            record=record,
            role_mode="member",
            scenario="timing",
            domain=LifeDomain.LIFE_TIMING,
            source_override=source,
        )
        assert plan.evidence_kind == "historical_timeline"
        assert plan.response_shape == "timeline_choice"
        assert year in plan.time_anchors
        assert plan.information_value.source_quality == "high"
        workspace, _ = apply_probe_response(
            workspace=workspace,
            plan=plan,
            option_id=plan.options[0].option_id,
            year_value=year,
        )
    belief = next(item for item in workspace.hidden_attribute_beliefs if item.attribute_id == "timing_response_pattern")
    assert belief.lifecycle == "stable"
    assert belief.confidence == "high"
    assert [item.year_value for item in workspace.probe_history] == years


def test_timeline_no_event_is_strong_counter_evidence_not_a_hidden_attribute():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    record = MingliCognitiveRecord.model_validate(store.get(case_id=case_id)["record"])
    source = _probe().model_copy(update={
        "probe_id": "timeline-negative",
        "question": "2022年前后是否出现结构变化？",
        "options": ["工作责任升级", "环境发生变化", "没有明显变化"],
    })
    plan = ProbePlanner().plan(
        record=record,
        role_mode="member",
        scenario="timing",
        domain=LifeDomain.LIFE_TIMING,
        source_override=source,
    )
    negative = plan.options[2]
    assert negative.evidence_strength == "strong"
    assert negative.hidden_attribute_observations == {}
    assert set(negative.hypothesis_updates.values()) == {"weaken"}


def test_abu_intake_and_public_ui_are_conversation_first():
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=MemoryAgentCaseStore(),
        )
    )
    intake = client.post("/api/v50/agent/intake", json={"message": "1987年5月12日下午六点，男，上海"})
    assert intake.status_code == 200
    assert intake.json()["draft"]["ready_for_confirmation"] is True
    html = client.get("/app").text
    assert "先看见命局" in html
    assert "说出出生信息" in html
    assert "Decision Confidence" not in html
    assert "Product Mode" not in html
    assert "Core Runtime" not in html


def test_relation_guard_distinguishes_denial_from_false_assertion():
    assert _contains_asserted_relation(text="这里是火克金，不是火生金。", relation="火生金") is False
    assert _contains_asserted_relation(text="模型错误地写成火生金。", relation="火生金") is True
    assert _contains_asserted_relation(text="湿土晦火生金。", relation="火生金") is False
    assert _contains_asserted_relation(text="需要补火生木。", relation="火生木") is False
    assert _contains_asserted_relation(text="乙木受金克土耗。", relation="金克土") is False


def test_relation_guard_does_not_join_parallel_predicates_into_false_edges():
    world = compile_chart_world(
        reading_id="reading.parallel-predicate",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        include_research_fixture_prior=False,
    )
    assert _semantic_text_errors(text="湿土晦火生金。", world=world) == []
    assert _semantic_text_errors(text="需要补火生木。", world=world) == []
    assert _semantic_text_errors(text="乙木受金克土耗。", world=world) == []
    assert "错误五行关系:火生金" in _semantic_text_errors(text="模型主张火生金。", world=world)


def test_traceability_accepts_bounded_existing_reference_ranges():
    allowed = {f"F{index:03d}" for index in range(1, 38)}
    assert _citation_allowed(ref="F001-F037", allowed=allowed) is True
    assert _citation_allowed(ref="F001-F099", allowed=allowed) is False


def test_role_guard_catches_role_drift_without_rejecting_explicit_denial():
    assert _contains_role_conflict(text="金的肃杀之势或财星", symbol="金", wrong="财星") is True
    assert _contains_role_conflict(text="金是官杀，并非财星", symbol="金", wrong="财星") is False


def test_visible_ten_god_guard_does_not_count_day_master_as_an_extra_peer():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload()}).json()["case_id"]
    world = ChartWorldInstance.model_validate(store.get(case_id=case_id)["world"])
    errors = _semantic_text_errors(text="天干透出三个比肩共同生火。", world=world)
    assert "比肩数量冲突:账本可见比肩为2不是3" in errors
    compressed = _semantic_text_errors(text="这条路径形成食伤生财化杀。", world=world)
    assert "因果链压缩:食伤生财与财生杀必须逐段表达" in compressed


def test_deterministic_fact_guard_catches_root_contradiction_and_unsupported_branch_relation():
    world = ChartWorldInstance(
        world_id="world.fact.guard",
        reading_id="reading.fact.guard",
        pillars=["壬辰", "戊申", "丙午", "丁丑"],
        birth_profile={},
        facts=[
            WorldFact(
                fact_id="F007",
                kind="fact",
                category="root_strength",
                statement="root_strength",
                payload={"day_stem": "丙", "has_root": True, "root_sources": [{"branch": "午", "hidden_stems": "丁"}]},
            ),
            WorldFact(
                fact_id="F008",
                kind="fact",
                category="branch_relations",
                statement="branch_relations",
                payload={"relations": []},
            ),
        ],
        knowledge=[],
        allowed_evidence_refs=["F007", "F008"],
    )

    errors = _semantic_text_errors(
        text="日主丙火地支无根，但日支午火又是强根，并且午火与申金暗合。",
        world=world,
    )

    assert "根气表述自相矛盾:同一段同时断言有根与无根" in errors
    assert "根气事实冲突:账本存在同类藏干根，不能断言地支无根" in errors
    assert "地支关系未建模:当前世界账本尚未覆盖午申暗合" in errors

    other_stem_errors = _semantic_text_errors(text="辛金正官虚浮无根，但日主丙火通根于午。", world=world)
    assert not any("根气事实冲突" in item or "根气表述自相矛盾" in item for item in other_stem_errors)
    repeated_stem_errors = _semantic_text_errors(text="月干丙下无根，但日主丙火通根于午。", world=world)
    assert not any("根气事实冲突" in item or "根气表述自相矛盾" in item for item in repeated_stem_errors)
    conditional_errors = _semantic_text_errors(
        text="日主丙火通根于午；若原局火势尽失且日主完全无根，才考虑从格。",
        world=world,
    )
    assert not any("根气事实冲突" in item or "根气表述自相矛盾" in item for item in conditional_errors)
    timing_relation_errors = _semantic_text_errors(
        text="若岁运见酉金冲卯，根基会受到扰动；原局本身并没有酉卯冲。",
        world=world,
    )
    assert not any("盘中不存在酉卯冲" in item for item in timing_relation_errors)
    split_timing_relation_errors = _semantic_text_errors(
        text=(
            "命主在逢金木相冲的流年（如酉年）时，根基容易受到扰动。\n"
            "卯木是当前命盘的根，酉金冲卯会改变这一条件。"
        ),
        world=world,
    )
    assert not any("盘中不存在酉卯冲" in item for item in split_timing_relation_errors)
    negated_errors = _semantic_text_errors(text="午中有丁火，显示日主并非无根。", world=world)
    assert not any("根气事实冲突" in item or "根气表述自相矛盾" in item for item in negated_errors)
    other_stem_branch_errors = _semantic_text_errors(text="辛金地支无根，但日主丙火通根于午。", world=world)
    assert not any("根气事实冲突" in item or "根气表述自相矛盾" in item for item in other_stem_branch_errors)

    descriptive_root_errors = _semantic_text_errors(
        text="日主丙火在午、巳有根，但寅未双根的另一命例会被冲克。",
        world=world,
    )
    assert not any("寅未冲" in item for item in descriptive_root_errors)


def test_locked_fact_wording_repair_preserves_hypothesis_authority() -> None:
    world = ChartWorldInstance(
        world_id="world.fact.repair",
        reading_id="reading.fact.repair",
        pillars=["庚申", "戊子", "甲辰", "辛巳"],
        birth_profile={},
        facts=[
            WorldFact(
                fact_id="F007",
                kind="fact",
                category="root_strength",
                statement="root_strength",
                payload={"day_stem": "甲", "day_element": "木", "has_root": True, "root_sources": [{"branch": "辰"}]},
            ),
            WorldFact(
                fact_id="F008",
                kind="fact",
                category="branch_relations",
                statement="branch_relations",
                payload={"relations": [{"type": "harmony", "branch_a": "巳", "branch_b": "申"}]},
            ),
        ],
        knowledge=[],
        allowed_evidence_refs=["F007", "F008"],
    )
    payload = {
        "first_look": "日主甲木无根，先比较两种解释。",
        "whole_chart_thesis": "根气受损后的承载能力是关键。",
        "selected_hypothesis_id": "h1",
        "hypotheses": [
            {"hypothesis_id": "h1", "name": "假从格", "thesis": "日主无根，故按假从格继续比较。"},
            {"hypothesis_id": "h2", "name": "身弱格", "thesis": "若日主完全无根，才排除本假设。"},
        ],
        "work_path": {"path_statement": "基于日主无根形成路径。"},
        "portrait": [{"claim": "依势而行。", "rationale": "基于日主甲木无根。"}],
        "salient_phenomena": [
            {
                "observation": "时柱巳火冲年申金；月令子水遥冲巳火；存在‘巳亥冲’的变体逻辑（此处为巳火受子水克制及与申金的复杂作用）",
                "why_it_matters": "需要区分实际关系。",
            }
        ],
    }

    repaired, receipts = repair_locked_fact_assertions(payload=payload, world=world)

    assert repaired["selected_hypothesis_id"] == "h1"
    assert "根气受损、支撑有限" in repaired["hypotheses"][0]["thesis"]
    assert repaired["hypotheses"][1]["thesis"] == payload["hypotheses"][1]["thesis"]
    assert "巳亥冲" not in repaired["salient_phenomena"][0]["observation"]
    assert "巳火与申金相合" in repaired["salient_phenomena"][0]["observation"]
    assert "子水克制巳火" in repaired["salient_phenomena"][0]["observation"]
    assert receipts


def test_element_role_guard_catches_natural_language_role_and_control_drift():
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(
        product_store=MemoryProductStore(),
        mingli_agent=MingliAgent(FakeCognitiveModel()),
        agent_case_store=store,
    ))
    birth = {
        "birth_input_id": "birth.role.guard.fire",
        "name": "丙火角色校验",
        "gender": "female",
        "calendar_type": "solar",
        "birth_date": "2000-08-16",
        "birth_time": "03:30",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
    }
    case_id = client.post("/api/v50/agent/cases", json={"birth_input": birth}).json()["case_id"]
    world = ChartWorldInstance.model_validate(store.get(case_id=case_id)["world"])
    errors = _semantic_text_errors(text="庚金的官杀压力很强，天干两透庚金直克日主。", world=world)

    assert any("金应属财星" in item for item in errors)
    assert any("金不是克制日主的官杀元素" in item for item in errors)
    relation_errors = _semantic_text_errors(text="这是子卯无礼之刑的变体，实际表现为寅申冲。", world=world)
    assert "地支关系冲突:盘中不存在子卯刑所需地支" in relation_errors
    assert not any("寅申冲" in item for item in relation_errors)

    sanitized = _sanitize_work_questions(
        WorkPathPortraitDraft(
            work_path=_work_path(),
            useful_god_reasoning=[],
            portrait=[],
            unresolved_questions=["是否存在卯酉冲", "现实工作是否长期依赖复杂问题解决"],
            evidence_refs=[],
        ),
        world=world,
    )
    assert sanitized.unresolved_questions == ["现实工作是否长期依赖复杂问题解决"]

    pattern = PatternHypothesisDraft(
        first_look="先比较两个结构解释。",
        whole_chart_thesis="主假设仍需与替代解释竞争。",
        salient_phenomena=[],
        hypotheses=[
            CognitiveHypothesis(hypothesis_id="p1", name="主假设", thesis="丙火日主以木印支持。", rank=1, status="primary", supporting_evidence_refs=[], failure_conditions=["木印失效"], confidence="medium"),
            CognitiveHypothesis(hypothesis_id="p2", name="错误替代", thesis="水是比劫。", rank=2, status="alternative", supporting_evidence_refs=[], failure_conditions=["条件不成立"], rejection_reason="账本不支持", confidence="low"),
            CognitiveHypothesis(hypothesis_id="p3", name="有效替代", thesis="若支持不足则财富压力更直接。", rank=3, status="alternative", supporting_evidence_refs=[], failure_conditions=["支持恢复"], rejection_reason="当前支持仍可见", confidence="low"),
        ],
        selected_hypothesis_id="p1",
        evidence_refs=[],
    )
    cleaned = _sanitize_pattern_alternatives(pattern, world=world)
    assert [item.hypothesis_id for item in cleaned.hypotheses] == ["p1", "p3"]


def test_local_pattern_repair_discards_a_primary_hypothesis_that_conflicts_with_locked_root_fact():
    world = ChartWorldInstance(
        world_id="world.local.pattern.repair",
        reading_id="reading.local.pattern.repair",
        pillars=["壬辰", "戊申", "丙午", "丁丑"],
        birth_profile={},
        facts=[
            WorldFact(
                fact_id="F007",
                kind="fact",
                category="root_strength",
                statement="root_strength",
                payload={"day_stem": "丙", "has_root": True, "root_sources": [{"branch": "午", "hidden_stems": "丁"}]},
            ),
        ],
        knowledge=[],
        allowed_evidence_refs=["F007"],
    )
    pattern = PatternHypothesisDraft(
        first_look="日主丙火地支无根，因此只能顺从外势。",
        whole_chart_thesis="丙火无根是整盘成立的唯一前提。",
        salient_phenomena=[],
        hypotheses=[
            CognitiveHypothesis(
                hypothesis_id="bad",
                name="无根顺从",
                thesis="日主丙火地支无根，所以放弃自身作用。",
                rank=1,
                status="primary",
                supporting_evidence_refs=["F007"],
                failure_conditions=["现实持续主动承担"],
                confidence="high",
            ),
            CognitiveHypothesis(
                hypothesis_id="safe",
                name="有根承压",
                thesis="丙火通根于午，但根气强弱仍需结合申月和全局作用判断。",
                rank=2,
                status="alternative",
                supporting_evidence_refs=["F007"],
                failure_conditions=["午火在结构中完全失去作用"],
                rejection_reason="仍需比较承压能力",
                confidence="medium",
            ),
        ],
        selected_hypothesis_id="bad",
        evidence_refs=["F007"],
    )

    repaired = _repair_pattern_locally(pattern, world=world)

    assert repaired.selected_hypothesis_id == "safe"
    assert [item.hypothesis_id for item in repaired.hypotheses] == ["safe"]
    assert repaired.first_look == repaired.hypotheses[0].thesis


def test_guided_deliberation_enforces_dependencies_and_never_changes_confidence_from_clicks():
    agent = MingliAgent(FakeCognitiveModel())
    store = MemoryAgentCaseStore()
    product_store = MemoryProductStore()
    client = TestClient(create_product_app(product_store=product_store, mingli_agent=agent, agent_case_store=store))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={"display_name": "命理师", "email": "practitioner-deliberation@example.com", "password": "secure-pass-123", "role": "practitioner"},
    )
    assert registered.status_code == 200
    started = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload(), "active_mode": "practitioner"})
    assert started.status_code == 200, started.text
    case_id = started.json()["case_id"]
    before = store.get(case_id=case_id)
    original_record = before["record"]

    view = client.get(f"/api/v50/agent/cases/{case_id}/deliberation?active_mode=practitioner").json()["deliberation"]
    pattern = next(item for item in view["stages"] if item["stage_id"] == "pattern")
    useful = next(item for item in view["stages"] if item["stage_id"] == "useful_god")
    assert pattern["status"] == "available"
    assert useful["status"] == "locked"
    pattern_support = pattern["options"][0]["support_percent"]

    blocked = client.post(
        f"/api/v50/agent/cases/{case_id}/deliberation/select",
        json={"active_mode": "practitioner", "stage_id": "useful_god", "option_id": "useful_god:0", "action": "select"},
    )
    assert blocked.status_code == 409
    selected = client.post(
        f"/api/v50/agent/cases/{case_id}/deliberation/select",
        json={"active_mode": "practitioner", "stage_id": "pattern", "option_id": pattern["options"][0]["option_id"], "action": "select", "rationale": "沿系统主假设继续"},
    )
    assert selected.status_code == 200, selected.text
    body = selected.json()
    assert body["receipt"]["confidence_modified_without_evidence"] is False
    updated_pattern = next(item for item in body["reading"]["deliberation"]["stages"] if item["stage_id"] == "pattern")
    assert updated_pattern["options"][0]["support_percent"] == pattern_support
    assert next(item for item in body["reading"]["deliberation"]["stages"] if item["stage_id"] == "useful_god")["status"] == "available"
    after = store.get(case_id=case_id)
    assert after["record"] == original_record
    assert after["world"] == before["world"]
    assert after["workspace"]["chart_facts_locked"] is True
    assert after["workspace"]["global_update_allowed"] is False

    undone = client.post(
        f"/api/v50/agent/cases/{case_id}/deliberation/undo",
        json={"active_mode": "practitioner"},
    )
    assert undone.status_code == 200
    assert next(item for item in undone.json()["reading"]["deliberation"]["stages"] if item["stage_id"] == "pattern")["status"] == "available"


def test_product_mode_permissions_are_role_strict_except_for_admin_preview():
    agent = MingliAgent(FakeCognitiveModel())
    store = MemoryAgentCaseStore()
    product_store = MemoryProductStore()
    practitioner = TestClient(create_product_app(product_store=product_store, mingli_agent=agent, agent_case_store=store))
    practitioner.post(
        "/api/v50/product/auth/register",
        json={"display_name": "命理师", "email": "strict-practitioner@example.com", "password": "secure-pass-123", "role": "practitioner"},
    )
    case_id = practitioner.post("/api/v50/agent/cases", json={"birth_input": _birth_payload(), "active_mode": "practitioner"}).json()["case_id"]
    assert practitioner.get(f"/api/v50/agent/cases/{case_id}?active_mode=member").status_code == 403
    assert practitioner.get(f"/api/v50/agent/cases/{case_id}?active_mode=research").status_code == 403

    admin_store = MemoryProductStore()
    admin_store.ensure_admin_account(email="jerrydidi@gmail.com", password="abcd1235", display_name="DeepBazi Admin")
    admin_cases = MemoryAgentCaseStore()
    admin = TestClient(create_product_app(product_store=admin_store, mingli_agent=agent, agent_case_store=admin_cases))
    admin.post("/api/v50/product/auth/login", json={"email": "jerrydidi@gmail.com", "password": "abcd1235"})
    admin_case_id = admin.post("/api/v50/agent/cases", json={"birth_input": _birth_payload(), "active_mode": "member"}).json()["case_id"]
    readings = {}
    for mode in ["guest", "member", "practitioner", "research"]:
        response = admin.get(f"/api/v50/agent/cases/{admin_case_id}?active_mode={mode}")
        assert response.status_code == 200
        readings[mode] = response.json()["reading"]
    assert readings["guest"]["projection_contract"]["name"] == "GuestReadingProjection"
    assert "hypotheses" not in readings["guest"]
    assert "hidden_attribute_beliefs" not in readings["member"]["workspace"]
    assert readings["practitioner"]["projection_contract"]["name"] == "PractitionerCognitiveProjection"
    assert readings["practitioner"]["hypotheses"]
    assert "review" not in readings["practitioner"]
    assert readings["research"]["projection_contract"]["name"] == "ResearchAuditProjection"
    assert readings["research"]["review"]


def test_research_fork_preserves_system_baseline_and_does_not_complete_the_stage():
    agent = MingliAgent(FakeCognitiveModel())
    store = MemoryAgentCaseStore()
    client = TestClient(create_product_app(product_store=MemoryProductStore(), mingli_agent=agent, agent_case_store=store))
    client.post(
        "/api/v50/product/auth/register",
        json={"display_name": "研究者", "email": "research-fork@example.com", "password": "secure-pass-123", "role": "research_master"},
    )
    started = client.post("/api/v50/agent/cases", json={"birth_input": _birth_payload(), "active_mode": "research"})
    case_id = started.json()["case_id"]
    original = store.get(case_id=case_id)
    pattern = next(item for item in started.json()["reading"]["deliberation"]["stages"] if item["stage_id"] == "pattern")
    assert sum(item["support_percent"] for item in pattern["options"]) == 100
    forked = client.post(
        f"/api/v50/agent/cases/{case_id}/deliberation/select",
        json={"active_mode": "research", "stage_id": "pattern", "option_id": pattern["options"][1]["option_id"], "action": "research_fork"},
    )
    assert forked.status_code == 200, forked.text
    reading = forked.json()["reading"]
    forked_pattern = next(item for item in reading["deliberation"]["stages"] if item["stage_id"] == "pattern")
    assert forked_pattern["status"] == "available"
    assert forked_pattern["options"][1]["research_forked"] is True
    assert reading["selected_hypothesis_id"] == reading["system_selected_hypothesis_id"]
    assert store.get(case_id=case_id)["record"] == original["record"]

    undone = client.post(
        f"/api/v50/agent/cases/{case_id}/deliberation/undo",
        json={"active_mode": "research"},
    )
    assert undone.status_code == 200
    undone_pattern = next(item for item in undone.json()["reading"]["deliberation"]["stages"] if item["stage_id"] == "pattern")
    assert undone_pattern["options"][1]["research_forked"] is False
