# V60 Gemini Audio Prompts V1

Generate every cue as a separate dry source. Preferred delivery is
uncompressed WAV, 48 kHz, 24-bit, stereo. No narration is included.

## Shared audio lock

```text
Create restrained sound for an Eastern fairy-tale picture-book world. Use
organic, tactile sources: soft leaf movement, paper fibers, dew, wood
resonance, distant air and very sparse bell-like overtones. Leave generous
headroom for Abu narration and accessibility cues.

No lyrics, spoken words, animal vocalization, strong melody, pop rhythm,
cinematic boom, bass drop, horror tension, xianxia spectacle, game reward
fanfare, success/failure sting or result-signaling harmony. Do not encode a
positive or negative answer in pitch, brightness, rhythm or intensity.
```

## V60_AUDIO_01_TREE_RESONANCE_LOOP_V1

```text
Duration 8 seconds, seamless ambience loop. Begin with nearly inaudible grove
air, add one layer of delicate leaves and a very low, warm wooden resonance
that feels as if it belongs inside an old living tree. Include at most one
very distant dew-like overtone. The loop boundary must preserve ambience phase
without a swell, impact or fade to silence. Calm, spacious, non-melodic.
```

## V60_AUDIO_02_FLOWER_OPEN_ONCE_V1

```text
Duration 3 seconds, one-shot. A small flower unfolds through soft handmade
paper fibers and a barely audible fresh-leaf movement. Add one tiny dew chime
near the midpoint, then return naturally to silence. It means availability,
not correctness or reward. No sparkle cascade and no tonal resolution.
```

## V60_AUDIO_03_FRUIT_SET_ONCE_V1

```text
Duration 3 seconds, one-shot. Fine paper fibers gather inward around one point,
supported by a muted wooden body resonance and a soft settling breath. The
sound ends closed and neutral. It means an answer collection has been sealed,
not that a result is known. No celebratory bell, lock click or success chord.
```

## V60_AUDIO_04_FRUIT_OPEN_ONCE_V1

```text
Duration 4 seconds, one-shot. A thin layered paper shell separates naturally,
followed by a sparse dispersal of fine dry gold dust and one quiet wooden
after-resonance. Leave the final 1.2 seconds open for Runtime narration. The
cue must sound identical for every result class and must not resolve into a
happy, sad or triumphant chord.
```

## Acceptance

```yaml
sample_rate: 48000
preferred_bit_depth: 24
voice: none
result_leakage: none
normalization: leave_headroom
runtime_pairing: assigned_only_after_owner_review
```
