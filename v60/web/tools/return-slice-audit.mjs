import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/return-slice");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl =
  process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience?scope=dream";
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
page.on("response", async (response) => {
  if (response.status() >= 400) failures.push(`response:${response.status()} ${response.url()}`);
  if (!response.url().includes("/api/v60/dream/")) return;
  const contentType = response.headers()["content-type"] ?? "";
  if (!contentType.includes("application/json")) return;
  const body = await response.text();
  if (body.includes("第五个清晨") || body.includes("午后土层仍会变干")) {
    failures.push(`return-future-evidence-leak:${response.url()}`);
  }
});

await page.goto(targetUrl, { waitUntil: "networkidle" });
await page.locator(".tree-base").waitFor({ state: "visible" });

const returnCommand = page.getByRole("button", {
  name: "过一段时间，再回到这棵树",
});
if (await returnCommand.isVisible()) {
  await returnCommand.click();
}

await page.waitForFunction(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  if (!response.ok) return false;
  const snapshot = await response.json();
  return (
    snapshot.encounter?.chapter === "RETURN_VISIT" &&
    snapshot.question?.question_ref === null &&
    snapshot.game?.episode_ref === "v60-dream-episode-yanzhou-wet-bank-v1"
  );
});
const questionBand = page.locator(".question-band");

const screenshot = async (name) => {
  const metrics = await page.evaluate(() => ({
    bodyScrollHeight: document.body.scrollHeight,
    bodyScrollWidth: document.body.scrollWidth,
    viewportHeight: window.innerHeight,
    viewportWidth: window.innerWidth,
  }));
  if (metrics.bodyScrollHeight > metrics.viewportHeight) {
    failures.push(`${name}:document-vertical-scroll`);
  }
  if (metrics.bodyScrollWidth > metrics.viewportWidth) {
    failures.push(`${name}:document-horizontal-scroll`);
  }
  const screenshotPath = path.join(artifactDirectory, `${name}.png`);
  await page.screenshot({ path: screenshotPath });
  return { screenshotPath, metrics };
};

const returned = await screenshot("00-returned-same-tree");
if (!(await page.locator(".answer-options").isVisible())) {
  await page.locator(".tree-organ-evidence_leaf_world").click();
  await page.locator(".tree-organ-evidence_leaf_structure").click();
  await page.locator(".tree-organ-structure_branch").click();
  await page.locator(".tree-organ-question_flower").click();
}

await page.getByText("砚舟只松开湿侧的一块挡水石后").waitFor();
const questionOpen = await screenshot("01-return-question-open");
const visibleText = await questionBand.innerText();
if (visibleText.includes("第五个清晨") || visibleText.includes("午后土层仍会变干")) {
  failures.push("return-future-evidence-visible-before-seal");
}

const beforeRefresh = await page.evaluate(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  return response.json();
});
if (beforeRefresh.encounter.chapter !== "RETURN_VISIT") {
  failures.push(`wrong-chapter:${beforeRefresh.encounter.chapter}`);
}
if (beforeRefresh.question?.question_ref !== "v60-question-yanzhou-wet-bank-v1") {
  failures.push(`wrong-question:${beforeRefresh.question?.question_ref}`);
}
if (beforeRefresh.human_seal !== null) failures.push("owner-answer-was-created");

await page.reload({ waitUntil: "networkidle" });
await page.getByText("砚舟只松开湿侧的一块挡水石后").waitFor();
const recovered = await screenshot("02-return-question-refresh-recovered");
const afterRefresh = await page.evaluate(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  return response.json();
});

if (afterRefresh.encounter.encounter_ref !== beforeRefresh.encounter.encounter_ref) {
  failures.push("encounter-changed-after-refresh");
}
if (afterRefresh.tree.tree_ref !== beforeRefresh.tree.tree_ref) {
  failures.push("tree-changed-after-refresh");
}
if (afterRefresh.tree.organs.some((organ) => !organ.organ_ref.endsWith("-v2"))) {
  failures.push("return-organ-identity-not-v2");
}

const audit = {
  targetUrl,
  returned,
  questionOpen,
  recovered,
  encounterRef: afterRefresh.encounter.encounter_ref,
  treeRef: afterRefresh.tree.tree_ref,
  questionRef: afterRefresh.question.question_ref,
  treeProjectionVersion: afterRefresh.tree.projection_version,
  humanSeal: afterRefresh.human_seal,
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
