from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_contracts import (
    MingliAgentCasePacket,
    MingliAgentReadingEnvelope,
)
from abu_v60.mingli.agent_normalization_receipt import (
    MingliAgentNormalizationDelta,
)
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.agent_runtime import MingliAgentRuntime
from abu_v60.mingli.agent_service import MingliAgentService
from abu_v60.mingli.agent_store import MingliAgentReadingStore
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.service import MingliCaseService
from abu_v60.mingli.stage import MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode, MingliStageProjection
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_MEMBERS,
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
    SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
    SYNTHETIC_MEMBER_BY_VARIANT,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    resolve_research_stage_subject,
    synthetic_experiment_public_definition,
)
from abu_v60.mingli.synthetic_experiment_contracts import (
    SYNTHETIC_EXPERIMENT_RUN_VERSION,
    SYNTHETIC_EXPERIMENT_SNAPSHOT_VERSION,
    SyntheticExperimentOutcome,
    SyntheticExperimentRunIdentity,
)
from abu_v60.mingli.synthetic_experiment_gold import (
    FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD,
    FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH,
)
from abu_v60.mingli.synthetic_experiment_seed import (
    seed_first_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_store import (
    MingliSyntheticExperimentRunStore,
    MingliSyntheticExperimentRunStoreError,
)
from abu_v60.mingli.timing_store import MingliTimingVectorStore
from abu_v60.provenance import content_hash, stable_ref


class SyntheticExperimentError(ValueError):
    pass


class SyntheticExperimentService:
    """Run paired blind readings offline and expose only sealed read-only snapshots."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliAgentRuntime | None = None,
    ) -> None:
        self._engine = engine
        self._runtime = runtime
        self._cases = MingliCaseService(engine)
        self._readings = MingliReadingStore(engine)
        self._agent_readings = MingliAgentReadingStore(engine)
        self._quant = MingliQuantVectorStore(engine)
        self._mechanism = MingliMechanismVectorStore(engine)
        self._timing = MingliTimingVectorStore(engine)
        self._packets = MingliAgentCasePacketCompiler()
        self._runs = MingliSyntheticExperimentRunStore(engine)

    def run_first_experiment(self) -> dict[str, Any]:
        seeded = seed_first_synthetic_experiment(self._engine)
        by_case = {item["case_ref"]: item for item in seeded["members"]}
        agent = MingliAgentService(self._engine, runtime=self._runtime)
        readings: dict[str, MingliAgentReadingEnvelope] = {}
        packets: dict[str, MingliAgentCasePacket] = {}
        stages: dict[str, MingliStageProjection] = {}
        stage_service = MingliStageService(
            self._engine,
            current_date_provider=lambda _: SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
            research_subject_resolver=resolve_research_stage_subject,
        )
        for member in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS:
            materialized = by_case[member.case_ref]
            generated = agent.generate(
                requester_account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                case_ref=member.case_ref,
                expected_reading_ref=str(materialized["reading_ref"]),
                expected_reading_hash=str(materialized["reading_hash"]),
            )
            readings[member.variant] = generated
            packets[member.variant] = self._packet(
                case_ref=member.case_ref,
                reading_ref=str(materialized["reading_ref"]),
            )
            stages[member.variant] = stage_service.project(
                account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                subject_id=member.subject_id,
                stage_mode=MingliStageMode.NATAL_4,
                pinned_reading_ref=generated.reading_ref,
                pinned_reading_hash=generated.reading_hash,
            )
        evaluation = self._evaluate(readings=readings, packets=packets)
        return self._ensure_run(
            readings=readings,
            stages=stages,
            evaluation=evaluation,
        )

    def catalog(self) -> dict[str, Any]:
        definition = synthetic_experiment_public_definition()
        latest = self._runs.latest(experiment_ref=FIRST_SYNTHETIC_EXPERIMENT_REF)
        return {
            "catalog_version": definition["catalog_version"],
            "experiments": [
                {
                    **definition,
                    "run_status": "SEALED" if latest is not None else "NOT_RUN",
                    "latest_run_ref": latest["run_ref"] if latest is not None else None,
                    "latest_outcome": latest["outcome"] if latest is not None else None,
                }
            ],
            "browser_generation_allowed": False,
            "read_only": True,
        }

    def snapshot(
        self,
        *,
        variant: Literal["A", "B"],
        run_ref: str | None = None,
    ) -> dict[str, Any]:
        run = (
            self._runs.get(run_ref=run_ref)
            if run_ref is not None
            else self._runs.latest(experiment_ref=FIRST_SYNTHETIC_EXPERIMENT_REF)
        )
        if run is None:
            raise SyntheticExperimentError("mingli_synthetic_experiment_not_run")
        if run["experiment_ref"] != FIRST_SYNTHETIC_EXPERIMENT_REF:
            raise SyntheticExperimentError("mingli_synthetic_experiment_run_mismatch")
        definition = synthetic_experiment_public_definition()
        if run["definition_hash"] != definition["definition_hash"]:
            raise SyntheticExperimentError("mingli_synthetic_experiment_definition_drift")
        member = SYNTHETIC_MEMBER_BY_VARIANT[variant]
        sealed_readings = {
            member_variant: self._agent_readings.get(
                requester_account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                agent_reading_ref=str(
                    run[
                        "member_a_agent_reading_ref"
                        if member_variant == "A"
                        else "member_b_agent_reading_ref"
                    ]
                ),
            )
            for member_variant in ("A", "B")
        }
        sealed_agent_reading = sealed_readings[variant]
        sealed_agent_reading_ref = sealed_agent_reading.agent_reading_ref
        if sealed_agent_reading.case_ref != member.case_ref:
            raise SyntheticExperimentError(
                "mingli_synthetic_experiment_member_reading_mismatch"
            )
        stage = MingliStageProjection.model_validate(
            run[
                "member_a_stage_json"
                if variant == "A"
                else "member_b_stage_json"
            ]
        )
        if (
            stage.subject_id != member.subject_id
            or stage.case_ref != member.case_ref
            or stage.reading_ref != sealed_agent_reading.reading_ref
            or stage.reading_hash != sealed_agent_reading.reading_hash
        ):
            raise SyntheticExperimentError(
                "mingli_synthetic_experiment_sealed_stage_mismatch"
            )
        identity = {
            "snapshot_version": SYNTHETIC_EXPERIMENT_SNAPSHOT_VERSION,
            "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
            "run_ref": run["run_ref"],
            "run_hash": run["run_hash"],
            "selected_variant": variant,
            "member_ref": member.member_ref,
            "sealed_agent_reading_ref": sealed_agent_reading_ref,
            "stage": stage.model_dump(mode="json"),
            "evaluation": run["evaluation_json"],
            "training_assessment": self._training_assessment(
                evaluation=run["evaluation_json"],
                readings=sealed_readings,
            ),
            "model_trace": self._model_trace(sealed_agent_reading),
        }
        return {
            "snapshot_ref": stable_ref("v60-mingli-synthetic-snapshot", identity),
            "snapshot_hash": content_hash(identity),
            **identity,
            "definition": definition,
            "browser_generation_allowed": False,
            "read_only": True,
        }

    @staticmethod
    def _training_assessment(
        *,
        evaluation: Mapping[str, Any],
        readings: Mapping[str, MingliAgentReadingEnvelope],
    ) -> dict[str, Any]:
        checks = tuple(evaluation["checks"])
        validity_failed = any(
            item["status"] == "FAIL"
            and item["group"] in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
            for item in checks
        )
        expected_failed = any(
            item["status"] == "FAIL" and item["group"] == "EXPECTED_CHANGE"
            for item in checks
        )
        issue_keys = {
            variant: tuple(evaluation["server_issue_keys"][variant])
            for variant in ("A", "B")
        }
        trace_count = sum(
            readings[variant].normalization_receipt is not None
            for variant in ("A", "B")
        )
        trace_coverage = (
            "FIELD_LEVEL"
            if trace_count == 2
            else "PARTIAL"
            if trace_count == 1
            else "LEGACY_SUMMARY_ONLY"
        )
        experiment_validity = "INVALID" if validity_failed else "VALID"
        model_independence = (
            "NOT_EVALUABLE"
            if validity_failed
            else "FAIL"
            if expected_failed or issue_keys["A"] or issue_keys["B"]
            else "PASS"
        )
        outcome = str(evaluation["outcome"])
        product_result = (
            "NOT_EVALUABLE"
            if validity_failed
            else "SAFE_MODEL_DIRECT"
            if outcome == "PASS"
            else "SAFE_WITH_REPAIR"
            if outcome == "PRODUCT_SAFE_MODEL_FAIL"
            else "WITHHELD"
        )
        return {
            "assessment_version": "v60.mingli-synthetic-training-assessment.001",
            "experiment_validity": experiment_validity,
            "model_independence": model_independence,
            "product_result": product_result,
            "trace_coverage": trace_coverage,
            "server_issue_keys": issue_keys,
            "summary": (
                "控制变量有效；产品结果已被规则收敛，但模型尚未独立通过。"
                if product_result == "SAFE_WITH_REPAIR"
                else "控制变量有效；模型与产品结果均独立通过当前 DEV 检查。"
                if product_result == "SAFE_MODEL_DIRECT"
                else "模型结果未进入产品结论，等待修正后重跑。"
                if product_result == "WITHHELD"
                else "控制变量发生漂移，不能评价模型或产品结果。"
            ),
            "qualification_effect": "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
        }

    @staticmethod
    def _model_trace(reading: MingliAgentReadingEnvelope) -> dict[str, Any]:
        receipt = reading.normalization_receipt
        if receipt is None:
            return {
                "trace_version": "v60.mingli-synthetic-model-trace.001",
                "availability": "LEGACY_NOT_CAPTURED",
                "selected_agent_reading_ref": reading.agent_reading_ref,
                "receipt_ref": None,
                "receipt_hash": None,
                "raw_output_hash": None,
                "normalized_output_hash": content_hash(
                    reading.output.model_dump(mode="json")
                ),
                "change_count": None,
                "stage_counts": [],
                "key_deltas": [],
                "server_issue_keys": list(reading.output.server_issue_keys),
                "limitation": (
                    "该历史运行只封存了归一化结果与修正码，没有保存模型原断；"
                    "系统不会补造字段级差异。"
                ),
            }
        key_deltas = tuple(
            item
            for item in receipt.changes
            if _is_professional_trace_delta(item)
        )[:16]
        stage_counts = tuple(
            {
                "stage": stage,
                "change_count": sum(item.stage == stage for item in receipt.changes),
            }
            for stage in (
                "EVIDENCE_ID_NORMALIZATION",
                "PACKET_FACT_BINDING",
                "PROFESSIONAL_ADJUDICATION",
                "PROSE_EVIDENCE_REPAIR",
                "OUTPUT_FORM_REPAIR",
                "LOCAL_FIELD_REPAIR",
            )
            if any(item.stage == stage for item in receipt.changes)
        )
        return {
            "trace_version": "v60.mingli-synthetic-model-trace.001",
            "availability": "FIELD_LEVEL",
            "selected_agent_reading_ref": reading.agent_reading_ref,
            "receipt_ref": receipt.receipt_ref,
            "receipt_hash": receipt.receipt_hash,
            "raw_output_hash": receipt.raw_output_hash,
            "normalized_output_hash": receipt.normalized_output_hash,
            "change_count": len(receipt.changes),
            "stage_counts": stage_counts,
            "key_deltas": tuple(item.model_dump(mode="json") for item in key_deltas),
            "server_issue_keys": list(receipt.server_issue_keys),
            "limitation": (
                "只保存 think=false 的结构化回答，不保存或展示隐藏思维链；"
                "字段差异证明系统改了什么，不自动证明专业 Gold 正确。"
            ),
        }

    def _packet(self, *, case_ref: str, reading_ref: str) -> MingliAgentCasePacket:
        workspace = self._cases.workspace(
            account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            case_ref=case_ref,
        )
        reading = self._readings.get(reading_ref=reading_ref)
        if (
            reading.quant_vector_ref is None
            or reading.mechanism_vector_ref is None
            or reading.timing_vector_ref is None
        ):
            raise SyntheticExperimentError("mingli_synthetic_experiment_reading_incomplete")
        return self._packets.compile(
            workspace=workspace,
            reading=reading,
            quant_vector=self._quant.get(vector_ref=reading.quant_vector_ref),
            mechanism_vector=self._mechanism.get(vector_ref=reading.mechanism_vector_ref),
            timing_vector=self._timing.get(vector_ref=reading.timing_vector_ref),
        )

    @staticmethod
    def _evaluate(
        *,
        readings: Mapping[str, MingliAgentReadingEnvelope],
        packets: Mapping[str, MingliAgentCasePacket],
    ) -> dict[str, Any]:
        a_packet, b_packet = packets["A"], packets["B"]
        a_output, b_output = readings["A"].output, readings["B"].output
        a_regime, b_regime = a_output.regime_decision, b_output.regime_decision
        if a_regime is None or b_regime is None:
            raise SyntheticExperimentError("mingli_synthetic_experiment_regime_missing")
        checks: list[dict[str, Any]] = []

        def add(
            check_ref: str,
            group: str,
            passed: bool,
            statement: str,
            a_value: object,
            b_value: object,
        ) -> None:
            checks.append(
                {
                    "check_ref": check_ref,
                    "group": group,
                    "status": "PASS" if passed else "FAIL",
                    "statement": statement,
                    "A": a_value,
                    "B": b_value,
                }
            )

        add(
            "LEGAL_HOUR_DELTA",
            "EXPERIMENT_VALIDITY",
            tuple(item.pillar for item in a_packet.pillars)
            == SYNTHETIC_MEMBER_BY_VARIANT["A"].expected_pillars
            and tuple(item.pillar for item in b_packet.pillars)
            == SYNTHETIC_MEMBER_BY_VARIANT["B"].expected_pillars,
            "两份命盘必须精确等于历法锁定的 A／B 四柱，且只有时柱位置不同。",
            [item.pillar for item in a_packet.pillars],
            [item.pillar for item in b_packet.pillars],
        )
        add(
            "PACKET_CONTEXT_BINDING",
            "EXPERIMENT_VALIDITY",
            a_packet.case_ref == SYNTHETIC_MEMBER_BY_VARIANT["A"].case_ref
            and b_packet.case_ref == SYNTHETIC_MEMBER_BY_VARIANT["B"].case_ref
            and a_packet.subject_kind == b_packet.subject_kind == "CANONICAL_SYNTHETIC"
            and a_packet.gender == b_packet.gender == "male"
            and a_packet.birth_timezone == b_packet.birth_timezone == "Asia/Shanghai"
            and a_packet.timing_analysis_date
            == b_packet.timing_analysis_date
            == SYNTHETIC_EXPERIMENT_ANALYSIS_DATE.isoformat(),
            "A／B 必须绑定各自实验 Case，并保持合成身份、性别、时区和分析日期一致。",
            {
                "case_ref": a_packet.case_ref,
                "subject_kind": a_packet.subject_kind,
                "gender": a_packet.gender,
                "timezone": a_packet.birth_timezone,
                "analysis_date": a_packet.timing_analysis_date,
            },
            {
                "case_ref": b_packet.case_ref,
                "subject_kind": b_packet.subject_kind,
                "gender": b_packet.gender,
                "timezone": b_packet.birth_timezone,
                "analysis_date": b_packet.timing_analysis_date,
            },
        )
        for check_ref, statement, a_value, b_value in (
            (
                "DAY_MASTER_HOLD",
                "日主必须保持。",
                a_packet.day_master_stem,
                b_packet.day_master_stem,
            ),
            (
                "MONTH_COMMAND_HOLD",
                "月令必须保持。",
                a_packet.month_command_branch,
                b_packet.month_command_branch,
            ),
            (
                "VISIBLE_PEERS_HOLD",
                "明干同类不得漂移。",
                a_packet.day_master_support.visible_peer_support,
                b_packet.day_master_support.visible_peer_support,
            ),
            (
                "RESOURCE_SUPPORT_HOLD",
                "印星生扶不得漂移。",
                a_packet.day_master_support.resource_support,
                b_packet.day_master_support.resource_support,
            ),
            (
                "MECHANISM_SET_HOLD",
                "候选机制集合不得漂移。",
                tuple(
                    sorted(item.pattern_ref for item in a_packet.mechanism_observations)
                ),
                tuple(
                    sorted(item.pattern_ref for item in b_packet.mechanism_observations)
                ),
            ),
            (
                "TIMING_COORDINATES_HOLD",
                "固定分析日的大运与流年坐标不得漂移。",
                tuple((item.layer, item.pillar) for item in a_packet.timing_coordinates),
                tuple((item.layer, item.pillar) for item in b_packet.timing_coordinates),
            ),
        ):
            add(
                check_ref,
                "MUST_HOLD",
                a_value == b_value,
                statement,
                a_value,
                b_value,
            )
        add(
            "ROOT_CANDIDATE_FLIP",
            "EXPERIMENT_VALIDITY",
            not a_packet.day_master_support.same_element_hidden_support
            and b_packet.day_master_support.same_element_hidden_support
            == ("hour支藏甲",),
            "根候选应从无变为寅中甲木主气坐标。",
            a_packet.day_master_support.same_element_hidden_support,
            b_packet.day_master_support.same_element_hidden_support,
        )
        gold = FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD
        add(
            "B_EFFECTIVE_ROOT",
            "EXPECTED_CHANGE",
            b_regime.effective_root_status == gold["B_effective_root_status"]
            and b_regime.effective_root_coordinates
            == gold["B_effective_root_coordinates"],
            "B 必须真正裁定新增根候选是否有效，不能只复述候选存在。",
            a_regime.effective_root_status,
            {
                "status": b_regime.effective_root_status,
                "coordinates": b_regime.effective_root_coordinates,
            },
        )
        add(
            "B_REGIME_EXIT_FOLLOW",
            "EXPECTED_CHANGE",
            b_regime.classification == gold["B_regime_classification"]
            and b_output.day_master_state == gold["B_required_day_master_state"],
            "B 的完整时柱证据支持有效根后，应退出从势并进入普通身弱工作判断；"
            "本实验不把变化单独归因于根气。",
            {
                "classification": a_regime.classification,
                "day_master_state": a_output.day_master_state,
            },
            {
                "classification": b_regime.classification,
                "day_master_state": b_output.day_master_state,
            },
        )
        add(
            "A_NO_FORCED_FOLLOW",
            "EXPECTED_CHANGE",
            a_regime.classification in gold["A_allowed_regime_classifications"],
            "A 无根不等于必须判从；主导链未闭合时允许保持未决。",
            a_regime.classification,
            b_regime.classification,
        )
        issue_keys = {
            "A": list(a_output.server_issue_keys),
            "B": list(b_output.server_issue_keys),
        }
        validity_failed = any(
            item["status"] == "FAIL" and item["group"] in {
                "EXPERIMENT_VALIDITY",
                "MUST_HOLD",
            }
            for item in checks
        )
        model_failed = any(
            item["status"] == "FAIL" and item["group"] == "EXPECTED_CHANGE"
            for item in checks
        )
        outcome: SyntheticExperimentOutcome = (
            "INVALID_EXPERIMENT"
            if validity_failed
            else "PRODUCT_SAFE_MODEL_FAIL"
            if issue_keys["A"] or issue_keys["B"]
            else "MODEL_FAIL"
            if model_failed
            else "PASS"
        )
        return {
            "evaluator_version": SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
            "dev_gold_version": gold["gold_version"],
            "dev_gold_hash": FIRST_SYNTHETIC_EXPERIMENT_DEV_GOLD_HASH,
            "outcome": outcome,
            "checks": checks,
            "server_issue_keys": issue_keys,
            "changed_pass_count": sum(
                item["status"] == "PASS" and item["group"] == "EXPECTED_CHANGE"
                for item in checks
            ),
            "hold_pass_count": sum(
                item["status"] == "PASS" and item["group"] == "MUST_HOLD"
                for item in checks
            ),
            "drift_checks": [
                item["check_ref"]
                for item in checks
                if item["status"] == "FAIL" and item["group"] == "MUST_HOLD"
            ],
            "qualification_effect": gold["qualification_effect"],
            "summary": {
                "PASS": "首组开发实验通过，但只进入复核，不代表方法已取得资格。",
                "PRODUCT_SAFE_MODEL_FAIL": (
                    "服务端修正后产品没有越界，但模型原始判断尚未独立通过。"
                ),
                "MODEL_FAIL": "实验结构有效，但模型没有完成该变与保持的全部要求。",
                "INVALID_EXPERIMENT": "控制变量发生漂移，本轮结果不能用于评价模型。",
            }[outcome],
        }

    def _ensure_run(
        self,
        *,
        readings: Mapping[str, MingliAgentReadingEnvelope],
        stages: Mapping[str, MingliStageProjection],
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        definition = synthetic_experiment_public_definition()
        identity = SyntheticExperimentRunIdentity(
            run_version=SYNTHETIC_EXPERIMENT_RUN_VERSION,
            experiment_ref=FIRST_SYNTHETIC_EXPERIMENT_REF,
            definition_hash=str(definition["definition_hash"]),
            evaluator_version=SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
            analysis_date=SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
            member_a_agent_reading_ref=readings["A"].agent_reading_ref,
            member_b_agent_reading_ref=readings["B"].agent_reading_ref,
            member_a_stage_json=stages["A"],
            member_b_stage_json=stages["B"],
            outcome=evaluation["outcome"],
            evaluation_json=evaluation,
        )
        try:
            return self._runs.ensure(identity=identity)
        except MingliSyntheticExperimentRunStoreError as exc:
            raise SyntheticExperimentError(str(exc)) from exc


_PROFESSIONAL_TRACE_PREFIXES = (
    "/regime_decision",
    "/day_master_state",
    "/day_master_rationale",
    "/support_selection",
    "/hypotheses",
    "/hypothesis_decision",
    "/work_path",
)


def _is_professional_trace_delta(
    delta: MingliAgentNormalizationDelta,
) -> bool:
    return (
        delta.path != "/hypotheses"
        and delta.path.startswith(_PROFESSIONAL_TRACE_PREFIXES)
    )
