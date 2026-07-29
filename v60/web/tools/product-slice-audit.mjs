import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/product-slice");
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

const homeUrl = new URL(targetUrl);
homeUrl.searchParams.set("view", "mingli");
await page.goto(homeUrl.toString(), { waitUntil: "networkidle" });
await page.locator(".home-tree-experience").waitFor({ state: "visible" });
await page.getByText("证据化初判", { exact: true }).waitFor();
await page.locator(".mingli-case-manager > summary").click();
const caseCount = await page.locator(".mingli-case-list button").count();
if (caseCount < 1) failures.push("mingli-case-manager:no-real-case");
if (!(await page.getByRole("button", { name: /建立命盘并开始测算/ }).isVisible())) {
  failures.push("mingli-case-manager:intake-not-visible");
}
const homeScreenshot = await screenshot("00-home-mingli-ready");

const dreamUrl = new URL(targetUrl);
dreamUrl.searchParams.set("scope", "dream");
await page.goto(dreamUrl.toString(), { waitUntil: "networkidle" });
await page.locator(".tree-base").waitFor({ state: "visible" });
const returnButton = page.getByRole("button", {
  name: "回到雾林，遇见另一棵树",
});
if (!(await returnButton.isVisible())) {
  failures.push("dream:completed-return-command-missing");
} else {
  await returnButton.click();
}

await page.locator(".dream-grove-scene").waitFor({ state: "visible" });
const groveTreeCount = await page.locator(".grove-tree-choice").count();
if (groveTreeCount !== 3) failures.push(`dream:grove-tree-count:${groveTreeCount}`);
const groveScreenshot = await screenshot("01-returned-to-grove");

await page.locator(".grove-tree-choice").first().click();
await page.locator(".tree-base").waitFor({ state: "visible" });
const started = await page.evaluate(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  if (!response.ok) throw new Error(`encounter:${response.status}`);
  return response.json();
});
if (started.encounter?.status !== "OBSERVING") {
  failures.push(`dream:new-encounter-status:${started.encounter?.status}`);
}
const encounterScreenshot = await screenshot("02-new-encounter");

await page.reload({ waitUntil: "networkidle" });
await page.locator(".tree-base").waitFor({ state: "visible" });
const recovered = await page.evaluate(async () => {
  const response = await fetch("/api/v60/dream/encounter");
  if (!response.ok) throw new Error(`encounter:${response.status}`);
  return response.json();
});
if (recovered.encounter?.encounter_ref !== started.encounter?.encounter_ref) {
  failures.push("dream:encounter-not-recovered");
}
const recoveredScreenshot = await screenshot("03-new-encounter-recovered");

const audit = {
  targetUrl,
  caseCount,
  groveTreeCount,
  newEncounterRef: recovered.encounter?.encounter_ref,
  newTreeRef: recovered.tree?.tree_ref,
  screenshots: {
    homeScreenshot,
    groveScreenshot,
    encounterScreenshot,
    recoveredScreenshot,
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
