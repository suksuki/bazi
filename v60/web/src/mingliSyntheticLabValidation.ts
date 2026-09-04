import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentCatalogEntry,
  MingliSyntheticExperimentDefinition,
  MingliSyntheticExperimentSnapshot,
  MingliSyntheticVariant,
} from "./mingliSyntheticLabTypes";
import { validateStageProjection } from "./mingliStageValidation";

const HASH = /^[0-9a-f]{64}$/;
const OUTCOMES = [
  "PASS",
  "PRODUCT_SAFE_MODEL_FAIL",
  "MODEL_FAIL",
  "INVALID_EXPERIMENT",
] as const;
const GROUPS = ["EXPERIMENT_VALIDITY", "MUST_HOLD", "EXPECTED_CHANGE"] as const;
const TRACE_STAGES = [
  "EVIDENCE_ID_NORMALIZATION",
  "PACKET_FACT_BINDING",
  "PROFESSIONAL_ADJUDICATION",
  "PROSE_EVIDENCE_REPAIR",
  "OUTPUT_FORM_REPAIR",
  "LOCAL_FIELD_REPAIR",
] as const;

export function validateSyntheticExperimentCatalog(
  value: unknown,
): MingliSyntheticExperimentCatalog {
  if (!isRecord(value) || !Array.isArray(value.experiments)) {
    throw new Error("mingli_synthetic_catalog_invalid");
  }
  const catalog = value as unknown as MingliSyntheticExperimentCatalog;
  if (
    catalog.catalog_version !== "v60.mingli-synthetic-experiment-catalog.007" ||
    catalog.browser_generation_allowed !== false ||
    catalog.read_only !== true ||
    catalog.experiments.length < 1
  ) {
    throw new Error("mingli_synthetic_catalog_shape_invalid");
  }
  catalog.experiments.forEach(validateCatalogEntry);
  if (
    new Set(catalog.experiments.map((item) => item.experiment_ref)).size
      !== catalog.experiments.length
  ) {
    throw new Error("mingli_synthetic_catalog_experiment_duplicate");
  }
  return catalog;
}

export function validateSyntheticExperimentSnapshot(
  value: unknown,
  expected: {
    experimentRef: string;
    runRef: string;
    variant: MingliSyntheticVariant;
  },
): MingliSyntheticExperimentSnapshot {
  if (
    !isRecord(value)
    || !isRecord(value.evaluation)
    || !isRecord(value.definition)
    || !isRecord(value.training_assessment)
    || !isRecord(value.model_trace)
  ) {
    throw new Error("mingli_synthetic_snapshot_invalid");
  }
  const snapshot = value as unknown as MingliSyntheticExperimentSnapshot;
  const member = snapshot.definition.members.find(
    (item) => item.variant === expected.variant,
  );
  if (
    snapshot.snapshot_version !== "v60.mingli-synthetic-experiment-snapshot.004" ||
    !snapshot.snapshot_ref ||
    !HASH.test(snapshot.snapshot_hash) ||
    snapshot.experiment_ref !== expected.experimentRef ||
    snapshot.definition.experiment_ref !== snapshot.experiment_ref ||
    snapshot.run_ref !== expected.runRef ||
    !snapshot.run_hash ||
    !HASH.test(snapshot.run_hash) ||
    snapshot.selected_variant !== expected.variant ||
    snapshot.browser_generation_allowed !== false ||
    snapshot.read_only !== true ||
    !snapshot.sealed_agent_reading_ref ||
    !member ||
    snapshot.member_ref !== member.member_ref
  ) {
    throw new Error("mingli_synthetic_snapshot_shape_invalid");
  }
  validateDefinition(snapshot.definition);
  validateEvaluation(snapshot.evaluation);
  validateTrainingAssessment(snapshot);
  validateModelTrace(snapshot);
  validateStageProjection(snapshot.stage, {
    subjectId: member.subject_id,
    mode: "NATAL_4",
    year: null,
  });
  if (
    snapshot.stage.identity_badge !== "研究合成命盘" ||
    snapshot.stage.privacy_scope !== "SYNTHETIC_RESEARCH"
  ) {
    throw new Error("mingli_synthetic_stage_scope_invalid");
  }
  return snapshot;
}

function validateTrainingAssessment(
  snapshot: MingliSyntheticExperimentSnapshot,
): void {
  const value = snapshot.training_assessment;
  const validityFailed = snapshot.evaluation.checks.some(
    (item) =>
      item.status === "FAIL"
      && (item.group === "EXPERIMENT_VALIDITY" || item.group === "MUST_HOLD"),
  );
  const expectedFailed = snapshot.evaluation.checks.some(
    (item) => item.status === "FAIL" && item.group === "EXPECTED_CHANGE",
  );
  const hasIssues =
    snapshot.evaluation.server_issue_keys.A.length > 0
    || snapshot.evaluation.server_issue_keys.B.length > 0;
  const expectedModel = validityFailed
    ? "NOT_EVALUABLE"
    : expectedFailed || hasIssues
      ? "FAIL"
      : "PASS";
  const expectedProduct = validityFailed
    ? "NOT_EVALUABLE"
    : snapshot.evaluation.outcome === "PASS"
      ? "SAFE_MODEL_DIRECT"
      : snapshot.evaluation.outcome === "PRODUCT_SAFE_MODEL_FAIL"
        ? "SAFE_WITH_REPAIR"
        : "WITHHELD";
  if (
    value.assessment_version
      !== "v60.mingli-synthetic-training-assessment.001"
    || value.experiment_validity !== (validityFailed ? "INVALID" : "VALID")
    || value.model_independence !== expectedModel
    || value.product_result !== expectedProduct
    || !["FIELD_LEVEL", "PARTIAL", "LEGACY_SUMMARY_ONLY"].includes(
      value.trace_coverage,
    )
    || value.qualification_effect !== "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION"
    || !value.summary
    || !isRecord(value.server_issue_keys)
    || !Array.isArray(value.server_issue_keys.A)
    || !Array.isArray(value.server_issue_keys.B)
    || !sameStrings(
      value.server_issue_keys.A,
      snapshot.evaluation.server_issue_keys.A,
    )
    || !sameStrings(
      value.server_issue_keys.B,
      snapshot.evaluation.server_issue_keys.B,
    )
  ) {
    throw new Error("mingli_synthetic_training_assessment_invalid");
  }
}

function validateModelTrace(snapshot: MingliSyntheticExperimentSnapshot): void {
  const value = snapshot.model_trace;
  const expectedIssues = snapshot.evaluation.server_issue_keys[
    snapshot.selected_variant
  ];
  const coverage = snapshot.training_assessment.trace_coverage;
  const commonInvalid =
    value.trace_version !== "v60.mingli-synthetic-model-trace.001"
    || !["FIELD_LEVEL", "LEGACY_NOT_CAPTURED"].includes(value.availability)
    || value.selected_agent_reading_ref !== snapshot.sealed_agent_reading_ref
    || !HASH.test(value.normalized_output_hash)
    || !Array.isArray(value.stage_counts)
    || !Array.isArray(value.key_deltas)
    || !Array.isArray(value.server_issue_keys)
    || value.server_issue_keys.some((item) => typeof item !== "string")
    || !sameStrings(value.server_issue_keys, expectedIssues)
    || (coverage === "FIELD_LEVEL" && value.availability !== "FIELD_LEVEL")
    || (
      coverage === "LEGACY_SUMMARY_ONLY"
      && value.availability !== "LEGACY_NOT_CAPTURED"
    )
    || !value.limitation;
  if (commonInvalid) throw new Error("mingli_synthetic_model_trace_invalid");

  if (value.availability === "LEGACY_NOT_CAPTURED") {
    if (
      value.receipt_ref !== null
      || value.receipt_hash !== null
      || value.raw_output_hash !== null
      || value.change_count !== null
      || value.stage_counts.length !== 0
      || value.key_deltas.length !== 0
    ) {
      throw new Error("mingli_synthetic_legacy_trace_invalid");
    }
    return;
  }
  const changeCount = value.change_count;
  if (
    !value.receipt_ref
    || !value.receipt_hash
    || !HASH.test(value.receipt_hash)
    || !value.raw_output_hash
    || !HASH.test(value.raw_output_hash)
    || typeof changeCount !== "number"
    || !Number.isInteger(changeCount)
    || changeCount < 0
    || changeCount < value.key_deltas.length
    || new Set(value.stage_counts.map((item) => item.stage)).size
      !== value.stage_counts.length
    || value.stage_counts.some(
      (item) =>
        !TRACE_STAGES.includes(item.stage as (typeof TRACE_STAGES)[number])
        || !Number.isInteger(item.change_count)
        || item.change_count < 1,
    )
    || value.stage_counts.reduce((total, item) => total + item.change_count, 0)
      !== changeCount
    || new Set(value.key_deltas.map((item) => `${item.stage}:${item.path}`)).size
      !== value.key_deltas.length
    || value.key_deltas.some(
      (item) =>
        !item.path.startsWith("/")
        || typeof item.before_present !== "boolean"
        || typeof item.after_present !== "boolean"
        || (!item.before_present && !item.after_present)
        || !TRACE_STAGES.includes(item.stage),
    )
  ) {
    throw new Error("mingli_synthetic_field_trace_invalid");
  }
}

function validateCatalogEntry(value: unknown): void {
  if (!isRecord(value)) throw new Error("mingli_synthetic_catalog_entry_invalid");
  const entry = value as unknown as MingliSyntheticExperimentCatalogEntry;
  validateDefinition(entry);
  const runs = entry.runs;
  if (
    !Array.isArray(runs) ||
    runs.some((item) => !isRecord(item)) ||
    !["SEALED", "NOT_RUN"].includes(entry.run_status) ||
    (entry.run_status === "SEALED" && !entry.latest_run_ref) ||
    (entry.run_status === "NOT_RUN" && entry.latest_run_ref !== null) ||
    (entry.run_status === "NOT_RUN" && entry.latest_outcome !== null) ||
    (entry.latest_outcome !== null && !OUTCOMES.includes(entry.latest_outcome)) ||
    (entry.run_status === "NOT_RUN" && runs.length !== 0) ||
    (entry.run_status === "SEALED" && runs.length < 1) ||
    new Set(runs.map((item) => item.run_ref)).size !== runs.length ||
    runs.some(
      (item) =>
        !item.run_ref ||
        item.experiment_ref !== entry.experiment_ref ||
        Number.isNaN(Date.parse(item.created_at)) ||
        !OUTCOMES.includes(item.outcome) ||
        !["PASS", "FAIL", "NOT_EVALUABLE"].includes(
          item.model_independence,
        ) ||
        ![
          "v60.mingli-synthetic-experiment-evaluator.001",
          "v60.mingli-synthetic-experiment-evaluator.002",
          "v60.mingli-synthetic-experiment-evaluator.003",
          "v60.mingli-synthetic-experiment-evaluator.004",
          "v60.mingli-synthetic-experiment-evaluator.005",
          "v60.mingli-synthetic-experiment-evaluator.006",
          "v60.mingli-synthetic-experiment-evaluator.007",
          "v60.mingli-synthetic-experiment-evaluator.008",
          "v60.mingli-synthetic-experiment-evaluator.009",
          "v60.mingli-synthetic-experiment-evaluator.010",
        ].includes(item.evaluator_version) ||
        ![
          "v60.mingli-synthetic-experiment-dev-gold.001",
          "v60.mingli-synthetic-experiment-dev-gold.002",
          "v60.mingli-synthetic-experiment-dev-gold.003",
          "v60.mingli-synthetic-experiment-dev-gold.004",
          "v60.mingli-synthetic-experiment-dev-gold.005",
          "v60.mingli-synthetic-experiment-dev-gold.006",
        ].includes(item.dev_gold_version) ||
        !["CURRENT", "SUPERSEDED"].includes(item.review_contract_status) ||
        !Number.isInteger(item.changed_pass_count) ||
        item.changed_pass_count < 0 ||
        !Number.isInteger(item.hold_pass_count) ||
        item.hold_pass_count < 0,
    ) ||
    runs.some(
      (item, index) =>
        index > 0 && item.created_at > runs[index - 1].created_at,
    ) ||
    (
      entry.run_status === "SEALED" &&
      (
        runs[0]?.run_ref !== entry.latest_run_ref ||
        runs[0]?.outcome !== entry.latest_outcome
      )
    )
  ) {
    throw new Error("mingli_synthetic_catalog_run_invalid");
  }
}

function validateDefinition(value: MingliSyntheticExperimentDefinition): void {
  if (
    ![
      "v60.mingli-synthetic-experiment-catalog.001",
      "v60.mingli-synthetic-experiment-catalog.002",
    ].includes(value.catalog_version) ||
    !value.experiment_ref ||
    !HASH.test(value.definition_hash) ||
    value.suite !== "DEV" ||
    ![
      "CONTROLLED_LEGAL_HOUR_PAIR",
      "CONTROLLED_ROOT_IDENTITY_PAIR",
      "CONTROLLED_HIDDEN_RANK_PRIMARY_SECONDARY_PAIR",
      "CONTROLLED_HIDDEN_RANK_SECONDARY_TERTIARY_PAIR",
      "CONTROLLED_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_PAIR",
      "CONTROLLED_REGIME_WORK_PATH_GENERALIZATION_PAIR",
      "CONTROLLED_DECISION_DISCIPLINE_GENERALIZATION_PAIR",
      "CONTROLLED_MONTH_COMMAND_REGIME_GENERALIZATION_PAIR",
    ].includes(value.family) ||
    !value.title ||
    !value.question ||
    value.blind_protocol !== "MEMBERS_INDEPENDENT_GOLD_NOT_IN_AGENT_PACKET" ||
    ![
      "WHOLE_HOUR_PILLAR_RESPONSE_NOT_ROOT_CAUSAL_ESTIMATE",
      "NATAL_ROOT_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL",
      "NATAL_HIDDEN_RANK_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL",
      "NATAL_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION",
      "WHOLE_CHART_DECISION_DISCIPLINE_WITH_FULL_HOUR_COLLATERAL",
      "MONTH_COMMAND_COORDINATE_AND_WHOLE_CHART_DISCIPLINE_WITH_FULL_HOUR_COLLATERAL",
    ].includes(value.inference_scope) ||
    !value.inference_limit ||
    !Array.isArray(value.known_collateral_deltas) ||
    value.known_collateral_deltas.length < 1 ||
    value.changed_input.field !== "birth_time" ||
    !value.changed_input.A ||
    !value.changed_input.B ||
    !Array.isArray(value.members) ||
    value.members.length !== 2 ||
    !Array.isArray(value.full_pillar_delta.A) ||
    !Array.isArray(value.full_pillar_delta.B) ||
    value.full_pillar_delta.A.length !== 4 ||
    value.full_pillar_delta.B.length !== 4
    || value.full_pillar_delta.changed_slots.join("") !== "hour"
    || !value.full_pillar_delta.legal_hour_pillar_change
  ) {
    throw new Error("mingli_synthetic_definition_invalid");
  }
  const variants = value.members.map((item) => item.variant).sort().join("");
  if (
    variants !== "AB" ||
    value.members.some(
      (item) =>
        !item.member_ref ||
        !item.subject_id.startsWith("research:") ||
        item.subject_id.length <= "research:".length,
    )
  ) {
    throw new Error("mingli_synthetic_member_identity_invalid");
  }
}

function validateEvaluation(
  value: MingliSyntheticExperimentSnapshot["evaluation"],
): void {
  if (
    ![
      "v60.mingli-synthetic-experiment-evaluator.001",
      "v60.mingli-synthetic-experiment-evaluator.002",
      "v60.mingli-synthetic-experiment-evaluator.003",
      "v60.mingli-synthetic-experiment-evaluator.004",
      "v60.mingli-synthetic-experiment-evaluator.005",
      "v60.mingli-synthetic-experiment-evaluator.006",
      "v60.mingli-synthetic-experiment-evaluator.007",
      "v60.mingli-synthetic-experiment-evaluator.008",
      "v60.mingli-synthetic-experiment-evaluator.009",
      "v60.mingli-synthetic-experiment-evaluator.010",
    ].includes(value.evaluator_version) ||
    ![
      "v60.mingli-synthetic-experiment-dev-gold.001",
      "v60.mingli-synthetic-experiment-dev-gold.002",
      "v60.mingli-synthetic-experiment-dev-gold.003",
      "v60.mingli-synthetic-experiment-dev-gold.004",
      "v60.mingli-synthetic-experiment-dev-gold.005",
      "v60.mingli-synthetic-experiment-dev-gold.006",
    ].includes(value.dev_gold_version) ||
    !HASH.test(value.dev_gold_hash) ||
    !OUTCOMES.includes(value.outcome) ||
    !Array.isArray(value.checks) ||
    value.checks.length < 1 ||
    value.checks.some(
      (item) =>
        !item.check_ref ||
        !GROUPS.includes(item.group) ||
        !["PASS", "FAIL"].includes(item.status) ||
        !item.statement,
    ) ||
    !isRecord(value.server_issue_keys) ||
    !Array.isArray(value.server_issue_keys.A) ||
    !Array.isArray(value.server_issue_keys.B) ||
    value.server_issue_keys.A.some((item) => typeof item !== "string") ||
    value.server_issue_keys.B.some((item) => typeof item !== "string") ||
    (
      value.raw_judgment_repair_variants !== undefined
      && (
        !Array.isArray(value.raw_judgment_repair_variants)
        || value.raw_judgment_repair_variants.some(
          (variant) => !["A", "B"].includes(variant),
        )
        || value.raw_judgment_repair_variants.join("")
          !== [...new Set(value.raw_judgment_repair_variants)].sort().join("")
      )
    ) ||
    value.qualification_effect !== "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION" ||
    !value.summary
  ) {
    throw new Error("mingli_synthetic_evaluation_invalid");
  }

  const changedPassCount = value.checks.filter(
    (item) => item.group === "EXPECTED_CHANGE" && item.status === "PASS",
  ).length;
  const holdPassCount = value.checks.filter(
    (item) => item.group === "MUST_HOLD" && item.status === "PASS",
  ).length;
  const driftChecks = value.checks
    .filter((item) => item.group === "MUST_HOLD" && item.status === "FAIL")
    .map((item) => item.check_ref);
  const validityFailed = value.checks.some(
    (item) =>
      (item.group === "EXPERIMENT_VALIDITY" || item.group === "MUST_HOLD")
      && item.status === "FAIL",
  );
  const expectedOutcome = validityFailed
    ? "INVALID_EXPERIMENT"
    : value.server_issue_keys.A.length || value.server_issue_keys.B.length
      ? "PRODUCT_SAFE_MODEL_FAIL"
      : value.checks.some(
          (item) => item.group === "EXPECTED_CHANGE" && item.status === "FAIL",
        )
        ? "MODEL_FAIL"
        : "PASS";
  if (
    value.changed_pass_count !== changedPassCount ||
    value.hold_pass_count !== holdPassCount ||
    !sameStrings(value.drift_checks, driftChecks) ||
    value.outcome !== expectedOutcome ||
    new Set(value.checks.map((item) => item.check_ref)).size !== value.checks.length
  ) {
    throw new Error("mingli_synthetic_evaluation_derived_values_invalid");
  }
}

function sameStrings(left: string[], right: string[]): boolean {
  return left.length === right.length
    && left.every((item, index) => item === right[index]);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
