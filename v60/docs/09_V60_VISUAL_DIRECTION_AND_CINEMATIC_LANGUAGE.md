# V60 Visual Direction and Cinematic Language

## 1. Decision

V60 adopts **Eastern fairy-tale picture-book** as its primary visual
direction.

The accepted reference is the Owner's `AbuKnows V60 Unified Prototype`,
Sites version 4:

```text
https://abuknows-v60-prototype.liujin.chatgpt.site
```

Exact reference provenance is retained in
`design/references/README.md`. The prototype is a visual and interaction
reference, not a codebase or Runtime authority.

## 2. Core Composition

V60 has two complementary visual layers:

```text
White product ground
└── clarity, trust, reading, navigation and professional work

Living illustrated world
└── LifeTree, Dream, Abu, Theater, time and emotional movement
```

White is the base, but V60 must not feel like a generic white SaaS dashboard.
The illustrated world provides depth and warmth; the white shell gives the
Mingli system precision and calm.

The reference succeeds because it combines:

- a large hand-painted LifeTree as the first visual fact;
- off-white negative space rather than beige parchment;
- deep ink green for authority and legibility;
- muted antique gold for sparse, meaningful feedback;
- soft fog gray and moss green for atmosphere;
- restrained cards and controls that do not compete with the tree;
- Abu as a nearby companion, not a floating mascot badge.

## 3. LifeTree Art Direction

The LifeTree is V60's principal visual identity.

It must read as:

- old, alive and structurally credible;
- asymmetrical, with a memorable silhouette;
- rooted into its environment rather than pasted above it;
- capable of localized response through bark, leaves, dew and light;
- visually distinct by LifeCase phenotype without changing into unrelated
  art styles;
- large enough to remain the dominant object when questions or evidence are
  present.

Avoid:

- icon-like or vector-flat tree anatomy;
- floating semantic badges that do not grow from real geometry;
- roots detached from the ground;
- uniform glow around every clickable object;
- color swaps as the only LifeCase difference;
- tree-to-chart morphs that impersonate Mingli proof.

## 3.1 Abu Character Identity

`ABU_CHARACTER_V60_V1` is the primary V60 Abu: watercolor-and-gouache texture,
large warm eyes, stable black/tan/cream markings and a rust-red scarf. The
transparent seated poster is the current Runtime fallback.

The earlier `ABU_CHARACTER_V1` cartoon actor remains in the media library for
historical compatibility. It is not deleted, but it does not define future
V60 motion generation.

## 4. Color and Material Language

| Role | Direction |
| --- | --- |
| Product ground | clean off-white, cool white, very light mist gray |
| Authority | deep ink green |
| Living structure | bark brown, moss and desaturated leaf greens |
| Meaningful response | muted antique gold in small amounts |
| Dream depth | fog gray, water reflection, cool shadow green |
| Warning | restrained neutral contrast, never theatrical red disaster cues |

Gold is an event material, not a permanent theme color. It may mark a moment
of recognition, sealing, dissolution or transfer, but it must not turn every
successful action into a reward animation.

Materials should feel painted, fibrous, moist or mineral. Glassmorphism,
neon bloom and glossy 3D plastic are outside this direction.

## 5. Typography and Interface

- Display Chinese uses a confident Song/Ming-inspired serif where available.
- Body, metadata and controls use a highly legible sans serif.
- Headings may be large only when they are the scene's true proposition.
- Technical IDs, rule codes and provenance remain in Lab, not in Dream.
- Functional cards use restrained radii; large rounded framing is reserved
  for a scene canvas, not nested card stacks.
- Commands remain live interface elements. Gemini video never contains
  readable labels, options or buttons.

On desktop, the reference pattern is valid:

```text
LifeTree scene / proposition
+ nearby Abu interpretation and next action
+ compact persistent navigation
```

It must remain one product composition rather than five unrelated portals.

## 6. One Visual System Across Five Units

| Unit | Expression |
| --- | --- |
| Abu Dream | immersive illustrated world, minimal interface, cinematic thresholds |
| Abu Mingli | white editorial ground, exact facts, tree as living case overview |
| Abu Says | quiet companion panel or in-scene utterance, never a chatbot takeover |
| Abu Theater | authored scene beats and time/path transitions |
| Mingli Lab | precise white/ink-green workspace using the same LifeCase and visual tokens |

Dream is not the only colorful section while the others become unrelated
admin tools. The five units share typography, color, evidence identity,
motion language and selected semantic object.

## 7. Video-First, State-Safe Motion

V60 is **cinematic where movement carries emotion or spatial continuity**.
It is not a video player pretending to be an interactive world.

### 7.1 Cinematic video

Use generated and postprocessed scene video for:

- entering or leaving Dream;
- crossing fog, water or a tree boundary;
- tree growth and major seasonal change;
- a flower opening or a fruit revealing when the shot is stable;
- Theater beats;
- text or symbolic matter dissolving into gold dust;
- one-time emotional responses that benefit from authored timing.

### 7.2 Transparent actor motion

Use alpha actor animation for:

- Abu idle, listening, acknowledging and guiding;
- walking while the Runtime moves the actor container;
- small one-shot reactions;
- reusable foreground actions across multiple scenes.

### 7.3 Runtime scene layers

PixiJS/React retain:

- canonical world and encounter state;
- click geometry and hit masks;
- tree phenotypes and semantic node placement;
- text, answer options and accessibility;
- loading, interruption and recovery;
- live OneCanvas and Lab data;
- any fact that can vary per LifeCase or viewer.

### 7.4 Interface motion

CSS or Runtime animation handles:

- focus, hover, panel transitions and reduced-motion fades;
- state changes that must respond immediately;
- small geometry-preserving feedback.

## 8. Video Handoff Contract

Every cinematic clip must declare:

```yaml
source_scene_ref:
target_scene_ref:
first_frame_reference:
last_frame_reference:
camera_and_crop:
subject_anchor:
interactive_handoff_ms:
audio_cue_ref:
skippable:
interrupt_policy:
reduced_motion_asset_ref:
failure_fallback:
```

The Runtime:

1. commits or obtains the next allowed state;
2. plays the approved clip;
3. crossfades into an interactive scene with matching composition;
4. resumes interaction only after the handoff;
5. restores the committed target state after refresh or interruption.

A video cannot commit a world event, answer, Seal, Reveal or Mingli fact.
Failure to load a clip falls back to the same target state through a declared
static transition; it does not roll back canonical state.

## 9. Reference Interaction: Gold-Text Dissolution

The prototype's post-answer beat is accepted as a useful language:

```text
user chooses
-> live UI commits the choice
-> selected words fracture
-> fragments become fine gold dust
-> dust disperses into the LifeTree world
-> the next committed story state remains
```

The animation communicates that a choice has entered the world's memory. It
must not imply correctness, reward value or a favorable outcome.

Implementation rule:

- option selection and persistence happen outside the video;
- the video receives only a non-semantic transition cue;
- answer text itself stays accessible until commit succeeds;
- reduced motion uses a short fade and localized gold settling;
- a failed commit never plays the irreversible dissolution.

## 10. Gemini Production Rule

All new visual prompts begin with
`media/prompts/V60_EASTERN_FAIRY_TALE_STYLE_LOCK.md`, followed by:

1. scene purpose;
2. exact first-frame reference;
3. exact last-frame reference;
4. one primary action;
5. camera and subject lock;
6. forbidden semantic implications;
7. technical delivery request.

Gemini creates source footage. Codex performs source QA, audio separation,
watermark-safe processing, alpha extraction, continuity repair, delivery
encoding and catalogue registration under the V60 Media Pipeline.

## 11. Accessibility and Performance

- No essential information exists only inside video.
- Captions and ARIA text come from approved Runtime content.
- Audible media requires a user gesture.
- Reduced motion replaces travel and particle dispersion with spatially
  coherent fades.
- Low-performance mode may use a poster plus short opacity transition.
- Scene video is preloaded only when the next legal state is known.
- Large media never blocks the first usable screen.

## 12. Implemented Visual Baseline

The first V60 vertical slice now uses the accepted visual language end to end:

- white product shell, ink-green authority text and restrained antique gold;
- the approved prototype LifeTree world as the scene reference;
- a clean pre-fruit Runtime derivative with the baked fruit removed;
- `ABU_CHARACTER_V60_V1` as the visible companion;
- tree-attached semantic marks instead of the former detached organ stickers;
- the question, sealed, matured, reveal, Abu, Theater and Lab projections in
  one shared composition;
- fixed desktop scene geometry with no document scrolling;
- reduced-motion and 390 px guardrails without a separate mobile product.

Runtime asset lineage:

```text
V60_LIFE_WORLD_BACKGROUND_REFERENCE_V1
sha256 1e7f5f82e20ad3817d67894f414fcddadfef50c89b5ed443b60d005298d45da4
-> remove only the pre-seal baked fruit
-> V60_LIFE_WORLD_BACKGROUND_CLEAN_V1
sha256 2b9c47ee05d0c6967ce5173e3fc353c64f9de82d09e13130797738d61b874df2
-> dream.v60.life-world.clean.v1
```

The source, derivative, operation and delivery are registered in
`media/catalog.json` and `assets/registry.json`. The previous semantic-tree
images remain archived for lineage but are no longer rendered by the current
LifeTree scene.

## 13. Remaining Production Media

The current slice is complete with static Runtime-safe presentation. Its next
media upgrades require approved sources rather than code-generated substitutes:

1. V60 Abu transparent motions: `IDLE`, `LISTEN`, `ACKNOWLEDGE`, `WAITING` and
   `GUIDE`, all locked to `ABU_CHARACTER_V60_V1`.
2. One tree-local cinematic set with identical camera and branch anchor:
   `FLOWER_BUD -> FLOWER_OPEN -> SEALED_FRUIT -> MATURE_FRUIT`.
3. A short question-seal transition using the accepted gold-dust language.
4. Separate subtle foliage, branch resonance and fruit-open audio stems.

These assets may improve motion and material fidelity. They may not own or
change AnswerSeal, WorldEvent, Fruit, Reveal or LifeCase state.
