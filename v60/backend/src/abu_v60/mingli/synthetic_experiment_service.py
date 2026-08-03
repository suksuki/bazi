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
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENT_CATALOG_VERSION,
    SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
    SYNTHETIC_EXPERIMENTS,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    SyntheticExperimentDefinition,
    resolve_research_stage_subject,
    resolve_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_contracts import (
    SYNTHETIC_EXPERIMENT_RUN_VERSION,
    SYNTHETIC_EXPERIMENT_SNAPSHOT_VERSION,
    SyntheticExperimentRunIdentity,
)
from abu_v60.mingli.synthetic_experiment_evaluator import (
    evaluate_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold
from abu_v60.mingli.synthetic_experiment_seed import (
    seed_synthetic_experiment,
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
        return self.run_experiment(experiment_ref=FIRST_SYNTHETIC_EXPERIMENT_REF)

    def run_experiment(self, *, experiment_ref: str) -> dict[str, Any]:
        try:
            experiment = resolve_synthetic_experiment(experiment_ref)
        except ValueError as exc:
            raise SyntheticExperimentError(str(exc)) from exc
        seeded = seed_synthetic_experiment(
            self._engine,
            experiment_ref=experiment.experiment_ref,
        )
        by_case = {item["case_ref"]: item for item in seeded["members"]}
        agent = MingliAgentService(self._engine, runtime=self._runtime)
        readings: dict[str, MingliAgentReadingEnvelope] = {}
        packets: dict[str, MingliAgentCasePacket] = {}
        stages: dict[str, MingliStageProjection] = {}
        stage_service = MingliStageService(
            self._engine,
            current_date_provider=lambda _: experiment.analysis_date,
            research_subject_resolver=resolve_research_stage_subject,
        )
        for member in experiment.members:
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
        evaluation = evaluate_synthetic_experiment(
            experiment=experiment,
            readings=readings,
            packets=packets,
        )
        return self._ensure_run(
            experiment=experiment,
            readings=readings,
            stages=stages,
            evaluation=evaluation,
        )

    def catalog(self) -> dict[str, Any]:
        experiments = []
        for experiment in SYNTHETIC_EXPERIMENTS:
            definition = experiment.public_definition()
            history = self._runs.history(experiment_ref=experiment.experiment_ref)
            latest = history[0] if history else None
            experiments.append(
                {
                    **definition,
                    "run_status": "SEALED" if latest is not None else "NOT_RUN",
                    "latest_run_ref": (
                        latest["run_ref"] if latest is not None else None
                    ),
                    "latest_outcome": (
                        latest["outcome"] if latest is not None else None
                    ),
                    "runs": [self._run_summary(item) for item in history],
                }
            )
        return {
            "catalog_version": SYNTHETIC_EXPERIMENT_CATALOG_VERSION,
            "experiments": experiments,
            "browser_generation_allowed": False,
            "read_only": True,
        }

    def snapshot(
        self,
        *,
        experiment_ref: str = FIRST_SYNTHETIC_EXPERIMENT_REF,
        variant: Literal["A", "B"],
        run_ref: str | None = None,
    ) -> dict[str, Any]:
        try:
            experiment = resolve_synthetic_experiment(experiment_ref)
        except ValueError as exc:
            raise SyntheticExperimentError(str(exc)) from exc
        run = (
            self._runs.get(run_ref=run_ref)
            if run_ref is not None
            else self._runs.latest(experiment_ref=experiment.experiment_ref)
        )
        if run is None:
            raise SyntheticExperimentError("mingli_synthetic_experiment_not_run")
        if run["experiment_ref"] != experiment.experiment_ref:
            raise SyntheticExperimentError("mingli_synthetic_experiment_run_mismatch")
        definition = experiment.public_definition()
        if run["definition_hash"] != definition["definition_hash"]:
            raise SyntheticExperimentError("mingli_synthetic_experiment_definition_drift")
        member = experiment.member_by_variant[variant]
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
        sealed_stages = {
            member_variant: MingliStageProjection.model_validate(
                run[
                    "member_a_stage_json"
                    if member_variant == "A"
                    else "member_b_stage_json"
                ]
            )
            for member_variant in ("A", "B")
        }
        self._validate_sealed_members(
            experiment=experiment,
            readings=sealed_readings,
            stages=sealed_stages,
        )
        sealed_agent_reading = sealed_readings[variant]
        sealed_agent_reading_ref = sealed_agent_reading.agent_reading_ref
        stage = sealed_stages[variant]
        identity = {
            "snapshot_version": SYNTHETIC_EXPERIMENT_SNAPSHOT_VERSION,
            "experiment_ref": experiment.experiment_ref,
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
    def _validate_sealed_members(
        *,
        experiment: SyntheticExperimentDefinition,
        readings: Mapping[str, MingliAgentReadingEnvelope],
        stages: Mapping[str, MingliStageProjection],
    ) -> None:
        """Close both sides of a paired run before either side is exposed."""

        for variant in ("A", "B"):
            member = experiment.member_by_variant[variant]
            reading = readings[variant]
            stage = stages[variant]
            if reading.case_ref != member.case_ref:
                raise SyntheticExperimentError(
                    "mingli_synthetic_experiment_member_reading_mismatch"
                )
            if (
                stage.subject_id != member.subject_id
                or stage.case_ref != member.case_ref
                or stage.reading_ref != reading.reading_ref
                or stage.reading_hash != reading.reading_hash
            ):
                raise SyntheticExperimentError(
                    "mingli_synthetic_experiment_sealed_stage_mismatch"
                )

    @staticmethod
    def _run_summary(run: Mapping[str, Any]) -> dict[str, Any]:
        evaluation = run["evaluation_json"]
        current_gold, current_gold_hash = synthetic_experiment_dev_gold(
            run["experiment_ref"]
        )
        checks = tuple(evaluation["checks"])
        issue_keys = evaluation["server_issue_keys"]
        model_independence = (
            "NOT_EVALUABLE"
            if any(
                item["group"] in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
                and item["status"] == "FAIL"
                for item in checks
            )
            else "FAIL"
            if issue_keys["A"]
            or issue_keys["B"]
            or any(
                item["group"] == "EXPECTED_CHANGE" and item["status"] == "FAIL"
                for item in checks
            )
            else "PASS"
        )
        return {
            "run_ref": run["run_ref"],
            "experiment_ref": run["experiment_ref"],
            "created_at": run["created_at"].isoformat(),
            "outcome": run["outcome"],
            "model_independence": model_independence,
            "evaluator_version": evaluation["evaluator_version"],
            "dev_gold_version": evaluation["dev_gold_version"],
            "review_contract_status": (
                "CURRENT"
                if evaluation["evaluator_version"]
                == SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION
                and evaluation["dev_gold_version"] == current_gold["gold_version"]
                and evaluation["dev_gold_hash"] == current_gold_hash
                else "SUPERSEDED"
            ),
            "changed_pass_count": evaluation["changed_pass_count"],
            "hold_pass_count": evaluation["hold_pass_count"],
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

    def _ensure_run(
        self,
        *,
        experiment: SyntheticExperimentDefinition,
        readings: Mapping[str, MingliAgentReadingEnvelope],
        stages: Mapping[str, MingliStageProjection],
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        definition = experiment.public_definition()
        identity = SyntheticExperimentRunIdentity(
            run_version=SYNTHETIC_EXPERIMENT_RUN_VERSION,
            experiment_ref=experiment.experiment_ref,
            definition_hash=str(definition["definition_hash"]),
            evaluator_version=SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
            analysis_date=experiment.analysis_date,
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
