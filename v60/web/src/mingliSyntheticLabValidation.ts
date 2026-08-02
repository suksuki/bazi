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

export function validateSyntheticExperimentCatalog(
  value: unknown,
): MingliSyntheticExperimentCatalog {
  if (!isRecord(value) || !Array.isArray(value.experiments)) {
    throw new Error("mingli_synthetic_catalog_invalid");
  }
  const catalog = value as unknown as MingliSyntheticExperimentCatalog;
  if (
    catalog.catalog_version !== "v60.mingli-synthetic-experiment-catalog.001" ||
    catalog.browser_generation_allowed !== false ||
    catalog.read_only !== true ||
    catalog.experiments.length < 1
  ) {
    throw new Error("mingli_synthetic_catalog_shape_invalid");
  }
  catalog.experiments.forEach(validateCatalogEntry);
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
  if (!isRecord(value) || !isRecord(value.evaluation) || !isRecord(value.definition)) {
    throw new Error("mingli_synthetic_snapshot_invalid");
  }
  const snapshot = value as unknown as MingliSyntheticExperimentSnapshot;
  const member = snapshot.definition.members.find(
    (item) => item.variant === expected.variant,
  );
  if (
    snapshot.snapshot_version !== "v60.mingli-synthetic-experiment-snapshot.001" ||
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

function validateCatalogEntry(value: unknown): void {
  if (!isRecord(value)) throw new Error("mingli_synthetic_catalog_entry_invalid");
  const entry = value as unknown as MingliSyntheticExperimentCatalogEntry;
  validateDefinition(entry);
  if (
    !["SEALED", "NOT_RUN"].includes(entry.run_status) ||
    (entry.run_status === "SEALED" && !entry.latest_run_ref) ||
    (entry.run_status === "NOT_RUN" && entry.latest_run_ref !== null) ||
    (entry.run_status === "NOT_RUN" && entry.latest_outcome !== null) ||
    (entry.latest_outcome !== null && !OUTCOMES.includes(entry.latest_outcome))
  ) {
    throw new Error("mingli_synthetic_catalog_run_invalid");
  }
}

function validateDefinition(value: MingliSyntheticExperimentDefinition): void {
  if (
    value.catalog_version !== "v60.mingli-synthetic-experiment-catalog.001" ||
    !value.experiment_ref ||
    !HASH.test(value.definition_hash) ||
    value.suite !== "DEV" ||
    value.family !== "CONTROLLED_LEGAL_HOUR_PAIR" ||
    !value.title ||
    !value.question ||
    !value.inference_limit ||
    !Array.isArray(value.known_collateral_deltas) ||
    value.known_collateral_deltas.length < 1 ||
    value.changed_input.field !== "birth_time" ||
    !Array.isArray(value.members) ||
    value.members.length !== 2 ||
    !Array.isArray(value.full_pillar_delta.A) ||
    !Array.isArray(value.full_pillar_delta.B) ||
    value.full_pillar_delta.A.length !== 4 ||
    value.full_pillar_delta.B.length !== 4
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
    value.evaluator_version !== "v60.mingli-synthetic-experiment-evaluator.001" ||
    value.dev_gold_version !== "v60.mingli-synthetic-experiment-dev-gold.001" ||
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
