import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/explanation-slice");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";
const sessionToken = process.env.V60_AUDIT_SESSION_TOKEN;

if (!sessionToken) throw new Error("V60_AUDIT_SESSION_TOKEN is required");
await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({ executablePath: chromePath, headless: true });
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
  failures.push(`request:${request.method()} ${request.url()} ${request.failure()?.errorText}`);
});
page.on("response", (response) => {
  if (response.status() >= 400) {
    failures.push(`response:${response.status()} ${response.url()}`);
  }
});

const screenshot = async (name) => {
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return screenshotPath;
};

const mingliUrl = new URL(targetUrl);
mingliUrl.searchParams.set("view", "mingli");
await page.goto(mingliUrl.toString(), { waitUntil: "networkidle" });
const mingliExplanation = page.locator(".mingli-explanation");
await mingliExplanation.waitFor({ state: "visible" });
const explanationRef = await mingliExplanation.getAttribute("data-explanation-ref");
const candidateClaim = mingliExplanation.locator('details[data-status="candidate"]').first();
if ((await mingliExplanation.locator('details[data-status="confirmed"]').count()) !== 1) {
  failures.push("mingli:confirmed-claim-count");
}
if ((await mingliExplanation.locator('details[data-status="candidate"]').count()) < 1) {
  failures.push("mingli:no-candidate-claim");
} else {
  await candidateClaim.locator("summary").click();
  const candidateText = await candidateClaim.innerText();
  for (const expected of ["支持它的材料", "反证与未知", "不能把“没有反证”当作支持"]) {
    if (!candidateText.includes(expected)) {
      failures.push(`mingli:candidate-boundary-missing:${expected}`);
    }
  }
}
const homeSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/experience/home");
  if (!response.ok) throw new Error(`home:${response.status}`);
  return response.json();
});
if (homeSnapshot.mingli?.explanation?.explanation_ref !== explanationRef) {
  failures.push("mingli:dom-api-explanation-ref-mismatch");
}
if (
  homeSnapshot.mingli?.abu_expression?.explanation_ref !== explanationRef ||
  homeSnapshot.lab?.explanation_ref !== explanationRef
) {
  failures.push("mingli:abu-lab-explanation-identity-mismatch");
}
const mingliScreenshot = await screenshot("01-mingli-evidence-explanation");

const labUrl = new URL(targetUrl);
labUrl.searchParams.set("view", "lab");
await page.goto(labUrl.toString(), { waitUntil: "networkidle" });
const labExplanation = page.locator(".mingli-explanation");
await labExplanation.waitFor({ state: "visible" });
if ((await labExplanation.getAttribute("data-explanation-ref")) !== explanationRef) {
  failures.push("lab:explanation-ref-mismatch");
}
if ((await labExplanation.locator('details[data-status="confirmed"]').count()) !== 0) {
  failures.push("lab:non-candidate-claim-visible");
}
const labClaim = labExplanation.locator('details[data-status="candidate"]').first();
if (await labClaim.count()) await labClaim.locator("summary").click();
const labScreenshot = await screenshot("02-lab-shared-candidate-evidence");

const dreamUrl = new URL(targetUrl);
dreamUrl.searchParams.set("scope", "dream");
await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
await page.locator(".tree-base").waitFor({ state: "visible" });
const questionBasis = page.locator(".dream-question-basis");
await questionBasis.waitFor({ state: "visible" });
await questionBasis.locator("summary").click();
const basisText = await questionBasis.innerText();
if (!basisText.includes("这些只是所有选项共同看到的既有事实")) {
  failures.push("dream:shared-baseline-boundary-missing");
}
const dreamSnapshot = await page.evaluate(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  if (!response.ok) throw new Error(`encounter:${response.status}`);
  return response.json();
});
if (dreamSnapshot.encounter?.status !== "QUESTION_OPEN") {
  failures.push(`dream:unexpected-status:${dreamSnapshot.encounter?.status}`);
}
if (dreamSnapshot.human_seal || dreamSnapshot.reveal) {
  failures.push("dream:pre-seal-state-contaminated");
}
const serializedDream = JSON.stringify(dreamSnapshot);
for (const forbidden of ["SUPPORTED", "NOT_SUPPORTED", "outcome_evidence"]) {
  if (serializedDream.includes(forbidden)) {
    failures.push(`dream:pre-outcome-leak:${forbidden}`);
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
  failures.push("dream:document-scroll");
}
const dreamScreenshot = await screenshot("03-dream-question-safe-basis");

const audit = {
  targetUrl,
  explanationRef,
  readingRef: homeSnapshot.mingli?.reading?.reading_ref,
  decisionAuthority: homeSnapshot.mingli?.explanation?.decision_authority,
  counts: {
    confirmed: homeSnapshot.mingli?.explanation?.confirmed_count,
    candidates: homeSnapshot.mingli?.explanation?.candidate_count,
    observations: homeSnapshot.mingli?.explanation?.observation_count,
  },
  dream: {
    encounterRef: dreamSnapshot.encounter?.encounter_ref,
    status: dreamSnapshot.encounter?.status,
    answerCreated: Boolean(dreamSnapshot.human_seal),
    revealVisible: Boolean(dreamSnapshot.reveal),
  },
  metrics,
  screenshots: {
    mingliScreenshot,
    labScreenshot,
    dreamScreenshot,
  },
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
