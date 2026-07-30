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

const candidateRef = "candidate-wenxi";
const encounterRef = "encounter-wenxi-return";
const treeRef = "tree-wenxi";
const requiredOrganRefs = [
  "organ-evidence-world",
  "organ-evidence-structure",
  "organ-structure-branch",
];
const response = {
  actual_event: "后来，闻溪把共同完成的工作连同署名一起公开。",
  evidence_refs: ["evidence-public-credit", "evidence-shared-release"],
  evidence_summaries: ["公开记录保留了共同署名。", "交付物按约定共同发布。"],
  material_count: 2,
};

const falseFlags = [
  "tree_candidate_set_or_order_changed",
  "question_changed",
  "answer_changed",
  "npc_choice_changed",
  "outcome_changed",
  "mingli_write_allowed",
  "decision_write_allowed",
  "knowledge_write_allowed",
];

const pending = {
  contract_version: "v60.dream-pending-attention.001",
  attention_ref: "attention-wenxi-credit",
  attention_hash: "a".repeat(64),
  source_encounter_ref: "encounter-wenxi-first",
  source_encounter_version: 8,
  source_echo_ref: "echo-wenxi-first",
  source_echo_hash: "b".repeat(64),
  source_candidate_ref: candidateRef,
  source_candidate_hash: "c".repeat(64),
  tree_ref: treeRef,
  observation_ref: "observation-credit",
  label: "再看结果如何落地",
  summary: "继续观察共同完成的工作是否留下明确署名。",
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

const followThroughFor = (status, observedCount, worldResponse = null) => ({
  contract_version: "v60.dream-attention-follow-through.001",
  application_ref: "application-wenxi-credit",
  application_hash: "d".repeat(64),
  attention_ref: pending.attention_ref,
  attention_hash: pending.attention_hash,
  source_encounter_ref: pending.source_encounter_ref,
  source_encounter_version: pending.source_encounter_version,
  source_echo_ref: pending.source_echo_ref,
  source_echo_hash: pending.source_echo_hash,
  source_candidate_ref: pending.source_candidate_ref,
  source_candidate_hash: pending.source_candidate_hash,
  source_tree_ref: treeRef,
  target_tree_ref: treeRef,
  target_encounter_ref: encounterRef,
  observation_ref: pending.observation_ref,
  label: pending.label,
  summary: pending.summary,
  status,
  progress: {
    required_count: 3,
    observed_count: observedCount,
    required_organ_refs: [...requiredOrganRefs],
    observed_organ_refs: requiredOrganRefs.slice(0, observedCount),
  },
  world_response: worldResponse,
  semantic_match_status:
    worldResponse === null
      ? "NOT_AVAILABLE_BEFORE_REVEAL"
      : "SEMANTIC_MATCH_NOT_EVALUATED",
  answer_status: "NOT_EVALUATED",
  semantics: "DREAM_ATTENTION_FOLLOW_THROUGH_ONLY",
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
});

const statusCases = [
  {
    status: "OBSERVING",
    observedCount: 2,
    encounterStatus: "OBSERVING",
    worldResponse: null,
  },
  {
    status: "OBSERVATIONS_COMPLETE",
    observedCount: 3,
    encounterStatus: "QUESTION_OPEN",
    worldResponse: null,
  },
  {
    status: "AWAITING_WORLD_RESPONSE",
    observedCount: 3,
    encounterStatus: "WAITING_FOR_WORLD",
    worldResponse: null,
  },
  {
    status: "WORLD_RESPONSE_READY_HIDDEN",
    observedCount: 3,
    encounterStatus: "REVEAL_READY",
    worldResponse: null,
  },
  {
    status: "WORLD_RESPONSE_AVAILABLE",
    observedCount: 3,
    encounterStatus: "REVEALED",
    worldResponse: response,
  },
  {
    status: "RECONCILED_NOT_EVALUATED",
    observedCount: 3,
    encounterStatus: "COMPLETED",
    worldResponse: response,
  },
  {
    status: "RETURNED_NOT_EVALUATED",
    observedCount: 3,
    encounterStatus: null,
    worldResponse: response,
  },
];

const snapshotFor = ({ encounterStatus, observedCount, worldResponse }) => ({
  encounter: {
    encounter_ref: encounterRef,
    status: encounterStatus,
    state: {
      observed_organs: requiredOrganRefs.slice(0, observedCount),
    },
  },
  tree: {
    tree_ref: treeRef,
    organs: [
      {
        key: "evidence_leaf_world",
        organ_ref: requiredOrganRefs[0],
        role: "EVIDENCE_LEAF",
      },
      {
        key: "evidence_leaf_structure",
        organ_ref: requiredOrganRefs[1],
        role: "EVIDENCE_LEAF",
      },
      {
        key: "structure_branch",
        organ_ref: requiredOrganRefs[2],
        role: "STRUCTURE_BRANCH",
      },
      {
        key: "question_flower",
        organ_ref: "organ-question-flower",
        role: "QUESTION_FLOWER",
      },
    ],
  },
  reveal:
    worldResponse === null
      ? null
      : {
          reveal_json: {
            actual_event: worldResponse.actual_event,
            actual_evidence: worldResponse.evidence_refs.map(
              (evidenceRef, index) => ({
                evidence_ref: evidenceRef,
                summary: worldResponse.evidence_summaries[index],
              }),
            ),
          },
        },
});

try {
  const {
    isDreamAttentionFollowThroughDisplayable,
    isDreamPendingAttentionDisplayable,
    isDreamPendingAttentionSupplied,
  } = await vite.ssrLoadModule("/src/dreamAttentionFollowThroughTypes.ts");
  const { DreamAttentionFollowThroughCard, DreamReturnedAttentionSummary } =
    await vite.ssrLoadModule(
      "/src/components/DreamAttentionFollowThroughCard.tsx",
    );
  const { DreamPendingAttentionBadge } = await vite.ssrLoadModule(
    "/src/components/DreamPendingAttentionBadge.tsx",
  );

  assertEqual(
    "valid-pending",
    isDreamPendingAttentionDisplayable(pending, {
      candidateRefs: [candidateRef],
    }),
    true,
  );
  const pendingMarkup = renderToStaticMarkup(
    React.createElement(DreamPendingAttentionBadge, {
      candidateRef,
      pending,
    }),
  );
  for (const expected of [
    'data-pending-attention-status="PENDING_SAME_TREE_RETURN"',
    'data-source-candidate-ref="candidate-wenxi"',
    'data-tree-candidate-set-or-order-changed="false"',
    'data-question-changed="false"',
    'data-answer-changed="false"',
    'data-npc-choice-changed="false"',
    'data-outcome-changed="false"',
    'data-mingli-write-allowed="false"',
    'data-decision-write-allowed="false"',
    'data-knowledge-write-allowed="false"',
    'data-read-only="true"',
    "上次留下的观察",
    pending.label,
    "回到这棵树继续",
  ]) {
    assertIncludes("pending-markup", pendingMarkup, expected);
  }

  for (const testCase of statusCases) {
    const followThrough = followThroughFor(
      testCase.status,
      testCase.observedCount,
      testCase.worldResponse,
    );
    const observedOrganRefs = requiredOrganRefs.slice(
      0,
      testCase.observedCount,
    );
    assertEqual(
      `valid-status-${testCase.status}`,
      isDreamAttentionFollowThroughDisplayable(followThrough, {
        targetEncounterRef: encounterRef,
        targetTreeRef: treeRef,
        requiredOrganRefs,
        observedOrganRefs,
        expectedStatus: testCase.status,
        worldResponse: testCase.worldResponse,
        candidateRefs: [candidateRef],
      }),
      true,
    );

    const markup =
      testCase.status === "RETURNED_NOT_EVALUATED"
        ? renderToStaticMarkup(
            React.createElement(DreamReturnedAttentionSummary, {
              candidateRefs: [candidateRef],
              followThrough,
            }),
          )
        : renderToStaticMarkup(
            React.createElement(DreamAttentionFollowThroughCard, {
              followThrough,
              snapshot: snapshotFor(testCase),
            }),
          );
    assertIncludes(
      `status-markup-${testCase.status}`,
      markup,
      `data-follow-through-status="${testCase.status}"`,
    );
    assertIncludes(
      `progress-${testCase.status}`,
      markup,
      `data-observed-count="${testCase.observedCount}"`,
    );
    assertIncludes(
      `semantic-${testCase.status}`,
      markup,
      `data-semantic-match-status="${
        testCase.worldResponse === null
          ? "NOT_AVAILABLE_BEFORE_REVEAL"
          : "SEMANTIC_MATCH_NOT_EVALUATED"
      }"`,
    );
    if (testCase.worldResponse === null) {
      assertExcludes(
        `pre-reveal-world-hidden-${testCase.status}`,
        markup,
        "data-world-response-material-count",
      );
    } else {
      assertIncludes(
        `post-reveal-world-visible-${testCase.status}`,
        markup,
        'data-world-response-material-count="2"',
      );
      assertIncludes(
        `post-reveal-not-evaluated-${testCase.status}`,
        markup,
        "未评价对应关系",
      );
    }
  }

  const authoredUnsortedSnapshot = snapshotFor(statusCases[4]);
  authoredUnsortedSnapshot.reveal.reveal_json.actual_evidence.reverse();
  const normalizedMarkup = renderToStaticMarkup(
    React.createElement(DreamAttentionFollowThroughCard, {
      followThrough: followThroughFor(
        "WORLD_RESPONSE_AVAILABLE",
        3,
        response,
      ),
      snapshot: authoredUnsortedSnapshot,
    }),
  );
  assertIncludes(
    "authored-unsorted-normalized",
    normalizedMarkup,
    'data-follow-through-status="WORLD_RESPONSE_AVAILABLE"',
  );
  assertEqual(
    "normalized-evidence-order",
    [...normalizedMarkup.matchAll(/data-evidence-ref="([^"]+)"/g)]
      .map((match) => match[1])
      .join(","),
    response.evidence_refs.join(","),
  );

  const preReveal = followThroughFor(
    "WORLD_RESPONSE_READY_HIDDEN",
    3,
    null,
  );
  const postReveal = followThroughFor(
    "WORLD_RESPONSE_AVAILABLE",
    3,
    response,
  );
  const invalidFollowThroughCases = [
    [
      "pre-reveal-response-not-null",
      { ...preReveal, world_response: response },
      {},
    ],
    [
      "post-reveal-response-null",
      { ...postReveal, world_response: null },
      {},
    ],
    [
      "post-reveal-semantic-not-evaluated-required",
      {
        ...postReveal,
        semantic_match_status: "NOT_AVAILABLE_BEFORE_REVEAL",
      },
      {},
    ],
    [
      "observed-count-mismatch",
      {
        ...preReveal,
        progress: { ...preReveal.progress, observed_count: 2 },
      },
      {},
    ],
    [
      "observed-not-required-subset",
      {
        ...preReveal,
        progress: {
          ...preReveal.progress,
          observed_organ_refs: [
            requiredOrganRefs[0],
            requiredOrganRefs[1],
            "organ-invented",
          ],
        },
      },
      {},
    ],
    [
      "observed-subset-order",
      {
        ...preReveal,
        progress: {
          ...preReveal.progress,
          observed_organ_refs: [
            requiredOrganRefs[1],
            requiredOrganRefs[0],
            requiredOrganRefs[2],
          ],
        },
      },
      {},
    ],
    [
      "required-organ-count",
      {
        ...preReveal,
        progress: {
          ...preReveal.progress,
          required_organ_refs: requiredOrganRefs.slice(0, 2),
        },
      },
      {},
    ],
    [
      "wrong-candidate-binding",
      postReveal,
      { candidateRefs: ["candidate-heyang"] },
    ],
    [
      "wrong-encounter-binding",
      postReveal,
      { targetEncounterRef: "encounter-heyang" },
    ],
    [
      "wrong-tree-binding",
      postReveal,
      { targetTreeRef: "tree-heyang" },
    ],
    [
      "source-target-tree-mismatch",
      { ...postReveal, source_tree_ref: "tree-heyang" },
      {},
    ],
    [
      "invalid-hash",
      { ...postReveal, application_hash: "not-a-sha256" },
      {},
    ],
    ["extra-top-level-field", { ...postReveal, invented: true }, {}],
    [
      "extra-progress-field",
      {
        ...postReveal,
        progress: { ...postReveal.progress, invented: true },
      },
      {},
    ],
    [
      "extra-world-response-field",
      {
        ...postReveal,
        world_response: { ...response, invented: true },
      },
      {},
    ],
    [
      "unsorted-world-evidence",
      {
        ...postReveal,
        world_response: {
          ...response,
          evidence_refs: ["evidence-shared-release", "evidence-public-credit"],
          evidence_summaries: [
            "交付物按约定共同发布。",
            "公开记录保留了共同署名。",
          ],
        },
      },
      {},
    ],
  ];

  for (const [label, candidate, bindings] of invalidFollowThroughCases) {
    assertEqual(
      label,
      isDreamAttentionFollowThroughDisplayable(candidate, bindings),
      false,
    );
  }

  for (const flag of falseFlags) {
    assertEqual(
      `follow-through-flag-${flag}`,
      isDreamAttentionFollowThroughDisplayable({
        ...postReveal,
        [flag]: true,
      }),
      false,
    );
    assertEqual(
      `pending-flag-${flag}`,
      isDreamPendingAttentionDisplayable({
        ...pending,
        [flag]: true,
      }),
      false,
    );
  }
  assertEqual(
    "follow-through-read-only",
    isDreamAttentionFollowThroughDisplayable({
      ...postReveal,
      read_only: false,
    }),
    false,
  );
  assertEqual(
    "pending-read-only",
    isDreamPendingAttentionDisplayable({ ...pending, read_only: false }),
    false,
  );

  for (const [label, unsafePending, bindings] of [
    [
      "pending-wrong-candidate",
      pending,
      { candidateRefs: ["candidate-heyang"] },
    ],
    [
      "pending-invalid-hash",
      { ...pending, attention_hash: "not-a-sha256" },
      {},
    ],
    ["pending-extra-field", { ...pending, invented: true }, {}],
  ]) {
    assertEqual(
      label,
      isDreamPendingAttentionDisplayable(unsafePending, bindings),
      false,
    );
  }
  assertEqual(
    "invalid-pending-remains-supplied-for-fail-closed-choice-suppression",
    isDreamPendingAttentionSupplied({
      ...pending,
      contract_version: "v60.dream-pending-attention.tampered",
    }),
    true,
  );
  assertEqual(
    "null-pending-is-not-supplied",
    isDreamPendingAttentionSupplied(null),
    false,
  );
  assertEqual(
    "pending-wrong-candidate-hidden",
    renderToStaticMarkup(
      React.createElement(DreamPendingAttentionBadge, {
        candidateRef: "candidate-heyang",
        pending,
      }),
    ),
    "",
  );
} finally {
  await vite.close();
}

const report = {
  pendingVersion: pending.contract_version,
  followThroughVersion: followThroughFor("OBSERVING", 0).contract_version,
  validStatuses: statusCases.map(({ status }) => status),
  requiredOrganCount: requiredOrganRefs.length,
  preRevealWorldResponse: null,
  revealSemanticStatus: "SEMANTIC_MATCH_NOT_EVALUATED",
  evidenceRefsSortedAndUnique: true,
  flagsRemainFalse: falseFlags,
  failures,
};

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (failures.length > 0) process.exitCode = 1;
