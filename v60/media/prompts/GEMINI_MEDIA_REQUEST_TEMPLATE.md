# Gemini Media Request Template

This template is completed by Codex from a real product state before Gemini is
asked to generate anything. One prompt produces one source candidate, not a
Runtime asset.

For V60 visual requests, prepend the complete
`V60_EASTERN_FAIRY_TALE_STYLE_LOCK.md`. Character and shot constraints below
remain mandatory when the style block is used.

## Request identity

```yaml
request_ref:
target_media_id:
target_revision:
product_state:
semantic_role:
action_type: LOOP | ONE_SHOT | TRANSITION | AUDIO
character_version: ABU_CHARACTER_V60_V1 | ABU_CHARACTER_V1 | null
reference_files: []
intended_cue_bundle:
```

## Video prompt

```text
Use the attached reference as the exact character identity lock. New V60
generation defaults to `ABU_CHARACTER_V60_V1`; the legacy cartoon identity
must be requested explicitly.

CHARACTER
- Preserve Abu's large round eyes, face proportions, black/tan/cream markings,
  curled tail, red-brown scarf and full-body proportions.
- Do not redesign the face, muzzle, ears, paws, scarf or coat pattern.
- Keep the mouth closed unless the product state explicitly requires speech.

SEMANTIC ACTION
- [Describe one product action in observable physical terms.]
- The action must not imply that Abu is independently calculating or deciding
  a Mingli conclusion.
- Start pose: [exact pose].
- End pose: [exact pose].
- Loop requirement: [exact gait/idle phase, or ONE_SHOT].
- Direction and gaze: [left/right/front and target].

CAMERA AND COMPOSITION
- Locked camera, no zoom, pan, crop change or focus breathing.
- Full body remains visible with stable scale.
- Prefer 1920x1080 or higher, 24 fps and 8-10 seconds unless the request
  specifies otherwise.
- Keep the bottom-center anchor stable.
- For locomotion, animate walking in place; Runtime moves the actor container.

BACKGROUND
- Actor motion: uniform chroma green #19A61E with no floor shadow, particles,
  gradients, reflections or scenery.
- Scene transition: use the supplied first and last composition references;
  preserve the destination geometry for a seamless Runtime handoff.

NEGATIVE CONSTRAINTS
- No text, subtitles, logos or decorative UI.
- No extra characters, duplicate limbs, changing costume or changing markings.
- No unrequested horizontal travel.
- No camera movement.
- Do not add narrative facts or Mingli symbolism.

OUTPUT
- One source video with the requested duration and frame rate.
- Platform corner marks are tolerated only inside the declared postprocess-safe
  region; they are not part of the approved artwork.
```

## Audio prompt

```text
Create one audio source for [product state and emotional function].

- Duration: [seconds].
- Structure: [opening / sustain / handoff / ending].
- Instrument and texture boundaries: [list].
- Emotional range: restrained, companionable and non-judgmental.
- No spoken words unless a separately approved voice script is attached.
- No success/failure sting that could leak a sealed result.
- No ominous disaster language or reward-game fanfare.
- Leave headroom for narration and accessibility cues.
- Deliver the cleanest available lossless or highest-quality source.
```

## Acceptance checklist

```yaml
character_lock:
motion_semantics:
camera_lock:
background_or_scene_handoff:
first_last_or_transition_handoff:
audio_content_boundary:
technical_format:
source_status:
```

The source is archived before any crop, key, audio removal, stabilization,
loop repair or mastering is performed.
