import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/dream-reading-lens-continuity",
);
const chromePath =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
});
await context.addCookies([
  {
    name: "abu_v60_session",
    value: sessionToken,
    url: new URL(targetUrl).origin,
    httpOnly: true,
    sameSite: "Lax",
  },
]);

const page = await context.newPage();
const failures = [];
const observedRequests = [];
const stages = {};
const expectedDomains = ["career", "wealth", "relationship"];

const fail = (message) => failures.push(message);
const sameJson = (left, right) => JSON.stringify(left) === JSON.stringify(right);

page.on("console", (message) => {
  if (message.type() === "error") fail(`console:${message.text()}`);
});
page.on("pageerror", (error) => fail(`page:${error.message}`));
page.on("requestfailed", (request) => {
  fail(
    `request:${request.method()} ${request.url()} ${request.failure()?.errorText}`,
  );
});
page.on("request", (request) => {
  let body = null;
  if (request.method() === "POST") {
    try {
      body = request.postDataJSON();
    } catch {
      body = request.postData();
    }
  }
  observedRequests.push({
    method: request.method(),
    url: request.url(),
    pathname: new URL(request.url()).pathname,
    body,
  });
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    fail(`response:${response.status()} ${response.url()}`);
  }
});

const readJson = async (pathname) =>
  page.evaluate(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}:${response.status}`);
    return response.json();
  }, pathname);

const homeIdentity = (home) => ({
  caseRef: home.case.case_ref,
  readingRef: home.mingli.reading.reading_ref,
  readingHash: home.mingli.reading.reading_hash,
  decisionRef: home.lab.mechanism_comparison.decision_ref,
  decisionHash: home.lab.mechanism_comparison.decision_hash,
  sourceReviewVectorRef: home.mingli.reading.source_review_vector_ref,
  sourceReviewVectorHash: home.mingli.reading.source_review_vector_hash,
});

const clickDreamPost = async (
  locator,
  { command = null, pathnamePrefix },
) => {
  const responsePromise = page.waitForResponse((response) => {
    const request = response.request();
    if (request.method() !== "POST") return false;
    const pathname = new URL(response.url()).pathname;
    if (!pathname.startsWith(pathnamePrefix)) return false;
    if (command === null) return true;
    try {
      return request.postDataJSON()?.command === command;
    } catch {
      return false;
    }
  });
  await locator.click();
  const response = await responsePromise;
  if (!response.ok()) fail(`command:${command ?? pathnamePrefix}:${response.status()}`);
  return response.json();
};

const waitForState = async (state, timeout = 10_000) => {
  await page
    .locator(`.life-tree-experience[data-state="${state}"]`)
    .waitFor({ state: "visible", timeout });
};

let canonicalObservations = [];
const inspectLens = async ({
  forbiddenValues = [],
  mode,
  stage,
}) => {
  const lens = page.locator(
    `.dream-reading-observation-lens[data-mode="${mode}"]`,
  );
  await lens.waitFor({ state: "visible" });
  const observationRows = await lens.locator("[data-domain]").evaluateAll(
    (nodes) =>
      nodes.map((node) => ({
        domain: node.getAttribute("data-domain"),
        label: node.querySelector("strong")?.textContent?.trim() ?? "",
        question: node.querySelector("p")?.textContent?.trim() ?? "",
        width: node.getBoundingClientRect().width,
      })),
  );
  const observations = observationRows.map(
    ({ domain, label, question }) => ({ domain, label, question }),
  );
  if (!sameJson(observations, canonicalObservations)) {
    fail(`${stage}:observation-projection-drift`);
  }
  if (
    observationRows.length !== 3 ||
    observationRows.map(({ domain }) => domain).join(",") !==
      expectedDomains.join(",")
  ) {
    fail(`${stage}:domain-order-invalid`);
  }
  if (
    observationRows.length === 3 &&
    Math.max(...observationRows.map(({ width }) => width)) -
      Math.min(...observationRows.map(({ width }) => width)) >
      1
  ) {
    fail(`${stage}:domains-not-equal-width`);
  }

  const attributes = await lens.evaluate((node) => ({
    canonicalWriteAllowed:
      node.getAttribute("data-canonical-write-allowed") === "true",
    decisionRole: node.getAttribute("data-decision-role"),
    futureEvidenceIncluded:
      node.getAttribute("data-future-evidence-included") === "true",
    pointerEvents: getComputedStyle(node).pointerEvents,
    semantics: node.getAttribute("data-semantics"),
    treeCandidateSetOrOrderChanged:
      node.getAttribute("data-tree-candidate-set-or-order-changed") === "true",
  }));
  if (
    attributes.semantics !== "ATTENTION_WINDOW_ONLY" ||
    attributes.decisionRole !==
      "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER" ||
    attributes.treeCandidateSetOrOrderChanged !== false ||
    attributes.futureEvidenceIncluded !== false ||
    attributes.canonicalWriteAllowed !== false ||
    attributes.pointerEvents !== "none"
  ) {
    fail(`${stage}:lens-boundary-invalid`);
  }

  const markup = await lens.evaluate((node) => node.outerHTML);
  for (const forbiddenValue of forbiddenValues.filter(Boolean)) {
    if (markup.includes(String(forbiddenValue))) {
      fail(`${stage}:reveal-value-leaked-into-lens`);
    }
  }
  for (const forbiddenToken of ["selected", "primary", "rank"]) {
    if (markup.toLowerCase().includes(forbiddenToken)) {
      fail(`${stage}:ranking-token:${forbiddenToken}`);
    }
  }

  const metrics = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    bodyScrollWidth: document.body.scrollWidth,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
  }));
  if (
    metrics.bodyScrollHeight > metrics.viewportHeight ||
    metrics.bodyScrollWidth > metrics.viewportWidth
  ) {
    fail(`${stage}:document-overflow`);
  }
  const screenshotPath = path.join(artifactDirectory, `${stage}.png`);
  await page.screenshot({ path: screenshotPath });
  stages[stage] = { attributes, metrics, observations, screenshotPath };
};

const dreamUrl = new URL(targetUrl);
dreamUrl.searchParams.set("scope", "dream");
dreamUrl.searchParams.delete("view");
await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
await page.locator(".dream-grove-scene").waitFor({ state: "visible" });

const homeBefore = await readJson("/api/v60/experience/home");
const initialHomeIdentity = homeIdentity(homeBefore);
canonicalObservations = expectedDomains.map((domain) => {
  const matches = homeBefore.mingli.reading_brief.life_domains.filter(
    (observation) => observation.domain === domain,
  );
  if (matches.length !== 1) {
    fail(`home:domain-contract:${domain}:${matches.length}`);
    return { domain, label: "", question: "" };
  }
  return {
    domain,
    label: matches[0].label.trim(),
    question: matches[0].question.trim(),
  };
});

const initialEntry = await readJson("/api/v60/dream/entry");
if (initialEntry.kind !== "GROVE") {
  throw new Error("dream_continuity_audit_requires_grove_entry");
}
const initialCandidateOrder = initialEntry.grove.candidates.map(
  ({ candidate_ref, display_order }) => ({ candidate_ref, display_order }),
);
if (
  initialCandidateOrder.length !== 3 ||
  new Set(initialCandidateOrder.map(({ candidate_ref }) => candidate_ref)).size !==
    3
) {
  fail("grove:initial-candidate-contract-invalid");
}

await inspectLens({ mode: "grove", stage: "00-grove" });
const selectedCandidateRef = initialCandidateOrder[0].candidate_ref;
await clickDreamPost(page.locator(".grove-tree-choice").first(), {
  pathnamePrefix: `/api/v60/dream/grove/${encodeURIComponent(
    selectedCandidateRef,
  )}`,
});
await waitForState("observing");
await inspectLens({ mode: "encounter", stage: "01-observing" });

for (const [selector, command] of [
  [".tree-organ-evidence_leaf_world", "OBSERVE_EVIDENCE"],
  [".tree-organ-evidence_leaf_structure", "OBSERVE_EVIDENCE"],
  [".tree-organ-structure_branch", "OBSERVE_STRUCTURE"],
  [".tree-organ-question_flower", "OPEN_QUESTION"],
]) {
  const organ = page.locator(selector);
  await organ.waitFor({ state: "visible" });
  await clickDreamPost(organ, {
    command,
    pathnamePrefix: "/api/v60/dream/command",
  });
}
await waitForState("question_open");
await inspectLens({ mode: "encounter", stage: "02-question-open" });

await clickDreamPost(page.locator(".answer-options button").first(), {
  command: "SEAL_ANSWER",
  pathnamePrefix: "/api/v60/dream/command",
});
await waitForState("waiting_for_world");
await inspectLens({ mode: "encounter", stage: "03-waiting-for-world" });

// Opportunity episodes can be scheduled several one-minute world ticks ahead.
// Keep this a normal runtime wait: the app polls the canonical encounter while
// the World owner settles and Dream projects the committed outcome.
await waitForState("reveal_ready", 420_000);
await inspectLens({ mode: "encounter", stage: "04-reveal-ready" });

const revealedSnapshot = await clickDreamPost(
  page.locator(".question-band .primary-command"),
  {
    command: "REVEAL",
    pathnamePrefix: "/api/v60/dream/command",
  },
);
await waitForState("revealed");
const revealValues = [
  revealedSnapshot.reveal?.reveal_ref,
  revealedSnapshot.reveal?.reveal_json?.decision_ref,
  revealedSnapshot.reveal?.reveal_json?.actual_event,
  ...(revealedSnapshot.reveal?.reveal_json?.actual_evidence ?? []).flatMap(
    ({ evidence_ref, summary }) => [evidence_ref, summary],
  ),
];
await inspectLens({
  forbiddenValues: revealValues,
  mode: "encounter",
  stage: "05-revealed",
});

await clickDreamPost(page.locator(".question-band .primary-command"), {
  command: "RECONCILE",
  pathnamePrefix: "/api/v60/dream/command",
});
await waitForState("completed");
await inspectLens({
  forbiddenValues: revealValues,
  mode: "encounter",
  stage: "06-completed",
});

await page.reload({ waitUntil: "networkidle" });
await waitForState("completed");
await inspectLens({
  forbiddenValues: revealValues,
  mode: "encounter",
  stage: "07-completed-refresh",
});

const returnedEntry = await clickDreamPost(
  page.locator(".grove-return-command"),
  {
    command: "RETURN_TO_GROVE",
    pathnamePrefix: "/api/v60/dream/command",
  },
);
await page.locator(".dream-grove-scene").waitFor({ state: "visible" });
if (returnedEntry.kind !== "GROVE") {
  fail("grove:return-command-did-not-return-grove");
}
const returnedCandidateOrder = (returnedEntry.grove?.candidates ?? []).map(
  ({ candidate_ref, display_order }) => ({ candidate_ref, display_order }),
);
if (!sameJson(returnedCandidateOrder, initialCandidateOrder)) {
  fail("grove:candidate-ref-or-order-changed");
}
await inspectLens({ mode: "grove", stage: "08-returned-grove" });

const homeAfter = await readJson("/api/v60/experience/home");
const finalHomeIdentity = homeIdentity(homeAfter);
if (!sameJson(finalHomeIdentity, initialHomeIdentity)) {
  fail("home:canonical-identity-changed");
}

const postRequests = observedRequests.filter(
  ({ method }) => method === "POST",
);
const expectedCommandSequence = [
  "OBSERVE_EVIDENCE",
  "OBSERVE_EVIDENCE",
  "OBSERVE_STRUCTURE",
  "OPEN_QUESTION",
  "SEAL_ANSWER",
  "REVEAL",
  "RECONCILE",
  "RETURN_TO_GROVE",
];
const commandSequence = postRequests
  .filter(({ pathname }) => pathname === "/api/v60/dream/command")
  .map(({ body }) =>
    typeof body === "object" && body !== null ? body.command : null,
  );
const groveSelectionPosts = postRequests.filter(({ pathname }) =>
  pathname.startsWith("/api/v60/dream/grove/"),
);
const nonDreamPosts = postRequests.filter(
  ({ pathname }) =>
    pathname !== "/api/v60/dream/command" &&
    !pathname.startsWith("/api/v60/dream/grove/"),
);
if (
  groveSelectionPosts.length !== 1 ||
  groveSelectionPosts[0].pathname !==
    `/api/v60/dream/grove/${encodeURIComponent(selectedCandidateRef)}`
) {
  fail("network:grove-selection-post-contract-invalid");
}
if (!sameJson(commandSequence, expectedCommandSequence)) {
  fail(`network:dream-command-sequence:${JSON.stringify(commandSequence)}`);
}
if (nonDreamPosts.length !== 0) {
  fail(
    `network:non-dream-post:${nonDreamPosts
      .map(({ pathname }) => pathname)
      .join(",")}`,
  );
}
const forbiddenWritePosts = postRequests.filter(({ pathname }) =>
  [
    "/api/v60/experience/home",
    "/api/v60/mingli",
    "mechanism-comparison",
    "decision",
    "case",
  ].some((fragment) => pathname.includes(fragment)),
);
if (forbiddenWritePosts.length !== 0) {
  fail(
    `network:home-mingli-decision-case-write:${forbiddenWritePosts
      .map(({ pathname }) => pathname)
      .join(",")}`,
  );
}

const audit = {
  targetUrl: dreamUrl.toString(),
  initialHomeIdentity,
  finalHomeIdentity,
  canonicalObservations,
  initialCandidateOrder,
  returnedCandidateOrder,
  selectedCandidateRef,
  postRequests: postRequests.map(({ body, method, pathname }) => ({
    body,
    method,
    pathname,
  })),
  stages,
  failures,
};
await writeFile(
  path.join(artifactDirectory, "runtime-audit.json"),
  `${JSON.stringify(audit, null, 2)}\n`,
  "utf8",
);

await context.close();
await browser.close();
if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify(audit, null, 2));
