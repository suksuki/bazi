# Abu Theater Mobile & Social Delivery v1

Date: 2026-07-20  
Status: `IMPLEMENTED / MACHINE PASS / LOCAL VISUAL PASS`

## Problem

The mobile theater had two coupled failures:

1. the sound control was hidden at the mobile breakpoint;
2. the story clock depended entirely on `audio.currentTime`, so blocked or unavailable audio also stopped the visual story.

The desktop composition was already acceptable and was treated as a protected baseline.

## Implemented Experience

### Mobile entry

- A phone opens on one explicit decision: `有声播放` or `静音观看`.
- Both actions start the same formal story timeline.
- The sound switch remains visible after entry.
- Play, pause, seek, sound and silent playback remain available inside the 390px safe area.

### Playback resilience

- Audio is the preferred clock when it is available.
- If audio playback is rejected, the theater changes to a visual fallback clock.
- The fallback continues subtitles, actor actions, OneCanvas changes and the Xiangfa handoff.
- Sound can be retried without restarting the story.

### Mobile composition

- Six pillars, the `甲 → 丁 → 庚` observation path, Abu, stage controls, subtitles and transport have separate visual zones.
- The path remains visible on phone instead of disappearing with the desktop SVG layer.
- Touch targets are at least 44px and respect the bottom safe area.

### Delivery profiles

```text
interactive phone: 390 × 844
desktop / YouTube: 1920 × 1080
Douyin / Shorts:   1080 × 1920
```

The 9:16 profile is an independent composition. It is not a crop or enlarged phone stylesheet.

## Evidence

- `mobile-390-entry-clean.jpg`
- `mobile-390-final-path-stable.jpg`
- `desktop-1440x900-regression.jpg`
- `portrait-1080x1920-final.jpg`

The portrait renderer produced a real `1080 × 1920` frame. The landscape renderer produced a real `1920 × 1080` frame.

## Protected Boundaries

This correction did not change:

- Scene Source;
- narration copy;
- approved Mingli relations;
- Runtime, Reasoner or LifeCase;
- Xiangfa semantic bindings;
- the accepted desktop narrative.

It changes only playback resilience, responsive composition and export profiles.

## Verification

```text
mobile entry:                 PASS
sound start:                  PASS
silent start:                 PASS
silent visual progression:    PASS
mid-story sound enable:       PASS
pause and resume:             PASS
390px safe-area controls:     PASS
desktop regression:           PASS
portrait render 1080×1920:    PASS
landscape render 1920×1080:   PASS
targeted tests:               15 passed
full regression:              439 passed
```

## Release Note

This is a local implementation and validation result. It has not been deployed to the 13 server in this task.
