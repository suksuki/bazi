import type { MingliSyntheticOutcome } from "./mingliSyntheticLabTypes";
import type {
  MingliSyntheticSuiteCatalog,
  MingliSyntheticSuiteCatalogEntry,
  MingliSyntheticSuiteCandidateIdentity,
  MingliSyntheticSuiteErrorCluster,
  MingliSyntheticSuiteRun,
  MingliSyntheticSuiteRunItem,
} from "./mingliSyntheticSuiteTypes";

const HASH = /^[0-9a-f]{64}$/;
const OUTCOMES: MingliSyntheticOutcome[] = [
  "PASS",
  "PRODUCT_SAFE_MODEL_FAIL",
  "MODEL_FAIL",
  "INVALID_EXPERIMENT",
];
const EXECUTION_STATUSES = ["SEALED", "ERROR"] as const;
const MODEL_RESULTS = ["PASS", "FAIL", "NOT_EVALUABLE"] as const;
const REVIEW_CONTRACTS = ["CURRENT", "SUPERSEDED"] as const;
const EVALUATOR_VERSIONS = [
  "v60.mingli-synthetic-experiment-evaluator.001",
  "v60.mingli-synthetic-experiment-evaluator.002",
  "v60.mingli-synthetic-experiment-evaluator.003",
  "v60.mingli-synthetic-experiment-evaluator.004",
  "v60.mingli-synthetic-experiment-evaluator.005",
] as const;
const GOLD_VERSIONS = [
  "v60.mingli-synthetic-experiment-dev-gold.001",
  "v60.mingli-synthetic-experiment-dev-gold.002",
  "v60.mingli-synthetic-experiment-dev-gold.003",
  "v60.mingli-synthetic-experiment-dev-gold.004",
] as const;

export function validateSyntheticSuiteCatalog(
  value: unknown,
): MingliSyntheticSuiteCatalog {
  if (!isRecord(value) || !Array.isArray(value.modes) || !Array.isArray(value.suites)) {
    throw new Error("mingli_synthetic_suite_catalog_invalid");
  }
  const catalog = value as unknown as MingliSyntheticSuiteCatalog;
  if (
    catalog.catalog_version !== "v60.mingli-synthetic-suite-catalog.001"
    || catalog.browser_generation_allowed !== false
    || catalog.read_only !== true
    || catalog.suites.length < 1
  ) {
    throw new Error("mingli_synthetic_suite_catalog_shape_invalid");
  }
  const modes = new Map(catalog.modes.map((item) => [item.mode, item]));
  if (
    modes.size !== 3
    || modes.get("DEV")?.availability !== "ACTIVE"
    || modes.get("QUALIFICATION")?.availability !== "LOCKED_OWNER_GATE"
    || modes.get("HOLDOUT")?.availability !== "LOCKED_OWNER_GATE"
    || catalog.modes.some((item) => !item.description)
  ) {
    throw new Error("mingli_synthetic_suite_modes_invalid");
  }
  catalog.suites.forEach(validateSuite);
  if (new Set(catalog.suites.map((item) => item.suite_ref)).size !== catalog.suites.length) {
    throw new Error("mingli_synthetic_suite_duplicate");
  }
  return catalog;
}

function validateSuite(suite: MingliSyntheticSuiteCatalogEntry): void {
  if (
    suite.suite_definition_version !== "v60.mingli-synthetic-suite-definition.001"
    || !suite.suite_ref
    || !HASH.test(suite.suite_definition_hash)
    || suite.mode !== "DEV"
    || suite.availability !== "ACTIVE"
    || !suite.title
    || !suite.question
    || !suite.inference_limit
    || suite.execution_policy !== "SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL"
    || !Array.isArray(suite.experiment_refs)
    || suite.experiment_refs.length < 1
    || new Set(suite.experiment_refs).size !== suite.experiment_refs.length
    || !Array.isArray(suite.experiment_definition_hashes)
    || suite.experiment_definition_hashes.length !== suite.experiment_refs.length
    || !Array.isArray(suite.runs)
    || !["SEALED", "NOT_RUN"].includes(suite.run_status)
  ) {
    throw new Error("mingli_synthetic_suite_definition_invalid");
  }
  suite.experiment_definition_hashes.forEach((binding, index) => {
    if (
      binding.experiment_ref !== suite.experiment_refs[index]
      || !HASH.test(binding.definition_hash)
    ) {
      throw new Error("mingli_synthetic_suite_definition_binding_invalid");
    }
  });
  suite.runs.forEach((run) => validateRun(suite, run));
  if (
    new Set(suite.runs.map((item) => item.suite_run_ref)).size !== suite.runs.length
    || (suite.run_status === "NOT_RUN" && (suite.latest_suite_run_ref !== null || suite.runs.length))
    || (suite.run_status === "SEALED" && suite.runs[0]?.suite_run_ref !== suite.latest_suite_run_ref)
    || suite.runs.some((run, index) => index > 0 && run.created_at > suite.runs[index - 1].created_at)
  ) {
    throw new Error("mingli_synthetic_suite_history_invalid");
  }
}

function validateRun(
  suite: MingliSyntheticSuiteCatalogEntry,
  run: MingliSyntheticSuiteRun,
): void {
  if (
    ![
      "v60.mingli-synthetic-suite-run.001",
      "v60.mingli-synthetic-suite-run.002",
    ].includes(run.suite_run_version)
    || ![
      "v60.mingli-synthetic-suite-runner.001",
      "v60.mingli-synthetic-suite-runner.002",
    ].includes(run.runner_version)
    || run.suite_ref !== suite.suite_ref
    || run.suite_definition_hash !== suite.suite_definition_hash
    || run.suite_mode !== "DEV"
    || !run.suite_run_ref
    || !HASH.test(run.suite_run_hash)
    || Number.isNaN(Date.parse(run.created_at))
    || !Array.isArray(run.items)
    || run.items.length !== suite.experiment_refs.length
    || !Array.isArray(run.error_clusters)
    || !isRecord(run.current_review_projection)
    || !isRecord(run.counts)
    || !isRecord(run.outcomes)
    || !["COMPLETED", "COMPLETED_WITH_ERRORS"].includes(run.status)
    || run.qualification_effect !== "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION"
  ) {
    throw new Error("mingli_synthetic_suite_run_invalid");
  }
  run.items.forEach((item, index) => validateItem(suite, item, index));
  const sealed = run.items.filter((item) => item.execution_status === "SEALED").length;
  const reviewRequired = run.items.filter((item) => item.review_required).length;
  const expectedOutcomes = Object.fromEntries(
    OUTCOMES.map((outcome) => [
      outcome,
      run.items.filter((item) => item.outcome === outcome).length,
    ]),
  ) as Record<MingliSyntheticOutcome, number>;
  if (
    !sameKeys(run.counts, ["experiments", "sealed", "runner_errors", "review_required"])
    || !sameKeys(run.outcomes, OUTCOMES)
    || Object.values(run.counts).some((value) => !isNonnegativeInteger(value))
    || Object.values(run.outcomes).some((value) => !isNonnegativeInteger(value))
    || run.counts.experiments < 1
    || run.counts.experiments !== run.items.length
    || run.counts.sealed !== sealed
    || run.counts.runner_errors !== run.items.length - sealed
    || run.counts.review_required !== reviewRequired
    || run.status !== (sealed === run.items.length ? "COMPLETED" : "COMPLETED_WITH_ERRORS")
    || OUTCOMES.some((outcome) => run.outcomes[outcome] !== expectedOutcomes[outcome])
    || (
      run.suite_run_version === "v60.mingli-synthetic-suite-run.001"
        ? Boolean(run.candidate_identity) !== (sealed > 0)
        : !run.candidate_identity
    )
  ) {
    throw new Error("mingli_synthetic_suite_run_counts_invalid");
  }
  if (run.candidate_identity) validateCandidate(run.candidate_identity);
  if (
    run.suite_run_version === "v60.mingli-synthetic-suite-run.002"
    && !run.candidate_identity?.agent_reading_version
  ) {
    throw new Error("mingli_synthetic_suite_attempted_candidate_invalid");
  }
  validateClusters(run.items, run.error_clusters);
  validateCurrentReviewProjection(suite, run);
}

function validateCurrentReviewProjection(
  suite: MingliSyntheticSuiteCatalogEntry,
  run: MingliSyntheticSuiteRun,
): void {
  const projection = run.current_review_projection;
  if (
    projection.projection_version
      !== "v60.mingli-synthetic-suite-review-projection.001"
    || !HASH.test(projection.projection_hash)
    || projection.source_suite_run_ref !== run.suite_run_ref
    || projection.source_suite_run_hash !== run.suite_run_hash
    || !Array.isArray(projection.items)
    || projection.items.length !== run.items.length
    || !isRecord(projection.counts)
    || !Array.isArray(projection.error_clusters)
  ) {
    throw new Error("mingli_synthetic_suite_review_projection_invalid");
  }
  projection.items.forEach((item, index) => validateItem(suite, item, index));
  const sealed = projection.items.filter((item) => item.execution_status === "SEALED").length;
  const reviewRequired = projection.items.filter((item) => item.review_required).length;
  if (
    !sameKeys(projection.counts, [
      "experiments",
      "sealed",
      "runner_errors",
      "review_required",
    ])
    || Object.values(projection.counts).some((value) => !isNonnegativeInteger(value))
    || projection.counts.experiments !== projection.items.length
    || projection.counts.sealed !== sealed
    || projection.counts.runner_errors !== projection.items.length - sealed
    || projection.counts.review_required !== reviewRequired
    || projection.items.some((item, index) =>
      !sameReviewInvariant(run.items[index], item)
      || !validReviewTransition(run.items[index], item)
    )
  ) {
    throw new Error("mingli_synthetic_suite_review_projection_counts_invalid");
  }
  validateClusters(projection.items, projection.error_clusters);
}

function sameReviewInvariant(
  sealed: MingliSyntheticSuiteRunItem | undefined,
  projected: MingliSyntheticSuiteRunItem,
): boolean {
  if (!sealed) return false;
  return sealed.position === projected.position
    && sealed.experiment_ref === projected.experiment_ref
    && sealed.definition_hash === projected.definition_hash
    && sealed.execution_status === projected.execution_status
    && sealed.experiment_run_ref === projected.experiment_run_ref
    && sealed.experiment_run_hash === projected.experiment_run_hash
    && sealed.outcome === projected.outcome
    && sealed.evaluator_version === projected.evaluator_version
    && sealed.dev_gold_version === projected.dev_gold_version
    && sealed.dev_gold_hash === projected.dev_gold_hash
    && sealed.model_independence === projected.model_independence
    && sealed.changed_pass_count === projected.changed_pass_count
    && sealed.hold_pass_count === projected.hold_pass_count
    && JSON.stringify(sealed.variant_reviews) === JSON.stringify(projected.variant_reviews)
    && sealed.error_code === projected.error_code;
}

function validReviewTransition(
  sealed: MingliSyntheticSuiteRunItem | undefined,
  projected: MingliSyntheticSuiteRunItem,
): boolean {
  if (!sealed) return false;
  if (sealed.execution_status === "ERROR") {
    return sealed.review_contract_status === projected.review_contract_status
      && sealed.review_required === projected.review_required
      && JSON.stringify(sealed.review_reason_keys) === JSON.stringify(projected.review_reason_keys);
  }
  const added = projected.review_reason_keys.filter(
    (reason) => !sealed.review_reason_keys.includes(reason),
  );
  return sealed.review_reason_keys.every((reason) =>
    projected.review_reason_keys.includes(reason)
  )
    && added.every((reason) => reason === "REVIEW_CONTRACT:SUPERSEDED")
    && (
      sealed.review_contract_status === projected.review_contract_status
      || (
        sealed.review_contract_status === "CURRENT"
        && projected.review_contract_status === "SUPERSEDED"
        && added.includes("REVIEW_CONTRACT:SUPERSEDED")
      )
    );
}

function validateItem(
  suite: MingliSyntheticSuiteCatalogEntry,
  item: MingliSyntheticSuiteRunItem,
  index: number,
): void {
  const binding = suite.experiment_definition_hashes[index];
  if (
    item.position !== index + 1
    || item.experiment_ref !== suite.experiment_refs[index]
    || item.definition_hash !== binding?.definition_hash
    || !EXECUTION_STATUSES.includes(item.execution_status)
    || !Array.isArray(item.review_reason_keys)
    || !Array.isArray(item.variant_reviews)
    || item.review_reason_keys.some((key) => typeof key !== "string" || !key)
    || item.variant_reviews.some((review) =>
      !isRecord(review)
        || !["A", "B"].includes(review.variant as string)
        || !Array.isArray(review.reason_keys)
        || review.reason_keys.some((key) => typeof key !== "string" || !key)
        || new Set(review.reason_keys).size !== review.reason_keys.length
        || review.reason_keys.some(
          (key, keyIndex) => keyIndex > 0 && key < review.reason_keys[keyIndex - 1],
        )
    )
    || new Set(item.review_reason_keys).size !== item.review_reason_keys.length
    || item.review_reason_keys.some((key, keyIndex) => keyIndex > 0 && key < item.review_reason_keys[keyIndex - 1])
    || item.review_required !== (item.review_reason_keys.length > 0)
  ) {
    throw new Error("mingli_synthetic_suite_item_invalid");
  }
  if (item.execution_status === "ERROR") {
    if (
      !item.error_code
      || !/^[A-Z0-9_]+$/.test(item.error_code)
      || item.experiment_run_ref !== null
      || item.experiment_run_hash !== null
      || item.outcome !== null
      || item.evaluator_version !== null
      || item.dev_gold_version !== null
      || item.dev_gold_hash !== null
      || item.model_independence !== null
      || item.changed_pass_count !== null
      || item.hold_pass_count !== null
      || item.review_contract_status !== null
      || item.variant_reviews.length
      || item.review_reason_keys.length !== 1
      || item.review_reason_keys[0] !== `RUNNER_ERROR:${item.error_code}`
    ) {
      throw new Error("mingli_synthetic_suite_error_item_invalid");
    }
    return;
  }
  if (
    !item.experiment_run_ref
    || !HASH.test(item.experiment_run_hash ?? "")
    || !OUTCOMES.includes(item.outcome as MingliSyntheticOutcome)
    || !EVALUATOR_VERSIONS.includes(item.evaluator_version as never)
    || !GOLD_VERSIONS.includes(item.dev_gold_version as never)
    || !HASH.test(item.dev_gold_hash ?? "")
    || !MODEL_RESULTS.includes(item.model_independence as never)
    || !Number.isInteger(item.changed_pass_count)
    || (item.changed_pass_count ?? -1) < 0
    || !Number.isInteger(item.hold_pass_count)
    || (item.hold_pass_count ?? -1) < 0
    || !REVIEW_CONTRACTS.includes(item.review_contract_status as never)
    || item.error_code !== null
    || item.variant_reviews.map((review) => review.variant).join("") !== "AB"
    || item.variant_reviews.some((review) =>
      review.reason_keys.some((reason) => !reason.startsWith("SERVER_REPAIR:"))
    )
  ) {
    throw new Error("mingli_synthetic_suite_sealed_item_invalid");
  }
}

function validateCandidate(candidate: MingliSyntheticSuiteCandidateIdentity): void {
  const hashKeys = [
    "agent_profile_hash",
    "model_digest",
    "provider_profile_hash",
    "prompt_hash",
  ] as const;
  const valueKeys = [
    "agent_profile_ref",
    "provider_id",
    "model_ref",
    "provider_profile_ref",
    "prompt_ref",
  ] as const;
  if (
    hashKeys.some((key) => !HASH.test(candidate[key] ?? ""))
    || valueKeys.some((key) => !candidate[key])
    || (candidate.agent_reading_version !== undefined && !candidate.agent_reading_version)
  ) {
    throw new Error("mingli_synthetic_suite_candidate_invalid");
  }
}

function validateClusters(
  items: MingliSyntheticSuiteRunItem[],
  clusters: MingliSyntheticSuiteErrorCluster[],
): void {
  const expected = deriveClusterMembers(items);
  if (
    clusters.length !== expected.size
    || new Set(clusters.map((item) => item.key)).size !== clusters.length
    || clusters.some((cluster) => {
      const member = expected.get(cluster.key);
      return !member
        || !cluster.label
        || cluster.kind !== clusterKind(cluster.key)
        || cluster.occurrence_count !== member.occurrences.size
        || cluster.experiment_count !== member.experiments.size
        || cluster.member_occurrences.join("|") !== [...member.occurrences].sort().join("|")
        || cluster.experiment_refs.join("|") !== [...member.experiments].sort().join("|");
    })
  ) {
    throw new Error("mingli_synthetic_suite_clusters_invalid");
  }
}

function deriveClusterMembers(items: MingliSyntheticSuiteRunItem[]) {
  const result = new Map<string, { occurrences: Set<string>; experiments: Set<string> }>();
  const add = (reason: string, experimentRef: string, occurrence: string) => {
    const entry = result.get(reason) ?? { occurrences: new Set(), experiments: new Set() };
    entry.occurrences.add(occurrence);
    entry.experiments.add(experimentRef);
    result.set(reason, entry);
  };
  items.forEach((item) => {
    const variantReasons = new Set<string>();
    item.variant_reviews.forEach((review) => review.reason_keys.forEach((reason) => {
      variantReasons.add(reason);
      add(reason, item.experiment_ref, `${item.experiment_ref}:${review.variant}`);
    }));
    item.review_reason_keys.forEach((reason) => {
      if (!variantReasons.has(reason)) add(reason, item.experiment_ref, `${item.experiment_ref}:PAIR`);
    });
  });
  return result;
}

function clusterKind(reason: string): MingliSyntheticSuiteErrorCluster["kind"] {
  if (reason.startsWith("SERVER_REPAIR:")) return "SERVER_REPAIR";
  if (reason.startsWith("CHECK_FAIL:EXPECTED_CHANGE:")) return "EXPECTED_CHECK_FAIL";
  if (reason.startsWith("CHECK_FAIL:")) return "EXPERIMENT_INVALID";
  if (reason === "REVIEW_CONTRACT:SUPERSEDED") return "CONTRACT_SUPERSEDED";
  return "RUNNER_ERROR";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function sameKeys(value: object, expected: readonly string[]): boolean {
  return Object.keys(value).sort().join("|") === [...expected].sort().join("|");
}

function isNonnegativeInteger(value: unknown): boolean {
  return Number.isInteger(value) && Number(value) >= 0;
}
