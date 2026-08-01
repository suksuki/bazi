import type {
  MingliAgentReading,
  MingliNarrationReadyResponse,
  MingliReadingSummaryProjection,
  MingliStageMode,
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
} from "./mingliStageTypes";

const HASH = /^[0-9a-f]{64}$/;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const STAGE_SLOTS = {
  NATAL_4: ["NATAL_YEAR", "NATAL_MONTH", "NATAL_DAY", "NATAL_HOUR"],
  NATAL_DAYUN_YEAR_6: [
    "NATAL_YEAR",
    "NATAL_MONTH",
    "NATAL_DAY",
    "NATAL_HOUR",
    "DAYUN",
    "ANNUAL",
  ],
} as const;

export function validateStageSubjects(value: unknown): MingliStageSubject[] {
  if (!Array.isArray(value) || value.length < 3) {
    throw new Error("mingli_stage_subjects_invalid");
  }
  const subjects = value as MingliStageSubject[];
  if (
    subjects.some(
      (item) =>
        !isStageSubjectId(item.subject_id) ||
        !item.display_name ||
        !["HUMAN_OWNER", "HUMAN_REFERENCE", "CANONICAL_SYNTHETIC"].includes(
          item.subject_kind,
        ),
    )
  ) {
    throw new Error("mingli_stage_subject_identity_invalid");
  }
  return subjects;
}

export function validateStageProjection(
  value: unknown,
  expected?: {
    subjectId: MingliStageSubjectId;
    mode: MingliStageMode;
    year: number | null;
  },
): MingliStageProjection {
  if (!isRecord(value)) throw new Error("mingli_stage_projection_invalid");
  const stage = value as unknown as MingliStageProjection;
  const slots = STAGE_SLOTS[stage.stage_mode];
  if (
    !slots ||
    (expected !== undefined && stage.subject_id !== expected.subjectId) ||
    (expected !== undefined && stage.stage_mode !== expected.mode) ||
    (expected?.year !== null &&
      expected?.year !== undefined &&
      stage.selected_year !== expected.year) ||
    !stageIdentityIsValid(stage) ||
    stage.projection_version !== "v60.mingli-stage-projection.003" ||
    !stage.projection_ref ||
    !HASH.test(stage.projection_hash) ||
    !Array.isArray(stage.source_refs) ||
    !stage.foundation_profile_ref ||
    !HASH.test(stage.foundation_profile_hash) ||
    !stage.source_refs.includes(stage.foundation_profile_ref) ||
    !stage.timing_profile_ref ||
    !HASH.test(stage.timing_profile_hash) ||
    !stage.source_refs.includes(stage.timing_profile_ref) ||
    !stage.source_refs.includes(stage.chart_version_ref) ||
    !stage.source_refs.includes(stage.life_case_revision_ref) ||
    (stage.reading_ref !== null && !stage.source_refs.includes(stage.reading_ref)) ||
    (stage.reading_ref === null
      ? stage.reading_hash !== null
      : !HASH.test(stage.reading_hash ?? "")) ||
    !ISO_DATE.test(stage.current_dayun_start_date) ||
    !ISO_DATE.test(stage.current_dayun_end_date) ||
    stage.current_dayun_start_date >= stage.current_dayun_end_date ||
    stage.dayun_boundary_precision !==
      "START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY" ||
    stage.dayun_calculation_policy !==
      "LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES" ||
    stage.dayun_resolution_status !== "RESOLVED_OUTSIDE_BOUNDARY_DAY" ||
    !Array.isArray(stage.columns) ||
    !Array.isArray(stage.bodies) ||
    !Array.isArray(stage.relations) ||
    !Array.isArray(stage.available_years) ||
    stage.columns.length !== slots.length ||
    stage.bodies.length !== slots.length * 2 ||
    stage.columns.some((column, index) => column.slot !== slots[index]) ||
    stage.columns.some((column) => column.source_layer === ("MONTHLY" as string)) ||
    stage.columns.some((column) =>
      column.source_layer === "DAYUN"
        ? !column.start_date ||
          !column.end_date ||
          !ISO_DATE.test(column.start_date) ||
          !ISO_DATE.test(column.end_date)
        : column.start_date !== undefined || column.end_date !== undefined,
    ) ||
    stage.columns.some(
      (column) =>
        column.source_layer === "DAYUN" &&
        (column.start_date !== stage.current_dayun_start_date ||
          column.end_date !== stage.current_dayun_end_date ||
          column.start_year !== stage.current_dayun_start_year ||
          column.end_year !== stage.current_dayun_end_year),
    ) ||
    stage.relation_effect_status !== "UNRESOLVED" ||
    stage.usable_source_status !== "UNRESOLVED" ||
    stage.professional_verdict_allowed !== false ||
    stage.relations.some(
      (relation) =>
        relation.effect_status !== "UNRESOLVED" ||
        relation.usable_source_status !== "UNRESOLVED" ||
        !HASH.test(relation.rule_hash),
    )
  ) {
    throw new Error("mingli_stage_projection_shape_invalid");
  }
  if (
    (stage.stage_mode === "NATAL_4" && stage.selected_year !== null) ||
    (stage.stage_mode === "NATAL_DAYUN_YEAR_6" && stage.selected_year === null)
  ) {
    throw new Error("mingli_stage_projection_time_state_invalid");
  }
  return stage;
}

export function validateReadingSummary(
  value: unknown,
  stage: MingliStageProjection,
): MingliReadingSummaryProjection {
  if (!isRecord(value) || !isRecord(value.reading_brief)) {
    throw new Error("mingli_reading_summary_invalid");
  }
  const summary = value as unknown as MingliReadingSummaryProjection;
  const lineage = summary.reading_brief.lineage;
  const agentReady = summary.agent_status === "READY";
  if (
    summary.summary_version !== "v60.mingli-reading-summary.002" ||
    !summary.summary_ref ||
    !HASH.test(summary.summary_hash) ||
    summary.case_ref !== stage.case_ref ||
    summary.chart_version_ref !== stage.chart_version_ref ||
    summary.life_case_revision_ref !== stage.life_case_revision_ref ||
    summary.reading_ref !== stage.reading_ref ||
    summary.reading_hash !== stage.reading_hash ||
    summary.subject_kind !== stage.subject_kind ||
    !["READY", "DISABLED", "MISCONFIGURED", "UNQUALIFIED"].includes(
      summary.agent_runtime_status,
    ) ||
    summary.agent_generation_available !== (summary.agent_runtime_status === "READY") ||
    !["READY", "NOT_GENERATED"].includes(summary.agent_status) ||
    summary.image_projection_status !== (
      agentReady ? "AGENT_INTERPRETATION" : "NOT_GENERATED"
    ) ||
    summary.professional_verdict_allowed !== false ||
    summary.canonical_write_allowed !== false ||
    summary.read_only !== true ||
    lineage.reading_ref !== summary.reading_ref ||
    lineage.reading_hash !== summary.reading_hash ||
    summary.reading_brief.qualification.status !== "FORMAL_BOUNDED_READING"
  ) {
    throw new Error("mingli_reading_summary_shape_invalid");
  }
  if (agentReady) {
    validateAgentReading(summary.agent_reading, stage);
  } else if (summary.agent_reading !== null) {
    throw new Error("mingli_reading_summary_agent_status_invalid");
  }
  return summary;
}

export function validateAgentReading(
  value: unknown,
  stage: MingliStageProjection,
): MingliAgentReading {
  if (!isRecord(value) || !isRecord(value.output)) {
    throw new Error("mingli_agent_reading_invalid");
  }
  const reading = value as unknown as MingliAgentReading;
  const output = reading.output;
  const selected = Array.isArray(output.hypotheses)
    ? output.hypotheses.filter(
        (item) => item.role === "PRIMARY",
      )
    : [];
  const domainOrder = [
    "personality",
    "career",
    "wealth",
    "relationship",
    "family",
  ] as const;
  const citedEvidence = [
    ...(Array.isArray(output.day_master_evidence_ids)
      ? output.day_master_evidence_ids
      : []),
    ...(Array.isArray(output.hypotheses)
      ? output.hypotheses.flatMap((item) => [
          ...item.mechanism_evidence_ids,
          ...item.evidence_ids,
        ])
      : []),
    ...(Array.isArray(output.work_path?.evidence_ids)
      ? output.work_path.evidence_ids
      : []),
    ...(Array.isArray(output.life_image?.evidence_ids)
      ? output.life_image.evidence_ids
      : []),
    ...domainOrder.flatMap((domain) => output.domains?.[domain]?.evidence_ids ?? []),
    ...(Array.isArray(output.timing?.natal_evidence_ids)
      ? output.timing.natal_evidence_ids
      : []),
    ...([output.timing?.dayun, output.timing?.annual].flatMap((item) => (
      item === undefined
        ? []
        : [item.coordinate_evidence_id, ...item.relation_evidence_ids, ...item.evidence_ids]
    ))),
  ];
  if (
    reading.agent_reading_version !== "v60.mingli-agent-reading.001" ||
    !reading.agent_reading_ref ||
    !HASH.test(reading.agent_reading_hash) ||
    !HASH.test(reading.generation_key) ||
    reading.case_ref !== stage.case_ref ||
    reading.chart_version_ref !== stage.chart_version_ref ||
    reading.life_case_revision_ref !== stage.life_case_revision_ref ||
    reading.reading_ref !== stage.reading_ref ||
    reading.reading_hash !== stage.reading_hash ||
    !HASH.test(reading.packet_hash) ||
    !HASH.test(reading.agent_profile_hash) ||
    !HASH.test(reading.model_digest) ||
    !HASH.test(reading.provider_profile_hash) ||
    !HASH.test(reading.prompt_hash) ||
    reading.interpretation_status !== "AGENT_INTERPRETATION" ||
    reading.owner_review_status !== "NOT_REVIEWED" ||
    reading.canonical_fact_write_allowed !== false ||
    reading.read_only !== true ||
    reading.total_tokens !== reading.input_tokens + reading.output_tokens ||
    typeof output.first_look !== "string" ||
    typeof output.whole_chart_thesis !== "string" ||
    !isRecord(output.support_selection) ||
    typeof output.day_master_rationale !== "string" ||
    !Array.isArray(output.hypotheses) ||
    output.hypotheses.length !== 2 ||
    selected.length !== 1 ||
    !isRecord(output.work_path) ||
    !isRecord(output.life_image) ||
    !isRecord(output.domains) ||
    domainOrder.some((domain) => !isRecord(output.domains[domain])) ||
    !isRecord(output.timing) ||
    !isRecord(output.timing.dayun) ||
    !isRecord(output.timing.annual) ||
    citedEvidence.some((item) => !/^E\d{3}$/.test(item))
  ) {
    throw new Error("mingli_agent_reading_shape_invalid");
  }
  return reading;
}

function isStageSubjectId(value: unknown): value is string {
  return typeof value === "string" && (
    ["current", "abu", "duoduo"].includes(value) ||
    (value.startsWith("case:") && value.length > "case:".length)
  );
}

function stageIdentityIsValid(stage: MingliStageProjection) {
  if (stage.subject_id === "current") {
    return stage.subject_kind === "HUMAN_OWNER" && stage.privacy_scope === "PRIVATE_OWNER";
  }
  if (stage.subject_id.startsWith("case:")) {
    return (
      (stage.subject_kind === "HUMAN_OWNER" && stage.privacy_scope === "PRIVATE_OWNER") ||
      (stage.subject_kind === "HUMAN_REFERENCE" && stage.privacy_scope === "PRIVATE_REFERENCE")
    );
  }
  return (
    ["abu", "duoduo"].includes(stage.subject_id) &&
    stage.subject_kind === "CANONICAL_SYNTHETIC" &&
    stage.privacy_scope === "PUBLIC_SYNTHETIC_SHOWCASE"
  );
}

export function validateNarrationReady(
  value: unknown,
  stage: MingliStageProjection,
): MingliNarrationReadyResponse {
  if (!isRecord(value) || !isRecord(value.asset) || typeof value.audio_url !== "string") {
    throw new Error("mingli_narration_response_invalid");
  }
  const response = value as unknown as MingliNarrationReadyResponse;
  const asset = response.asset;
  if (
    !response.audio_url.startsWith("/api/v60/mingli/narrations/") ||
    asset.narration_version !== "v60.mingli-narration.002" ||
    asset.stage_projection_ref !== stage.projection_ref ||
    asset.stage_projection_hash !== stage.projection_hash ||
    asset.case_ref !== stage.case_ref ||
    asset.reading_ref !== stage.reading_ref ||
    asset.actor_ref !== stage.narrator_actor_id ||
    asset.preparation_status !== "READY" ||
    asset.clock_source !== "HTML_AUDIO_CURRENT_TIME" ||
    asset.upstream_exposed_to_client !== false ||
    !HASH.test(asset.narration_hash) ||
    !HASH.test(asset.audio_sha256) ||
    asset.provider_profile_ref !== "v60.qwen3-tts-proxy.001" ||
    !HASH.test(asset.provider_profile_hash) ||
    !["dblife-public-proxy", "dblife-server13-private-upstream"].includes(
      asset.provider_deployment_ref,
    ) ||
    !Array.isArray(asset.cues) ||
    asset.cues.length !== 4 ||
    asset.cues[0]?.start_ms !== 0 ||
    asset.cues.at(-1)?.end_ms !== asset.duration_ms ||
    asset.cues.some(
      (cue, index) =>
        cue.end_ms <= cue.start_ms ||
        (index > 0 && asset.cues[index - 1]?.end_ms !== cue.start_ms),
    )
  ) {
    throw new Error("mingli_narration_response_binding_invalid");
  }
  return response;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
