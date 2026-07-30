import type { DreamSnapshot } from "./api";
import type {
  DreamLifeDomain,
  DreamPersonalCheckInStatus,
  DreamPersonalJourney,
} from "./dreamPersonalJourneyTypes";
import { isDreamPersonalJourneyDisplayable } from "./dreamPersonalJourneyTypes";
import { request } from "./http";

const DREAM_LIFE_DOMAINS: readonly DreamLifeDomain[] = [
  "career",
  "wealth",
  "relationship",
];
const DREAM_CHECKIN_STATUSES: readonly DreamPersonalCheckInStatus[] = [
  "OBSERVED",
  "NOT_OBSERVED",
  "STILL_OBSERVING",
];

function idempotencyKey(kind: string): string {
  return [
    "v60-dream-personal-journey",
    kind,
    crypto.randomUUID(),
  ].join(":");
}

function normalizePrivateText(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

export function startDreamPersonalJourney(
  candidateRef: string,
  domain: DreamLifeDomain,
  question: string,
): Promise<DreamSnapshot> {
  const normalizedQuestion = normalizePrivateText(question);
  if (
    !candidateRef ||
    !DREAM_LIFE_DOMAINS.includes(domain) ||
    normalizedQuestion.length < 4 ||
    normalizedQuestion.length > 120
  ) {
    return Promise.reject(
      new Error("dream_private_inquiry_request_invalid"),
    );
  }
  return request(
    `/api/v60/dream/grove/${encodeURIComponent(candidateRef)}/personal-inquiry`,
    {
      method: "POST",
      body: JSON.stringify({
        domain,
        question: normalizedQuestion,
        idempotency_key: idempotencyKey("inquiry"),
      }),
    },
  );
}

export function selectDreamPersonalObservation(
  journey: DreamPersonalJourney,
  optionRef: string,
): Promise<DreamPersonalJourney> {
  if (!isDreamPersonalJourneyDisplayable(journey)) {
    return Promise.reject(
      new Error("dream_personal_journey_not_displayable"),
    );
  }
  if (
    journey.status !== "AWAITING_OBSERVATION" ||
    !journey.observation_options.some(
      (option) => option.option_ref === optionRef,
    )
  ) {
    return Promise.reject(
      new Error("dream_personal_observation_option_not_server_issued"),
    );
  }
  return request("/api/v60/dream/personal-observation", {
    method: "POST",
    body: JSON.stringify({
      inquiry_ref: journey.inquiry.inquiry_ref,
      inquiry_hash: journey.inquiry.inquiry_hash,
      option_ref: optionRef,
      idempotency_key: idempotencyKey("observation"),
    }),
  });
}

export function recordDreamPersonalCheckIn(
  journey: DreamPersonalJourney,
  status: DreamPersonalCheckInStatus,
  note: string,
): Promise<DreamPersonalJourney> {
  if (!isDreamPersonalJourneyDisplayable(journey)) {
    return Promise.reject(
      new Error("dream_personal_journey_not_displayable"),
    );
  }
  if (!journey.observation) {
    return Promise.reject(
      new Error("dream_personal_observation_required"),
    );
  }
  const normalizedNote = normalizePrivateText(note);
  if (
    !DREAM_CHECKIN_STATUSES.includes(status) ||
    normalizedNote.length > 160
  ) {
    return Promise.reject(
      new Error("dream_personal_checkin_request_invalid"),
    );
  }
  return request("/api/v60/dream/personal-check-in", {
    method: "POST",
    body: JSON.stringify({
      task_ref: journey.observation.task_ref,
      task_hash: journey.observation.task_hash,
      status,
      note: normalizedNote || null,
      idempotency_key: idempotencyKey("check-in"),
    }),
  });
}
