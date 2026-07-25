const MP3_SOURCE = "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.mp3";
const SESSION_ENABLED_KEY = "deepbeing.opening_music.enabled.v1";
const SESSION_PLAYED_KEY = "deepbeing.opening_music.played.v1";

export type OpeningMusicState = "armed" | "playing" | "paused" | "complete" | "blocked";

export class OpeningMusicController {
  private readonly audio: HTMLAudioElement;
  private state: OpeningMusicState;
  private armed = false;

  constructor(private readonly onStateChange: () => void) {
    this.audio = new Audio(MP3_SOURCE);
    this.audio.preload = "metadata";
    this.audio.loop = false;
    this.audio.volume = 0.52;
    const enabled = window.sessionStorage.getItem(SESSION_ENABLED_KEY) !== "off";
    const alreadyPlayed = window.sessionStorage.getItem(SESSION_PLAYED_KEY) === "1";
    this.state = enabled && !alreadyPlayed ? "armed" : alreadyPlayed ? "complete" : "paused";
    this.reflectState();
    this.audio.addEventListener("play", () => this.setState("playing"));
    this.audio.addEventListener("pause", () => {
      if (!this.audio.ended && this.state === "playing") this.setState("paused");
    });
    this.audio.addEventListener("ended", () => {
      window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
      this.setState("complete");
    });
    this.audio.addEventListener("error", () => {
      document.documentElement.dataset.openingMusicError = "media_error";
      this.setState("blocked");
    });
  }

  arm(): void {
    if (this.armed || this.state !== "armed") return;
    this.armed = true;
    document.addEventListener("pointerdown", this.onFirstGesture, { capture: true });
    document.addEventListener("keydown", this.onFirstKeyGesture, { capture: true });
  }

  async toggle(): Promise<void> {
    this.disarm();
    if (this.state === "playing") {
      window.sessionStorage.setItem(SESSION_ENABLED_KEY, "off");
      this.audio.pause();
      return;
    }
    window.sessionStorage.setItem(SESSION_ENABLED_KEY, "on");
    if (this.state === "complete" || this.audio.ended) this.audio.currentTime = 0;
    await this.tryPlay();
  }

  pauseForNarration(): void {
    this.disarm();
    window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
    if (!this.audio.paused) this.audio.pause();
    if (this.state === "armed") this.setState("complete");
  }

  syncControls(root: ParentNode = document): void {
    root.querySelectorAll<HTMLButtonElement>("[data-opening-music-control]").forEach((button) => {
      const label = this.controlLabel();
      button.dataset.musicState = this.state;
      button.setAttribute("aria-pressed", String(this.state === "playing"));
      button.setAttribute("aria-label", label);
      button.title = label;
    });
  }

  private readonly onFirstGesture = (event: Event): void => {
    if (this.shouldDeferToControl(event.target)) return;
    this.disarm();
    void this.tryPlay();
  };

  private readonly onFirstKeyGesture = (event: KeyboardEvent): void => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if (this.shouldDeferToControl(event.target)) return;
    this.disarm();
    void this.tryPlay();
  };

  private shouldDeferToControl(target: EventTarget | null): boolean {
    if (!(target instanceof Element)) return false;
    return Boolean(target.closest("[data-opening-music-control], [data-command='listen'], [data-play-segment]"));
  }

  private async tryPlay(): Promise<void> {
    try {
      await this.audio.play();
      window.sessionStorage.setItem(SESSION_PLAYED_KEY, "1");
    } catch (error) {
      document.documentElement.dataset.openingMusicError = error instanceof DOMException
        ? error.name
        : "playback_rejected";
      this.setState("blocked");
    }
  }

  private disarm(): void {
    if (!this.armed) return;
    this.armed = false;
    document.removeEventListener("pointerdown", this.onFirstGesture, { capture: true });
    document.removeEventListener("keydown", this.onFirstKeyGesture, { capture: true });
  }

  private setState(state: OpeningMusicState): void {
    this.state = state;
    this.reflectState();
    this.onStateChange();
  }

  private reflectState(): void {
    document.documentElement.dataset.openingMusicState = this.state;
  }

  private controlLabel(): string {
    if (this.state === "playing") return "暂停开场音乐";
    if (this.state === "armed") return "播放开场音乐；首次操作后会自动开始";
    if (this.state === "complete") return "重播开场音乐";
    if (this.state === "blocked") return "浏览器未能播放；点击重试";
    return "播放开场音乐";
  }
}
