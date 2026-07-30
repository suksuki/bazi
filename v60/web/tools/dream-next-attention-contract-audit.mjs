import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const webRoot = new URL("..", import.meta.url).pathname;
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
    fail(`${label}:expected:${JSON.stringify(expected)}:actual:${JSON.stringify(actual)}`);
  }
};
const assertIncludes = (label, value, expected) => {
  if (!value.includes(expected)) fail(`${label}:missing:${expected}`);
};
const assertExcludes = (label, value, forbidden) => {
  if (value.includes(forbidden)) fail(`${label}:forbidden:${forbidden}`);
};

const echo = {
  contract_version: "v60.dream-return-echo.001",
  echo_ref: "echo-attention-contract",
  echo_hash: "e".repeat(64),
  encounter_ref: "encounter-private",
  public_alias: "闻溪",
  episode_title: "共同修复，共同署名",
  judgment: { choice_label: "保留试案", summary: "当时的判断。" },
  world_response: {
    summary: "后来抵达了已经提交的事实。",
    evidence_summaries: ["事实一。"],
  },
  still_to_observe: { summary: "仍需继续观察。" },
  abu_recap: {
    meaning: "只说明这段梦中经历。",
    boundary: "不能说明主人的命理。",
    next_attention: "下一次继续观察。",
  },
  semantics: "DREAM_LIFE_RETURN_ECHO_ONLY",
  owner_mingli_evidence_allowed: false,
  dream_outcome_admitted_as_owner_evidence: false,
  tree_candidate_set_or_order_changed: false,
  read_only: true,
  decision_write_allowed: false,
  knowledge_write_allowed: false,
  mingli_write_allowed: false,
  canonical_write_allowed: false,
};

const options = Object.freeze([
  Object.freeze({
    observation_ref: "observe-recognition",
    kind: "WORLD_RESPONSE",
    label: "职责是否被承认",
    summary: "继续观察共同工作是否得到明确署名。",
  }),
  Object.freeze({
    observation_ref: "observe-boundary",
    kind: "OUTCOME_EVIDENCE",
    label: "边界是否更清楚",
    summary: "继续观察新的合作怎样划分职责。",
  }),
  Object.freeze({
    observation_ref: "observe-follow-through",
    kind: "OPEN_OBSERVATION",
    label: "承诺是否兑现",
    summary: "继续观察已经说出口的安排是否真正发生。",
  }),
]);

const prompt = {
  contract_version: "v60.dream-return-attention.001",
  source_encounter_ref: "encounter-private",
  source_encounter_version: 8,
  source_echo_ref: echo.echo_ref,
  source_echo_hash: echo.echo_hash,
  source_candidate_ref: "candidate-career",
  source_candidate_hash: "c".repeat(64),
  tree_ref: "tree-career",
  status: "AWAITING_SELECTION",
  options,
  selection: null,
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
};

const openingAttention = {
  contract_version: "v60.dream-opening-attention.001",
  application_ref: "opening-application-contract",
  application_hash: "a".repeat(64),
  attention_ref: "attention-contract",
  attention_hash: "b".repeat(64),
  source_echo_ref: echo.echo_ref,
  source_tree_ref: "tree-career",
  target_tree_ref: "tree-career",
  target_encounter_ref: "encounter-return-visit",
  observation_ref: options[0].observation_ref,
  label: options[0].label,
  summary: options[0].summary,
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

try {
  const { DreamNextAttentionCard } = await vite.ssrLoadModule(
    "/src/components/DreamNextAttentionCard.tsx",
  );
  const { DreamOpeningAttention } = await vite.ssrLoadModule(
    "/src/components/DreamOpeningAttention.tsx",
  );
  const { selectDreamNextAttention } = await vite.ssrLoadModule(
    "/src/dreamRuntimeApi.ts",
  );

  const awaitingMarkup = renderToStaticMarkup(
    React.createElement(DreamNextAttentionCard, {
      attention: prompt,
      busy: false,
      echo,
      onSelect: () => {},
    }),
  );
  for (const expected of [
    'data-next-attention-status="AWAITING_SELECTION"',
    'data-semantics="DREAM_RETURN_ATTENTION_ONLY"',
    'data-evidence-role="NOT_EVIDENCE"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-outcome-changed="false"',
    'data-mingli-write-allowed="false"',
    'data-decision-write-allowed="false"',
    'data-knowledge-write-allowed="false"',
    "留给下一次相遇",
    "你想继续观察什么？",
    "由这次已提交的梦中经历整理",
    "不改变三棵树",
    "不写入命理",
  ]) {
    assertIncludes("awaiting-copy", awaitingMarkup, expected);
  }
  assertEqual(
    "server-option-count",
    (awaitingMarkup.match(/data-observation-ref=/g) ?? []).length,
    3,
  );
  assertEqual(
    "server-option-order",
    [...awaitingMarkup.matchAll(/data-observation-ref="([^"]+)"/g)]
      .map((match) => match[1])
      .join(","),
    options.map(({ observation_ref }) => observation_ref).join(","),
  );

  const selection = {
    attention_ref: "attention-contract",
    attention_hash: "b".repeat(64),
    ...options[0],
  };
  const selectedMarkup = renderToStaticMarkup(
    React.createElement(DreamNextAttentionCard, {
      attention: { ...prompt, status: "SELECTED", selection },
      busy: false,
      echo,
    }),
  );
  assertIncludes(
    "selected-status",
    selectedMarkup,
    'data-next-attention-status="SELECTED"',
  );
  assertIncludes("selected-copy", selectedMarkup, "世界已记住");
  assertIncludes("selected-label", selectedMarkup, options[0].label);
  assertEqual(
    "selected-has-no-options",
    (selectedMarkup.match(/<button/g) ?? []).length,
    0,
  );

  for (const [label, unsafePrompt] of [
    ["wrong-version", { ...prompt, contract_version: "unsafe" }],
    ["echo-mismatch", { ...prompt, source_echo_ref: "another-echo" }],
    ["too-few-options", { ...prompt, options: options.slice(0, 1) }],
    ["evidence-role", { ...prompt, evidence_role: "OWNER_EVIDENCE" }],
    ["tree-order", { ...prompt, tree_candidate_set_or_order_changed: true }],
    ["question", { ...prompt, question_changed: true }],
    ["answer", { ...prompt, answer_changed: true }],
    ["npc-choice", { ...prompt, npc_choice_changed: true }],
    ["outcome", { ...prompt, outcome_changed: true }],
    ["mingli-write", { ...prompt, mingli_write_allowed: true }],
    ["decision-write", { ...prompt, decision_write_allowed: true }],
    ["knowledge-write", { ...prompt, knowledge_write_allowed: true }],
    [
      "selection-status-mismatch",
      { ...prompt, status: "SELECTED", selection: null },
    ],
  ]) {
    const markup = renderToStaticMarkup(
      React.createElement(DreamNextAttentionCard, {
        attention: unsafePrompt,
        busy: false,
        echo,
        onSelect: () => {},
      }),
    );
    assertIncludes(
      `${label}-withheld`,
      markup,
      'data-next-attention-status="WITHHELD"',
    );
    for (const option of options) {
      assertExcludes(`${label}-option-hidden`, markup, option.summary);
    }
  }

  const openingMarkup = renderToStaticMarkup(
    React.createElement(DreamOpeningAttention, {
      attention: openingAttention,
      targetEncounterRef: openingAttention.target_encounter_ref,
      targetTreeRef: openingAttention.target_tree_ref,
    }),
  );
  for (const expected of [
    'data-opening-attention-status="REMEMBERED"',
    'data-source-tree-ref="tree-career"',
    'data-target-tree-ref="tree-career"',
    'data-target-encounter-ref="encounter-return-visit"',
    'data-semantics="DREAM_RETURN_ATTENTION_ONLY"',
    'data-evidence-role="NOT_EVIDENCE"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-outcome-changed="false"',
    'data-mingli-write-allowed="false"',
    'data-decision-write-allowed="false"',
    'data-knowledge-write-allowed="false"',
    'data-read-only="true"',
    "上次留下的观察目标",
    "世界已记住",
    options[0].label,
    options[0].summary,
    "不预告答案",
  ]) {
    assertIncludes("opening", openingMarkup, expected);
  }
  for (const [field, value] of [
    ["extra_key", true],
    ["contract_version", "unsafe"],
    ["application_hash", "z".repeat(64)],
    ["semantics", "OWNER_MINGLI_EVIDENCE"],
    ["target_tree_ref", "tree-wealth"],
    ["evidence_role", "OWNER_EVIDENCE"],
    ["tree_candidate_set_or_order_changed", true],
    ["question_changed", true],
    ["answer_changed", true],
    ["npc_choice_changed", true],
    ["outcome_changed", true],
    ["mingli_write_allowed", true],
    ["decision_write_allowed", true],
    ["knowledge_write_allowed", true],
  ]) {
    const markup = renderToStaticMarkup(
      React.createElement(DreamOpeningAttention, {
        attention: { ...openingAttention, [field]: value },
        targetEncounterRef: openingAttention.target_encounter_ref,
        targetTreeRef: openingAttention.target_tree_ref,
      }),
    );
    assertEqual(`unsafe-opening-${field}`, markup, "");
  }

  let capturedUrl = null;
  let capturedInit = null;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    capturedUrl = String(url);
    capturedInit = init;
    return new Response(
      JSON.stringify({
        kind: "GROVE",
        grove: { next_attention: { ...prompt, status: "SELECTED", selection } },
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  };
  try {
    await selectDreamNextAttention(prompt, options[0].observation_ref);
  } finally {
    globalThis.fetch = originalFetch;
  }
  assertEqual("command-url", capturedUrl, "/api/v60/dream/command");
  assertEqual("command-method", capturedInit?.method, "POST");
  const commandPayload = JSON.parse(String(capturedInit?.body));
  assertEqual(
    "command-name",
    commandPayload.command,
    "SELECT_NEXT_ATTENTION",
  );
  assertEqual(
    "command-encounter-ref",
    commandPayload.encounter_ref,
    prompt.source_encounter_ref,
  );
  assertEqual(
    "command-expected-version",
    commandPayload.expected_version,
    prompt.source_encounter_version,
  );
  assertEqual(
    "command-target",
    commandPayload.target_ref,
    options[0].observation_ref,
  );
  assertEqual("command-choice-null", commandPayload.choice_id, null);
  assertIncludes(
    "command-idempotency",
    commandPayload.idempotency_key,
    "SELECT_NEXT_ATTENTION",
  );

  capturedUrl = null;
  let forgedError = null;
  try {
    await selectDreamNextAttention(prompt, "browser-invented-observation");
  } catch (error) {
    forgedError = error instanceof Error ? error.message : String(error);
  }
  assertEqual(
    "invented-option-rejected",
    forgedError,
    "dream_return_attention_option_not_server_issued",
  );
  assertEqual("invented-option-not-sent", capturedUrl, null);
} finally {
  await vite.close();
}

const report = {
  promptVersion: prompt.contract_version,
  openingVersion: openingAttention.contract_version,
  optionCount: options.length,
  optionOrderPreserved: true,
  commandEndpoint: "/api/v60/dream/command",
  command: "SELECT_NEXT_ATTENTION",
  ownerMingliEvidenceAllowed: false,
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
