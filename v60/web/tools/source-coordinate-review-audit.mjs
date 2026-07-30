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
const assertNoForbiddenDiscussionClaims = (surface, text) => {
  for (const forbidden of [
    "六冲受损",
    "六合增益",
    "关系增益",
    "有效做功已确认",
    "关系作用已确认",
    "来源已可用",
    "来源不可用已确认",
  ]) {
    if (text.includes(forbidden)) {
      failures.push(`${surface}:discussion-forbidden-copy:${forbidden}`);
    }
  }
  if (/(?:概率|置信度)[：:\s]*\d+(?:\.\d+)?%/.test(text)) {
    failures.push(`${surface}:discussion-forbidden-numeric-authority`);
  }
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
const mingliDiscussionReceipt = page.locator(
  '.source-discussion-abstention[data-mode="summary"]',
);
await mingliDiscussionReceipt.waitFor({ state: "visible" });
const discussionReceiptRef = await mingliDiscussionReceipt.getAttribute(
  "data-receipt-ref",
);
const discussionReceiptHash = await mingliDiscussionReceipt.getAttribute(
  "data-receipt-hash",
);
const discussionDisposition = await mingliDiscussionReceipt.getAttribute(
  "data-disposition",
);
const mingliRelationFrontier = page.locator(
  '.relation-effect-frontier[data-mode="summary"]',
);
await mingliRelationFrontier.waitFor({ state: "visible" });
const relationFrontierRef = await mingliRelationFrontier.getAttribute(
  "data-frontier-ref",
);
const relationFrontierHash = await mingliRelationFrontier.getAttribute(
  "data-frontier-hash",
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
const mingliDiscussionText = await mingliDiscussionReceipt.innerText();
for (const expected of [
  "下游讨论授权",
  "拒答凭据",
  "这些来源怎样作用、现在能不能用？",
  "个明干载体达到门槛",
  "不判断关系作用，也不判断可用或不可用",
]) {
  if (!mingliDiscussionText.includes(expected)) {
    failures.push(`mingli:discussion-receipt-missing:${expected}`);
  }
}
assertNoForbiddenDiscussionClaims("mingli", mingliDiscussionText);
const mingliRelationFrontierText = await mingliRelationFrontier.innerText();
for (const expected of [
  "关系作用规则需求",
  "研究顺序，不是结论",
  "跨口径作用规则",
  "先补匹配口径",
  "已准入作用规则",
  "关系作用与来源可用性仍为",
  "UNRESOLVED",
]) {
  if (!mingliRelationFrontierText.includes(expected)) {
    failures.push(`mingli:relation-frontier-missing:${expected}`);
  }
}
assertNoForbiddenDiscussionClaims(
  "mingli-frontier",
  mingliRelationFrontierText,
);

const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
const vector = homeSnapshot.mingli?.source_coordinate_review;
const prerequisite = homeSnapshot.mingli?.source_usability_prerequisite;
const discussionReceipt = homeSnapshot.mingli?.source_discussion_receipt;
const relationFrontier = homeSnapshot.mingli?.relation_effect_frontier;
const initialDecisionIdentity = JSON.stringify({
  decisionRefs: homeSnapshot.mingli?.reading?.decision_refs ?? [],
  comparisonDecisionRef:
    homeSnapshot.lab?.mechanism_comparison?.decision_ref ?? null,
});
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
  discussionReceipt?.receipt_ref !== discussionReceiptRef ||
  discussionReceipt?.receipt_hash !== discussionReceiptHash ||
  discussionDisposition !== "ABSTAIN"
) {
  failures.push("mingli:dom-api-discussion-receipt-identity-mismatch");
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
  homeSnapshot.lab?.source_discussion_receipt_ref !== discussionReceiptRef ||
  homeSnapshot.lab?.source_discussion_receipt_hash !== discussionReceiptHash
) {
  failures.push("mingli:shared-source-discussion-identity-mismatch");
}
if (
  relationFrontier?.frontier_ref !== relationFrontierRef ||
  relationFrontier?.frontier_hash !== relationFrontierHash ||
  homeSnapshot.lab?.relation_effect_frontier_ref !== relationFrontierRef ||
  homeSnapshot.lab?.relation_effect_frontier_hash !== relationFrontierHash
) {
  failures.push("mingli:shared-relation-frontier-identity-mismatch");
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
  discussionReceipt?.case_ref !== vector?.case_ref ||
  discussionReceipt?.case_ref !== homeSnapshot.case?.case_ref ||
  discussionReceipt?.chart_version_ref !== vector?.chart_version_ref ||
  discussionReceipt?.chart_version_ref !==
    homeSnapshot.chart?.chart_version_ref ||
  discussionReceipt?.reading_ref !==
    homeSnapshot.mingli?.reading?.reading_ref ||
  discussionReceipt?.reading_hash !==
    homeSnapshot.mingli?.reading?.reading_hash ||
  discussionReceipt?.source_review_vector_ref !== vectorRef ||
  discussionReceipt?.source_review_vector_hash !== vector?.vector_hash ||
  discussionReceipt?.prerequisite_ref !== prerequisiteRef ||
  discussionReceipt?.prerequisite_hash !== prerequisiteHash ||
  discussionReceipt?.carrier_count !== prerequisite?.carrier_count ||
  discussionReceipt?.ready_carrier_count !==
    prerequisite?.ready_carrier_count ||
  JSON.stringify(discussionReceipt?.carrier_refs) !==
    JSON.stringify(
      (prerequisite?.carriers ?? []).map((carrier) => carrier.carrier_ref),
    )
) {
  failures.push("mingli:source-discussion-lineage-mismatch");
}
if (
  discussionReceipt?.receipt_version !==
    "v60.mingli-source-discussion-abstention-receipt.001" ||
  discussionReceipt?.disposition !== "ABSTAIN" ||
  discussionReceipt?.reason !== "NO_ADMITTED_PROFESSIONAL_RULE_CHAIN" ||
  discussionReceipt?.output_mode !== "FACTS_AND_GAPS_ONLY" ||
  JSON.stringify(discussionReceipt?.abstained_claims) !==
    JSON.stringify(["RELATION_EFFECT", "SOURCE_USABILITY"])
) {
  failures.push("mingli:source-discussion-abstention-contract-mismatch");
}
if (
  discussionReceipt?.provider_invoked !== false ||
  discussionReceipt?.decision_created !== false ||
  discussionReceipt?.discussion_allowed !== false ||
  discussionReceipt?.professional_verdict_allowed !== false ||
  discussionReceipt?.probability_claim_allowed !== false ||
  discussionReceipt?.canonical_write_allowed !== false ||
  discussionReceipt?.read_only !== true
) {
  failures.push("mingli:source-discussion-authority-enabled");
}
if (
  relationFrontier?.frontier_version !==
    "v60.mingli-relation-effect-research-frontier.001" ||
  relationFrontier?.research_semantics !==
    "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY" ||
  relationFrontier?.source_discussion_disposition !== "ABSTAIN" ||
  relationFrontier?.effect_status !== "UNRESOLVED" ||
  relationFrontier?.usability_status !== "UNRESOLVED" ||
  relationFrontier?.demand_count !== 3 ||
  relationFrontier?.scope_invariant_rule_demand_count !== 1 ||
  relationFrontier?.match_scope_rule_first_count !== 2 ||
  relationFrontier?.admitted_effect_rule_count !== 0
) {
  failures.push("mingli:relation-frontier-contract-mismatch");
}
if (
  relationFrontier?.case_ref !== vector?.case_ref ||
  relationFrontier?.chart_version_ref !== vector?.chart_version_ref ||
  relationFrontier?.reading_ref !==
    homeSnapshot.mingli?.reading?.reading_ref ||
  relationFrontier?.reading_hash !==
    homeSnapshot.mingli?.reading?.reading_hash ||
  relationFrontier?.source_review_vector_ref !== vectorRef ||
  relationFrontier?.source_review_vector_hash !== vector?.vector_hash ||
  relationFrontier?.prerequisite_ref !== prerequisiteRef ||
  relationFrontier?.prerequisite_hash !== prerequisiteHash ||
  relationFrontier?.refusal_receipt_ref !== discussionReceiptRef ||
  relationFrontier?.refusal_receipt_hash !== discussionReceiptHash
) {
  failures.push("mingli:relation-frontier-lineage-mismatch");
}
if (
  relationFrontier?.provider_invoked !== false ||
  relationFrontier?.decision_created !== false ||
  relationFrontier?.gate_invoked !== false ||
  relationFrontier?.selection_authority !== false ||
  relationFrontier?.professional_verdict_allowed !== false ||
  relationFrontier?.probability_claim_allowed !== false ||
  relationFrontier?.canonical_write_allowed !== false ||
  relationFrontier?.read_only !== true
) {
  failures.push("mingli:relation-frontier-authority-enabled");
}
const expectedRuleDimensions = [
  "APPLICABILITY_CONTEXT",
  "EFFECT_DIRECTION",
  "COMPLETION_CONDITIONS",
  "BLOCKING_CONDITIONS",
  "COUNTER_EVIDENCE",
  "PROFESSIONAL_PROVENANCE",
];
const relationIntersectionRefs = new Set(
  (vector?.reviews ?? []).flatMap((review) =>
    review.relation_intersections.map(
      (intersection) => intersection.intersection_ref,
    ),
  ),
);
if (
  JSON.stringify(
    (relationFrontier?.demands ?? [])
      .map((demand) => demand.intersection_ref)
      .sort(),
  ) !== JSON.stringify([...relationIntersectionRefs].sort())
) {
  failures.push("mingli:relation-frontier-intersection-bijection-mismatch");
}
for (const demand of relationFrontier?.demands ?? []) {
  const expectedDependency =
    demand.source_match_kind === "EXACT_IDENTITY"
      ? "SCOPE_INVARIANT_RULE_DEMAND"
      : "MATCH_SCOPE_RULE_FIRST";
  const expectedScopes =
    expectedDependency === "SCOPE_INVARIANT_RULE_DEMAND"
      ? ["EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED"]
      : ["ELEMENT_AFFINITY_INCLUDED"];
  if (
    demand.dependency_status !== expectedDependency ||
    JSON.stringify(demand.scope_presence) !== JSON.stringify(expectedScopes) ||
    JSON.stringify(demand.required_rule_dimensions) !==
      JSON.stringify(expectedRuleDimensions) ||
    demand.effect_status !== "UNRESOLVED" ||
    demand.usability_status !== "UNRESOLVED" ||
    demand.selection_authority !== false
  ) {
    failures.push(`mingli:relation-frontier-demand-invalid:${demand.demand_ref}`);
  }
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

await openView("abu");
const abuDiscussionReceipt = page.locator(
  '.source-discussion-abstention[data-mode="summary"]',
);
await abuDiscussionReceipt.waitFor({ state: "visible" });
if (
  (await abuDiscussionReceipt.getAttribute("data-receipt-ref")) !==
    discussionReceiptRef ||
  (await abuDiscussionReceipt.getAttribute("data-receipt-hash")) !==
    discussionReceiptHash ||
  (await abuDiscussionReceipt.getAttribute("data-disposition")) !== "ABSTAIN"
) {
  failures.push("abu:source-discussion-receipt-identity-mismatch");
}
const abuDiscussionText = await abuDiscussionReceipt.innerText();
for (const expected of [
  "拒答凭据",
  "这些来源怎样作用、现在能不能用？",
  "不判断关系作用，也不判断可用或不可用",
]) {
  if (!abuDiscussionText.includes(expected)) {
    failures.push(`abu:discussion-receipt-missing:${expected}`);
  }
}
assertNoForbiddenDiscussionClaims("abu", abuDiscussionText);

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
const labDiscussionReceipt = page.locator(
  '.source-discussion-abstention[data-mode="detailed"]',
);
await labDiscussionReceipt.waitFor({ state: "visible" });
if (
  (await labDiscussionReceipt.getAttribute("data-receipt-ref")) !==
    discussionReceiptRef ||
  (await labDiscussionReceipt.getAttribute("data-receipt-hash")) !==
    discussionReceiptHash ||
  (await labDiscussionReceipt.getAttribute("data-disposition")) !== "ABSTAIN"
) {
  failures.push("lab:source-discussion-receipt-identity-mismatch");
}
const labReceiptDetails = labDiscussionReceipt.locator(
  ".source-discussion-receipt-detail",
);
const labDiscussionText = await labDiscussionReceipt.innerText();
assertNoForbiddenDiscussionClaims("lab", labDiscussionText);
if (!(await labReceiptDetails.evaluate((node) => node.open))) {
  failures.push("lab:source-discussion-receipt-details-not-open");
}
const renderedBlockerIds = await labDiscussionReceipt
  .locator(".source-discussion-blockers code")
  .allTextContents();
if (
  JSON.stringify(renderedBlockerIds) !==
  JSON.stringify(discussionReceipt?.blocking_requirement_ids ?? [])
) {
  failures.push("lab:source-discussion-blocker-ids-mismatch");
}
const labRelationFrontier = page.locator(
  '.relation-effect-frontier[data-mode="detailed"]',
);
await labRelationFrontier.waitFor({ state: "visible" });
if (
  (await labRelationFrontier.getAttribute("data-frontier-ref")) !==
    relationFrontierRef ||
  (await labRelationFrontier.getAttribute("data-frontier-hash")) !==
    relationFrontierHash
) {
  failures.push("lab:relation-frontier-identity-mismatch");
}
for (const attribute of [
  "data-provider-invoked",
  "data-decision-created",
  "data-gate-invoked",
  "data-selection-authority",
  "data-professional-verdict-allowed",
  "data-probability-claim-allowed",
  "data-canonical-write-allowed",
]) {
  if ((await labRelationFrontier.getAttribute(attribute)) !== "false") {
    failures.push(`lab:relation-frontier-boundary:${attribute}`);
  }
}
const renderedDemandCount = await labRelationFrontier
  .locator(".relation-effect-demand")
  .count();
if (renderedDemandCount !== relationFrontier?.demand_count) {
  failures.push("lab:relation-frontier-demand-count-mismatch");
}
const renderedDependencyStatuses = await labRelationFrontier
  .locator(".relation-effect-demand")
  .evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("data-dependency-status")),
  );
if (
  JSON.stringify(renderedDependencyStatuses) !==
  JSON.stringify(
    (relationFrontier?.demands ?? []).map(
      (demand) => demand.dependency_status,
    ),
  )
) {
  failures.push("lab:relation-frontier-dependency-order-mismatch");
}
const labRelationFrontierText = await labRelationFrontier.innerText();
assertNoForbiddenDiscussionClaims(
  "lab-frontier",
  labRelationFrontierText,
);
for (const expected of [
  "跨两种口径共现",
  "仅宽口径出现",
  "尚缺规则证据",
  "六维规则缺口",
]) {
  if (!labRelationFrontierText.includes(expected)) {
    failures.push(`lab:relation-frontier-missing:${expected}`);
  }
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
await labDiscussionReceipt.scrollIntoViewIfNeeded();
const labReceiptScreenshot = await screenshot(
  "02-lab-source-discussion-receipt",
);
await labRelationFrontier.scrollIntoViewIfNeeded();
const labRelationFrontierScreenshot = await screenshot(
  "03-lab-relation-effect-research-frontier",
);
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
const refreshedDiscussionReceipt = page.locator(
  '.source-discussion-abstention[data-mode="detailed"]',
);
await refreshedDiscussionReceipt.waitFor({ state: "visible" });
const refreshedRelationFrontier = page.locator(
  '.relation-effect-frontier[data-mode="detailed"]',
);
await refreshedRelationFrontier.waitFor({ state: "visible" });
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
if (
  (await refreshedDiscussionReceipt.getAttribute("data-receipt-ref")) !==
    discussionReceiptRef ||
  (await refreshedDiscussionReceipt.getAttribute("data-receipt-hash")) !==
    discussionReceiptHash ||
  (await refreshedDiscussionReceipt.getAttribute("data-disposition")) !==
    "ABSTAIN" ||
  refreshedSnapshot.mingli?.source_discussion_receipt?.receipt_ref !==
    discussionReceiptRef ||
  refreshedSnapshot.mingli?.source_discussion_receipt?.receipt_hash !==
    discussionReceiptHash ||
  refreshedSnapshot.lab?.source_discussion_receipt_ref !==
    discussionReceiptRef ||
  refreshedSnapshot.lab?.source_discussion_receipt_hash !==
    discussionReceiptHash
) {
  failures.push("lab:refresh-source-discussion-receipt-identity-mismatch");
}
if (
  (await refreshedRelationFrontier.getAttribute("data-frontier-ref")) !==
    relationFrontierRef ||
  (await refreshedRelationFrontier.getAttribute("data-frontier-hash")) !==
    relationFrontierHash ||
  refreshedSnapshot.mingli?.relation_effect_frontier?.frontier_ref !==
    relationFrontierRef ||
  refreshedSnapshot.mingli?.relation_effect_frontier?.frontier_hash !==
    relationFrontierHash ||
  refreshedSnapshot.lab?.relation_effect_frontier_ref !==
    relationFrontierRef ||
  refreshedSnapshot.lab?.relation_effect_frontier_hash !== relationFrontierHash
) {
  failures.push("lab:refresh-relation-frontier-identity-mismatch");
}
const refreshedDecisionIdentity = JSON.stringify({
  decisionRefs: refreshedSnapshot.mingli?.reading?.decision_refs ?? [],
  comparisonDecisionRef:
    refreshedSnapshot.lab?.mechanism_comparison?.decision_ref ?? null,
});
if (refreshedDecisionIdentity !== initialDecisionIdentity) {
  failures.push("experience:source-discussion-created-decision");
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
const postRequests = observedRequests.filter(
  (request) => request.method === "POST",
);
if (postRequests.length) {
  failures.push(
    `experience:unexpected-post:${postRequests
      .map((request) => new URL(request.url).pathname)
      .join(",")}`,
  );
}

const audit = {
  targetUrl,
  vectorRef,
  vectorHash: vector?.vector_hash,
  prerequisiteRef,
  prerequisiteHash,
  discussionReceiptRef,
  discussionReceiptHash,
  discussionDisposition: discussionReceipt?.disposition,
  discussionReason: discussionReceipt?.reason,
  discussionOutputMode: discussionReceipt?.output_mode,
  discussionAbstainedClaims: discussionReceipt?.abstained_claims,
  discussionBlockingRequirementIds:
    discussionReceipt?.blocking_requirement_ids,
  discussionNonTriggeredRequirementIds:
    discussionReceipt?.non_triggered_requirement_ids,
  discussionBoundaries: {
    providerInvoked: discussionReceipt?.provider_invoked,
    decisionCreated: discussionReceipt?.decision_created,
    discussionAllowed: discussionReceipt?.discussion_allowed,
    professionalVerdictAllowed:
      discussionReceipt?.professional_verdict_allowed,
    probabilityClaimAllowed: discussionReceipt?.probability_claim_allowed,
    canonicalWriteAllowed: discussionReceipt?.canonical_write_allowed,
    readOnly: discussionReceipt?.read_only,
  },
  relationFrontierRef,
  relationFrontierHash,
  relationFrontierCounts: {
    demandCount: relationFrontier?.demand_count,
    scopeInvariantRuleDemandCount:
      relationFrontier?.scope_invariant_rule_demand_count,
    matchScopeRuleFirstCount:
      relationFrontier?.match_scope_rule_first_count,
    admittedEffectRuleCount:
      relationFrontier?.admitted_effect_rule_count,
  },
  relationFrontierBoundaries: {
    providerInvoked: relationFrontier?.provider_invoked,
    decisionCreated: relationFrontier?.decision_created,
    gateInvoked: relationFrontier?.gate_invoked,
    selectionAuthority: relationFrontier?.selection_authority,
    professionalVerdictAllowed:
      relationFrontier?.professional_verdict_allowed,
    probabilityClaimAllowed: relationFrontier?.probability_claim_allowed,
    canonicalWriteAllowed: relationFrontier?.canonical_write_allowed,
    readOnly: relationFrontier?.read_only,
  },
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
  refreshStable:
    !failures.includes("lab:refresh-identity-mismatch") &&
    !failures.includes(
      "lab:refresh-source-discussion-receipt-identity-mismatch",
    ),
  decisionIdentityStable:
    refreshedDecisionIdentity === initialDecisionIdentity,
  postRequestCount: postRequests.length,
  screenshots: {
    mingliScreenshot,
    labReceiptScreenshot,
    labScreenshot,
    labRelationFrontierScreenshot,
  },
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
