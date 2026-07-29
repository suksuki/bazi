# V60 Eastern Fairy-Tale Picture-Book Style Lock

Use this block in every Gemini visual request before the shot-specific
instructions. Shot requirements and character locks remain separate.

## Positive direction

```text
Visual identity: an Eastern fairy-tale picture-book world for AbuKnows V60.
Luminous hand-painted illustration, poetic Chinese-inspired forest space,
soft off-white daylight, restrained ink green, moss green, mist gray and
small accents of muted antique gold. The image should feel tactile and
authored: layered watercolor-and-gouache foliage, subtle paper grain,
delicate atmospheric depth, natural irregularity and calm visual breathing.

The LifeTree is an old living organism, not a decorative icon. It has a
recognizable silhouette, broad asymmetrical canopy, credible trunk weight,
branch tension, roots that visibly belong to the ground, and localized warm
light moving through real bark and leaves. Its growth must remain organic and
specific rather than symmetrical or procedural.

Magic is quiet and material: fine gold dust, dew, reflected light, ink-like
mist and minute leaf responses. It never becomes neon energy, game reward
fireworks or a generic fantasy portal.

Composition must reserve clean negative space for live V60 interface text.
Never generate readable UI text, buttons, cards, icons or diagrams inside the
video. The Runtime will render all interface and semantic content.
```

## Negative direction

```text
Avoid generic anime, chibi redesign, glossy 3D, plastic surfaces, mobile-game
fantasy, cyberpunk light, saturated xianxia spectacle, beige parchment UI,
heavy sepia grading, symmetrical clip-art trees, floating roots, decorative
gradient blobs, baked-in captions, fake interface controls, progress bars,
logos and invented symbols.

Do not morph tree branches into a chart or imply a Mingli conclusion through
color, brightness, fruit size or weather. Do not change Abu's approved face,
markings, eye proportions, scarf, body ratio or tail.
```

## Abu identity reference

New V60 Abu generation must use:

```text
media.abu.v60.character-reference.v1
character version ABU_CHARACTER_V60_V1
```

`ABU_CHARACTER_V1` is retained for historical cartoon assets and compatibility
only. It is not a visual reference for new V60 generation unless the Owner
explicitly asks for the legacy style.

## Motion direction

```text
Motion is restrained and motivated. Use one primary action per shot. Preserve
continuity of scale, lens, horizon, light direction and subject anchor. Start
and end with stable handoff frames that can match the interactive Runtime.
Leaves, mist, cloth and gold particles may lag naturally, but the world must
not rewind when a transition closes.
```

## Delivery defaults

```yaml
aspect_ratio: 16:9
preferred_source_resolution: 1920x1080_or_higher
camera: LOCKED_UNLESS_SHOT_CONTRACT_REQUIRES_MOVEMENT
embedded_text_or_ui: FORBIDDEN
source_audio: SEPARATE_STEM_PREFERRED
first_frame_reference: REQUIRED_FOR_CONTINUITY_TRANSITION
last_frame_reference: REQUIRED_FOR_RUNTIME_HANDOFF
reduced_motion_poster: REQUIRED_AT_POSTPROCESS
```
