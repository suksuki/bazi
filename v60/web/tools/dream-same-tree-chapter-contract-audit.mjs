import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import {
  auditDreamGroveAccessibility,
  hasNativeDisabledAttribute,
} from "./dream-grove-accessibility-contract.mjs";

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

const refs = {
  candidate: "candidate-wenxi",
  candidateHash: "a".repeat(64),
  tree: "tree-wenxi",
  firstQuestion: "question-wenxi-first",
  firstEpisode: "episode-wenxi-first",
  secondQuestion: "question-wenxi-second",
  secondEpisode: "episode-wenxi-second",
  transition: "transition-wenxi-first-second",
};

const routeBase = {
  contract_version: "v60.dream-grove-chapter-route.001",
  route_hash: "b".repeat(64),
  status: "AVAILABLE",
  basis: "CANONICAL_TRANSITION",
  candidate_ref: refs.candidate,
  candidate_hash: refs.candidateHash,
  tree_ref: refs.tree,
  previous_source_question_ref: refs.firstQuestion,
  previous_source_episode_ref: refs.firstEpisode,
  target_source_question_ref: refs.secondQuestion,
  target_source_episode_ref: refs.secondEpisode,
  target_source_episode_version: 1,
  target_chapter: "RETURN_VISIT",
  transition_ref: refs.transition,
  transition_hash: "c".repeat(64),
  title: "共同署名之后的新委托",
  premise: "馆方把一份新目录交给闻溪，公开范围与最终责任仍未决定。",
  chapter_label: "再次相遇 · 新事件",
  routing_authority: "CANONICAL_EPISODE_GRAPH",
  attention_routing_allowed: false,
  attention_ref_used: false,
  tree_candidate_set_or_order_changed: false,
  question_changed: false,
  answer_changed: false,
  npc_choice_changed: false,
  outcome_changed: false,
  read_only: true,
};

const entryRoute = {
  ...routeBase,
  route_hash: "d".repeat(64),
  basis: "ENTRYPOINT",
  previous_source_question_ref: null,
  previous_source_episode_ref: null,
  target_source_question_ref: "question-entry",
  target_source_episode_ref: "episode-entry",
  target_chapter: "FIRST_VISIT",
  transition_ref: null,
  transition_hash: null,
  title: "第一次走近这棵树",
  premise: "一段尚未回答的人生问题正在树下等待。",
  chapter_label: "初次相遇",
};

const terminalRoute = {
  ...routeBase,
  route_hash: "e".repeat(64),
  status: "STORY_CURRENTLY_COMPLETE",
  basis: "TERMINAL_CHAPTER",
  previous_source_question_ref: refs.secondQuestion,
  previous_source_episode_ref: refs.secondEpisode,
  transition_ref: null,
  transition_hash: null,
  title: "共同署名之后的新委托",
  premise: "这段新委托已经走完，新的世界事件尚未抵达。",
  chapter_label: "这一段暂告一段落 · 等待新章",
};

const phenotype = {
  profile_version: "v60.tree-phenotype.001",
  fact_basis: "contract fixture",
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
};

const candidate = ({
  candidateRef = refs.candidate,
  candidateHash = refs.candidateHash,
  treeRef = refs.tree,
  alias = "馆页树",
  domain = "career",
  displayOrder = 1,
  route = routeBase,
} = {}) => ({
  candidate_ref: candidateRef,
  candidate_hash: candidateHash,
  tree_ref: treeRef,
  domain,
  public_alias: alias,
  premise: `STALE_LEGACY_PREMISE_${candidateRef}`,
  display_order: displayOrder,
  chapter_route: {
    ...route,
    candidate_ref: candidateRef,
    candidate_hash: candidateHash,
    tree_ref: treeRef,
  },
  tree: {
    state: "READY",
    version: 2,
    phenotype,
    scene_hash: "scene-hash",
  },
});

const candidates = [
  candidate(),
  candidate({
    candidateRef: "candidate-heyang",
    candidateHash: "1".repeat(64),
    treeRef: "tree-heyang",
    alias: "染布树",
    domain: "wealth",
    displayOrder: 2,
    route: {
      ...entryRoute,
      route_hash: "2".repeat(64),
      target_source_question_ref: "question-heyang-entry",
      target_source_episode_ref: "episode-heyang-entry",
      title: "河岸铺的新染布",
      premise: "三匹新染布正在等待第一批真实询价。",
    },
  }),
  candidate({
    candidateRef: "candidate-zhaoning",
    candidateHash: "3".repeat(64),
    treeRef: "tree-zhaoning",
    alias: "灯册树",
    domain: "relationship",
    displayOrder: 3,
    route: {
      ...entryRoute,
      route_hash: "4".repeat(64),
      target_source_question_ref: "question-zhaoning-entry",
      target_source_episode_ref: "episode-zhaoning-entry",
      title: "山灯驿的新轮值",
      premise: "共享轮值刚开始形成，边界仍未稳定。",
    },
  }),
];

const pending = {
  contract_version: "v60.dream-pending-attention.001",
  attention_ref: "attention-wenxi",
  attention_hash: "5".repeat(64),
  source_encounter_ref: "encounter-wenxi-first",
  source_encounter_version: 10,
  source_echo_ref: "echo-wenxi-first",
  source_echo_hash: "6".repeat(64),
  source_candidate_ref: refs.candidate,
  source_candidate_hash: refs.candidateHash,
  tree_ref: refs.tree,
  observation_ref: "observation-wenxi-credit",
  label: "再核对第1条事实",
  summary: "共同职责已经发生，但下一章仍由生命线自己推进。",
  status: "PENDING_SAME_TREE_RETURN",
  semantics: "DREAM_RETURN_ATTENTION_ONLY",
  evidence_role: "NOT_EVIDENCE",
  tree_candidate_set_or_order_changed: false,
  question_changed: false,
  answer_changed: false,
  npc_choice_changed: false,
  outcome_changed: false,
  mingli_write_allowed: false,
  decision_write_allowed: false,
  knowledge_write_allowed: false,
  read_only: true,
};

const delivery = (ref, mediaType) => ({
  asset_ref: ref,
  asset_version: "asset.001",
  url: `/${ref}`,
  media_type: mediaType,
  sha256: "asset-sha256",
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

const grove = (overrides = {}) => ({
  grove_version: "v60.dream-grove.004",
  selection_status: "AWAITING_TREE_SELECTION",
  candidates,
  return_echo: null,
  next_attention: null,
  pending_attention: pending,
  attention_follow_through: null,
  hidden_outcome_included: false,
  hidden_npc_choice_included: false,
  ...overrides,
});

const groveProps = (groveValue) => ({
  background: media.assets.grove_background,
  busy: false,
  grove: groveValue,
  lens,
  media,
  onSelect: () => {},
  onSelectAttention: () => {},
});

const buttonTag = (markup, candidateRef) =>
  markup.match(
    new RegExp(`<button[^>]*data-candidate-ref="${candidateRef}"[^>]*>`),
  )?.[0] ?? "";
const buttonTags = (markup, candidateRef) =>
  [
    ...markup.matchAll(
      new RegExp(
        `<button[^>]*data-candidate-ref="${candidateRef}"[^>]*>`,
        "g",
      ),
    ),
  ].map((match) => match[0]);

let accessibilityReport = null;
try {
  const { isDreamGroveChapterRouteDisplayable } =
    await vite.ssrLoadModule("/src/dreamChapterRouteTypes.ts");
  const { DreamGroveScene } = await vite.ssrLoadModule(
    "/src/DreamGroveScene.tsx",
  );
  const { DreamOpeningAttention } = await vite.ssrLoadModule(
    "/src/components/DreamOpeningAttention.tsx",
  );
  const { LifeTreeScene } = await vite.ssrLoadModule(
    "/src/LifeTreeScene.tsx",
  );

  const bindings = {
    candidateRef: refs.candidate,
    candidateHash: refs.candidateHash,
    treeRef: refs.tree,
  };
  assertEqual(
    "valid-entrypoint",
    isDreamGroveChapterRouteDisplayable(
      {
        ...entryRoute,
        candidate_ref: refs.candidate,
        candidate_hash: refs.candidateHash,
        tree_ref: refs.tree,
      },
      bindings,
    ),
    true,
  );
  assertEqual(
    "valid-canonical-transition",
    isDreamGroveChapterRouteDisplayable(routeBase, bindings),
    true,
  );
  assertEqual(
    "valid-terminal",
    isDreamGroveChapterRouteDisplayable(terminalRoute, bindings),
    true,
  );

  const invalidRoutes = {
    extra_key: { ...routeBase, extra_key: true },
    wrong_version: { ...routeBase, contract_version: "route.999" },
    wrong_hash: { ...routeBase, route_hash: "not-a-hash" },
    wrong_status: { ...routeBase, status: "UNKNOWN" },
    wrong_basis: { ...routeBase, basis: "RETURN_ATTENTION" },
    wrong_candidate: { ...routeBase, candidate_ref: "candidate-other" },
    wrong_candidate_hash: { ...routeBase, candidate_hash: "7".repeat(64) },
    wrong_tree: { ...routeBase, tree_ref: "tree-other" },
    zero_episode_version: {
      ...routeBase,
      target_source_episode_version: 0,
    },
    entrypoint_with_previous: {
      ...entryRoute,
      previous_source_question_ref: refs.firstQuestion,
      previous_source_episode_ref: refs.firstEpisode,
    },
    entrypoint_return_chapter: {
      ...entryRoute,
      target_chapter: "RETURN_VISIT",
    },
    transition_without_previous: {
      ...routeBase,
      previous_source_question_ref: null,
      previous_source_episode_ref: null,
    },
    transition_half_identity: { ...routeBase, transition_hash: null },
    transition_first_chapter: {
      ...routeBase,
      target_chapter: "FIRST_VISIT",
    },
    transition_same_question: {
      ...routeBase,
      target_source_question_ref: refs.firstQuestion,
    },
    transition_same_episode: {
      ...routeBase,
      target_source_episode_ref: refs.firstEpisode,
    },
    terminal_previous_mismatch: {
      ...terminalRoute,
      previous_source_question_ref: refs.firstQuestion,
    },
    terminal_with_transition: {
      ...terminalRoute,
      transition_ref: refs.transition,
      transition_hash: "c".repeat(64),
    },
    available_terminal_basis: {
      ...terminalRoute,
      status: "AVAILABLE",
    },
    complete_transition_basis: {
      ...routeBase,
      status: "STORY_CURRENTLY_COMPLETE",
    },
    attention_can_route: {
      ...routeBase,
      attention_routing_allowed: true,
    },
    attention_used: { ...routeBase, attention_ref_used: true },
    candidate_order_changed: {
      ...routeBase,
      tree_candidate_set_or_order_changed: true,
    },
    question_changed: { ...routeBase, question_changed: true },
    answer_changed: { ...routeBase, answer_changed: true },
    npc_choice_changed: { ...routeBase, npc_choice_changed: true },
    outcome_changed: { ...routeBase, outcome_changed: true },
    writable: { ...routeBase, read_only: false },
    wrong_authority: {
      ...routeBase,
      routing_authority: "RETURN_ATTENTION",
    },
  };
  for (const [label, route] of Object.entries(invalidRoutes)) {
    assertEqual(
      `invalid-${label}`,
      isDreamGroveChapterRouteDisplayable(route, bindings),
      false,
    );
  }

  const withPendingMarkup = renderToStaticMarkup(
    React.createElement(DreamGroveScene, groveProps(grove())),
  );
  const withoutPendingMarkup = renderToStaticMarkup(
    React.createElement(
      DreamGroveScene,
      groveProps(grove({ pending_attention: null })),
    ),
  );
  for (const expected of [
    'aria-label="选择一棵生命树"',
    'data-chapter-route-status="AVAILABLE"',
    `data-chapter-route-version="${routeBase.contract_version}"`,
    'data-route-basis="CANONICAL_TRANSITION"',
    `data-route-hash="${routeBase.route_hash}"`,
    `data-route-candidate-ref="${refs.candidate}"`,
    `data-route-candidate-hash="${refs.candidateHash}"`,
    `data-route-tree-ref="${refs.tree}"`,
    `data-previous-source-question-ref="${refs.firstQuestion}"`,
    `data-previous-source-episode-ref="${refs.firstEpisode}"`,
    `data-target-source-question-ref="${refs.secondQuestion}"`,
    `data-target-source-episode-ref="${refs.secondEpisode}"`,
    'data-target-source-episode-version="1"',
    'data-target-chapter="RETURN_VISIT"',
    `data-transition-ref="${refs.transition}"`,
    `data-transition-hash="${routeBase.transition_hash}"`,
    'data-routing-authority="CANONICAL_EPISODE_GRAPH"',
    'data-attention-routing-allowed="false"',
    'data-attention-ref-used="false"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-outcome-changed="false"',
    'data-read-only="true"',
    routeBase.chapter_label,
    routeBase.title,
    routeBase.premise,
    pending.label,
  ]) {
    assertIncludes("available-route-with-pending", withPendingMarkup, expected);
  }
  assertExcludes(
    "available-route-does-not-use-stale-premise",
    withPendingMarkup,
    `STALE_LEGACY_PREMISE_${refs.candidate}`,
  );
  assertExcludes(
    "same-tree-route-is-not-described-as-strange",
    withPendingMarkup,
    "陌生生命树",
  );
  assertExcludes(
    "available-button-enabled",
    buttonTag(withPendingMarkup, refs.candidate),
    'aria-disabled="true"',
  );
  assertIncludes(
    "available-button-aria-enabled",
    buttonTag(withPendingMarkup, refs.candidate),
    'aria-disabled="false"',
  );
  assertIncludes(
    "available-button-keyboard-focusable",
    buttonTag(withPendingMarkup, refs.candidate),
    'tabindex="0"',
  );
  assertEqual(
    "available-button-has-no-native-disabled",
    hasNativeDisabledAttribute(buttonTag(withPendingMarkup, refs.candidate)),
    false,
  );
  for (const routeIdentity of [
    `data-route-hash="${routeBase.route_hash}"`,
    `data-target-source-question-ref="${refs.secondQuestion}"`,
    `data-target-source-episode-ref="${refs.secondEpisode}"`,
    `data-transition-ref="${refs.transition}"`,
  ]) {
    assertIncludes(
      "route-same-without-pending",
      withoutPendingMarkup,
      routeIdentity,
    );
  }
  assertExcludes(
    "pending-is-independent",
    withoutPendingMarkup,
    pending.label,
  );
  assertEqual(
    "candidate-order-stable",
    [...withPendingMarkup.matchAll(/data-candidate-ref="([^"]+)"/g)]
      .map((match) => match[1])
      .join(","),
    "candidate-wenxi,candidate-heyang,candidate-zhaoning",
  );

  const invalidCandidate = candidate({
    route: { ...routeBase, route_hash: "invalid" },
  });
  const invalidMarkup = renderToStaticMarkup(
    React.createElement(
      DreamGroveScene,
      groveProps(grove({ candidates: [invalidCandidate, ...candidates.slice(1)] })),
    ),
  );
  assertIncludes(
    "invalid-route-withheld",
    invalidMarkup,
    'data-chapter-route-status="WITHHELD"',
  );
  assertIncludes(
    "invalid-route-aria-disabled",
    buttonTag(invalidMarkup, refs.candidate),
    'aria-disabled="true"',
  );
  assertIncludes(
    "invalid-route-keyboard-focusable",
    buttonTag(invalidMarkup, refs.candidate),
    'tabindex="0"',
  );
  assertEqual(
    "invalid-route-has-no-native-disabled",
    hasNativeDisabledAttribute(buttonTag(invalidMarkup, refs.candidate)),
    false,
  );
  assertIncludes(
    "invalid-route-readable-label",
    buttonTag(invalidMarkup, refs.candidate),
    "路线凭据没有完整对上，不能进入",
  );
  assertIncludes(
    "invalid-route-boundary-copy",
    invalidMarkup,
    "路线凭据没有完整对上",
  );
  assertExcludes("invalid-route-title-hidden", invalidMarkup, routeBase.title);
  assertIncludes(
    "invalid-route-pending-independent",
    invalidMarkup,
    pending.label,
  );

  const duplicateCandidateMarkup = renderToStaticMarkup(
    React.createElement(
      DreamGroveScene,
      groveProps(
        grove({
          candidates: [
            candidate(),
            candidate({
              candidateRef: refs.candidate,
              candidateHash: "9".repeat(64),
              treeRef: "tree-wenxi-shadow",
              alias: "重号馆页树",
              route: {
                ...routeBase,
                route_hash: "8".repeat(64),
                title: "不应串到前一张卡片的章节",
              },
            }),
            ...candidates.slice(1),
          ],
        }),
      ),
    ),
  );
  const duplicateButtons = buttonTags(
    duplicateCandidateMarkup,
    refs.candidate,
  );
  assertEqual("duplicate-candidate-count", duplicateButtons.length, 2);
  assertEqual(
    "duplicate-candidates-fail-closed",
    duplicateButtons.every(
      (tag) =>
        tag.includes('data-chapter-route-status="WITHHELD"') &&
        tag.includes('aria-disabled="true"') &&
        tag.includes('tabindex="0"') &&
        !hasNativeDisabledAttribute(tag),
    ),
    true,
  );

  const exactDuplicateCandidateMarkup = renderToStaticMarkup(
    React.createElement(
      DreamGroveScene,
      groveProps(
        grove({
          candidates: [
            candidate(),
            candidate(),
            ...candidates.slice(1),
          ],
        }),
      ),
    ),
  );
  const exactDuplicateButtons = buttonTags(
    exactDuplicateCandidateMarkup,
    refs.candidate,
  );
  assertEqual("exact-duplicate-candidate-count", exactDuplicateButtons.length, 2);
  assertEqual(
    "exact-duplicate-candidates-fail-closed-and-focusable",
    exactDuplicateButtons.every(
      (tag) =>
        tag.includes('data-chapter-route-status="WITHHELD"') &&
        tag.includes('aria-disabled="true"') &&
        tag.includes('tabindex="0"') &&
        !hasNativeDisabledAttribute(tag),
    ),
    true,
  );

  const completedCandidate = candidate({ route: terminalRoute });
  const completedMarkup = renderToStaticMarkup(
    React.createElement(
      DreamGroveScene,
      groveProps(
        grove({ candidates: [completedCandidate, ...candidates.slice(1)] }),
      ),
    ),
  );
  assertIncludes(
    "terminal-status",
    completedMarkup,
    'data-chapter-route-status="STORY_CURRENTLY_COMPLETE"',
  );
  assertIncludes(
    "terminal-button-aria-disabled",
    buttonTag(completedMarkup, refs.candidate),
    'aria-disabled="true"',
  );
  assertIncludes(
    "terminal-button-keyboard-focusable",
    buttonTag(completedMarkup, refs.candidate),
    'tabindex="0"',
  );
  assertEqual(
    "terminal-button-has-no-native-disabled",
    hasNativeDisabledAttribute(buttonTag(completedMarkup, refs.candidate)),
    false,
  );
  for (const expected of [
    terminalRoute.chapter_label,
    terminalRoute.title,
    terminalRoute.premise,
    "暂时没有下一章可进入",
    `aria-label="${terminalRoute.title}，${terminalRoute.chapter_label}"`,
  ]) {
    assertIncludes("terminal-copy", completedMarkup, expected);
  }
  assertExcludes(
    "terminal-accessible-name-does-not-repeat-waiting",
    completedMarkup,
    `${terminalRoute.chapter_label}已经完成，等待新章`,
  );

  accessibilityReport = auditDreamGroveAccessibility({
    DreamGroveScene,
    assertEqual,
    candidateRef: refs.candidate,
    availableProps: groveProps(grove()),
    busyProps: { ...groveProps(grove()), busy: true },
    blockedCases: [
      {
        label: "invalid",
        props: groveProps(
          grove({ candidates: [invalidCandidate, ...candidates.slice(1)] }),
        ),
      },
      {
        expectedButtonCount: 2,
        label: "duplicate",
        props: groveProps(
          grove({
            candidates: [
              candidate(),
              candidate({
                candidateRef: refs.candidate,
                candidateHash: "9".repeat(64),
                treeRef: "tree-wenxi-shadow",
              }),
              ...candidates.slice(1),
            ],
          }),
        ),
      },
      {
        label: "terminal",
        props: groveProps(
          grove({ candidates: [completedCandidate, ...candidates.slice(1)] }),
        ),
      },
    ],
  });

  const openingAttention = {
    contract_version: "v60.dream-opening-attention.001",
    application_ref: "application-wenxi",
    application_hash: "8".repeat(64),
    attention_ref: pending.attention_ref,
    attention_hash: pending.attention_hash,
    source_echo_ref: pending.source_echo_ref,
    source_tree_ref: refs.tree,
    target_tree_ref: refs.tree,
    target_encounter_ref: "encounter-wenxi-second",
    observation_ref: pending.observation_ref,
    label: pending.label,
    summary: pending.summary,
    semantics: "DREAM_RETURN_ATTENTION_ONLY",
    evidence_role: "NOT_EVIDENCE",
    tree_candidate_set_or_order_changed: false,
    question_changed: false,
    answer_changed: false,
    npc_choice_changed: false,
    outcome_changed: false,
    mingli_write_allowed: false,
    decision_write_allowed: false,
    knowledge_write_allowed: false,
    read_only: true,
  };
  const openingMarkup = renderToStaticMarkup(
    React.createElement(DreamOpeningAttention, {
      attention: openingAttention,
      targetEncounterRef: openingAttention.target_encounter_ref,
      targetTreeRef: openingAttention.target_tree_ref,
    }),
  );
  for (const expected of [
    "不选择本章",
    "不改变问题、答案或世界结果",
    'data-tree-candidate-set-or-order-changed="false"',
    'data-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-outcome-changed="false"',
    'data-read-only="true"',
  ]) {
    assertIncludes("opening-attention-boundary", openingMarkup, expected);
  }
  const mismatchedOpeningMarkup = renderToStaticMarkup(
    React.createElement(DreamOpeningAttention, {
      attention: {
        ...openingAttention,
        target_encounter_ref: "encounter-wenxi-other",
      },
      targetEncounterRef: openingAttention.target_encounter_ref,
      targetTreeRef: openingAttention.target_tree_ref,
    }),
  );
  assertEqual(
    "opening-attention-target-encounter-bound",
    mismatchedOpeningMarkup,
    "",
  );

  const returnSnapshot = {
    encounter: {
      encounter_ref: "encounter-wenxi-second",
      status: "OBSERVING",
      chapter: "RETURN_VISIT",
      state: { observed_organs: [] },
    },
    game: {
      episode_ref: refs.secondEpisode,
      available_commands: ["OBSERVE_EVIDENCE"],
    },
    actor: { display_name: "闻溪" },
    tree: {
      tree_ref: refs.tree,
      projection_version: 3,
      organs: [],
    },
    world: { current_tick: 42 },
    question: null,
    human_seal: null,
    fruit: null,
    reveal: null,
    projections: {
      dream: {
        journey_title: routeBase.title,
        journey_status: "先看新事件已经留下的两片叶。",
      },
    },
    continuation: { available: false, label: null },
    opening_attention: openingAttention,
    attention_follow_through: null,
  };
  const lifeTreeMarkup = renderToStaticMarkup(
    React.createElement(LifeTreeScene, {
      background: media.assets.life_world_background,
      snapshot: returnSnapshot,
      busy: false,
      focusedOrganRef: null,
      onFocus: () => {},
      onOrgan: () => {},
      onAnswer: () => {},
      onReveal: () => {},
      onReconcile: () => {},
      onContinue: () => {},
      onReturnToGrove: () => {},
    }),
  );
  for (const expected of [
    'data-chapter="RETURN_VISIT"',
    `data-episode-ref="${refs.secondEpisode}"`,
    'data-dream-chapter-marker="RETURN_VISIT"',
    "再次相遇 · 新事件",
    routeBase.title,
  ]) {
    assertIncludes("return-visit-scene", lifeTreeMarkup, expected);
  }

  const firstVisitMarkup = renderToStaticMarkup(
    React.createElement(LifeTreeScene, {
      background: media.assets.life_world_background,
      snapshot: {
        ...returnSnapshot,
        encounter: {
          ...returnSnapshot.encounter,
          chapter: "FIRST_VISIT",
        },
        game: {
          ...returnSnapshot.game,
          episode_ref: refs.firstEpisode,
        },
      },
      busy: false,
      focusedOrganRef: null,
      onFocus: () => {},
      onOrgan: () => {},
      onAnswer: () => {},
      onReveal: () => {},
      onReconcile: () => {},
      onContinue: () => {},
      onReturnToGrove: () => {},
    }),
  );
  assertIncludes(
    "first-visit-root",
    firstVisitMarkup,
    'data-chapter="FIRST_VISIT"',
  );
  assertExcludes(
    "first-visit-no-return-marker",
    firstVisitMarkup,
    'data-dream-chapter-marker="RETURN_VISIT"',
  );

  const styles = await readFile(
    path.join(webRoot, "src/styles/dream-chapter-route.css"),
    "utf8",
  );
  for (const expected of [
    ".dream-grove-chapter-route",
    ".dream-grove-chapter-route-withheld",
    ".dream-grove-chapter-route-complete",
    '.grove-tree-choice[data-chapter-route-status="WITHHELD"]',
    '.grove-tree-choice[data-chapter-route-status="STORY_CURRENTLY_COMPLETE"]',
    '[aria-disabled="true"]',
    ".dream-chapter-marker",
  ]) {
    assertIncludes("route-styles", styles, expected);
  }
} finally {
  await vite.close();
}

const report = {
  contractVersion: routeBase.contract_version,
  groveVersion: "v60.dream-grove.004",
  validStates: [
    "AVAILABLE:ENTRYPOINT",
    "AVAILABLE:CANONICAL_TRANSITION",
    "STORY_CURRENTLY_COMPLETE:TERMINAL_CHAPTER",
  ],
  invalidMutationCount: 29,
  attentionRoutingAllowed: false,
  attentionRefUsed: false,
  routeSameWithOrWithoutPendingAttention: true,
  invalidRouteFailsClosed: true,
  duplicateCandidateRefsFailClosed: true,
  ...accessibilityReport,
  terminalChapterAriaDisabled: true,
  returnVisitMarkerVisible: true,
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
