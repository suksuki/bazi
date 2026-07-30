import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/dream-reading-lens",
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

page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console:${message.text()}`);
});
page.on("pageerror", (error) => failures.push(`page:${error.message}`));
page.on("request", (request) => {
  observedRequests.push({
    method: request.method(),
    url: request.url(),
  });
});
page.on("requestfailed", (request) => {
  failures.push(
    `request:${request.method()} ${request.url()} ${request.failure()?.errorText}`,
  );
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    failures.push(`response:${response.status()} ${response.url()}`);
  }
});

const url = new URL(targetUrl);
url.searchParams.set("scope", "dream");
url.searchParams.delete("view");
await page.goto(url.toString(), { waitUntil: "networkidle" });

const lens = page.locator(".dream-reading-observation-lens");
await lens.waitFor({ state: "visible" });
const home = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home_api:${response.status}`);
  return response.json();
});
const rendered = await lens.locator("[data-domain]").evaluateAll((nodes) =>
  nodes.map((node) => ({
    domain: node.getAttribute("data-domain"),
    label: node.querySelector("strong")?.textContent?.trim() ?? "",
    question: node.querySelector("p")?.textContent?.trim() ?? "",
    width: node.getBoundingClientRect().width,
  })),
);
const expectedDomains = ["career", "wealth", "relationship"];
const expected = expectedDomains.map((domain) => {
  const matches = home.mingli.reading_brief.life_domains.filter(
    (item) => item.domain === domain,
  );
  if (matches.length !== 1) {
    failures.push(`api:domain-contract:${domain}:${matches.length}`);
    return { domain, label: "", question: "" };
  }
  return {
    domain,
    label: matches[0].label.trim(),
    question: matches[0].question.trim(),
  };
});
for (const [index, observation] of rendered.entries()) {
  const source = expected[index];
  if (
    observation.domain !== source?.domain ||
    observation.label !== source?.label ||
    observation.question !== source?.question
  ) {
    failures.push(`lens:reading-projection-mismatch:${index}`);
  }
}
if (rendered.length !== 3) failures.push(`lens:domain-count:${rendered.length}`);
if (
  rendered.length === 3 &&
  Math.max(...rendered.map((item) => item.width)) -
    Math.min(...rendered.map((item) => item.width)) >
    1
) {
  failures.push("lens:domains-not-equal-width");
}

const comparison = home.lab.mechanism_comparison;
const expectedAttentionRecorded =
  comparison.status === "RESOLVED" && comparison.decision_ref !== null;
const lensAttributes = await lens.evaluate((node) => ({
  attentionOrderRecorded:
    node.getAttribute("data-attention-order-recorded") === "true",
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
if (lensAttributes.attentionOrderRecorded !== expectedAttentionRecorded) {
  failures.push("lens:attention-recording-mismatch");
}
if (
  lensAttributes.semantics !== "ATTENTION_WINDOW_ONLY" ||
  lensAttributes.decisionRole !==
    "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER" ||
  lensAttributes.treeCandidateSetOrOrderChanged !== false ||
  lensAttributes.futureEvidenceIncluded !== false ||
  lensAttributes.canonicalWriteAllowed !== false ||
  lensAttributes.pointerEvents !== "none"
) {
  failures.push("lens:authority-boundary-mismatch");
}

const lensMarkup = await lens.evaluate((node) => node.outerHTML);
const lensText = await lens.innerText();
for (const expectedCopy of [
  "三条等权",
  "系统不会据此改动三棵树的候选或顺序",
  "不预测结果",
  "不回写命理",
]) {
  if (!lensText.includes(expectedCopy)) {
    failures.push(`lens:missing-copy:${expectedCopy}`);
  }
}
const forbiddenSecrets = [
  home.mingli.reading.reading_ref,
  home.mingli.reading.reading_hash,
  comparison.decision_ref,
  comparison.decision_hash,
  comparison.selected_candidate_ref,
].filter(Boolean);
for (const secret of forbiddenSecrets) {
  if (lensMarkup.includes(secret)) {
    failures.push(`lens:identity-leak:${secret}`);
  }
}
for (const forbidden of [
  "data-decision-ref",
  "data-decision-hash",
  "data-candidate",
  "data-rationale",
  "data-evidence-count",
  "data-timing",
  "data-confidence",
  "selected",
  "primary",
  "rank",
]) {
  if (lensMarkup.toLowerCase().includes(forbidden)) {
    failures.push(`lens:forbidden-markup:${forbidden}`);
  }
}

const treeChoices = page.locator(".grove-tree-choice");
const treeChoiceCount = await treeChoices.count();
const enabledTreeChoiceCount = await treeChoices.evaluateAll(
  (nodes) => nodes.filter((node) => !node.disabled).length,
);
if (treeChoiceCount !== 3 || enabledTreeChoiceCount !== 3) {
  failures.push(
    `grove:tree-playability:${treeChoiceCount}:${enabledTreeChoiceCount}`,
  );
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
  failures.push("layout:document-overflow");
}
const postRequestCount = observedRequests.filter(
  (request) => request.method === "POST",
).length;
if (postRequestCount !== 0) failures.push(`network:post:${postRequestCount}`);

const screenshotPath = path.join(
  artifactDirectory,
  "01-dream-reading-observation-lens.png",
);
await page.screenshot({ path: screenshotPath });
const audit = {
  targetUrl: url.toString(),
  readingRef: home.mingli.reading.reading_ref,
  caseRef: home.mingli.reading.case_ref,
  domains: rendered.map(({ domain, label, question }) => ({
    domain,
    label,
    question,
  })),
  lensAttributes,
  treeChoiceCount,
  enabledTreeChoiceCount,
  postRequestCount,
  metrics,
  screenshotPath,
  failures,
};
await writeFile(
  path.join(artifactDirectory, "runtime-audit.json"),
  `${JSON.stringify(audit, null, 2)}\n`,
);
await browser.close();

if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify(audit, null, 2));
