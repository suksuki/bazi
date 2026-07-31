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
-> four-pillar natal stage
-> six-pillar time layer
-> server-locked Abu narration
-> audio-clocked subtitles and deterministic stage emphasis
```

Dream, the ten-tree loop, multi-NPC scenes, the question bank and mobile are
not part of this slice.

## Owner decisions now in the executable baseline

- There is no directed invitation. The Mingli entry remains the profile leaf
  on the Home LifeTree.
- The default stage is the complete natal four pillars.
- Expanding time shows exactly natal four pillars plus current Dayun plus the
  selected annual pillar. A five-pillar state is invalid.
- The first layout targets Desktop and iPad. Mobile remains a separate visual
  design problem.
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

1. the authenticated account's active `HUMAN_OWNER` Case; and
2. the two explicitly admitted `CANONICAL_SYNTHETIC` character Cases.

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
PREPARING -> READY -> PLAYING <-> PAUSED -> ENDED
```

While PREPARING, semantic subtitles and motion do not run. During PLAYING,
`HTMLAudioElement.currentTime` is the sole subtitle, cue and deterministic
stage-emphasis clock. PAUSED freezes the same clock. Refresh preserves the selected Case,
four/six-pillar mode and year through the URL, while narration returns to
`IDLE`; it never pretends to recover an in-flight audio position.

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
Foundation       v60.foundation.019
Architecture     v60.runtime-architecture.053
Mingli Engine    v60.mingli-cognitive-engine.026
Media            v60.media-library.003
Unit Mingli      v60.unit-mingli.020
Stage            v60.mingli-stage-projection.002
Timing           v60.mingli-timing-evidence-vector.002
Narration        v60.mingli-narration.002
Migration        0027_mingli_narration_v2
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
The current semantic cue output drives subtitles and stage emphasis; V108 actor
motion, mouth shapes and particle asset mappings still require the designer's
source handoff and are not claimed as delivered here.

## Design handoff and next constraint

The current V60 shell preserves its warm, restrained stage language; this
slice does not replace it with a dashboard. Exact V108 prototype-source merge
still requires the designer's source handoff. The design review should focus
on fitting this Projection and playback contract into the frozen V108 visual
baseline, not rebuilding the facts or adding another Mingli entry.

The remaining Mingli blocker is professional, not audiovisual: V60 still
lacks an Owner-reviewed complete relation-effect rule family and therefore
cannot yet resolve strength, source usability, effective work or a direct
life-domain destiny answer. The next Mingli functional slice must qualify one
complete rule chain over an authorized real Case; another page that merely
restates the same evidence gap is not progress.
