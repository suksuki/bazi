import { request } from "./http";
import type {
  MingliNarrationReadyResponse,
  MingliStageMode,
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
} from "./mingliStageTypes";
import {
  validateNarrationReady,
  validateStageProjection,
  validateStageSubjects,
} from "./mingliStageValidation";

export async function loadMingliStageSubjects(
  signal?: AbortSignal,
): Promise<MingliStageSubject[]> {
  const value = await request<unknown>("/api/v60/mingli/stage/subjects", { signal });
  return validateStageSubjects(value);
}

export async function loadMingliStage(
  subjectId: MingliStageSubjectId,
  mode: MingliStageMode,
  year: number | null,
  signal?: AbortSignal,
): Promise<MingliStageProjection> {
  const parameters = new URLSearchParams({ subject_id: subjectId, mode });
  if (mode === "NATAL_DAYUN_YEAR_6" && year !== null) {
    parameters.set("year", String(year));
  }
  const value = await request<unknown>(`/api/v60/mingli/stage?${parameters}`, { signal });
  return validateStageProjection(value, { subjectId, mode, year });
}

export async function prepareMingliNarration(
  stage: MingliStageProjection,
  signal?: AbortSignal,
): Promise<MingliNarrationReadyResponse> {
  const value = await request<unknown>("/api/v60/mingli/narrations", {
    method: "POST",
    signal,
    body: JSON.stringify({
      request_version: "v60.mingli-narration-request.001",
      subject_id: stage.subject_id,
      stage_mode: stage.stage_mode,
      selected_year: stage.selected_year,
      expected_stage_projection_ref: stage.projection_ref,
      expected_stage_projection_hash: stage.projection_hash,
      cue_set_ref: "v60.mingli-stage-guide-cues.001",
    }),
  });
  return validateNarrationReady(value, stage);
}
