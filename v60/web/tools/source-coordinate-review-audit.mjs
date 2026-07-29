import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(
  here,
  "../../.artifacts/source-coordinate-review",
);
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
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

page.on("console", (message) => {
  if (message.type() === "error") failures.push(`console:${message.text()}`);
});
page.on("pageerror", (error) => failures.push(`page:${error.message}`));
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

const openView = async (view) => {
  const url = new URL(targetUrl);
  url.searchParams.set("view", view);
  await page.goto(url.toString(), { waitUntil: "networkidle" });
};
const screenshot = async (name) => {
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return screenshotPath;
};

await openView("mingli");
const summaryPanel = page.locator(
  '.source-coordinate-review[data-mode="summary"]',
);
await summaryPanel.waitFor({ state: "visible" });
await summaryPanel.scrollIntoViewIfNeeded();
const vectorRef = await summaryPanel.getAttribute("data-vector-ref");
const summaryReadiness = summaryPanel.locator(
  '.source-usability-prerequisite[data-mode="summary"]',
);
const prerequisiteRef = await summaryReadiness.getAttribute(
  "data-prerequisite-ref",
);
const prerequisiteHash = await summaryReadiness.getAttribute(
  "data-prerequisite-hash",
);
const summaryText = await summaryPanel.innerText();
for (const expected of [
  "来源坐标复核",
  "不判旺衰",
  "严格同干 · 6 个来源",
  "同五行扩展 · 10 个来源",
  "口径竞争",
  "可进入可用性讨论",
  "关系作用仍待定",
]) {
  if (!summaryText.includes(expected)) failures.push(`mingli:missing:${expected}`);
}

const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const vector = homeSnapshot.mingli?.source_coordinate_review;
const prerequisite = homeSnapshot.mingli?.source_usability_prerequisite;
if (vector?.vector_ref !== vectorRef) {
  failures.push("mingli:dom-api-vector-ref-mismatch");
}
if (
  prerequisite?.prerequisite_ref !== prerequisiteRef ||
  prerequisite?.prerequisite_hash !== prerequisiteHash
) {
  failures.push("mingli:dom-api-prerequisite-identity-mismatch");
}
if (
  homeSnapshot.mingli?.reading?.source_review_vector_ref !== vectorRef ||
  homeSnapshot.mingli?.reading?.source_review_vector_hash !== vector?.vector_hash ||
  homeSnapshot.lab?.source_review_vector_ref !== vectorRef ||
  homeSnapshot.lab?.source_review_vector_hash !== vector?.vector_hash
) {
  failures.push("mingli:shared-source-review-identity-mismatch");
}
if (
  homeSnapshot.lab?.source_usability_prerequisite_ref !== prerequisiteRef ||
  homeSnapshot.lab?.source_usability_prerequisite_hash !== prerequisiteHash ||
  JSON.stringify(homeSnapshot.lab?.source_usability_prerequisite_carriers) !==
    JSON.stringify(prerequisite?.carriers)
) {
  failures.push("mingli:shared-source-usability-identity-mismatch");
}
if (
  prerequisite?.case_ref !== vector?.case_ref ||
  prerequisite?.chart_version_ref !== vector?.chart_version_ref ||
  prerequisite?.quant_vector_ref !== vector?.quant_vector_ref ||
  prerequisite?.quant_vector_hash !== vector?.quant_vector_hash ||
  prerequisite?.source_review_vector_ref !== vectorRef ||
  prerequisite?.source_review_vector_hash !== vector?.vector_hash
) {
  failures.push("mingli:source-usability-lineage-mismatch");
}
if (
  vector?.source_evidence_count !== 10 ||
  vector?.clear_coordinate_count !== 7 ||
  vector?.review_required_count !== 3
) {
  failures.push("mingli:expected-source-review-sample-mismatch");
}
if (
  prerequisite?.exact_identity_only_clear_count !== 5 ||
  prerequisite?.exact_identity_only_review_required_count !== 1 ||
  prerequisite?.element_affinity_included_clear_count !== 7 ||
  prerequisite?.element_affinity_included_review_required_count !== 3 ||
  prerequisite?.carrier_count !== 4 ||
  prerequisite?.competing_carrier_count !== 3 ||
  prerequisite?.ready_carrier_count !== 0
) {
  failures.push("mingli:expected-competing-scope-sample-mismatch");
}
if (
  vector?.professional_verdict_allowed !== false ||
  vector?.probability_claim_allowed !== false ||
  vector?.canonical_write_allowed !== false
) {
  failures.push("mingli:forbidden-authority-enabled");
}
if (
  prerequisite?.professional_verdict_allowed !== false ||
  prerequisite?.probability_claim_allowed !== false ||
  prerequisite?.canonical_write_allowed !== false ||
  prerequisite?.read_only !== true
) {
  failures.push("mingli:source-usability-authority-enabled");
}
if (
  (vector?.reviews ?? []).some(
    (item) =>
      item.root_usability_status !== "UNRESOLVED" ||
      item.relation_effect_status !== "UNRESOLVED",
  )
) {
  failures.push("mingli:unadmitted-conclusion-present");
}
const expectedScopeIds = [
  "ELEMENT_AFFINITY_INCLUDED",
  "EXACT_IDENTITY_ONLY",
];
const expectedRequirementIds = [
  "MATCH_SCOPE_RULE",
  "MULTI_SOURCE_AGGREGATION_RULE",
  "PROFESSIONAL_ADMISSION",
  "RELATION_EFFECT_RULE",
  "ROOT_USABILITY_RULE",
  "SEASONAL_CAPACITY_RULE",
];
for (const carrier of prerequisite?.carriers ?? []) {
  const scopeIds = carrier.scopes
    .map((scope) => scope.scope_id)
    .sort();
  const requirementIds = carrier.requirements
    .map((requirement) => requirement.requirement_id)
    .sort();
  if (
    carrier.discussion_ready !== false ||
    JSON.stringify(scopeIds) !== JSON.stringify(expectedScopeIds) ||
    JSON.stringify(requirementIds) !== JSON.stringify(expectedRequirementIds)
  ) {
    failures.push(`mingli:carrier-contract-mismatch:${carrier.carrier_ref}`);
  }
  for (const scope of carrier.scopes) {
    if (
      scope.relation_effect_status !== "UNRESOLVED" ||
      scope.root_usability_status !== "UNRESOLVED" ||
      scope.selection_authority !== false
    ) {
      failures.push(`mingli:scope-overreach:${scope.scope_ref}`);
    }
  }
  for (const requirement of carrier.requirements) {
    if (
      !["NOT_ADMITTED", "NOT_TRIGGERED", "UNRESOLVED"].includes(
        requirement.status,
      )
    ) {
      failures.push(
        `mingli:requirement-overreach:${carrier.carrier_ref}:${requirement.requirement_id}`,
      );
    }
  }
}
for (const forbidden of ["六冲受损", "六合增益", "可用概率", "有效做功已确认"]) {
  if (summaryText.includes(forbidden)) {
    failures.push(`mingli:forbidden-copy:${forbidden}`);
  }
}
const mingliScreenshot = await screenshot("01-mingli-source-coordinate-review");

await openView("lab");
const detailedPanel = page.locator(
  '.source-coordinate-review[data-mode="detailed"]',
);
await detailedPanel.waitFor({ state: "visible" });
await detailedPanel.scrollIntoViewIfNeeded();
if ((await detailedPanel.getAttribute("data-vector-ref")) !== vectorRef) {
  failures.push("lab:vector-ref-mismatch");
}
const detailedReadiness = detailedPanel.locator(
  '.source-usability-prerequisite[data-mode="detailed"]',
);
if (
  (await detailedReadiness.getAttribute("data-prerequisite-ref")) !==
  prerequisiteRef
) {
  failures.push("lab:prerequisite-ref-mismatch");
}
const detailedText = await detailedPanel.innerText();
for (const expected of [
  "来源候选",
  "需要复核",
  "严格同干",
  "同五行扩展",
  "核验条件",
  "关系作用仍待定",
]) {
  if (!detailedText.includes(expected)) failures.push(`lab:missing:${expected}`);
}
const renderedReviewCount = await detailedPanel
  .locator(".source-review-detail-list article")
  .count();
const expectedReviewCount = vector?.review_required_count
  ? vector.review_required_count
  : Math.min(vector?.reviews?.length ?? 0, 4);
if (renderedReviewCount !== expectedReviewCount) {
  failures.push("lab:rendered-review-count-mismatch");
}
const renderedCarrierCount = await detailedReadiness
  .locator(".source-usability-carrier")
  .count();
if (renderedCarrierCount !== prerequisite?.carrier_count) {
  failures.push("lab:rendered-carrier-count-mismatch");
}
const renderedScopeCount = await detailedReadiness
  .locator(".source-usability-carrier-scopes > section")
  .count();
if (renderedScopeCount !== (prerequisite?.carrier_count ?? 0) * 2) {
  failures.push("lab:rendered-scope-count-mismatch");
}
const requirementDisclosures = detailedReadiness.locator(
  ".source-usability-requirements",
);
if ((await requirementDisclosures.count()) !== prerequisite?.carrier_count) {
  failures.push("lab:rendered-requirement-disclosure-count-mismatch");
}
if (
  (await requirementDisclosures.count()) > 0 &&
  !(await requirementDisclosures.first().evaluate((node) => node.open))
) {
  failures.push("lab:first-requirement-disclosure-not-open");
}
const renderedRequirementCount = await detailedReadiness
  .locator("[data-requirement-id]")
  .count();
if (renderedRequirementCount !== (prerequisite?.carrier_count ?? 0) * 6) {
  failures.push("lab:rendered-requirement-count-mismatch");
}
await detailedReadiness.evaluate((node) =>
  node.scrollIntoView({ block: "start" }),
);
const labScreenshot = await screenshot("02-lab-source-coordinate-review");

await page.reload({ waitUntil: "networkidle" });
const refreshedDetailedPanel = page.locator(
  '.source-coordinate-review[data-mode="detailed"]',
);
await refreshedDetailedPanel.waitFor({ state: "visible" });
const refreshedReadiness = refreshedDetailedPanel.locator(
  '.source-usability-prerequisite[data-mode="detailed"]',
);
const refreshedSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home-refresh:${response.status}`);
  return response.json();
});
if (
  (await refreshedDetailedPanel.getAttribute("data-vector-ref")) !== vectorRef ||
  (await refreshedReadiness.getAttribute("data-prerequisite-ref")) !==
    prerequisiteRef ||
  refreshedSnapshot.mingli?.source_coordinate_review?.vector_ref !== vectorRef ||
  refreshedSnapshot.mingli?.source_usability_prerequisite?.prerequisite_ref !==
    prerequisiteRef ||
  refreshedSnapshot.mingli?.source_usability_prerequisite?.prerequisite_hash !==
    prerequisiteHash
) {
  failures.push("lab:refresh-identity-mismatch");
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
  failures.push("experience:document-scroll");
}

const audit = {
  targetUrl,
  vectorRef,
  vectorHash: vector?.vector_hash,
  prerequisiteRef,
  prerequisiteHash,
  readingRef: homeSnapshot.mingli?.reading?.reading_ref,
  caseRef: vector?.case_ref,
  sourceEvidenceCount: vector?.source_evidence_count,
  clearCoordinateCount: vector?.clear_coordinate_count,
  reviewRequiredCount: vector?.review_required_count,
  clashIntersectionCount: vector?.six_clash_intersection_count,
  harmonyIntersectionCount: vector?.six_harmony_intersection_count,
  carrierCount: prerequisite?.carrier_count,
  strictScope: {
    clearCount: prerequisite?.exact_identity_only_clear_count,
    reviewRequiredCount:
      prerequisite?.exact_identity_only_review_required_count,
  },
  inclusiveScope: {
    clearCount: prerequisite?.element_affinity_included_clear_count,
    reviewRequiredCount:
      prerequisite?.element_affinity_included_review_required_count,
  },
  competingCarrierCount: prerequisite?.competing_carrier_count,
  readyCarrierCount: prerequisite?.ready_carrier_count,
  professionalVerdictAllowed: vector?.professional_verdict_allowed,
  probabilityClaimAllowed: vector?.probability_claim_allowed,
  canonicalWriteAllowed: vector?.canonical_write_allowed,
  refreshStable: !failures.includes("lab:refresh-identity-mismatch"),
  screenshots: { mingliScreenshot, labScreenshot },
  metrics,
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
