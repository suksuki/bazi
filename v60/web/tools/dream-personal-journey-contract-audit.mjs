import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const vite = await createServer({
  root: webRoot,
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});

const failures = [];
const fail = (message) => failures.push(message);
const assertEqual = (label, actual, expected) => {
  if (actual !== expected) {
    fail(
      `${label}:expected:${JSON.stringify(expected)}:actual:${JSON.stringify(actual)}`,
    );
  }
};
const assertIncludes = (label, value, expected) => {
  if (!value.includes(expected)) fail(`${label}:missing:${expected}`);
};
const assertExcludes = (label, value, forbidden) => {
  if (value.includes(forbidden)) fail(`${label}:forbidden:${forbidden}`);
};
const captureError = async (operation) => {
  try {
    await operation();
    return null;
  } catch (error) {
    return error instanceof Error ? error.message : String(error);
  }
};

const hash = (character) => character.repeat(64);
const candidate = (candidateRef, domain, publicAlias, displayOrder) => {
  const candidateHash = String(displayOrder).repeat(64);
  const treeRef = `tree-${domain}`;
  const questionRef = `question-${domain}`;
  const episodeRef = `episode-${domain}`;
  return {
    candidate_ref: candidateRef,
    candidate_hash: candidateHash,
    tree_ref: treeRef,
    domain,
    public_alias: publicAlias,
    premise: `${publicAlias}正在面对一件仍未确定的事。`,
    display_order: displayOrder,
    chapter_route: {
      contract_version: "v60.dream-grove-chapter-route.001",
      route_hash: hash(String(displayOrder + 3)),
      status: "AVAILABLE",
      basis: "ENTRYPOINT",
      candidate_ref: candidateRef,
      candidate_hash: candidateHash,
      tree_ref: treeRef,
      previous_source_question_ref: null,
      previous_source_episode_ref: null,
      target_source_question_ref: questionRef,
      target_source_episode_ref: episodeRef,
      target_source_episode_version: 1,
      target_chapter: "FIRST_VISIT",
      transition_ref: null,
      transition_hash: null,
      title: `${publicAlias}的第一章`,
      premise: `${publicAlias}正在面对一件仍未确定的事。`,
      chapter_label: "初次相遇",
      routing_authority: "CANONICAL_EPISODE_GRAPH",
      attention_routing_allowed: false,
      attention_ref_used: false,
      tree_candidate_set_or_order_changed: false,
      question_changed: false,
      answer_changed: false,
      npc_choice_changed: false,
      outcome_changed: false,
      read_only: true,
    },
    tree: {
      state: "READY",
      version: 1,
      phenotype: {
        profile_version: "phenotype.001",
        fact_basis: "personal journey contract fixture",
        element_membership_ratios: {
          wood: 0.2,
          fire: 0.2,
          earth: 0.2,
          metal: 0.2,
          water: 0.2,
        },
        crown_spread: 1,
        branch_lift: 0.84,
        root_spread: 1,
        bark_definition: 0.86,
        surface_moisture: 0.9,
        semantic_status: "VISUAL_METAPHOR_ONLY",
      },
      scene_hash: `scene-${domain}`,
    },
  };
};

const candidates = Object.freeze([
  Object.freeze(candidate("candidate-career", "career", "闻溪", 1)),
  Object.freeze(candidate("candidate-wealth", "wealth", "禾央", 2)),
  Object.freeze(
    candidate("candidate-relationship", "relationship", "照宁", 3),
  ),
]);
const selectedCandidate = candidates[2];
const inquiry = Object.freeze({
  contract_version: "v60.dream-private-inquiry.001",
  inquiry_ref: "inquiry-private-relationship",
  inquiry_hash: hash("a"),
  domain: "relationship",
  question: "这次合作里，双方的边界是否真的说清了？",
  candidate_ref: selectedCandidate.candidate_ref,
  candidate_hash: selectedCandidate.candidate_hash,
  public_alias: selectedCandidate.public_alias,
  tree_ref: selectedCandidate.tree_ref,
  encounter_ref: "encounter-private-relationship",
  episode_question_ref: "question-relationship",
  private_to_account: true,
  owner_self_report_only: true,
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE",
  reading_used_to_select_candidate: false,
  llm_interpretation_used: false,
  dream_answers_owner_question: false,
});
const observationOptions = Object.freeze(
  [
    ["option-boundary", "边界有没有被双方说清", "记录一次双方明确说明边界的时刻。"],
    ["option-repeat", "协作有没有持续发生", "观察同一件事是否出现第二次共同投入。"],
    ["option-care", "关心有没有落成行动", "记录一个已经发生、可以复核的支持行为。"],
  ].map(([optionRef, label, summary]) =>
    Object.freeze({
      option_ref: optionRef,
      inquiry_ref: inquiry.inquiry_ref,
      domain: inquiry.domain,
      label,
      summary,
      checkpoint_days: 7,
    }),
  ),
);
const observation = Object.freeze({
  contract_version: "v60.dream-personal-observation.001",
  task_ref: "task-private-relationship",
  task_hash: hash("b"),
  inquiry_ref: inquiry.inquiry_ref,
  inquiry_hash: inquiry.inquiry_hash,
  encounter_ref: inquiry.encounter_ref,
  option: observationOptions[0],
  checkpoint_on: "2026-08-07",
  semantics: "PRIVATE_REALITY_OBSERVATION_ONLY",
  private_to_account: true,
  owner_self_report_only: true,
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE",
  dream_result_validates_owner_question: false,
});
const latestCheckin = Object.freeze({
  contract_version: "v60.dream-personal-check-in.001",
  checkin_ref: "checkin-private-relationship",
  checkin_hash: hash("c"),
  task_ref: observation.task_ref,
  task_hash: observation.task_hash,
  status: "OBSERVED",
  note: "双方在新的安排里明确写下了各自负责的部分。",
  checked_in_on: "2026-08-08",
  semantics: "PRIVATE_SELF_REPORTED_CHECK_IN",
  private_to_account: true,
  owner_self_report_only: true,
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE",
  validates_dream_or_mingli: false,
});
const boundaries = Object.freeze({
  private_to_account: true,
  owner_self_report_only: true,
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE",
  dream_answers_owner_question: false,
  tree_candidate_set_or_order_changed: false,
  chapter_route_changed: false,
  episode_question_changed: false,
  answer_changed: false,
  npc_choice_changed: false,
  world_outcome_changed: false,
  mingli_write_allowed: false,
  decision_write_allowed: false,
  knowledge_write_allowed: false,
});
const journey = (status, overrides = {}) => ({
  contract_version: "v60.dream-personal-journey.001",
  status,
  inquiry,
  observation_options:
    status === "IN_DREAM" || status === "DREAM_INTERRUPTED"
      ? []
      : observationOptions,
  observation:
    status === "OBSERVING" || status === "FOLLOWED_UP"
      ? observation
      : null,
  latest_checkin: status === "FOLLOWED_UP" ? latestCheckin : null,
  checkin_count: status === "FOLLOWED_UP" ? 1 : 0,
  ...boundaries,
  ...overrides,
});

const inDream = journey("IN_DREAM");
const interrupted = journey("DREAM_INTERRUPTED");
const awaiting = journey("AWAITING_OBSERVATION");
const observing = journey("OBSERVING");
const followedUp = journey("FOLLOWED_UP");

const delivery = (ref, mediaType) => ({
  asset_ref: ref,
  asset_version: "asset.001",
  url: `/${ref}`,
  media_type: mediaType,
  sha256: `${ref}-sha256`,
});
const media = {
  registry_version: "registry.001",
  catalog_version: "catalog.001",
  assets: {
    brand_logo: delivery("brand", "image/svg+xml"),
    grove_background: delivery("grove-background", "image/png"),
    life_world_background: delivery("life-background", "image/png"),
  },
  cues: {
    abu_idle: {
      cue_ref: "abu-idle",
      version: "cue.001",
      trigger: "IDLE",
      playback: "LOOP",
      interruptible: true,
      deliveries: {
        VP9_ALPHA_WEBM: delivery("abu-idle-video", "video/webm"),
        REDUCED_MOTION_POSTER: delivery("abu-idle-poster", "image/png"),
      },
    },
    abu_guide_left: {
      cue_ref: "abu-guide",
      version: "cue.001",
      trigger: "GUIDE_LEFT",
      playback: "PLAY_ONCE",
      interruptible: true,
      deliveries: {
        VP9_ALPHA_WEBM: delivery("abu-guide-video", "video/webm"),
        REDUCED_MOTION_POSTER: delivery("abu-guide-poster", "image/png"),
      },
    },
  },
};
const lens = {
  semantics: "ATTENTION_WINDOW_ONLY",
  decision_role: "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER",
  attention_order_recorded: false,
  tree_candidate_set_or_order_changed: false,
  future_evidence_included: false,
  canonical_write_allowed: false,
  observations: [
    { domain: "career", label: "事业与职责", question: "事业观察？" },
    { domain: "wealth", label: "成果与交换", question: "成果观察？" },
    { domain: "relationship", label: "关系与边界", question: "关系观察？" },
  ],
};
const grove = (personalJourney) => ({
  grove_version: "v60.dream-grove.005",
  selection_status: "AWAITING_TREE_SELECTION",
  candidates,
  return_echo: null,
  next_attention: null,
  pending_attention: null,
  attention_follow_through: null,
  personal_journey: personalJourney,
  hidden_outcome_included: false,
  hidden_npc_choice_included: false,
});
const candidateOrder = (markup) =>
  [...markup.matchAll(/data-candidate-ref="([^"]+)"/g)]
    .map((match) => match[1])
    .join(",");

let invalidMutationCount = 0;
try {
  const {
    isDreamPersonalJourneyDisplayable,
    DREAM_PERSONAL_JOURNEY_VERSION,
  } = await vite.ssrLoadModule("/src/dreamPersonalJourneyTypes.ts");
  const { DreamPersonalJourneyCard } = await vite.ssrLoadModule(
    "/src/components/DreamPersonalJourneyCard.tsx",
  );
  const { DreamPersonalJourneyEncounter } = await vite.ssrLoadModule(
    "/src/components/DreamPersonalJourneyEncounter.tsx",
  );
  const { DreamGroveScene } = await vite.ssrLoadModule(
    "/src/DreamGroveScene.tsx",
  );
  const {
    startDreamPersonalJourney,
    selectDreamPersonalObservation,
    recordDreamPersonalCheckIn,
  } = await vite.ssrLoadModule("/src/dreamPersonalJourneyApi.ts");

  assertEqual(
    "journey-version",
    DREAM_PERSONAL_JOURNEY_VERSION,
    "v60.dream-personal-journey.001",
  );
  for (const [status, value] of [
    ["IN_DREAM", inDream],
    ["DREAM_INTERRUPTED", interrupted],
    ["AWAITING_OBSERVATION", awaiting],
    ["OBSERVING", observing],
    ["FOLLOWED_UP", followedUp],
  ]) {
    assertEqual(
      `valid-${status}`,
      isDreamPersonalJourneyDisplayable(value, {
        candidateRef: inquiry.candidate_ref,
        candidateHash: inquiry.candidate_hash,
        treeRef: inquiry.tree_ref,
        encounterRef: inquiry.encounter_ref,
      }),
      true,
    );
  }

  const invalidJourneys = {
    extra_key: { ...awaiting, extra_key: true },
    wrong_version: { ...awaiting, contract_version: "unsafe" },
    wrong_status: { ...awaiting, status: "ANSWERED_BY_DREAM" },
    public: { ...awaiting, private_to_account: false },
    evidence: { ...awaiting, mingli_evidence_role: "MINGLI_EVIDENCE" },
    dream_answers: { ...awaiting, dream_answers_owner_question: true },
    tree_changed: {
      ...awaiting,
      tree_candidate_set_or_order_changed: true,
    },
    route_changed: { ...awaiting, chapter_route_changed: true },
    episode_changed: { ...awaiting, episode_question_changed: true },
    answer_changed: { ...awaiting, answer_changed: true },
    npc_changed: { ...awaiting, npc_choice_changed: true },
    outcome_changed: { ...awaiting, world_outcome_changed: true },
    mingli_write: { ...awaiting, mingli_write_allowed: true },
    decision_write: { ...awaiting, decision_write_allowed: true },
    knowledge_write: { ...awaiting, knowledge_write_allowed: true },
    duplicate_options: {
      ...awaiting,
      observation_options: [
        observationOptions[0],
        observationOptions[0],
        observationOptions[2],
      ],
    },
    bad_state_shape: {
      ...awaiting,
      observation: observation,
    },
    inquiry_hash: {
      ...awaiting,
      inquiry: { ...inquiry, inquiry_hash: "not-a-hash" },
    },
    inquiry_short: {
      ...awaiting,
      inquiry: { ...inquiry, question: "短" },
    },
    inquiry_candidate: {
      ...awaiting,
      inquiry: { ...inquiry, candidate_ref: "another-candidate" },
    },
    inquiry_reading_used: {
      ...awaiting,
      inquiry: { ...inquiry, reading_used_to_select_candidate: true },
    },
    option_cross_inquiry: {
      ...awaiting,
      observation_options: observationOptions.map((option, index) =>
        index === 0
          ? { ...option, inquiry_ref: "another-inquiry" }
          : option,
      ),
    },
    observation_unknown_option: {
      ...observing,
      observation: {
        ...observation,
        option: { ...observation.option, option_ref: "unknown-option" },
      },
    },
    observation_wrong_encounter: {
      ...observing,
      observation: {
        ...observation,
        encounter_ref: "another-encounter",
      },
    },
    observation_invalid_date: {
      ...observing,
      observation: {
        ...observation,
        checkpoint_on: "2026-99-99",
      },
    },
    checkin_wrong_task: {
      ...followedUp,
      latest_checkin: {
        ...latestCheckin,
        task_ref: "another-task",
      },
    },
    checkin_invalid_status: {
      ...followedUp,
      latest_checkin: {
        ...latestCheckin,
        status: "DREAM_CONFIRMED",
      },
    },
    checkin_invalid_date: {
      ...followedUp,
      latest_checkin: {
        ...latestCheckin,
        checked_in_on: "2026-02-31",
      },
    },
    checkin_validates: {
      ...followedUp,
      latest_checkin: {
        ...latestCheckin,
        validates_dream_or_mingli: true,
      },
    },
    checkin_count_zero: { ...followedUp, checkin_count: 0 },
  };
  for (const [label, value] of Object.entries(invalidJourneys)) {
    invalidMutationCount += 1;
    assertEqual(
      `invalid-${label}`,
      isDreamPersonalJourneyDisplayable(value, {
        candidateRef: inquiry.candidate_ref,
        candidateHash: inquiry.candidate_hash,
        treeRef: inquiry.tree_ref,
      }),
      false,
    );
  }

  const intakeMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: null,
      onStart: () => {},
    }),
  );
  for (const expected of [
    'data-personal-journey-status="INTAKE"',
    "带一个现实问题入梦",
    "系统只按主题对应一条人生",
    'maxLength="120"',
    "不进入命理证据",
    "不改变树里的问题、选择或结果",
  ]) {
    assertIncludes("intake", intakeMarkup, expected);
  }
  assertEqual(
    "intake-domain-count",
    (intakeMarkup.match(/data-route-status=/g) ?? []).length,
    3,
  );
  const intakeStartTag =
    intakeMarkup.match(
      /<button[^>]*class="dream-personal-primary"[^>]*>/,
    )?.[0] ?? "";
  assertIncludes(
    "empty-intake-disabled",
    intakeStartTag,
    "disabled",
  );

  const awaitingMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: awaiting,
      onStart: () => {},
    }),
  );
  for (const expected of [
    'data-personal-journey-status="AWAITING_OBSERVATION"',
    'data-private-to-account="true"',
    'data-mingli-evidence-role="NOT_MINGLI_EVIDENCE"',
    'data-dream-answers-owner-question="false"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-chapter-route-changed="false"',
    'data-episode-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-world-outcome-changed="false"',
    'data-mingli-write-allowed="false"',
    'data-decision-write-allowed="false"',
    'data-knowledge-write-allowed="false"',
    inquiry.question,
    "梦中结局没有回答它",
    "未来七天",
  ]) {
    assertIncludes("awaiting-card", awaitingMarkup, expected);
  }
  assertEqual(
    "awaiting-option-count",
    (awaitingMarkup.match(/data-personal-observation-option-ref=/g) ?? [])
      .length,
    3,
  );

  const observingMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: observing,
      onStart: () => {},
    }),
  );
  assertIncludes(
    "observing-task",
    observingMarkup,
    `data-personal-observation-task-ref="${observation.task_ref}"`,
  );
  assertIncludes("observing-checkpoint", observingMarkup, "2026年8月7日");
  assertIncludes("observing-checkin", observingMarkup, "记录一次回访");
  assertExcludes(
    "observing-cannot-hide-active-task",
    observingMarkup,
    "换一个现实问题",
  );

  const followedMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: followedUp,
      onStart: () => {},
    }),
  );
  assertIncludes(
    "followed-checkin",
    followedMarkup,
    `data-personal-checkin-ref="${latestCheckin.checkin_ref}"`,
  );
  assertIncludes("followed-count", followedMarkup, "第 1 次回访");
  assertIncludes("followed-note", followedMarkup, latestCheckin.note);
  assertIncludes("followed-boundary", followedMarkup, "不验证梦境");
  assertIncludes(
    "completed-followup-can-change-question",
    followedMarkup,
    "换一个现实问题",
  );
  const stillObservingFollowedMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: journey("FOLLOWED_UP", {
        latest_checkin: {
          ...latestCheckin,
          status: "STILL_OBSERVING",
        },
      }),
      onStart: () => {},
    }),
  );
  assertExcludes(
    "still-observing-followup-cannot-change-question",
    stillObservingFollowedMarkup,
    "换一个现实问题",
  );

  const invalidMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyCard, {
      busy: false,
      candidates,
      journey: invalidJourneys.knowledge_write,
      onStart: () => {},
    }),
  );
  assertIncludes(
    "invalid-card-withheld",
    invalidMarkup,
    'data-personal-journey-status="WITHHELD"',
  );
  assertExcludes("invalid-card-private-copy", invalidMarkup, inquiry.question);

  const encounterMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyEncounter, {
      busy: false,
      encounterRef: inquiry.encounter_ref,
      journey: inDream,
    }),
  );
  assertIncludes(
    "encounter-in-dream",
    encounterMarkup,
    'data-personal-journey-status="IN_DREAM"',
  );
  assertIncludes("encounter-question", encounterMarkup, inquiry.question);
  assertIncludes("encounter-mirror", encounterMarkup, "只是一面观察镜");

  const encounterAwaitingMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyEncounter, {
      busy: false,
      encounterRef: inquiry.encounter_ref,
      journey: awaiting,
    }),
  );
  assertEqual(
    "encounter-option-count",
    (
      encounterAwaitingMarkup.match(
        /data-personal-observation-option-ref=/g,
      ) ?? []
    ).length,
    3,
  );
  const wrongEncounterMarkup = renderToStaticMarkup(
    React.createElement(DreamPersonalJourneyEncounter, {
      busy: false,
      encounterRef: "wrong-encounter",
      journey: inDream,
    }),
  );
  assertIncludes(
    "encounter-binding-withheld",
    wrongEncounterMarkup,
    'data-personal-journey-status="WITHHELD"',
  );
  assertExcludes(
    "encounter-binding-private-copy",
    wrongEncounterMarkup,
    inquiry.question,
  );

  const groveMarkup = renderToStaticMarkup(
    React.createElement(DreamGroveScene, {
      background: media.assets.grove_background,
      busy: false,
      grove: grove(awaiting),
      lens,
      media,
      onSelect: () => {},
      onSelectAttention: () => {},
      onStartPersonalJourney: () => {},
    }),
  );
  assertIncludes(
    "grove-version-state",
    groveMarkup,
    'data-personal-journey="AWAITING_OBSERVATION"',
  );
  assertEqual(
    "grove-candidate-order",
    candidateOrder(groveMarkup),
    candidates.map(({ candidate_ref }) => candidate_ref).join(","),
  );
  assertEqual(
    "grove-personal-tree-count",
    (groveMarkup.match(/data-personal-journey-tree="true"/g) ?? []).length,
    1,
  );
  const unsafeGroveMarkup = renderToStaticMarkup(
    React.createElement(DreamGroveScene, {
      background: media.assets.grove_background,
      busy: false,
      grove: grove(invalidJourneys.knowledge_write),
      lens,
      media,
      onSelect: () => {},
      onSelectAttention: () => {},
      onStartPersonalJourney: () => {},
    }),
  );
  assertIncludes(
    "unsafe-grove-withheld",
    unsafeGroveMarkup,
    'data-personal-journey-status="WITHHELD"',
  );
  assertExcludes(
    "unsafe-grove-private-copy",
    unsafeGroveMarkup,
    inquiry.question,
  );
  assertEqual(
    "unsafe-grove-candidate-order",
    candidateOrder(unsafeGroveMarkup),
    candidateOrder(groveMarkup),
  );

  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return new Response(JSON.stringify(followedUp), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  try {
    await startDreamPersonalJourney(
      "candidate/relationship",
      "relationship",
      "  这次合作里，   双方边界是否说清？  ",
    );
    await selectDreamPersonalObservation(
      awaiting,
      observationOptions[0].option_ref,
    );
    await recordDreamPersonalCheckIn(
      observing,
      "OBSERVED",
      "  双方已经写下   各自负责的部分。  ",
    );

    assertEqual(
      "start-endpoint",
      calls[0]?.url,
      "/api/v60/dream/grove/candidate%2Frelationship/personal-inquiry",
    );
    const startPayload = JSON.parse(String(calls[0]?.init?.body));
    assertEqual("start-method", calls[0]?.init?.method, "POST");
    assertEqual("start-domain", startPayload.domain, "relationship");
    assertEqual(
      "start-question-normalized",
      startPayload.question,
      "这次合作里， 双方边界是否说清？",
    );
    assertIncludes(
      "start-idempotency",
      startPayload.idempotency_key,
      "v60-dream-personal-journey:inquiry:",
    );
    for (const forbidden of [
      "account_ref",
      "case_ref",
      "reading_ref",
      "evidence_ref",
      "world_outcome",
    ]) {
      assertEqual(
        `start-forbidden-${forbidden}`,
        Object.hasOwn(startPayload, forbidden),
        false,
      );
    }

    assertEqual(
      "observation-endpoint",
      calls[1]?.url,
      "/api/v60/dream/personal-observation",
    );
    const observationPayload = JSON.parse(
      String(calls[1]?.init?.body),
    );
    assertEqual(
      "observation-inquiry",
      observationPayload.inquiry_ref,
      inquiry.inquiry_ref,
    );
    assertEqual(
      "observation-option",
      observationPayload.option_ref,
      observationOptions[0].option_ref,
    );

    assertEqual(
      "checkin-endpoint",
      calls[2]?.url,
      "/api/v60/dream/personal-check-in",
    );
    const checkinPayload = JSON.parse(String(calls[2]?.init?.body));
    assertEqual("checkin-task", checkinPayload.task_ref, observation.task_ref);
    assertEqual("checkin-status", checkinPayload.status, "OBSERVED");
    assertEqual(
      "checkin-note-normalized",
      checkinPayload.note,
      "双方已经写下 各自负责的部分。",
    );

    const sentCount = calls.length;
    assertEqual(
      "invented-option-error",
      await captureError(() =>
        selectDreamPersonalObservation(awaiting, "invented-option"),
      ),
      "dream_personal_observation_option_not_server_issued",
    );
    assertEqual(
      "unsafe-observation-error",
      await captureError(() =>
        selectDreamPersonalObservation(
          invalidJourneys.knowledge_write,
          observationOptions[0].option_ref,
        ),
      ),
      "dream_personal_journey_not_displayable",
    );
    assertEqual(
      "checkin-without-task-error",
      await captureError(() =>
        recordDreamPersonalCheckIn(
          awaiting,
          "OBSERVED",
          "不应发送",
        ),
      ),
      "dream_personal_observation_required",
    );
    assertEqual(
      "unsafe-checkin-error",
      await captureError(() =>
        recordDreamPersonalCheckIn(
          { ...observing, knowledge_write_allowed: true },
          "OBSERVED",
          "不应发送",
        ),
      ),
      "dream_personal_journey_not_displayable",
    );
    assertEqual(
      "invalid-checkin-status-error",
      await captureError(() =>
        recordDreamPersonalCheckIn(
          observing,
          "DREAM_CONFIRMED",
          "不应发送",
        ),
      ),
      "dream_personal_checkin_request_invalid",
    );
    assertEqual(
      "overlong-checkin-note-error",
      await captureError(() =>
        recordDreamPersonalCheckIn(
          observing,
          "OBSERVED",
          "长".repeat(161),
        ),
      ),
      "dream_personal_checkin_request_invalid",
    );
    assertEqual(
      "invalid-inquiry-error",
      await captureError(() =>
        startDreamPersonalJourney(
          "candidate-relationship",
          "relationship",
          "短",
        ),
      ),
      "dream_private_inquiry_request_invalid",
    );
    assertEqual("invalid-actions-not-sent", calls.length, sentCount);
  } finally {
    globalThis.fetch = originalFetch;
  }

  const styles = await readFile(
    path.join(webRoot, "src/styles/dream-personal-journey.css"),
    "utf8",
  );
  for (const expected of [
    ".dream-personal-card",
    ".dream-personal-question",
    ".dream-personal-observation-options",
    ".dream-personal-checkin",
    ".dream-personal-encounter",
    '.grove-tree-choice[data-personal-journey-tree="true"]',
  ]) {
    assertIncludes("personal-styles", styles, expected);
  }
} finally {
  await vite.close();
}

const report = {
  groveVersion: "v60.dream-grove.005",
  journeyVersion: "v60.dream-personal-journey.001",
  validStates: [
    "IN_DREAM",
    "DREAM_INTERRUPTED",
    "AWAITING_OBSERVATION",
    "OBSERVING",
    "FOLLOWED_UP",
  ],
  invalidMutationCount,
  observationOptionCount: observationOptions.length,
  candidateOrderStable: true,
  privateToAccount: true,
  mingliEvidenceRole: "NOT_MINGLI_EVIDENCE",
  crossDomainWritesAllowed: false,
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
