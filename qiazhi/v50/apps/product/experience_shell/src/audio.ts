import { prepareNarrationSegment } from "./api";
import type { NarrationManifest, NarrationSegment, NarrationStatus, SpeechAsset } from "./contracts";

export interface NarrationEvents {
  onPreparing(segment: NarrationSegment, index: number): void;
  onPlaying(segment: NarrationSegment, index: number): void;
  onPaused(segment: NarrationSegment, index: number): void;
  onComplete(): void;
  onError(error: Error): void;
  onCue(anchor: string): void;
}

export class NarrationTimeline {
  private audio: HTMLAudioElement | null = null;
  private index = -1;
  private cueTimers: number[] = [];
  private stopped = false;

  constructor(
    private readonly caseId: string,
    private readonly manifest: NarrationManifest,
    private readonly statuses: Record<string, NarrationStatus>,
    private readonly events: NarrationEvents,
  ) {}

  async play(): Promise<void> {
    if (this.audio?.paused && this.index >= 0) {
      await this.audio.play();
      this.scheduleCues(this.manifest.segments[this.index]);
      return;
    }
    this.stopped = false;
    this.index = this.index >= 0 ? this.index : 0;
    await this.playIndex(this.index);
  }

  pause(): void {
    this.clearCues();
    this.audio?.pause();
    const segment = this.manifest.segments[this.index];
    if (segment) this.events.onPaused(segment, this.index);
  }

  stop(): void {
    this.stopped = true;
    this.clearCues();
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    this.index = -1;
  }

  async playSegment(index: number): Promise<void> {
    this.stop();
    this.stopped = false;
    this.index = index;
    await this.playIndex(index);
  }

  private async playIndex(index: number): Promise<void> {
    const segment = this.manifest.segments[index];
    if (!segment || this.stopped) {
      this.events.onComplete();
      return;
    }
    try {
      this.events.onPreparing(segment, index);
      const audioUrl = await this.resolveAudioUrl(segment);
      if (this.stopped) return;
      this.audio = new Audio(audioUrl);
      this.audio.preload = "auto";
      this.audio.addEventListener("play", () => {
        this.events.onPlaying(segment, index);
        this.scheduleCues(segment);
      });
      this.audio.addEventListener("ended", () => {
        this.clearCues();
        this.index = index + 1;
        void this.playIndex(this.index);
      });
      this.audio.addEventListener("error", () => this.events.onError(new Error("audio_playback_failed")));
      await this.audio.play();
    } catch (error) {
      this.events.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  private async resolveAudioUrl(segment: NarrationSegment): Promise<string> {
    const status = this.statuses[segment.segment_id];
    if (status?.status === "ready" && status.audio_url) return status.audio_url;
    const asset: SpeechAsset = await prepareNarrationSegment(this.caseId, segment.segment_id);
    const opus = asset.media.playback_variants.find((item) => item.format === "opus");
    return opus?.audio_url || asset.media.audio_url;
  }

  private scheduleCues(segment: NarrationSegment): void {
    this.clearCues();
    for (const cue of segment.visual_cues || []) {
      const remaining = Math.max(0, cue.at_ms - Math.round((this.audio?.currentTime || 0) * 1000));
      this.cueTimers.push(window.setTimeout(() => this.events.onCue(cue.target), remaining));
    }
  }

  private clearCues(): void {
    this.cueTimers.forEach((timer) => window.clearTimeout(timer));
    this.cueTimers = [];
  }
}
