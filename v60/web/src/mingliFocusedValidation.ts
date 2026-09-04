import type {
  MingliFocusedPassRecord,
  MingliFocusedReading,
  MingliFocus,
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "./mingliStageTypes";

const HASH = /^[0-9a-f]{64}$/;

export const FOCUSED_PASS_ORDER: MingliFocus[] = [
  "STRUCTURE",
  "LIFE_IMAGE_PERSONALITY",
  "CAREER_WEALTH",
  "RELATIONSHIP_FAMILY",
  "TIMING",
];

export function focusedSummaryState(summary: MingliReadingSummaryProjection): {
  hasFocused: boolean;
  status: MingliReadingSummaryProjection["focused_status"];
} {
  const records = summary.focused_pass_records;
  const hasFocused = summary.focused_reading !== null
    || (Array.isArray(records) && records.length > 0);
  return {
    hasFocused,
    status: summary.focused_reading !== null
      || (Array.isArray(records) && records.length === FOCUSED_PASS_ORDER.length)
      ? "READY"
      : Array.isArray(records) && records.length > 0
        ? "PARTIAL"
        : "NOT_GENERATED",
  };
}

export function validateFocusedSummary(
  summary: MingliReadingSummaryProjection,
  stage: MingliStageProjection,
): void {
  if (summary.focused_reading !== null) {
    validateFocusedReading(summary.focused_reading, stage);
  }
  const records = summary.focused_pass_records.map((record) =>
    validateFocusedPassRecord(record, stage)
  );
  const focuses = records.map((record) => record.focus);
  const expectedOrder = FOCUSED_PASS_ORDER.filter((focus) => focuses.includes(focus));
  const structureHash = records.find(
    (record) => record.focus === "STRUCTURE",
  )?.pass_result.pass_hash ?? null;
  if (
    records.length > FOCUSED_PASS_ORDER.length
    || focuses.some((focus, index) => focus !== expectedOrder[index])
    || records.some((record) => (
      record.focus === "STRUCTURE"
        ? record.structure_pass_hash !== null
        : record.structure_pass_hash !== structureHash
    ))
  ) {
    throw new Error("mingli_reading_summary_focused_pass_order_invalid");
  }
}

export function validateFocusedReading(
  value: unknown,
  stage: MingliStageProjection,
): MingliFocusedReading {
  if (!isRecord(value) || !Array.isArray(value.passes)) {
    throw new Error("mingli_focused_reading_invalid");
  }
  const reading = value as unknown as MingliFocusedReading;
  const inputTokens = reading.passes.reduce(
    (total, item) => total + item.input_tokens,
    0,
  );
  const outputTokens = reading.passes.reduce(
    (total, item) => total + item.output_tokens,
    0,
  );
  const durationMs = reading.passes.reduce(
    (total, item) => total + item.duration_ms,
    0,
  );
  if (
    reading.focused_reading_version !== "v60.mingli-focused-reading.001"
    || reading.runtime_ref !== "v60.mingli-focused-runtime.001"
    || reading.prompt_version !== "v60.prompt.mingli-focused-reading.001"
    || !reading.focused_reading_ref
    || !HASH.test(reading.focused_reading_hash)
    || !HASH.test(reading.generation_key)
    || reading.case_ref !== stage.case_ref
    || reading.chart_version_ref !== stage.chart_version_ref
    || reading.life_case_revision_ref !== stage.life_case_revision_ref
    || reading.reading_ref !== stage.reading_ref
    || reading.reading_hash !== stage.reading_hash
    || !HASH.test(reading.packet_hash)
    || !HASH.test(reading.model_digest)
    || !HASH.test(reading.provider_profile_hash)
    || !HASH.test(reading.prompt_hash)
    || reading.passes.length !== FOCUSED_PASS_ORDER.length
    || reading.passes.some((item, index) => (
      !isRecord(item)
      || "raw_text" in item
      || item.pass_version !== "v60.mingli-focused-pass.001"
      || item.focus !== FOCUSED_PASS_ORDER[index]
      || !item.pass_ref
      || !HASH.test(item.pass_hash)
      || !HASH.test(item.context_hash)
      || !item.provider_response_ref
      || typeof item.question !== "string"
      || typeof item.normalized_text !== "string"
      || item.normalized_text.trim().length === 0
      || !Array.isArray(item.normalization_codes)
      || item.normalization_codes.some((code) => typeof code !== "string")
      || item.total_tokens !== item.input_tokens + item.output_tokens
      || item.duration_ms < 0
    ))
    || reading.input_tokens !== inputTokens
    || reading.output_tokens !== outputTokens
    || reading.total_tokens !== inputTokens + outputTokens
    || reading.duration_ms !== durationMs
    || reading.interpretation_status !== "FOCUSED_AGENT_INTERPRETATION"
    || reading.owner_review_status !== "NOT_REVIEWED"
    || reading.publication_allowed !== false
    || reading.canonical_fact_write_allowed !== false
    || reading.read_only !== true
  ) {
    throw new Error("mingli_focused_reading_shape_invalid");
  }
  return reading;
}

export function validateFocusedPassRecord(
  value: unknown,
  stage: MingliStageProjection,
): MingliFocusedPassRecord {
  if (!isRecord(value) || !isRecord(value.pass_result)) {
    throw new Error("mingli_focused_pass_record_invalid");
  }
  const record = value as unknown as MingliFocusedPassRecord;
  const result = record.pass_result;
  if (
    record.record_version !== "v60.mingli-focused-pass-record.001"
    || record.runtime_ref !== "v60.mingli-focused-runtime.001"
    || record.prompt_version !== "v60.prompt.mingli-focused-reading.001"
    || !record.record_ref
    || !HASH.test(record.record_hash)
    || !HASH.test(record.generation_key)
    || record.case_ref !== stage.case_ref
    || record.chart_version_ref !== stage.chart_version_ref
    || record.life_case_revision_ref !== stage.life_case_revision_ref
    || record.reading_ref !== stage.reading_ref
    || record.reading_hash !== stage.reading_hash
    || !HASH.test(record.packet_hash)
    || !HASH.test(record.model_digest)
    || !HASH.test(record.provider_profile_hash)
    || !HASH.test(record.prompt_hash)
    || !FOCUSED_PASS_ORDER.includes(record.focus)
    || (record.structure_pass_hash !== null
      && !HASH.test(record.structure_pass_hash))
    || "raw_text" in result
    || result.pass_version !== "v60.mingli-focused-pass.001"
    || result.focus !== record.focus
    || !result.pass_ref
    || !HASH.test(result.pass_hash)
    || !HASH.test(result.context_hash)
    || !result.provider_response_ref
    || typeof result.question !== "string"
    || typeof result.normalized_text !== "string"
    || result.normalized_text.trim().length === 0
    || !Array.isArray(result.normalization_codes)
    || result.normalization_codes.some((code) => typeof code !== "string")
    || result.total_tokens !== result.input_tokens + result.output_tokens
    || result.duration_ms < 0
    || record.interpretation_status !== "FOCUSED_AGENT_INTERPRETATION"
    || record.owner_review_status !== "NOT_REVIEWED"
    || record.publication_allowed !== false
    || record.canonical_fact_write_allowed !== false
    || record.read_only !== true
  ) {
    throw new Error("mingli_focused_pass_record_shape_invalid");
  }
  return record;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
