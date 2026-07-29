import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const artifactDirectory = path.resolve(here, "../../.artifacts/visual");
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const targetUrl = process.env.V60_AUDIT_URL ?? "http://127.0.0.1:8060/experience";

await mkdir(artifactDirectory, { recursive: true });

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
});

const profiles = [
  { name: "desktop", viewport: { width: 1440, height: 900 }, reducedMotion: "no-preference" },
  { name: "mobile-390", viewport: { width: 390, height: 844 }, reducedMotion: "no-preference" },
  { name: "reduced-motion", viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" },
];

const results = [];

for (const profile of profiles) {
  const context = await browser.newContext({
    viewport: profile.viewport,
    reducedMotion: profile.reducedMotion,
  });
  const page = await context.newPage();
  const failures = [];

  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      !message.text().startsWith("Failed to load resource:")
    ) {
      failures.push(`console:${message.text()}`);
    }
  });
  page.on("pageerror", (error) => failures.push(`page:${error.message}`));
  page.on("requestfailed", (request) => {
    failures.push(`request:${request.method()} ${request.url()} ${request.failure()?.errorText}`);
  });
  page.on("response", (response) => {
    if (
      response.status() === 401 &&
      response.url().endsWith("/api/v60/auth/me")
    ) {
      return;
    }
    if (response.status() >= 400) {
      failures.push(`response:${response.status()} ${response.url()}`);
    }
  });

  await page.goto(targetUrl, { waitUntil: "networkidle" });
  await page.locator(".login-panel").waitFor({ state: "visible" });
  await page.waitForTimeout(500);

  const metrics = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const video = document.querySelector("video");
    const abu = document.querySelector(".login-abu");
    return {
      title: document.title,
      bodyScrollHeight: document.body.scrollHeight,
      bodyScrollWidth: document.body.scrollWidth,
      viewportHeight: window.innerHeight,
      viewportWidth: window.innerWidth,
      canvasWidth: canvas?.width ?? 0,
      canvasHeight: canvas?.height ?? 0,
      videoReadyState: video?.readyState ?? -1,
      abuTagName: abu?.tagName ?? null,
      abuVideoSource: video?.querySelector("source")?.getAttribute("src") ?? null,
      visibleText: document.body.innerText.replace(/\s+/g, " ").trim(),
    };
  });

  if (metrics.bodyScrollHeight > metrics.viewportHeight) failures.push("document:vertical-scroll");
  if (metrics.bodyScrollWidth > metrics.viewportWidth) failures.push("document:horizontal-scroll");
  if (
    profile.name !== "mobile-390" &&
    (metrics.canvasWidth < 1 || metrics.canvasHeight < 1)
  ) {
    failures.push("canvas:blank-size");
  }
  if (
    profile.name !== "mobile-390" &&
    profile.reducedMotion === "no-preference" &&
    (
      metrics.abuTagName !== "VIDEO" ||
      metrics.videoReadyState < 2 ||
      metrics.abuVideoSource !==
        "/assets/abu/v60/abu-v60-seated-idle-loop-v1/actor.webm"
    )
  ) {
    failures.push("abu-idle:video-not-ready");
  }
  if (profile.reducedMotion === "reduce" && metrics.abuTagName !== "IMG") {
    failures.push("abu-idle:reduced-motion-poster-missing");
  }

  const screenshotPath = path.join(artifactDirectory, `${profile.name}.png`);
  await page.screenshot({ path: screenshotPath });

  const abuInteraction =
    profile.name === "mobile-390"
      ? "mobile-guardrail"
      : await page.locator(".login-abu").getAttribute("aria-label");

  results.push({ ...profile, screenshotPath, metrics, abuInteraction, failures });
  await context.close();
}

await browser.close();

const resultPath = path.join(artifactDirectory, "runtime-audit.json");
await writeFile(resultPath, `${JSON.stringify(results, null, 2)}\n`, "utf8");

const failures = results.flatMap((result) => result.failures);
if (failures.length > 0) {
  throw new Error(`Visual audit failed:\n${failures.join("\n")}`);
}

console.log(JSON.stringify({ targetUrl, resultPath, profiles: results }, null, 2));
