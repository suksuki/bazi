# V60 Media Library and Production Pipeline

## 1. Purpose

V60 treats animation, sound and scene media as versioned product assets, not
loose files copied into a web directory.

```text
Product state and action contract
-> detailed Gemini request
-> immutable generated source
-> technical and character QA
-> reproducible postprocess
-> Owner review
-> Runtime delivery
-> versioned audio/visual Cue Bundle
```

This pipeline supports:

- transparent Abu actor animation;
- full-scene Dream transitions;
- static scene layers and posters;
- music, ambience, Foley and voice;
- later upgrades without overwriting an accepted version;
- exact reconstruction of what the Runtime played.

The shared art direction and video handoff rules are defined in
`docs/09_V60_VISUAL_DIRECTION_AND_CINEMATIC_LANGUAGE.md`. New Gemini visual
requests must include `media/prompts/V60_EASTERN_FAIRY_TALE_STYLE_LOCK.md`.

## 2. Responsibilities

| Role | Responsibility |
| --- | --- |
| Owner | Product intent, character acceptance, aesthetic acceptance and release approval |
| Codex | Derive action needs from real product states, write prompts, preserve sources, postprocess, verify, catalogue and publish approved deliveries |
| Gemini | Generate requested source video or audio; it does not decide Runtime state or asset eligibility |
| V60 Runtime | Resolve only registered asset versions and approved Cue Bundles |

The action contract comes before generation. An attractive motion with no
valid product trigger is not admitted merely because it exists.

## 3. Two Authorities, One Chain

`media/catalog.json` owns production lineage:

- original file and generator;
- prompt reference;
- revision;
- processing manifest;
- masters and review artifacts;
- Owner-review status;
- Runtime deliveries;
- audio/visual pairing.

`assets/registry.json` owns Runtime publication:

- stable `asset_ref`;
- exact `asset_version`;
- deployable path;
- media type;
- SHA-256;
- V60 product role.

The Runtime registry is a release projection of the Media Catalog. It is not
a second production catalogue. Product components may never read
`media/sources`, `media/masters` or `media/review`.

The executable resolver is `abu_v60.media.runtime.runtime_media_manifest`.
`/api/v60/bootstrap` exposes only its named, admitted bindings. React and
PixiJS consume those projected URLs and hashes; they do not embed
`/assets/...` paths. A missing asset, incomplete Cue Bundle, non-public
delivery or non-registered media item fails closed before the experience
loads. There is no cross-identity or legacy visual fallback.

## 4. Directory Contract

```text
media/
├── catalog.json
├── schemas/
├── prompts/
├── jobs/
├── sources/<ASSET_ID>/<revision>/
├── masters/<ASSET_ID>/<revision>/
├── manifests/
└── review/<ASSET_ID>/<revision>/

web/public/assets/
└── approved Runtime deliveries only
```

- `sources`: immutable Gemini originals and ingest receipts.
- `masters`: clean, high-quality intermediates from which deliveries can be
  reproduced.
- `manifests`: processing decisions, hashes, frame ranges, anchors and output
  contracts.
- `review`: checkerboards, contact sheets, first/last-frame comparisons and
  handoff previews.
- `web/public/assets`: approved delivery files only.

## 5. Naming and Versioning

An identity and a revision are different:

```text
asset_id: ABU_02_CALM_FOLLOW_WALK_LOOP_V1
revision: v1
media_ref: media.abu.calm-follow-walk.v1
```

Rules:

1. An ingested `(asset_id, revision)` is immutable.
2. A changed Gemini source is a new revision.
3. A materially changed action contract is a new asset identity.
4. An existing Runtime delivery is never silently replaced.
5. Existing scenes and visits remain bound to the exact version they used.
6. Retirement removes an item from new selection; it does not erase lineage.

## 6. Request and Ingest

### 6.1 Product Contract

Before prompting Gemini, record:

- semantic state and trigger;
- `loop`, `one-shot` or transition;
- duration and useful action window;
- interruptibility and return action;
- body and camera constraints;
- anchor and expected bounding box;
- preferred screen side and direction;
- desktop/mobile suitability;
- reduced-motion fallback;
- audio role and synchronization needs.

Use `media/prompts/GEMINI_MEDIA_REQUEST_TEMPLATE.md`.

### 6.2 Source Admission

A source requires explicit Owner authorization. Ingest records:

- original filename;
- SHA-256 and byte size;
- generator and prompt reference;
- video/audio stream probe;
- ingest timestamp;
- publication status `NOT_PUBLISHED`.

```bash
.venv/bin/python tools/ingest_media_source.py \
  --media-id ABU_04_LISTEN_ONCE_V1 \
  --revision v1 \
  --kind ACTOR_MOTION \
  --source /absolute/path/source.mp4 \
  --generator Gemini \
  --prompt-ref media/prompts/ABU_04_LISTEN_ONCE_V1.md \
  --authorization OWNER_APPROVED_GENERATED_SOURCE
```

The command refuses a different file at an existing revision.

## 7. Video Postprocess

Every job starts from the preserved source and a versioned job manifest.

### 7.1 Source QA

Inspect:

- character identity and proportions;
- mouth, eyes, scarf, tail and limb continuity;
- camera lock and framing;
- accumulated translation or scale drift;
- useful action interval;
- first/last loop phase;
- background key stability;
- watermark position;
- source audio streams.

### 7.2 Clean Master

For Owner-authorized generated media:

1. Keep the original unchanged.
2. Remove embedded audio from the visual master.
3. Exclude a platform mark using a safe crop, mask outside the subject, or
   transparent actor isolation.
4. Do not use generative inpainting to invent missing character pixels.
5. Do not remove attribution or marks from material the Owner is not
   authorized to process.

Scene video remains opaque. Actor video is keyed, despilled and exported with
alpha.

### 7.3 Actor Extraction

- chroma key and despill without eroding eye, fur or scarf edges;
- stabilize the declared anchor and bounding box;
- preserve natural breathing and gait rise/fall;
- move locomotion through the Runtime container, not baked translation;
- select a real motion phase for loops;
- avoid forced crossfades that create double limbs or ghosting.

Standard actor deliveries:

```text
VP9 Alpha WebM
Animated WebP
Reduced Motion PNG poster
Transparent PNG master frames
Checkerboard loop preview
```

PNG master frames may be archived outside the web bundle when large; their
manifest and hash remain part of production lineage.

### 7.3.1 Current V60 Actor Mapping

```text
QUIET_COMPANION_IDLE
-> ABU_V60_SEATED_IDLE_LOOP_V1

GUIDE_LEFT
-> ABU_V60_05_GUIDE_LEFT_ONCE_V1
-> PLAY_ONCE
-> return to ABU_V60_SEATED_IDLE_LOOP_V1
```

`GUIDE_LEFT` is admitted from source frames 12-115. The repeated source gesture
and the complete right-side generated window are excluded before alpha
delivery. It is shown only when Abu is on the right and a real tree action is
available on the left.

Runtime cue bindings:

```text
cue.dream.abu-idle.v1
-> ABU_V60_SEATED_IDLE_LOOP_V1
-> VP9 alpha or same-identity reduced-motion poster

cue.dream.abu-guide-left.v1
-> ABU_V60_05_GUIDE_LEFT_ONCE_V1
-> return to cue.dream.abu-idle.v1
```

### 7.4 Scene and Transition Delivery

For full-screen scenes:

- preserve the clean high-quality master;
- record source and delivery framing;
- extract first/last reference frames;
- verify the final frame aligns with the interactive scene;
- use a local fog or occlusion handoff when actor poses differ;
- never use the tail of a video as a substitute for the interactive scene.

## 8. Audio Postprocess

Audio remains independent from transparent actor video.

1. Preserve the original generated or extracted source.
2. Create a `48 kHz / 24-bit` WAV master when production processing is
   required.
3. Remove unintended silence, clicks and DC offset.
4. Use a default integrated target of `-20 LUFS` and `-2 dBTP` ceiling unless
   the scene mix contract says otherwise.
5. Publish Opus plus MP3 fallback for web playback.
6. Give narration priority through ducking; music may not obscure speech.
7. Audible playback starts only after a user gesture and always respects mute
   and volume controls.

Music, ambience, Foley and speech are separate stems when independent control
is useful.

## 9. Cue Bundles

A `CueBundle` binds approved visual and audio identities without modifying
either source:

```yaml
cue_ref: cue.dream.grove-arrival.v1
trigger: FIRST_GROVE_ARRIVAL_AFTER_USER_GESTURE
visual_media_ref: media.abu.seated-idle.v1
audio_media_refs:
  - media.audio.morning-glints.v1
sync:
  mode: INDEPENDENT_AMBIENCE
  visual_offset_ms: 0
  audio_offset_ms: 0
  end_policy: VISUAL_CONTINUES_SILENTLY
```

A cue also owns:

- visual/audio offsets;
- loop and end policy;
- timeline handoff;
- narration priority;
- reduced-motion behavior;
- honest `AUDIO_GAP` status when no suitable sound exists.

No arbitrary audio is attached merely to make a cue appear complete.

## 10. Review and Publication

Lifecycle:

```text
DRAFT_REQUEST
-> SOURCE_RECEIVED
-> SOURCE_APPROVED
-> POSTPROCESSING
-> POSTPROCESS_COMPLETE
-> OWNER_REVIEW
-> LIBRARY_READY
-> RUNTIME_REGISTERED
-> RETIRED
```

Owner review checks:

- identity and motion;
- loop or transition continuity;
- alpha edges and ground contact;
- anchor/bounding-box stability;
- scene handoff;
- audio quality and synchronization;
- reduced-motion fallback.

Only an accepted item may gain Runtime deliveries. Publication requires:

1. all catalogue paths and hashes verify;
2. every delivery matches `assets/registry.json`;
3. the Runtime registry verifies every local file hash;
4. the database registry is synchronized;
5. product code selects only the registered version.

```bash
.venv/bin/python tools/verify_media_library.py
.venv/bin/python tools/audit_media_technical_contracts.py
.venv/bin/python tools/sync_asset_registry.py
```

## 11. Upgrade and Rollback

- A better source or postprocess becomes a new revision.
- The old revision remains reproducible.
- Cue Bundles choose exact media refs and versions.
- Rollback selects a previous registered version; it never edits hashes.
- A bad item becomes `RETIRED`, while manifests and original sources remain.
- Missing media fails explicitly; the Runtime may use only a declared,
  approved fallback from the same contract.

## 12. Provenance and Safety

- V60 keeps local copies of admitted media; Runtime never reads V50 paths.
- File existence does not imply release approval.
- Generated visuals, audio, prompts and transformations retain source hashes.
- Media may express a committed scene but cannot become a LifeCase fact,
  world outcome or Mingli conclusion.
- Audio, captions and ARIA text must not disclose sealed outcomes.
- Review files and source audio are excluded from Runtime caches and preload.

## 13. Initial V60 Inventory

| Media | State | Runtime use |
| --- | --- | --- |
| `ABU_01_SEATED_IDLE_LOOP_V3` | `RUNTIME_REGISTERED` | Alpha WebM, WebP and poster |
| `ABU_02_CALM_FOLLOW_WALK_LOOP_V1` | `RUNTIME_REGISTERED` | Alpha WebM, WebP and poster |
| `ABU_V60_CHARACTER_REFERENCE_V1` | `LIBRARY_READY` | Primary V60 identity lock |
| `ABU_V60_SEATED_TRANSPARENT_V1` | `RUNTIME_REGISTERED` | Primary V60 static companion |
| `ABU_03_DREAM_ENTRY_TRANSITION_V1` | `OWNER_REVIEW` | Blocked pending V60 review |
| `AUDIO_MORNING_GLINTS_IN_THE_GROVE_V1` | `RUNTIME_REGISTERED` | Opus and MP3 |

Current Cue status:

- grove arrival: visual and music pairing recorded, product wiring pending;
- follow walk: actor available, dedicated step/scarf audio is an explicit gap;
- Dream entry: pairing recorded, blocked with ABU_03 pending V60 review.

This initial import proves the production chain. It does not automatically
authorize any new Dream scene or audible autoplay.

Character identity policy:

- `ABU_CHARACTER_V60_V1` is primary for new V60 art and motion generation.
- `ABU_CHARACTER_V1` remains intact for legacy cartoon animations.
- A legacy motion cannot be relabeled as V60 character motion.
- Product scenes may use the V60 static poster until an approved V60 motion
  exists.
