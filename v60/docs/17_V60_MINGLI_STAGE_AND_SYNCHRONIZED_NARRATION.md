# V60 Mingli Stage and Synchronized Narration

Status: `IMPLEMENTED_AND_REAL_BROWSER_AUDITED_LOCAL`

Date: 2026-08-01

This is the first implementation slice for the pre-prototype-merge Mingli
vertical. It does not claim that V60 has reached advanced-practitioner-grade
destiny reading. It turns the existing canonical Case and bounded Reading
foundation into one visible, recoverable product path:

```text
Home profile leaf
-> real Mingli branch
-> branches / leaves / flowers / fruit for the four evidence layers
-> four-pillar natal stage
-> six-pillar time layer
-> server-locked Abu narration
-> audio-clocked subtitles and deterministic stage emphasis
```

Dream, the ten-tree loop, multi-NPC scenes, the question bank, iPad book layout
and mobile are not part of this slice. The current acceptance target is
Desktop Chrome.

## Owner decisions now in the executable baseline

- There is no directed invitation. The Mingli entry remains the profile leaf
  on the Home LifeTree.
- The default stage is the complete natal four pillars.
- Expanding time shows exactly natal four pillars plus current Dayun plus the
  selected annual pillar. A five-pillar state is invalid.
- The current layout target is Desktop Chrome. iPad portrait is deferred to
  the book-edition design round, and mobile remains a separate visual design
  problem.
- Abu is the boy narrator and now uses the Owner-selected Qwen3-TTS speaker
  `Dylan`. Dodo remains the girl narrator using the `Vivian` audition profile.
- The older Eric generation is append-only historical audition evidence. It
  was not deleted or rewritten.
- Sichuanese expression remains reserved for Theater rather than the formal
  Mingli Reading.

The selected Abu voice identity is
`v60.voice-profile.abu-dylan-owner-selected.001`. An environment override is
automatically demoted to `AUDITION_CANDIDATE`; it cannot inherit the
Owner-selected label.

## Canonical subjects

The stage can project only:

1. the authenticated account's active `HUMAN_OWNER` Case;
2. that account's private `HUMAN_REFERENCE` Cases; and
3. the two explicitly admitted `CANONICAL_SYNTHETIC` character Cases.

Private reference subjects use stable `case:{case_ref}` routes and require the
same account authorization as their Case workspace. Their Stage and branch
summary bind the exact Case, Chart, LifeCase and formal Reading Ref/Hash. The
Home API that carries private birth details is explicitly `private, no-store`.
The canonical evidence drawer remains available only when all of those
identities match the active Owner Home snapshot; a reference route fails
closed rather than reading from or writing to the Owner Case.

The synthetic character birth details are Owner-approved fictional product
fixtures, not biographies and not substitutes for a real user Case:

| Character | Setting | Canonical four pillars |
| --- | --- | --- |
| Abu | male, 1998-11-11 12:00, Beijing | 戊寅 / 癸亥 / 壬戌 / 丙午 |
| Dodo | female, 2001-05-08 18:00, Shanghai | 辛巳 / 癸巳 / 辛未 / 丁酉 |

They use stable Profile and Case identities under a separate inactive system
account. Replay is idempotent. Historical human profiles with similar display
names are neither selected nor overwritten. The public stage API exposes no
birth date, time or location.

## Four- and six-pillar contract

`NATAL_4` contains four columns and eight bodies:

```text
year / month / day / hour
```

`NATAL_DAYUN_YEAR_6` contains six columns and twelve bodies:

```text
year / month / day / hour / current Dayun / selected annual year
```

The current Dayun is compiled through the existing canonical timing engine.
The calculation policy is now explicit as
`LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES`; the displayed boundary
precision is the exact start-solar date returned by the pinned calendar
engine. On a transition date, a Case that has no observation time fails closed
with `START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY` rather than claiming a
current Dayun that the evidence cannot distinguish.

The selected annual column uses that solar year's Ganzhi
(`SELECTED_SOLAR_YEAR_GANZHI`). It is not derived from the current instant, so
January and pre-Lichun viewing cannot silently substitute the previous annual
label.

Every Projection binds the exact Case, Chart, LifeCase, active Foundation and
Timing profiles, source Refs and Hash. A formal Owner Reading identity is
included when present; the stage does not compile a new timing vector and
mislabel it as the historical Reading's evidence.

## Epistemic boundary

The stage can draw only admitted six-clash and six-harmony membership facts.
It deliberately holds these fields:

```text
stage_semantics = COORDINATES_AND_MEMBERSHIP_ONLY
relation_effect_status = UNRESOLVED
usable_source_status = UNRESOLVED
professional_verdict_allowed = false
```

It does not infer strength, usable root, relation effect, timing activation,
probability, effective work or auspiciousness. A visible relation line means
only that two displayed coordinates are members of an admitted relation
pair. It does not prove that the relation acts or that a source is usable.

This is the product form of the current professional evidence gap: the system
can locate the question and show competing or missing explanations, but it
cannot invent a professional relation-effect rule.

## Narration authority and playback

The browser submits only the subject, stage mode, year and expected Projection
Ref/Hash. It cannot submit narration text, speaker, model, provider or TTS URL.
The Media owner locks:

```text
Projection Ref/Hash
+ server-authored script Ref/Hash
+ actor and voice profile Ref/Hash
+ provider profile Ref/Hash
+ frame-exact cue ranges
+ WAV Ref/Hash
```

The service calls Qwen3-TTS on the server. The default public proxy is
`https://dblife.com/abu-tts/tts`; Server 13 may configure the private upstream
`http://192.168.0.7:7860/tts`. Neither address is returned to the browser. The
client receives only an authenticated same-origin audio URL with private,
no-store and Range semantics.

The playback states are:

```text
PREPARING -> READY -> PLAYING <-> PAUSED
                         <-> BUFFERING
                         -> ENDED / FAILED
```

While PREPARING, semantic subtitles and motion do not run. During PLAYING,
`HTMLAudioElement.currentTime` is the sole subtitle, cue and deterministic
stage-emphasis clock. PAUSED freezes the same clock. Refresh preserves the selected Case,
four/six-pillar mode and year through the URL, while narration returns to
`IDLE`; it never pretends to recover an in-flight audio position.

### Current-layer silent rehearsal

The grown LifeTree branch now has a separate companion action before formal
audio delivery. It projects the selected four-layer Reading surface from the
same validated ClaimGraph used by Reading and Lab:

```text
current layer
-> admitted ClaimGraph claims only
-> ordered rehearsal chapters
-> same four/six-pillar Scene Player
-> LISTENING / PAUSED character state
```

This is deliberately not a cosmetic wrapper around the earlier coordinate
narration. It does not call `/api/v60/mingli/narrations`, mount an audio element
or claim that semantic Cue choreography has been approved. `WITHHELD` claims
are excluded, internal codes such as `WEAK` are translated into user-facing
Chinese, Work Path closure and assessment states preserve their distinct
professional meanings, and each visible chapter carries the exact Claim Ref
plus Graph Ref/Hash. A layer with no admitted/projectable Claim cannot enter
rehearsal. The time-trend layer opens the full six-pillar coordinate state; the
other three layers open the natal four-pillar state.

The six-pillar coordinate state is not itself permission to attach frozen
Reading prose to the selected year. Until ClaimGraph carries a typed binding
between its Dayun/annual claims and the independently selected Stage timing
vector, time rehearsal contains only `TIMING_NATAL` and
`DISCRIMINATING_QUESTION`. It visibly says that Dayun/annual paragraphs are
still being aligned, and never paints an old annual judgment onto a new year.

The route distinguishes three product intents:

```text
mingli_stage=1&mingli_rehearsal=1  companion rehearsal
mingli_stage=1                     ordinary Reading observation
view=lab                           explicit Lab research surface
```

Refresh restores rehearsal. Back returns to the same branch and selected
layer, Forward restores it, and closing rehearsal returns to Reading
observation without opening Lab. Formal server-locked TTS remains available
from the ordinary Reading/Lab stage, but its current coordinate script is not
silently reused as four-layer destiny narration.

## One shared Scene Player

The first frozen-V108 integration slice no longer treats Abu Says as a panel
inside Lab. `MingliSceneHost` remains mounted while the user switches among
Mingli Reading, Lab observation and narrated presentation. It owns exactly one
lazy-loaded React Three Fiber Scene Player:

```text
MingliSceneHost
├── MingliScenePlayer          one Canvas / one Projection
├── ReadingSceneGuide          presentation only
├── MingliLabSceneInspector    selection and evidence only
└── MingliNarrationDirector
    ├── MingliAudioPlayer      audio transport and sole clock
    └── CharacterPerformance  actor state and transparent media
```

Reading and Lab never mount their own Canvas. Opening or closing narration
also leaves the same Scene Player instance in place. Moving from four to six
pillars updates the server-issued Projection in that instance; it does not
create a second stage or a five-pillar intermediate state.

The earlier canonical Reading and Lab controls remain reachable through a
collapsible evidence drawer beside the shared stage only for an exact active
Owner lineage match. It preserves Case management, formal Reading details,
evidence requests and mechanism-candidate comparison without placing the
narrator inside that drawer. Reference Cases already have a real branch
Reading summary and 4/6-column stage, but their full mutable evidence drawer
is visibly withheld until a Case-bound projection replaces the Owner-only Home
contract. Closing the narration layer explicitly pauses and releases its
captured audio element; reduced-motion clients use the Registry poster rather
than a moving character delivery.

The 3D renderer consumes only stable `column_ref`, `body_ref`, `relation_ref`
and the bounded Director frame. Its admitted semantic actions are:

```text
PILLARS_PRESENT
RELATIONS_PRESENT
BOUNDARY_HOLD
TIME_COORDINATES_PRESENT
```

Relation paths are neutral arcs between exact branch members. Bodies do not
aggregate, collide, morph into “合”, grow a usable-root channel or perform an
effect animation. `PAUSED` and `BUFFERING` freeze semantic motion at the exact
audio time; a separate non-semantic ambient clock may continue only when the
Director permits it. WebGL2 failure or context loss falls back to the existing
bounded 2D stage without changing the Projection.

The actor layer now supports Abu and Dodo media independently through the
Hash-locked Runtime Media Registry `.004`; the browser does not own their
paths. It reports its current fidelity as
`IDLE_MEDIA_WITH_AUDIO_BOUND_STATE`: the transparent video
instance follows READY/PLAYING/PAUSED/BUFFERING, but the current assets are not
claimed as phoneme lip-sync, gaze direction or final Cue choreography.

## Persistence and ownership

Migration `0026_mingli_narration_assets` adds the account-scoped, append-only
`media.mingli_narration_assets` ledger. Migration
`0027_mingli_narration_v2` advances Foundation to `.019` and pins Stage `.002`,
Timing `.002` and Narration `.002`. The ledger stores exact Projection, script,
voice, provider deployment, audio and cue identities plus the validated mono
24 kHz 16-bit PCM WAV. Historical Narration `.001` rows remain readable and
immutable.

The Timing upgrade also preserves historical Dream Episode truth. Seed replay
may recover an Episode's already-admitted Timing `.001` and derived Life-domain
Refs only after validating the persisted contract, question, organ, resolution
rule and admission-manifest Hashes; the recovered package then passes the same
normal Story lineage and admission checks. New Mingli projections continue to
use Timing `.002`.

Media owns TTS generation and this schema write. Mingli owns the chart, stage
Projection and narration script facts. Architecture tests now include Media
in the unique-writer audit so a future Mingli service cannot write the Media
schema directly.

Current executable identities are:

```text
Foundation       v60.foundation.032
Architecture     v60.runtime-architecture.072
Mingli Engine    v60.mingli-cognitive-engine.043
Media            v60.media-library.005
Runtime Media    v60.runtime-media-registry.006
Unit Mingli      v60.unit-mingli.033
Unit Abu Says    v60.unit-abu-says.008
Stage            v60.mingli-stage-projection.004
Timing           v60.mingli-timing-evidence-vector.002
Narration        v60.mingli-narration.002
Migration        0040_mingli_model_field_contract
```

## Real evidence

The real public TTS service generated a new Dylan six-pillar asset:

```text
narration_ref       v60-mingli-narration-63140c06781936faa540
voice_profile_ref   v60.voice-profile.abu-dylan-owner-selected.001
provider             v60.qwen3-tts-proxy.001 / dblife-public-proxy
duration             56.480 seconds
WAV bytes            2,711,084
cue boundaries       0 / 10080 / 18720 / 32160 / 56480 ms
```

The database contains three historical Narration `.001` assets (two Dylan and
one Eric audition) and the new Dylan Narration `.002` asset. This proves the
voice and contract changes appended rather than overwrote history. Assets stay
account-scoped rather than becoming a globally reusable public audio object.

The real signed-in product page verified:

- Desktop natal stage: four columns, eight bodies, no horizontal overflow;
- Desktop time layer: six columns, twelve bodies, no monthly or five-pillar
  column;
- relation endpoints remain bound to the exact two branch bodies, including
  the tall iPad portrait layout (measured vertical drift below 0.45 px there);
- in-app Chrome iPad landscape and portrait viewports: the same six/twelve
  contract with no horizontal overflow;
- PLAYING: DOM clock 1380 ms versus audio clock 1384 ms, with the STRUCTURE cue
  and matching subtitle;
- PAUSED: zero DOM-clock drift over 700 ms;
- refresh: exact synthetic Abu, six-pillar mode and 2026 selection recovered,
  narration returned to IDLE;
- browser Back/Forward restored the exact four/six-pillar route, and the
  authenticated Owner rail appeared only for an exact Case/Chart/LifeCase/
  Reading lineage match.

Screenshots and machine-readable metrics are in
`.artifacts/mingli-stage-narration/`.

The iPad checks are responsive viewport evidence in the in-app Chrome runtime,
not a claim of physical iPad Safari, touch or autoplay-policy certification.
The shared-player browser audit additionally verified:

- Reading -> Lab -> narration -> Lab kept the same Scene instance and exactly
  one Canvas;
- four pillars -> six pillars kept that instance while changing from eight to
  twelve bodies;
- a Lab relation selection retained its exact `relation_ref` and never changed
  the professional boundary;
- READY exposed one private audio element without advancing subtitles;
- PLAYING followed real `audio.currentTime`; PAUSED held both audio time and
  Scene `cueProgress` exactly constant across a 500 ms sample;
- 1440x900 Desktop, 1024x768 iPad landscape and 768x1024 iPad portrait showed
  all six columns without inspector overlap or document overflow;
- Dodo used her own transparent media source while sharing the same Director,
  audio transport and Scene Player.
- the canonical evidence drawer exposed Case management, Reading and source
  evidence at Desktop and iPad portrait sizes without adding document overflow
  or a second Canvas; closing an actively playing narration removed its audio
  node after playback had started.

Evidence is in `.artifacts/mingli-shared-scene/`. These iPad checks remain
responsive Chrome evidence, not physical iPad Safari, touch or autoplay-policy
certification. The Three renderer is isolated in a lazy chunk; the current
chunk-size warning is recorded performance debt, not proof of a second stage.

The real-profile branch integration additionally verified:

- all 20 authorized V50 Owner-corpus profiles were already present in V60 as
  one `HUMAN_OWNER` and 19 `HUMAN_REFERENCE` Cases; the UI now exposes them
  without duplicating migration lineage;
- all 20 Stage and Reading-summary projections match on Case, Chart, LifeCase,
  Reading Ref and Reading Hash, and all 20 produce four natal columns or six
  time-layer columns with twelve bodies;
- the frozen V108 day/night growth films are byte-identical, 1612×974,
  24 fps and 7.208333 seconds, with the same four organ hotspots;
- `命局原理` uses the formal bounded Reading, `生命意象` remains an explicit
  unadmitted gap, `人生主题` uses the three real life-domain windows, and
  `时间趋势` exposes only deterministic coordinates and admitted relation
  membership;
- refresh restores the final static branch and exact layer; closing replaces
  the leaf-route history entry so browser Back/Forward cannot reopen a closed
  branch; and reference pages cannot expose or mutate the Owner evidence
  drawer.

Evidence is in `.artifacts/real-profile-mingli-branch/`.

## Design handoff and next constraint

The frozen V108 source at commit
`a6cf762684e14514f58c8f45b82cca86d9a7ec4c` is available and remains the
experience authority. This slice extracted its particle-stage and transparent
actor language. The active Home and profile-leaf branch now preserve the V108
scene plane, day/night growth film, organ positions, opening/closing timing and
companion placement while replacing mock conclusions with V60 Case-bound
projections. The formal product also improves one prototype limitation: V108
Lab and Abu Says each mounted a separate Canvas, whereas the formal product
keeps one shared Scene Player. Remaining fidelity work concerns future Dream
and scene-specific narration design, not a second Mingli entry or replacement
UI framework.

```text
DESIGN_REQUEST
- scene: Mingli Reading / Lab / Abu Says shared six-pillar stage
- source_files: frozen V108 MingliStage3D, MingliStageLabPreview, AbuSays
- observed_behavior: one real Canvas now survives all three surfaces; current
  Abu/Dodo media prove audio-bound state but not final speaking choreography
- design_question: provide the final single-player Desktop Chrome composition,
  six-column spacing and Abu/Dodo listening/speaking/paused/attention states;
  leave iPad book composition for its separate design round
- current_assumption: Reading and Lab reserve space around the same stage;
  narration expands that stage without remounting it
- implementation_constraint: audio.currentTime is the sole semantic clock;
  only coordinates, admitted relation members and evidence holds may animate
- options: refine V108 into a true one-player prototype, or provide annotated
  states/assets that can be applied directly to the current shared Host
- recommendation: prototype the real one-player transition and deliver the
  minimum controllable actor-state assets; do not add a second Canvas
- owner_decision_required: NO, unless the design requests a semantic relation
  action beyond the currently admitted evidence boundary
```

The remaining Mingli blocker is professional, not audiovisual. The Stage now
also renders sealed synthetic research Cases through the same Player without
placing `research:*` identities in the ordinary profile list. Method discovery
no longer stays on one Owner Case: the first legal A/B pair and minimum
anti-follow root rule are recorded in
[`20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md`](20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md).
Desktop Chrome is the active first-round target; the older responsive iPad
checks above remain historical evidence, not a current iPad portrait product
commitment.

The current-layer rehearsal browser audit additionally verified:

- principle rehearsal showed three admitted chapters and translated the Day
  Master title to `日主偏弱` rather than exposing `WEAK`;
- timing rehearsal restored a six-column/twelve-body stage with current Dayun
  and 2026 annual coordinates, while no unbound Dayun/annual prose was attached
  to those columns;
- there was no audio element, playback state or narration generation request;
- refresh, Back and Forward retained the exact Case, layer and rehearsal mode;
- close returned to Reading observation, ordinary stage entry stayed on
  Reading, and the explicit Lab action alone entered `view=lab`.
