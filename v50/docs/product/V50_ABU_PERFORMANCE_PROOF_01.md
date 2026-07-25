# V50 Abu Performance Proof 01

Status: runtime-side proof passed; full Performance Runtime v1 acceptance blocked by Rive actor assets
Reference performance: `topic-00-performance-proof-01@1.0.0`

## Purpose

The Theater Control Runtime already proved that scenes can be compiled, kept private, synchronized and replayed. The Performance Runtime adds the missing audience-facing layer: Abu now speaks one approved Mingli cognition while the four pillars, approved reasoning path and unresolved condition enter the stage on the same clock.

It does not generate a new reading.

```text
Approved MingliExperienceEnvelope
        +
Frozen PerformanceCueInstance
        +
Frozen Qwen audio metadata
        -> PerformancePackage
        -> audio-clock playback
        -> subtitle / actor / viseme / stage / camera tracks
```

## Cognitive Boundary

The experience layer may stage only content already present in the envelope:

- chart facts;
- committed claims;
- committed reasoning steps;
- approved competing hypotheses or uncertainty;
- evidence and theory references already disclosed to the topic.

The performance compiler may split exact dialogue into timed subtitle blocks and schedule visual reveals. It may not summarize, strengthen, weaken or invent Mingli meaning. Theater choices remain participant-local and never write back into the LifeCase.

## Immutable PerformancePackage

One package freezes:

| Track | Responsibility |
| --- | --- |
| `audio` | URI, duration, speaker, voice version and audio hash |
| `subtitle_track` | Exact frozen dialogue split against the real audio duration |
| `actor_track` | Abu actions such as enter, speak, point and listen |
| `viseme_track` | Voice activity derived from the generated WAV energy |
| `stage_track` | Four pillars, reasoning steps, approved path and unresolved condition |
| `camera_track` | Wide, chart, path and choice framing |
| `stage_snapshot` | Complete frozen stage data for seeking and deterministic replay |

The package key binds cue hash, voice version and compiler version. The file-backed repository is write-once. A missing or corrupt frozen audio file fails loudly; Replay never silently regenerates it.

## Audio Authority

The HTML audio element is the sole playback clock. All subtitle, action, voice-activity, stage and camera events read `audio.currentTime`.

```text
Audio currentTime
  -> active subtitle
  -> latest Abu action
  -> latest voice activity
  -> due stage events
  -> latest camera framing
```

Pause stops the full performance. Seek rebuilds the stage from zero to the selected time. Replay resets the same package and reuses the same WAV. It does not call TTS, LLM or Reasoner.

## Qwen TTS Configuration

The v1 adapter uses the existing Qwen3-TTS HTTP service.

```bash
export V50_TTS_BASE_URL=http://127.0.0.1:17860
export V50_ABU_TTS_SPEAKER=Eric
```

The adapter calls `POST /tts` with text, speaker, language and a restrained Abu voice instruction. The first successful result is normalized into one WAV with a short entry and exit silence, then frozen with its SHA-256.

## First Performance

`topic00_performance_proof01.json` is deliberately small:

1. public entry;
2. one private Mingli performance;
3. one private continuation choice;
4. public close.

The private performance must show:

- the participant's four pillars;
- the committed reasoning path;
- one approved whole-chart line;
- one unresolved condition or competing hypothesis;
- exactly one choice after Abu finishes speaking.

If the participant has no eligible committed cognition, the same topic uses an honest chart-facts or observer path. It never pretends to know more.

## Actor Rendering Boundary

The current renderer is an honest WebP fallback. It changes Abu's action asset and uses actual WAV energy for voice presence. It does not claim frame-accurate mouth shapes.

`PerformancePackage.viseme_track` is ready for a future Rive actor renderer. True lip sync, smooth action blending and interruption-safe skeletal motion remain asset/runtime work, not completed v1 capabilities.

The required `.riv` delivery must provide:

```text
layered Abu character and stable stage anchor
idle breathing / blink / ear / tail motion
enter / speak / push / point / listen actions
warm / curious / serious / uncertain / closing expressions
closed / small-open / large-open / round / relaxed mouth shapes
gaze target / point target / speech intensity / tail speed inputs
```

Until that asset exists, the WebP renderer remains a visible proof fallback and the full `Abu Performance Runtime v1` gate stays open.

## Product Controls

The participant can:

- play and pause;
- seek on the frozen audio clock;
- mute;
- replay the same package;
- switch to the complete frozen text if sound is unavailable;
- inspect the stage timeline;
- choose one continuation only after the performance completes or text fallback is selected.

The near-player caption keeps the current Abu line visible on desktop and mobile even when the large opening dialogue has scrolled away.

## Verification

Targeted:

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi/v50
PYTHONPATH=packages:apps /Users/liujin/DEV/AIProjects/bazi/qiazhi/.venv312/bin/python \
  -m pytest tests/test_v50_abu_living_theater.py -q
```

Full regression:

```bash
PYTHONPATH=packages:apps /Users/liujin/DEV/AIProjects/bazi/qiazhi/.venv312/bin/python -m pytest -q
```

Open:

```text
http://127.0.0.1:8053/theater
```

## Proof Acceptance Boundary

Accepted:

- a real 60-90 second Abu performance can be produced;
- sound is the shared clock;
- real case facts and approved cognition visibly drive the stage;
- Replay is deterministic and regeneration-free;
- private audio is participant-authorized;
- desktop and mobile playback are usable.

Still required before `Abu Performance Runtime v1` can be accepted:

- a Rive character rig;
- true mouth-shape lip sync;
- automatic action blending across all Abu assets;
- a produced multi-person premiere;
- audience delight or retention claims.
