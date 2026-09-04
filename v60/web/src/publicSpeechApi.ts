import type { MingliFocusedPassRecord, MingliStageProjection } from "./mingliStageTypes";

const FOCUSED_SPEECH_TIMELINE_HEADER = "X-Abu-Focused-Speech-Timeline";
const FOCUSED_SPEECH_TIMELINE_VERSION = "v60.mingli-focused-speech-timeline.001";

export interface MingliFocusedSpeechCue {
  cueIndex: number;
  text: string;
  startMs: number;
  endMs: number;
}

export interface MingliFocusedSpeechAsset {
  blob: Blob;
  cues: MingliFocusedSpeechCue[];
  durationMs: number;
}

export async function loadFocusedPassSpeech(
  stage: MingliStageProjection,
  record: MingliFocusedPassRecord,
  signal?: AbortSignal,
): Promise<MingliFocusedSpeechAsset> {
  const response = await fetch("/api/v60/mingli/narrations/focused-pass", {
    method: "POST",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "audio/wav",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      request_version: "v60.mingli-focused-speech-request.001",
      subject_id: stage.subject_id,
      stage_mode: stage.stage_mode,
      selected_year: stage.selected_year,
      expected_stage_projection_ref: stage.projection_ref,
      expected_stage_projection_hash: stage.projection_hash,
      record_ref: record.record_ref,
      expected_record_hash: record.record_hash,
    }),
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(detail?.detail ?? `focused_speech_failed:${response.status}`);
  }
  const blob = await response.blob();
  const timeline = parseFocusedSpeechTimeline(
    response.headers.get(FOCUSED_SPEECH_TIMELINE_HEADER),
  );
  return { blob, ...timeline };
}

function parseFocusedSpeechTimeline(value: string | null): {
  cues: MingliFocusedSpeechCue[];
  durationMs: number;
} {
  if (!value) throw new Error("focused_speech_timeline_missing");
  const padded = value.replace(/-/g, "+").replace(/_/g, "/")
    .padEnd(Math.ceil(value.length / 4) * 4, "=");
  let payload: unknown;
  try {
    const bytes = Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
    payload = JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    throw new Error("focused_speech_timeline_invalid");
  }
  if (!isRecord(payload)
    || payload.timeline_version !== FOCUSED_SPEECH_TIMELINE_VERSION
    || !Number.isInteger(payload.duration_ms)
    || Number(payload.duration_ms) <= 0
    || !Array.isArray(payload.cues)
    || payload.cues.length === 0
    || payload.cues.length > 64) {
    throw new Error("focused_speech_timeline_invalid");
  }
  const durationMs = Number(payload.duration_ms);
  let expectedStartMs = 0;
  const cues = payload.cues.map((candidate, cueIndex) => {
    if (!isRecord(candidate)
      || candidate.cue_index !== cueIndex
      || typeof candidate.text !== "string"
      || !candidate.text.trim()
      || !Number.isInteger(candidate.start_ms)
      || !Number.isInteger(candidate.end_ms)) {
      throw new Error("focused_speech_timeline_invalid");
    }
    const startMs = Number(candidate.start_ms);
    const endMs = Number(candidate.end_ms);
    if (startMs !== expectedStartMs || endMs <= startMs || endMs > durationMs) {
      throw new Error("focused_speech_timeline_invalid");
    }
    expectedStartMs = endMs;
    return {
      cueIndex,
      text: candidate.text,
      startMs,
      endMs,
    };
  });
  if (expectedStartMs !== durationMs) {
    throw new Error("focused_speech_timeline_invalid");
  }
  return { cues, durationMs };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
