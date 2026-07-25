import { DREAM_RUNTIME_ASSETS } from "./dream_asset_registry";


const STORAGE_KEY = "deepbazi.dream.entry-transition.v1";
const HANDOFF_START_MS = 7_100;
const RUNTIME_END_MS = 7_750;
const STALE_AFTER_MS = 30_000;


interface StoredDreamEntry {
  startedAt: number;
  visitId: string;
}


export interface DreamEntryTransitionController {
  bindVisit(visitId: string): void;
  markDestinationReady(): void;
  waitUntilVisible(): Promise<void>;
  cancel(): void;
}


class DreamEntryTransition implements DreamEntryTransitionController {
  private readonly shell: HTMLElement;
  private readonly video: HTMLVideoElement | null;
  private readonly reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  private destinationReady = false;
  private handoffTimer = 0;
  private maskTimer = 0;
  private removeTimer = 0;

  constructor(private state: StoredDreamEntry) {
    document.querySelector<HTMLElement>("[data-dream-entry-cinematic]")?.remove();
    document.documentElement.classList.add("is-dream-entry-active");
    this.shell = document.createElement("div");
    this.shell.className = `dream-entry-cinematic${this.reducedMotion ? " is-reduced-motion" : ""}`;
    this.shell.dataset.dreamEntryCinematic = "active";
    this.shell.setAttribute("aria-hidden", "true");
    this.shell.innerHTML = this.reducedMotion
      ? `<img src="${DREAM_RUNTIME_ASSETS.dreamEntry.fallback}" alt="" draggable="false">`
      : `<video
          src="${DREAM_RUNTIME_ASSETS.dreamEntry.source}"
          poster="${DREAM_RUNTIME_ASSETS.dreamEntry.poster}"
          autoplay muted playsinline preload="auto"
        ></video>`;
    this.shell.insertAdjacentHTML(
      "beforeend",
      `<span class="dream-entry-cinematic-mist" aria-hidden="true"></span>
       <span class="dream-entry-cinematic-local-fog" aria-hidden="true"></span>`,
    );
    document.body.append(this.shell);
    this.video = this.shell.querySelector("video");
    this.resumeAtElapsedTime();
  }

  bindVisit(visitId: string): void {
    this.state = { ...this.state, visitId };
    writeStoredEntry(this.state);
  }

  markDestinationReady(): void {
    this.destinationReady = true;
    this.scheduleHandoff();
  }

  async waitUntilVisible(): Promise<void> {
    if (this.reducedMotion || !this.video) {
      await nextPaint();
      return;
    }
    if (this.video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      await nextPaint();
      return;
    }
    await Promise.race([
      new Promise<void>((resolve) => {
        this.video?.addEventListener("loadeddata", () => resolve(), { once: true });
      }),
      new Promise<void>((resolve) => window.setTimeout(resolve, 480)),
    ]);
    await nextPaint();
  }

  cancel(): void {
    this.clearTimers();
    this.shell.remove();
    document.documentElement.classList.remove("is-dream-entry-active");
    clearStoredEntry();
  }

  private resumeAtElapsedTime(): void {
    const elapsedMs = Math.max(0, Date.now() - this.state.startedAt);
    if (this.reducedMotion || !this.video) return;
    const seek = () => {
      this.video!.currentTime = Math.min(elapsedMs / 1000, (RUNTIME_END_MS - 40) / 1000);
      void this.video!.play().catch(() => undefined);
    };
    if (this.video.readyState >= HTMLMediaElement.HAVE_METADATA) seek();
    else this.video.addEventListener("loadedmetadata", seek, { once: true });
  }

  private scheduleHandoff(): void {
    if (!this.destinationReady) return;
    const elapsedMs = Math.max(0, Date.now() - this.state.startedAt);
    const waitMs = this.reducedMotion
      ? 180
      : Math.max(0, HANDOFF_START_MS - elapsedMs);
    window.clearTimeout(this.handoffTimer);
    this.handoffTimer = window.setTimeout(() => {
      this.handoffTimer = 0;
      if (!this.destinationReady) return;
      this.shell.classList.add("is-masking-abu");
      window.clearTimeout(this.maskTimer);
      this.maskTimer = window.setTimeout(() => {
        this.maskTimer = 0;
        this.shell.classList.add("is-handing-off");
        window.clearTimeout(this.removeTimer);
        this.removeTimer = window.setTimeout(
          () => this.cancel(),
          this.reducedMotion ? 240 : 760,
        );
      }, this.reducedMotion ? 40 : 220);
    }, waitMs);
  }

  private clearTimers(): void {
    window.clearTimeout(this.handoffTimer);
    window.clearTimeout(this.maskTimer);
    window.clearTimeout(this.removeTimer);
    this.handoffTimer = 0;
    this.maskTimer = 0;
    this.removeTimer = 0;
  }
}


export function beginDreamEntryTransition(): DreamEntryTransitionController {
  const state = { startedAt: Date.now(), visitId: "" };
  writeStoredEntry(state);
  return new DreamEntryTransition(state);
}


export function resumeDreamEntryTransition(): DreamEntryTransitionController | null {
  const state = readStoredEntry();
  if (!state || !state.visitId || Date.now() - state.startedAt > STALE_AFTER_MS) {
    clearStoredEntry();
    return null;
  }
  const routeVisitId = decodeURIComponent(
    location.pathname.match(/\/experience\/dream\/visits\/([^/]+)/)?.[1] || "",
  );
  if (!routeVisitId || routeVisitId !== state.visitId) {
    clearStoredEntry();
    return null;
  }
  return new DreamEntryTransition(state);
}


function readStoredEntry(): StoredDreamEntry | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null") as StoredDreamEntry | null;
    if (!value || !Number.isFinite(value.startedAt) || typeof value.visitId !== "string") return null;
    return value;
  } catch {
    return null;
  }
}


function writeStoredEntry(value: StoredDreamEntry): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}


function clearStoredEntry(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}


function nextPaint(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
}
